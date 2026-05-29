import json
import os
import re
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright, Page

from models import TikTokPost
from config import config


def _parse_count(text) -> int:
    if not text:
        return 0
    if isinstance(text, (int, float)):
        return int(text)
    text = str(text).strip().upper().replace(",", "")
    try:
        if text.endswith("K"):
            return int(float(text[:-1]) * 1_000)
        if text.endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        if text.endswith("B"):
            return int(float(text[:-1]) * 1_000_000_000)
        return int(text)
    except (ValueError, AttributeError):
        return 0


def _extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#(\w+)", text or "")


async def _load_cookies(page: Page, cookies_file: str):
    path = Path(cookies_file)
    if path.exists():
        cookies = json.loads(path.read_text())
        await page.context.add_cookies(cookies)


def _parse_item_from_api(item: dict) -> TikTokPost | None:
    """Parse satu item dari response JSON internal API TikTok."""
    try:
        video = item.get("video") or {}
        author = item.get("author") or {}
        stats = item.get("stats") or {}
        desc = item.get("desc", "")

        post_id = item.get("id", "")
        if not post_id:
            return None

        username = author.get("uniqueId", "")
        post_url = f"https://www.tiktok.com/@{username}/video/{post_id}"

        create_time = item.get("createTime")
        timestamp = (
            datetime.fromtimestamp(int(create_time), tz=timezone.utc)
            if create_time
            else None
        )

        return TikTokPost(
            post_id=post_id,
            username=username,
            display_name=author.get("nickname", username),
            caption=desc,
            like_count=_parse_count(stats.get("diggCount", 0)),
            comment_count=_parse_count(stats.get("commentCount", 0)),
            share_count=_parse_count(stats.get("shareCount", 0)),
            view_count=_parse_count(stats.get("playCount", 0)),
            video_url=video.get("playAddr") or video.get("downloadAddr"),
            thumbnail_url=video.get("cover") or video.get("dynamicCover"),
            post_url=post_url,
            timestamp=timestamp,
            hashtags=_extract_hashtags(desc),
        )
    except Exception as e:
        print(f"[TikTok] Error parse API item: {e}")
        return None


async def _parse_item_from_dom(item) -> TikTokPost | None:
    """Fallback: parse dari DOM jika API intercept tidak dapat data."""
    try:
        link_el = await item.query_selector("a[href*='/video/']")
        post_url = await link_el.get_attribute("href") if link_el else ""
        if not post_url:
            return None
        if not post_url.startswith("http"):
            post_url = f"https://www.tiktok.com{post_url}"

        match = re.search(r"/video/(\d+)", post_url)
        post_id = match.group(1) if match else post_url.split("/")[-1]

        # Username dari href profil
        user_link = await item.query_selector("a[href*='/@']")
        username = ""
        if user_link:
            href = await user_link.get_attribute("href")
            m = re.search(r"/@([^/?]+)", href or "")
            username = m.group(1) if m else ""

        # Caption
        caption_el = await item.query_selector('[data-e2e="search-card-video-caption"]')
        caption = (await caption_el.inner_text()).strip() if caption_el else ""

        # Like count — cari angka di samping ikon hati
        like_el = await item.query_selector('[data-e2e="video-card-like-count"]')
        like_count = _parse_count(await like_el.inner_text() if like_el else "0")

        img_el = await item.query_selector("img")
        thumbnail_url = await img_el.get_attribute("src") if img_el else None

        return TikTokPost(
            post_id=post_id,
            username=username,
            display_name=username,
            caption=caption,
            like_count=like_count,
            comment_count=0,
            share_count=0,
            view_count=0,
            video_url=None,
            thumbnail_url=thumbnail_url,
            post_url=post_url,
            timestamp=None,
            hashtags=_extract_hashtags(caption),
        )
    except Exception as e:
        print(f"[TikTok] Error parse DOM item: {e}")
        return None


async def scrape_tiktok(query: str) -> list[TikTokPost]:
    posts: list[TikTokPost] = []
    captured_items: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.headless,
            slow_mo=config.slow_mo,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )

        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        page = await context.new_page()

        if config.tiktok_cookies_file:
            await _load_cookies(page, config.tiktok_cookies_file)

        # Intercept API response untuk data mentah
        async def handle_response(response):
            try:
                req_url = response.url
                if "api/search" in req_url or ("search" in req_url and "item_list" in req_url):
                    data = await response.json()
                    item_list = (
                        data.get("data", [])
                        or data.get("item_list", [])
                        or data.get("itemList", [])
                    )
                    for entry in item_list:
                        raw = entry.get("item") or entry
                        if raw.get("id"):
                            captured_items.append(raw)
                    if item_list:
                        print(f"[TikTok] Captured {len(item_list)} items dari API")
            except Exception:
                pass

        page.on("response", handle_response)

        os.makedirs("screenshots", exist_ok=True)

        # Step 1: buka homepage TikTok
        print("[TikTok] Membuka homepage tiktok.com...")
        await page.goto("https://www.tiktok.com", wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(3)
        await page.screenshot(path="screenshots/tiktok_01_homepage.png")

        # Step 2: klik tombol search (data-e2e="nav-search")
        print("[TikTok] Klik tombol search...")
        search_btn = await page.query_selector('[data-e2e="nav-search"]')
        if search_btn:
            await search_btn.click()
            await asyncio.sleep(1)
            await page.screenshot(path="screenshots/tiktok_02_search_clicked.png")
        else:
            await page.screenshot(path="screenshots/tiktok_02_no_search_btn.png")
            print("[TikTok] Tombol search tidak ditemukan, coba langsung ke URL search...")
            await page.goto(
                f"https://www.tiktok.com/search?q={query}",
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            await asyncio.sleep(3)
            await page.screenshot(path="screenshots/tiktok_02b_direct_url.png")

        # Step 3: ketik query ke input search
        print(f"[TikTok] Mengetik query: '{query}'...")
        search_input = await page.query_selector('[data-e2e="search-user-input"], input[type="search"], input[placeholder*="Search"]')
        if search_input:
            await search_input.click()
            await asyncio.sleep(0.5)
            for char in query:
                await search_input.type(char, delay=80)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
        else:
            print("[TikTok] Input search tidak ditemukan")
            await page.screenshot(path="screenshots/tiktok_03_no_input.png")

        # Step 4: tunggu hasil load
        print("[TikTok] Menunggu hasil search...")
        await asyncio.sleep(4)
        await page.screenshot(path="screenshots/tiktok_04_search_results.png")

        # Scroll untuk load lebih banyak & trigger API call
        for i in range(3):
            await page.keyboard.press("End")
            await asyncio.sleep(2)
        await page.screenshot(path="screenshots/tiktok_05_after_scroll.png")

        # Ambil data
        if captured_items:
            print(f"[TikTok] Total dari API: {len(captured_items)}, memproses maks {config.tiktok_max_results}...")
            for item in captured_items[: config.tiktok_max_results]:
                post = _parse_item_from_api(item)
                if post:
                    posts.append(post)
        else:
            # Fallback ke DOM parsing
            print("[TikTok] API intercept kosong, mencoba parse DOM...")
            grid_items = await page.query_selector_all(
                'div[class*="SearchGridLayoutContainer"] > div, '
                'div[class*="DivItemContainer"], '
                '[data-e2e="search_video-item"]'
            )
            print(f"[TikTok] DOM items ditemukan: {len(grid_items)}")
            for item in grid_items[: config.tiktok_max_results]:
                post = await _parse_item_from_dom(item)
                if post:
                    posts.append(post)

        await browser.close()

    print(f"[TikTok] Berhasil scrape {len(posts)} post")
    return posts
