"""
Script debug: buka halaman, screenshot, dan dump HTML untuk cari selector yang benar.
Jalankan: python debug_inspect.py
"""
import asyncio
from playwright.async_api import async_playwright


async def inspect(platform: str, url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        print(f"\n[{platform}] Membuka {url}")
        await page.goto(url, wait_until="networkidle", timeout=60_000)
        await asyncio.sleep(3)

        # Scroll sekali
        await page.keyboard.press("End")
        await asyncio.sleep(2)

        # Screenshot
        screenshot_file = f"debug_{platform}.png"
        await page.screenshot(path=screenshot_file, full_page=False)
        print(f"[{platform}] Screenshot disimpan: {screenshot_file}")

        # Cek beberapa selector umum dan cetak hasilnya
        selectors_to_try = {
            "tiktok": [
                '[data-e2e="search_video-item"]',
                '[data-e2e="search-item-container"]',
                'div[class*="DivItemContainer"]',
                'div[class*="search"] article',
                "article",
                '[class*="video-feed-item"]',
            ],
            "threads": [
                "article",
                '[data-pressable-container]',
                'div[role="article"]',
                '[class*="post"]',
                'div[class*="x1yztbdb"]',
            ],
        }

        for selector in selectors_to_try.get(platform, []):
            count = await page.locator(selector).count()
            print(f"  Selector '{selector}': {count} item")

        # Dump 3000 karakter pertama body HTML untuk analisis
        html = await page.inner_html("body")
        html_file = f"debug_{platform}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[{platform}] HTML body disimpan: {html_file}")

        input(f"\n[{platform}] Tekan Enter untuk tutup browser dan lanjut...")
        await browser.close()


async def main():
    await inspect("tiktok", "https://www.tiktok.com/search?q=automation")
    await inspect("threads", "https://www.threads.com/search?q=automation")


if __name__ == "__main__":
    asyncio.run(main())
