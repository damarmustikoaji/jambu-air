import json
import os
import re
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page

from models import ThreadsPost
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
        return int(text)
    except (ValueError, AttributeError):
        return 0


def _extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#(\w+)", text or "")


def _parse_timestamp(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


async def _load_cookies(page: Page, cookies_file: str):
    path = Path(cookies_file)
    if path.exists():
        cookies = json.loads(path.read_text())
        await page.context.add_cookies(cookies)


def _parse_from_graphql(data: dict) -> list[ThreadsPost]:
    """Coba ekstrak post dari berbagai bentuk GraphQL response Threads."""
    posts = []
    raw_text = json.dumps(data)

    # Cari semua node yang punya post_id / text_post_app_info
    def find_posts(obj):
        if isinstance(obj, dict):
            # Node post biasanya punya 'pk' atau 'id' + 'caption'
            if obj.get("__typename") in ("XDTThreadItem", "XDTThread", "Thread"):
                posts_in_thread = obj.get("thread_items") or []
                for ti in posts_in_thread:
                    node = ti.get("post") or ti
                    p = _extract_post_node(node)
                    if p:
                        posts.append(p)
            elif obj.get("__typename") == "XDTMediaDict" or (
                obj.get("pk") and obj.get("user")
            ):
                p = _extract_post_node(obj)
                if p:
                    posts.append(p)
            for v in obj.values():
                find_posts(v)
        elif isinstance(obj, list):
            for item in obj:
                find_posts(item)

    find_posts(data)
    return posts


def _extract_post_node(node: dict) -> ThreadsPost | None:
    try:
        post_id = str(node.get("pk") or node.get("id") or "")
        if not post_id:
            return None

        user = node.get("user") or {}
        username = user.get("username", "")
        display_name = user.get("full_name", username)

        caption_data = node.get("caption") or {}
        caption = caption_data.get("text", "") if isinstance(caption_data, dict) else str(caption_data)

        like_count = node.get("like_count", 0)
        reply_count = node.get("text_post_app_info", {}).get("direct_reply_count", 0)

        taken_at = node.get("taken_at")
        timestamp = (
            datetime.fromtimestamp(int(taken_at))
            if taken_at
            else None
        )

        post_url = f"https://www.threads.com/@{username}/post/{post_id}"

        # Media
        media_urls = []
        for img in (node.get("image_versions2") or {}).get("candidates", []):
            url = img.get("url")
            if url:
                media_urls.append(url)
                break  # ambil resolusi pertama saja

        return ThreadsPost(
            post_id=post_id,
            username=username,
            display_name=display_name,
            caption=caption,
            like_count=_parse_count(like_count),
            reply_count=reply_count,
            repost_count=0,
            share_count=0,
            post_url=post_url,
            timestamp=timestamp,
            media_urls=media_urls,
            hashtags=_extract_hashtags(caption),
        )
    except Exception:
        return None


async def _parse_from_dom(page) -> list[ThreadsPost]:
    """
    Fallback DOM parsing.
    Strategi: ambil semua data post via JavaScript evaluate di page level
    tanpa navigasi — aman dari accidental click.
    """
    posts = []

    # Jalankan JS di page context untuk kumpulkan semua data post sekaligus
    raw_posts = await page.evaluate("""() => {
        const results = [];
        const seen = new Set();

        // Cari container post: utama pakai data-pagelet, fallback ke semua link /post/
        let containers = Array.from(document.querySelectorAll('[data-pagelet^="threads_search_results_"]'));

        // Fallback: jika data-pagelet tidak cukup, kumpulkan semua post link dan naik ke container
        if (containers.length < 3) {
            const allPostLinks = document.querySelectorAll('a[href*="/post/"]');
            const containerSet = new Set();
            for (const link of allPostLinks) {
                let node = link;
                for (let i = 0; i < 15; i++) {
                    node = node.parentElement;
                    if (!node) break;
                    if (node.querySelector('time')) {
                        containerSet.add(node);
                        break;
                    }
                }
            }
            containers = Array.from(containerSet);
        }

        for (const pagelet of containers) {
            try {
                // Post link untuk post_id dan username
                const postLink = pagelet.querySelector('a[href*="/post/"]');
                if (!postLink) continue;

                const href = postLink.getAttribute('href') || '';
                const m = href.match(/\\/@([^\\/]+)\\/post\\/([A-Za-z0-9_-]+)/);
                if (!m) continue;

                const username = m[1];
                const postId = m[2];
                if (seen.has(postId)) continue;
                seen.add(postId);

                // Timestamp
                const timeEl = pagelet.querySelector('time');
                const datetime = timeEl ? timeEl.getAttribute('datetime') : null;

                // Caption: ambil SEMUA span[dir=auto], pilih yang paling panjang
                // (bukan username, bukan tanggal pendek)
                let caption = '';
                const spans = pagelet.querySelectorAll('span[dir="auto"]');
                let maxLen = 0;
                for (const span of spans) {
                    // Ambil hanya teks langsung span ini, bukan children (cegah duplikasi)
                    const text = span.innerText.trim();
                    if (text.length > maxLen && text.length > 3) {
                        maxLen = text.length;
                        caption = text;
                    }
                }

                // Counts: cari semua teks angka dalam pagelet secara berurutan
                // Threads menampilkan: like | reply | repost | share
                const allText = [];
                const walker = document.createTreeWalker(
                    pagelet,
                    NodeFilter.SHOW_TEXT,
                    null
                );
                let node;
                while ((node = walker.nextNode())) {
                    const t = node.textContent.trim();
                    if (/^[0-9]+[KMB]?$/i.test(t)) {
                        allText.push(t);
                    }
                }

                // Hapus duplikat berurutan, ambil 4 pertama (like, reply, repost, share)
                const uniqueCounts = [];
                for (const t of allText) {
                    if (uniqueCounts[uniqueCounts.length - 1] !== t) {
                        uniqueCounts.push(t);
                    }
                }

                results.push({
                    post_id: postId,
                    username: username,
                    caption: caption,
                    datetime: datetime,
                    like_count: uniqueCounts[0] || '0',
                    reply_count: uniqueCounts[1] || '0',
                    repost_count: uniqueCounts[2] || '0',
                    share_count: uniqueCounts[3] || '0',
                    post_url: 'https://www.threads.com' + href,
                });
            } catch (e) {
                continue;
            }
        }

        // Fallback jika data-pagelet tidak ditemukan: gunakan time element sebagai anchor
        if (results.length === 0) {
            const links = document.querySelectorAll('a[href*="/post/"]');
            for (const link of links) {
                const href = link.getAttribute('href') || '';
                const m = href.match(/\\/@([^\\/]+)\\/post\\/([A-Za-z0-9_-]+)/);
                if (!m) continue;
                const postId = m[2];
                if (seen.has(postId)) continue;
                seen.add(postId);

                let container = link;
                for (let i = 0; i < 15; i++) {
                    container = container.parentElement;
                    if (!container) break;
                    if (container.querySelector('time')) break;
                }
                if (!container) continue;

                const timeEl = container.querySelector('time');
                const datetime = timeEl ? timeEl.getAttribute('datetime') : null;

                const spans = container.querySelectorAll('span[dir="auto"]');
                let caption = '';
                let maxLen = 0;
                for (const span of spans) {
                    const text = span.innerText.trim();
                    if (text.length > maxLen && text.length > 3) {
                        maxLen = text.length;
                        caption = text;
                    }
                }

                results.push({
                    post_id: postId,
                    username: m[1],
                    caption: caption,
                    datetime: datetime,
                    like_count: '0',
                    reply_count: '0',
                    repost_count: '0',
                    share_count: '0',
                    post_url: 'https://www.threads.com' + href,
                });
            }
        }

        return results;
    }""")

    for item in raw_posts:
        try:
            posts.append(ThreadsPost(
                post_id=item["post_id"],
                username=item["username"],
                display_name=item["username"],
                caption=item["caption"],
                like_count=_parse_count(item.get("like_count", 0)),
                reply_count=_parse_count(item.get("reply_count", 0)),
                repost_count=_parse_count(item.get("repost_count", 0)),
                share_count=_parse_count(item.get("share_count", 0)),
                post_url=item["post_url"],
                timestamp=_parse_timestamp(item.get("datetime")),
                media_urls=[],
                hashtags=_extract_hashtags(item["caption"]),
            ))
        except Exception as e:
            print(f"[Threads] Error build post dari DOM: {e}")
            continue

    return posts


async def _dismiss_popup(page, label: str = ""):
    """Cek dan tutup popup login Threads jika ada."""
    dismissed = False

    # Coba selector tombol close yang diketahui
    close_selectors = [
        'div[role="dialog"] [aria-label="Close"]',
        'div[role="dialog"] button[type="button"]',
    ]
    for sel in close_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1_500):
                await btn.click()
                dismissed = True
                print(f"[Threads] Popup ditutup via selector ({label})")
                await asyncio.sleep(1)
                break
        except Exception:
            continue

    if not dismissed:
        # Escape sebagai fallback
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.5)

        # Cek apakah popup masih ada setelah Escape
        try:
            dialog = page.locator('div[role="dialog"]').first
            if await dialog.is_visible(timeout=1_000):
                print(f"[Threads] Popup masih ada setelah Escape ({label}), coba klik luar modal")
                # Klik area di luar modal (pojok kiri atas konten)
                await page.mouse.click(100, 400)
                await asyncio.sleep(0.5)
        except Exception:
            pass


