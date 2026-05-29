"""
Helper untuk export cookies ke base64 (untuk disimpan di GitHub Secrets).

Usage:
  python export_cookies.py            # export semua platform
  python export_cookies.py --platform tiktok
  python export_cookies.py --platform threads
"""
import argparse
import base64
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def export_cookies(platform: str):
    if platform == "tiktok":
        cookies_file = os.getenv("TIKTOK_COOKIES_FILE", "cookies/tiktok_cookies.json")
        secret_name = "TIKTOK_COOKIES_B64"
    else:
        cookies_file = os.getenv("THREADS_COOKIES_FILE", "cookies/threads_cookies.json")
        secret_name = "THREADS_COOKIES_B64"

    path = Path(cookies_file)
    if not path.exists():
        print(f"[{platform}] File tidak ditemukan: {cookies_file}")
        print(f"[{platform}] Jalankan 'python login.py --platform {platform}' dulu")
        return

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")

    print(f"\n{'='*60}")
    print(f"GitHub Secret untuk {platform.upper()}")
    print(f"{'='*60}")
    print(f"Name : {secret_name}")
    print(f"Value:")
    print(encoded)
    print(f"{'='*60}")
    print(f"Copy value di atas ke:")
    print(f"repo → Settings → Secrets and variables → Actions → New secret")
    print(f"Name: {secret_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", "-p", choices=["tiktok", "threads"], default=None)
    args = parser.parse_args()

    platforms = [args.platform] if args.platform else ["tiktok", "threads"]
    for p in platforms:
        export_cookies(p)


if __name__ == "__main__":
    main()
