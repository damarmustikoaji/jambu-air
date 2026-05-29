import asyncio
import argparse
from datetime import datetime, timezone

from config import config
from models import ScrapeResult
from scrapers import scrape_tiktok, scrape_threads
from sender import send_to_api, save_to_file


async def run(query: str, platforms: list[str], save_output: bool = False, dry_run: bool = False):
    run_tiktok = "tiktok" in platforms and config.tiktok_enabled
    run_threads = "threads" in platforms and config.threads_enabled

    print(f"{'='*50}")
    print(f"Scraping query: '{query}'")
    print(f"TikTok: {'aktif' if run_tiktok else 'nonaktif'}")
    print(f"Threads: {'aktif' if run_threads else 'nonaktif'}")
    print(f"{'='*50}")

    result = ScrapeResult(
        query=query,
        scraped_at=datetime.now(tz=timezone.utc),
    )

    tasks = []
    if run_tiktok:
        tasks.append(("tiktok", scrape_tiktok(query)))
    if run_threads:
        tasks.append(("threads", scrape_threads(query)))

    if not tasks:
        print("Tidak ada platform yang aktif. Set TIKTOK_ENABLED atau THREADS_ENABLED=true")
        return

    scrape_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    for (platform, _), scrape_result in zip(tasks, scrape_results):
        if isinstance(scrape_result, Exception):
            print(f"[{platform.upper()}] Gagal: {scrape_result}")
            continue
        if platform == "tiktok":
            result.tiktok_posts = scrape_result
        elif platform == "threads":
            result.threads_posts = scrape_result

    print(f"\nTotal hasil: {len(result.tiktok_posts)} TikTok, {len(result.threads_posts)} Threads")

    if save_output:
        output_file = f"output_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_to_file(result, output_file)

    if dry_run:
        print("[Dry Run] Skip pengiriman ke API")
        return

    if not config.api_url:
        print("API_URL tidak diset, melewati pengiriman. Gunakan --save untuk menyimpan ke file.")
        return

    success = await send_to_api(result)
    if not success:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Social media scraper - TikTok & Threads")
    parser.add_argument(
        "--query", "-q",
        type=str,
        default=config.search_query,
        help="Keyword pencarian (default dari SEARCH_QUERY env)",
    )
    parser.add_argument(
        "--platform", "-p",
        nargs="+",
        choices=["tiktok", "threads"],
        default=["tiktok", "threads"],
        metavar="PLATFORM",
        help="Platform yang di-scrape: tiktok, threads, atau keduanya (default: keduanya)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Simpan hasil ke file JSON lokal",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape tapi jangan kirim ke API",
    )
    args = parser.parse_args()

    try:
        if not args.dry_run:
            config.validate()
    except ValueError as e:
        print(f"Config error: {e}")
        raise SystemExit(1)

    asyncio.run(run(args.query, platforms=args.platform, save_output=args.save, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
