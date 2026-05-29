# jambu-air

Scraper otomatis untuk mengambil data postingan dari **TikTok** dan **Threads** berdasarkan keyword pencarian, kemudian mengirimkan hasilnya ke backend API dalam format JSON.

## Fitur

- Scraping search result TikTok dan Threads secara paralel
- Ekstraksi data lengkap: caption, like, comment, repost, share, timestamp, hashtag
- Intercept API response internal platform (lebih akurat dari DOM parsing)
- Auto-dismiss login popup dan captcha
- Kirim hasil ke backend API via HTTP POST
- Simpan output ke file JSON lokal (opsional)
- CLI dengan pilihan platform dan keyword
- GitHub Actions: scheduled harian + manual trigger

---

## Struktur Proyek

```
jambu-air/
├── scrapers/
│   ├── __init__.py
│   ├── tiktok.py         # Scraper TikTok
│   └── threads.py        # Scraper Threads
├── models.py             # Dataclass TikTokPost, ThreadsPost, ScrapeResult
├── config.py             # Konfigurasi dari environment variable
├── sender.py             # Kirim JSON payload ke API
├── main.py               # Entry point CLI
├── debug_inspect.py      # Script debug inspect HTML & selector
├── requirements.txt
├── .env.example
└── .github/
    └── workflows/
        └── scraper.yml   # GitHub Actions workflow
```

---

## Instalasi

### Prasyarat

- Python 3.11+
- pip

### Setup

```bash
# Clone repository
git clone https://github.com/damarmustikoaji/jambu-air.git
cd jambu-air

# Buat virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Install browser Chromium untuk Playwright
playwright install chromium
```

### Konfigurasi

```bash
cp .env.example .env
```

Edit file `.env`:

```env
# Keyword pencarian default
SEARCH_QUERY=automation

# Platform aktif
TIKTOK_ENABLED=true
THREADS_ENABLED=true

# Batas hasil per platform
TIKTOK_MAX_RESULTS=20
THREADS_MAX_RESULTS=20

# Browser (false = tampilkan browser, true = background)
HEADLESS=true
SLOW_MO=500

# Cookies login (opsional, untuk bypass bot detection)
TIKTOK_COOKIES_FILE=
THREADS_COOKIES_FILE=

# API tujuan pengiriman data
API_URL=https://your-backend.com/api/scrape
API_KEY=your-api-key
API_TIMEOUT=30
```

---

## Cara Penggunaan

### Jalankan Lokal

```bash
# Aktifkan virtual environment dulu
source venv/bin/activate

# Scrape kedua platform (default)
python main.py

# Scrape dengan keyword tertentu
python main.py --query "AI tools"

# Pilih platform tertentu
python main.py --platform tiktok
python main.py --platform threads
python main.py --platform tiktok threads

# Dry run (scrape tapi tidak kirim ke API)
python main.py --dry-run

# Simpan hasil ke file JSON lokal
python main.py --save

# Kombinasi: dry run + simpan file + keyword custom
python main.py --platform threads --query "automation test" --dry-run --save
```

### Opsi CLI

| Flag | Shorthand | Default | Keterangan |
|---|---|---|---|
| `--query` | `-q` | dari `SEARCH_QUERY` env | Keyword pencarian |
| `--platform` | `-p` | `tiktok threads` | Platform: `tiktok`, `threads`, atau keduanya |
| `--dry-run` | — | false | Scrape tanpa kirim ke API |
| `--save` | — | false | Simpan hasil ke file `output_*.json` |

---

## Format Output JSON

```json
{
  "query": "automation",
  "scraped_at": "2026-05-29T03:00:00+00:00",
  "results": {
    "tiktok": [
      {
        "platform": "tiktok",
        "post_id": "7380123456789",
        "username": "john.doe",
        "display_name": "John Doe",
        "caption": "This is my automation workflow #automation #AI",
        "like_count": 12500,
        "comment_count": 340,
        "share_count": 89,
        "view_count": 250000,
        "video_url": "https://...",
        "thumbnail_url": "https://...",
        "post_url": "https://www.tiktok.com/@john.doe/video/7380123456789",
        "timestamp": "2026-05-20T10:30:00+00:00",
        "hashtags": ["automation", "AI"]
      }
    ],
    "threads": [
      {
        "platform": "threads",
        "post_id": "DYdBUaJEoUk",
        "username": "jane.smith",
        "display_name": "jane.smith",
        "caption": "Looking for QA automation engineers!",
        "like_count": 49,
        "reply_count": 7,
        "repost_count": 4,
        "share_count": 2,
        "post_url": "https://www.threads.com/@jane.smith/post/DYdBUaJEoUk",
        "timestamp": "2026-05-17T20:37:39+00:00",
        "media_urls": [],
        "hashtags": []
      }
    ]
  },
  "summary": {
    "tiktok_count": 20,
    "threads_count": 7,
    "total_count": 27
  }
}
```

