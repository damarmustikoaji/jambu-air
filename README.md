# jambu-air

Scraper otomatis untuk mengambil data postingan dari **TikTok** dan **Threads** berdasarkan keyword pencarian, kemudian mengirimkan hasilnya ke backend API dalam format JSON.

## Fitur

- Scraping search result TikTok dan Threads secara paralel
- Ekstraksi data lengkap: caption, like, comment, repost, share, timestamp, hashtag
- Intercept API response internal platform (lebih akurat dari DOM parsing)
- Support login dengan cookies untuk hasil lebih banyak dan menghindari bot detection
- Auto-dismiss login popup dan captcha
- Kirim hasil ke backend API via HTTP POST
- Simpan output ke file JSON lokal (opsional)
- CLI dengan pilihan platform dan keyword
- GitHub Actions: scheduled harian + manual trigger dengan cookies dari Secrets

---

## Struktur Proyek

```
jambu-air/
├── scrapers/
│   ├── __init__.py
│   ├── tiktok.py         # Scraper TikTok
│   └── threads.py        # Scraper Threads
├── cookies/              # Cookies login (di-gitignore, tidak ter-commit)
│   ├── tiktok_cookies.json
│   └── threads_cookies.json
├── screenshots/          # Screenshot debug per run (di-gitignore)
├── models.py             # Dataclass TikTokPost, ThreadsPost, ScrapeResult
├── config.py             # Konfigurasi dari environment variable
├── sender.py             # Kirim JSON payload ke API
├── main.py               # Entry point CLI scraper
├── login.py              # Script login sekali untuk generate cookies
├── export_cookies.py     # Helper encode cookies ke base64 (untuk GitHub Secrets)
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
# ============================
# Search Configuration
# ============================
SEARCH_QUERY=automation
TIKTOK_ENABLED=true
THREADS_ENABLED=true

# ============================
# Scraping Limits
# ============================
TIKTOK_MAX_RESULTS=20
THREADS_MAX_RESULTS=20

# Jumlah scroll di halaman search TikTok (lebih banyak = lebih banyak hasil)
TIKTOK_SCROLL_COUNT=6

# ============================
# Browser Settings
# ============================
HEADLESS=true      # false = tampilkan browser (berguna untuk debug)
SLOW_MO=500        # delay ms antar aksi browser

# ============================
# Cookies Login (dihasilkan oleh login.py)
# ============================
TIKTOK_COOKIES_FILE=cookies/tiktok_cookies.json
THREADS_COOKIES_FILE=cookies/threads_cookies.json

# ============================
# Login Credentials (untuk login.py saja)
# ============================
TIKTOK_USERNAME=your_tiktok_username
TIKTOK_PASSWORD=your_tiktok_password
THREADS_USERNAME=your_threads_username
THREADS_PASSWORD=your_threads_password

# ============================
# API Destination
# ============================
API_URL=https://your-backend.com/api/scrape
API_KEY=your-api-key
API_TIMEOUT=30
```

---

## Login & Cookies

Login diperlukan untuk mendapatkan hasil yang lebih banyak dan menghindari bot detection. Cookies disimpan lokal dan tidak perlu login ulang setiap scraping.

### Login Pertama Kali

```bash
# Login kedua platform sekaligus (browser akan terbuka)
python login.py

# Atau pilih per platform
python login.py --platform tiktok
python login.py --platform threads
```

- Browser akan terbuka **tidak headless** agar bisa selesaikan captcha atau 2FA secara manual jika muncul
- Setelah login berhasil, cookies disimpan ke `cookies/tiktok_cookies.json` dan `cookies/threads_cookies.json`
- Scraper otomatis menggunakan cookies tersebut pada run berikutnya

### Refresh Cookies

Cookies biasanya valid **1-3 bulan**. Jalankan ulang `login.py` jika scraper mulai gagal login atau hasil berkurang drastis.

---

## Cara Penggunaan

### Jalankan Lokal

```bash
# Aktifkan virtual environment
source venv/bin/activate

# Scrape kedua platform dengan query default dari .env
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

# Kombinasi lengkap
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

**Variables** (tab Variables — tidak sensitif):

| Name | Contoh | Keterangan |
|---|---|---|
| `SEARCH_QUERY` | `automation sdet` | Keyword default untuk scheduled run |
| `API_URL` | `https://api.example.com/scrape` | Endpoint API tujuan |

**Secrets** (tab Secrets — disembunyikan di log):

| Name | Keterangan |
|---|---|
| `API_KEY` | Bearer token untuk API (kosongkan jika tidak perlu auth) |
| `TIKTOK_COOKIES_B64` | Cookies TikTok dalam format base64 (lihat bagian di bawah) |
| `THREADS_COOKIES_B64` | Cookies Threads dalam format base64 (lihat bagian di bawah) |

### Cara Upload Cookies ke GitHub Secrets

Setelah login berhasil di lokal, jalankan:

```bash
python export_cookies.py
```

Output akan menampilkan base64 string seperti:

