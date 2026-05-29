"""
Script login sekali untuk generate cookies.
Cookies disimpan ke file dan dipakai oleh scraper.

Usage:
  python login.py --platform tiktok
  python login.py --platform threads
  python login.py --platform tiktok threads
"""
import asyncio
import argparse
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()


async def login_tiktok(headless: bool = False):
    username = os.getenv("TIKTOK_USERNAME", "")
    password = os.getenv("TIKTOK_PASSWORD", "")
    cookies_file = os.getenv("TIKTOK_COOKIES_FILE", "cookies/tiktok_cookies.json")

    if not username or not password:
        print("[TikTok] TIKTOK_USERNAME dan TIKTOK_PASSWORD harus diset di .env")
        return False

    print(f"[TikTok] Login sebagai '{username}'...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=500)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # Buka halaman login email/username
        await page.goto(
            "https://www.tiktok.com/login/phone-or-email/email",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        await asyncio.sleep(3)

        # Isi username
        username_input = await page.query_selector('input[name="username"], input[placeholder*="Email"]')
        if not username_input:
            print("[TikTok] Input username tidak ditemukan")
            await browser.close()
            return False

        await username_input.click()
        await username_input.fill(username)
        await asyncio.sleep(1)

        # Isi password
        password_input = await page.query_selector('input[type="password"]')
        if not password_input:
            print("[TikTok] Input password tidak ditemukan")
            await browser.close()
            return False

        await password_input.click()
        await password_input.fill(password)
        await asyncio.sleep(1)

        # Klik tombol login
        login_btn = await page.query_selector('button[data-e2e="login-button"], button[type="submit"]')
        if login_btn:
            await login_btn.click()
        else:
            await page.keyboard.press("Enter")

        print("[TikTok] Menunggu login selesai (maks 30 detik)...")
        print("[TikTok] Jika ada captcha/verifikasi, selesaikan manual di browser...")

        # Tunggu redirect ke homepage setelah login berhasil
        try:
            await page.wait_for_url("https://www.tiktok.com/", timeout=30_000)
            print("[TikTok] Login berhasil!")
        except Exception:
            # Cek manual apakah sudah login
            current_url = page.url
            print(f"[TikTok] URL saat ini: {current_url}")
            if "login" in current_url:
                input("[TikTok] Selesaikan login manual di browser, lalu tekan Enter di sini...")

        # Simpan cookies
        cookies = await context.cookies()
        Path(cookies_file).parent.mkdir(parents=True, exist_ok=True)
        with open(cookies_file, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"[TikTok] Cookies disimpan ke {cookies_file} ({len(cookies)} cookies)")

        await browser.close()
        return True


async def login_threads(headless: bool = False):
    username = os.getenv("THREADS_USERNAME", "")
    password = os.getenv("THREADS_PASSWORD", "")
    cookies_file = os.getenv("THREADS_COOKIES_FILE", "cookies/threads_cookies.json")

    if not username or not password:
        print("[Threads] THREADS_USERNAME dan THREADS_PASSWORD harus diset di .env")
        return False

    print(f"[Threads] Login sebagai '{username}'...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=500)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        await page.goto("https://www.threads.com/login", wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(3)

        # Isi username
        username_input = await page.query_selector(
            'input[placeholder*="Username"], input[placeholder*="username"], input[autocomplete="username"]'
        )
        if not username_input:
            print("[Threads] Input username tidak ditemukan")
            await browser.close()
            return False

        await username_input.click()
        await username_input.fill(username)
        await asyncio.sleep(1)

        # Isi password
        password_input = await page.query_selector('input[type="password"]')
        if not password_input:
            print("[Threads] Input password tidak ditemukan")
            await browser.close()
            return False

        await password_input.click()
        await password_input.fill(password)
        await asyncio.sleep(1)

        # Submit form — coba beberapa cara
        submitted = False

        # Cara 1: klik via JS langsung (bypass visibility check)
        try:
            await page.evaluate("""() => {
                const btn = document.querySelector('input[type="submit"]');
                if (btn) { btn.click(); return true; }
                const divBtn = Array.from(document.querySelectorAll('div[role="button"]'))
                    .find(el => el.innerText.trim().toLowerCase() === 'log in');
                if (divBtn) { divBtn.click(); return true; }
                return false;
            }""")
            submitted = True
            print("[Threads] Submit via JS click")
        except Exception:
            pass

        if not submitted:
            await page.keyboard.press("Enter")
            print("[Threads] Submit via Enter key")

        print("[Threads] Menunggu login selesai (maks 30 detik)...")
        print("[Threads] Jika ada verifikasi 2FA, selesaikan manual di browser...")

        # Tunggu redirect ke home setelah login
        try:
            await page.wait_for_url("https://www.threads.com/", timeout=30_000)
            print("[Threads] Login berhasil!")
        except Exception:
            current_url = page.url
            print(f"[Threads] URL saat ini: {current_url}")
            if "login" in current_url:
                input("[Threads] Selesaikan login manual di browser, lalu tekan Enter di sini...")

        # Simpan cookies
        cookies = await context.cookies()
        Path(cookies_file).parent.mkdir(parents=True, exist_ok=True)
        with open(cookies_file, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"[Threads] Cookies disimpan ke {cookies_file} ({len(cookies)} cookies)")

        await browser.close()
        return True


async def main(platforms: list[str], headless: bool):
    for platform in platforms:
        if platform == "tiktok":
            await login_tiktok(headless=headless)
        elif platform == "threads":
            await login_threads(headless=headless)
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Login dan simpan cookies untuk scraper")
    parser.add_argument(
        "--platform", "-p",
        nargs="+",
        choices=["tiktok", "threads"],
        default=["tiktok", "threads"],
        metavar="PLATFORM",
        help="Platform yang di-login (default: keduanya)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Jalankan browser tanpa tampilan (tidak direkomendasikan untuk login)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.platform, args.headless))