---

## GitHub Actions

### Setup Secrets & Variables

Masuk ke **repo → Settings → Secrets and variables → Actions**:

**Variables** (tidak sensitif, tampil di log):

| Name | Contoh | Keterangan |
|---|---|---|
| `SEARCH_QUERY` | `automation sdet` | Keyword default untuk scheduled run |
| `API_URL` | `https://api.example.com/scrape` | Endpoint API tujuan |

**Secrets** (sensitif, disembunyikan di log):

| Name | Keterangan |
|---|---|
| `API_KEY` | Bearer token untuk API (kosongkan jika tidak perlu auth) |

### Scheduled Run

Workflow berjalan otomatis setiap hari **jam 20:00 WIB (13:00 UTC)**, scrape kedua platform dengan keyword dari `SEARCH_QUERY` variable.

Untuk ubah jadwal, edit `cron` di [`.github/workflows/scraper.yml`](.github/workflows/scraper.yml):

```yaml
schedule:
  - cron: "0 13 * * *"  # 20:00 WIB = 13:00 UTC
```

### Manual Trigger

1. Buka tab **Actions** di repository
2. Pilih workflow **Social Media Scraper**
3. Klik **Run workflow**
4. Isi form:
   - **Platform**: `tiktok threads` / `tiktok` / `threads`
   - **Query**: keyword pencarian (kosongkan = pakai `SEARCH_QUERY` variable)
5. Klik **Run workflow**

Hasil (JSON + screenshot debug) tersedia sebagai **artifact** yang bisa didownload di halaman run, tersimpan selama 7 hari.

---

## Debug

### Inspect Selector Halaman

Jika scraper mengembalikan 0 hasil, jalankan script debug untuk melihat kondisi browser:

```bash
python debug_inspect.py
```

Script ini akan membuka browser (tidak headless), screenshot halaman, dan mencoba berbagai selector untuk membantu identifikasi perubahan UI platform.

### Screenshot Otomatis

Setiap run menyimpan screenshot per langkah di folder `screenshots/`:

| File | Keterangan |
|---|---|
| `tiktok_01_homepage.png` | Homepage TikTok setelah load |
| `tiktok_02_search_loaded.png` | Halaman search setelah navigasi |
| `tiktok_02_after_modal_dismiss.png` | Setelah dismiss popup/captcha |
| `tiktok_03_content_wait.png` | Setelah tunggu konten render |
| `tiktok_04_after_scroll.png` | Setelah scroll |
| `threads_01_homepage.png` | Homepage Threads |
| `threads_02_search_loaded.png` | Halaman search Threads |
| `threads_03_after_scroll.png` | Setelah scroll |

### Cookies Login (Bypass Bot Detection)

TikTok menerapkan bot detection ketat. Solusi paling andal adalah menggunakan cookies dari browser yang sudah login:

1. Login TikTok/Threads di Chrome
2. Install extension **Cookie-Editor**
3. Buka halaman platform → klik extension → **Export as JSON**
4. Simpan file sebagai `tiktok_cookies.json` atau `threads_cookies.json`
5. Set path di `.env`:
   ```env
   TIKTOK_COOKIES_FILE=tiktok_cookies.json
   ```

Untuk GitHub Actions, encode cookies ke base64 dan simpan sebagai secret:
```bash
base64 -i tiktok_cookies.json | tr -d '\n'
```
Tambahkan secret `TIKTOK_COOKIES_B64`, lalu decode di workflow sebelum run:
```yaml
- name: Decode cookies
  run: echo "${{ secrets.TIKTOK_COOKIES_B64 }}" | base64 -d > tiktok_cookies.json
```

---

## Catatan

- Selector HTML platform dapat berubah sewaktu-waktu. Jika scraper tiba-tiba 0 hasil, cek dengan `debug_inspect.py`
- TikTok membatasi pencarian tanpa login — hasil mungkin terbatas tanpa cookies
- Threads menampilkan login popup yang perlu di-dismiss sebelum scraping
- Gunakan `SLOW_MO=1000` atau lebih tinggi di CI untuk stabilitas
