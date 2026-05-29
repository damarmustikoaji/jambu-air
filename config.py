import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Search
    search_query: str = os.getenv("SEARCH_QUERY", "automation")
    tiktok_enabled: bool = os.getenv("TIKTOK_ENABLED", "true").lower() == "true"
    threads_enabled: bool = os.getenv("THREADS_ENABLED", "true").lower() == "true"

    # Scraping limits
    tiktok_max_results: int = int(os.getenv("TIKTOK_MAX_RESULTS", "20"))
    threads_max_results: int = int(os.getenv("THREADS_MAX_RESULTS", "20"))
    tiktok_scroll_count: int = int(os.getenv("TIKTOK_SCROLL_COUNT", "6"))

    # Browser
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"
    slow_mo: int = int(os.getenv("SLOW_MO", "500"))  # ms delay antar aksi browser

    # Credentials (opsional, untuk platform yang butuh login)
    tiktok_cookies_file: str = os.getenv("TIKTOK_COOKIES_FILE", "")
    threads_cookies_file: str = os.getenv("THREADS_COOKIES_FILE", "")

    # API destination
    api_url: str = os.getenv("API_URL", "")
    api_key: str = os.getenv("API_KEY", "")
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))

    def validate(self):
        if not self.api_url:
            raise ValueError("API_URL harus diset di .env atau environment variable")
        if not self.search_query:
            raise ValueError("SEARCH_QUERY harus diset")


config = Config()