async def scrape_threads(query: str) -> list[ThreadsPost]:
    posts: list[ThreadsPost] = []
    captured_graphql: list[dict] = []

    url = f"https://www.threads.com/search?q={query}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.headless,
            slow_mo=config.slow_mo,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        page = await context.new_page()

        if config.threads_cookies_file:
            await _load_cookies(page, config.threads_cookies_file)

        # Flag: mulai capture GraphQL hanya setelah berada di halaman search
        capture_active = False

        async def handle_response(response):
            if not capture_active:
                return
            try:
                req_url = response.url
                if "graphql" in req_url or "api/graphql" in req_url:
                    data = await response.json()
                    captured_graphql.append(data)
            except Exception:
                pass

        page.on("response", handle_response)

        os.makedirs("screenshots", exist_ok=True)

        # Step 1: buka homepage (untuk bangun session, tidak capture GraphQL)
        print("[Threads] Membuka homepage threads.com...")
        await page.goto("https://www.threads.com", wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(3)
        await page.screenshot(path="screenshots/threads_01_homepage.png")
        await _dismiss_popup(page, "threads_01")

        # Step 2: navigasi ke halaman search (tanpa query dulu)
        print("[Threads] Membuka halaman search...")
        await page.goto("https://www.threads.com/search", wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(2)
        await page.screenshot(path="screenshots/threads_02_search_page.png")
        await _dismiss_popup(page, "threads_02")

        # Step 3: ketik query di input search dan Enter
        print(f"[Threads] Mengetik query: '{query}'...")
        search_input = await page.query_selector('input[type="search"], input[placeholder="Search"]')
        if search_input:
            await search_input.click()
            await asyncio.sleep(0.5)
            for char in query:
                await search_input.type(char, delay=60)
            await asyncio.sleep(1)
            await page.screenshot(path="screenshots/threads_03_typed_query.png")
            # Aktifkan capture GraphQL tepat sebelum Enter — hasil search mulai dari sini
            capture_active = True
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
        else:
            print("[Threads] Input search tidak ditemukan, fallback ke direct URL...")
            capture_active = True
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await asyncio.sleep(4)

        await page.screenshot(path="screenshots/threads_04_results_loaded.png")
        await _dismiss_popup(page, "threads_04")

        # Step 4: scroll untuk load lebih banyak konten
        for i in range(8):
            await page.keyboard.press("End")
            await asyncio.sleep(2)
            await _dismiss_popup(page, f"threads_scroll_{i}")

        await page.screenshot(path="screenshots/threads_05_after_scroll.png")

        # Log berapa pagelet yang ditemukan sebelum parse
        pagelet_count = await page.evaluate("""() => {
            const byPagelet = document.querySelectorAll('[data-pagelet^="threads_search_results_"]').length;
            const byPostLink = new Set(
                Array.from(document.querySelectorAll('a[href*="/post/"]'))
                    .map(a => a.getAttribute('href').match(/\\/post\\/([A-Za-z0-9_-]+)/)?.[1])
                    .filter(Boolean)
            ).size;
            return { byPagelet, byPostLink };
        }""")
        print(f"[Threads] Pagelet ditemukan: {pagelet_count['byPagelet']}, unique post links: {pagelet_count['byPostLink']}")

        # Parse dari GraphQL jika ada
        all_gql_posts = []
        for gql_data in captured_graphql:
            gql_posts = _parse_from_graphql(gql_data)
            all_gql_posts.extend(gql_posts)

        if all_gql_posts:
            print(f"[Threads] {len(all_gql_posts)} post dari GraphQL, memproses maks {config.threads_max_results}...")
            seen = set()
            for post in all_gql_posts:
                if post.post_id not in seen and len(posts) < config.threads_max_results:
                    seen.add(post.post_id)
                    posts.append(post)
        else:
            # Fallback ke DOM
            print("[Threads] GraphQL kosong, mencoba parse DOM...")
            dom_posts = await _parse_from_dom(page)
            print(f"[Threads] {len(dom_posts)} post dari DOM, memproses maks {config.threads_max_results}...")
            posts = dom_posts[: config.threads_max_results]

        await browser.close()

    print(f"[Threads] Berhasil scrape {len(posts)} post")
    return posts