```
============================================================
GitHub Secret untuk TIKTOK
============================================================
Name : TIKTOK_COOKIES_B64
Value:
eyJjb29raWVzIjogW3sibmFtZSI6ICJ0dGlkIiwgInZhbHVlIjogIi4uLiJ9XX0=
============================================================
```

Copy nilai `Value` tersebut ke GitHub Secret dengan nama yang sesuai.

**Alur lengkap cookies:**

```
Lokal                              GitHub
────────────────────────────────────────────────────
python login.py                    
  → cookies/tiktok_cookies.json    
  → cookies/threads_cookies.json   

python export_cookies.py           
  → base64 string             →  Settings → Secrets
                                   TIKTOK_COOKIES_B64
                                   THREADS_COOKIES_B64
                          ↓
                CI run workflow
                decode secret → cookies/tiktok_cookies.json
                decode secret → cookies/threads_cookies.json
                python main.py (scrape dengan cookies)
```

> **Kapan perlu refresh cookies?**
> Biasanya setiap **1-3 bulan** atau ketika scraper mulai gagal / hasil berkurang drastis.
> Cukup jalankan ulang `login.py` → `export_cookies.py` → update secret di GitHub.

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

Hasil (JSON + screenshot debug) tersedia sebagai **artifact** yang bisa didownload di halaman run, tersimpan selama **7 hari**.

---

## Environment Variables Lengkap

| Variable | Default | Keterangan |
|---|---|---|
| `SEARCH_QUERY` | `automation` | Keyword pencarian default |
| `TIKTOK_ENABLED` | `true` | Aktifkan scraper TikTok |
| `THREADS_ENABLED` | `true` | Aktifkan scraper Threads |
| `TIKTOK_MAX_RESULTS` | `20` | Maks post TikTok yang diambil |
| `THREADS_MAX_RESULTS` | `20` | Maks post Threads yang diambil |
| `TIKTOK_SCROLL_COUNT` | `6` | Jumlah scroll di halaman TikTok |
| `HEADLESS` | `true` | `false` untuk tampilkan browser |
| `SLOW_MO` | `500` | Delay ms antar aksi browser |
| `TIKTOK_COOKIES_FILE` | `cookies/tiktok_cookies.json` | Path file cookies TikTok |
| `THREADS_COOKIES_FILE` | `cookies/threads_cookies.json` | Path file cookies Threads |
| `TIKTOK_USERNAME` | — | Username TikTok (untuk `login.py`) |
| `TIKTOK_PASSWORD` | — | Password TikTok (untuk `login.py`) |
| `THREADS_USERNAME` | — | Username Threads (untuk `login.py`) |
| `THREADS_PASSWORD` | — | Password Threads (untuk `login.py`) |
| `API_URL` | — | Endpoint API tujuan (wajib) |
| `API_KEY` | — | Bearer token API (opsional) |
| `API_TIMEOUT` | `30` | Timeout HTTP request ke API (detik) |

---

## Debug

### Screenshot Otomatis

Setiap run menyimpan screenshot per langkah ke folder `screenshots/`. Di GitHub Actions tersedia sebagai bagian dari artifact download.

| File | Keterangan |
|---|---|
| `tiktok_01_homepage.png` | Homepage TikTok setelah load |
| `tiktok_02_search_loaded.png` | Halaman search setelah navigasi |
| `tiktok_03_after_dismiss.png` | Setelah dismiss popup/captcha |
| `tiktok_scroll_N.png` | Setiap 2 scroll |
| `tiktok_04_after_scroll.png` | Setelah semua scroll selesai |
| `threads_01_homepage.png` | Homepage Threads |
| `threads_02_search_page.png` | Halaman search kosong |
| `threads_03_typed_query.png` | Setelah ketik query |
| `threads_04_results_loaded.png` | Setelah hasil muncul |
| `threads_05_after_scroll.png` | Setelah scroll |

### Inspect Selector

Jika scraper mengembalikan 0 hasil karena platform update UI:

```bash
python debug_inspect.py
```

Script ini membuka browser (tidak headless), screenshot halaman, dan mencoba berbagai selector untuk identifikasi perubahan.

### Troubleshooting Umum

| Masalah | Kemungkinan Penyebab | Solusi |
|---|---|---|
| TikTok 0 hasil | Bot detection / cookies expired | Jalankan `login.py` ulang, update secret |
| TikTok "Something went wrong" | Bot detection di Chromium | Scraper auto-reload, pastikan cookies tersedia |
| Threads hasil tidak relevan | GraphQL capture dari homepage | Pastikan flow search berjalan (cek screenshot) |
| Threads 0 post | Popup tidak ter-dismiss | Cek `screenshots/threads_0*.png` di artifact |
| Login gagal | Captcha / 2FA muncul | Jalankan `login.py` dengan `HEADLESS=false`, selesaikan manual |
| Cookies expired | Lebih dari 1-3 bulan | Jalankan `login.py` → `export_cookies.py` → update secret |
