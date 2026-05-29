# 🍋 jambu-air

Tool otomatis untuk mengambil postingan dari **TikTok** dan **Threads** berdasarkan keyword, lalu mengirim hasilnya ke API backend.

---

## 📋 Daftar Isi

- [Apa yang Dilakukan Tool Ini?](#-apa-yang-dilakukan-tool-ini)
- [Persiapan Awal (Sekali Saja)](#-persiapan-awal-sekali-saja)
- [Login ke Platform](#-login-ke-platform)
- [Cara Menjalankan](#-cara-menjalankan)
- [Setup GitHub Actions (CI)](#-setup-github-actions-ci)
- [Cara Trigger Manual di GitHub](#-cara-trigger-manual-di-github)
- [Format Data yang Dihasilkan](#-format-data-yang-dihasilkan)
- [Pengaturan Lanjutan](#-pengaturan-lanjutan)
- [Troubleshooting](#-troubleshooting)

---

## 🤔 Apa yang Dilakukan Tool Ini?

1. Membuka browser otomatis (tidak perlu dilakukan manual)
2. Mencari keyword di TikTok dan/atau Threads
3. Mengambil data postingan: caption, like, komentar, waktu posting, dll
4. Mengirim semua data ke API backend dalam format JSON
5. Bisa dijadwalkan otomatis setiap hari, atau dijalankan manual

---

## 🚀 Persiapan Awal (Sekali Saja)

### Langkah 1 — Install Python

Pastikan Python 3.11 atau lebih baru sudah terinstall.

```bash
python3 --version
# Harus menampilkan: Python 3.11.x atau lebih tinggi
```

Jika belum ada, download di [python.org](https://www.python.org/downloads/).

### Langkah 2 — Download Project

```bash
git clone https://github.com/damarmustikoaji/jambu-air.git
cd jambu-air
```

### Langkah 3 — Setup Virtual Environment

Virtual environment adalah ruang isolasi agar library project tidak bercampur dengan library lain di komputer.

```bash
# Buat virtual environment
python3.11 -m venv venv

# Aktifkan (Mac/Linux)
source venv/bin/activate

# Tanda berhasil: nama folder (venv) muncul di awal baris terminal
```

> **Catatan:** Setiap kali membuka terminal baru, jalankan `source venv/bin/activate` terlebih dahulu sebelum menjalankan script apapun.

### Langkah 4 — Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

Proses ini membutuhkan koneksi internet dan memakan waktu beberapa menit.

### Langkah 5 — Buat File Konfigurasi

```bash
cp .env.example .env
```

Buka file `.env` dan isi bagian yang diperlukan:

```env
# Keyword yang akan dicari (bisa diubah kapan saja)
SEARCH_QUERY=automation

# URL API tujuan pengiriman data
API_URL=https://your-backend.com/api/scrape

# API Key jika diperlukan (kosongkan jika tidak ada)
API_KEY=
```

---

## 🔐 Login ke Platform

Login diperlukan agar scraper bisa mendapatkan lebih banyak data dan tidak diblok oleh platform. **Login hanya perlu dilakukan sekali** — hasilnya disimpan sebagai file cookies dan dipakai untuk scraping berikutnya.

### Langkah 1 — Isi Credential di `.env`

Buka file `.env` dan isi:

```env
TIKTOK_USERNAME=username_tiktok_kamu
TIKTOK_PASSWORD=password_tiktok_kamu
THREADS_USERNAME=username_threads_kamu
THREADS_PASSWORD=password_threads_kamu
```

> Threads menggunakan akun Instagram. Isi dengan username/password Instagram.

### Langkah 2 — Jalankan Script Login

```bash
# Login ke kedua platform sekaligus
python login.py

# Atau pilih satu platform
python login.py --platform tiktok
python login.py --platform threads
```

Browser akan terbuka secara otomatis. **Biarkan browser terbuka** — jika muncul captcha atau verifikasi 2FA, selesaikan secara manual, lalu tekan Enter di terminal.

### Langkah 3 — Verifikasi Login Berhasil

Jika berhasil, akan muncul pesan seperti:

```
[TikTok] Cookies disimpan ke cookies/tiktok_cookies.json (45 cookies)
[Threads] Cookies disimpan ke cookies/threads_cookies.json (32 cookies)
```

File cookies tersimpan di folder `cookies/` dan **tidak akan ter-upload ke GitHub** (sudah di-gitignore).

### Kapan Perlu Login Ulang?

Cookies biasanya valid **1–3 bulan**. Login ulang diperlukan jika:
- Scraper tiba-tiba tidak mendapat data
- Muncul pesan error terkait sesi/autentikasi
- Sudah lebih dari 3 bulan sejak login terakhir

---

## ▶️ Cara Menjalankan

Pastikan virtual environment sudah aktif (`source venv/bin/activate`).

### Perintah Dasar

```bash
# Scrape kedua platform, keyword dari .env
python main.py

# Tentukan keyword langsung
python main.py --query "software testing"

# Hanya TikTok
python main.py --platform tiktok

# Hanya Threads
python main.py --platform threads

# Simpan hasil ke file JSON lokal
python main.py --save

# Test tanpa kirim ke API (untuk coba-coba)
python main.py --dry-run --save
```

### Contoh Kombinasi Lengkap

```bash
# Scrape Threads dengan keyword custom, simpan ke file, tanpa kirim ke API
python main.py --platform threads --query "automation test" --dry-run --save

# Scrape TikTok saja, langsung kirim ke API
python main.py --platform tiktok --query "AI tools"
```

### Hasil Scraping

Jika menggunakan `--save`, file hasil tersimpan di folder project dengan nama:

```
output_automation_20260529_130000.json
```

---

## ☁️ Setup GitHub Actions (CI)

GitHub Actions memungkinkan scraper berjalan otomatis di cloud setiap hari tanpa perlu komputer menyala.

### Langkah 1 — Fork atau Push ke GitHub

Pastikan kode sudah ada di repository GitHub kamu.

### Langkah 2 — Setup Variables (Tidak Sensitif)

Masuk ke **repository → Settings → Secrets and variables → Actions → tab Variables → New repository variable**:

| Name | Value | Keterangan |
|---|---|---|
| `SEARCH_QUERY` | `automation sdet` | Keyword default untuk jadwal otomatis |
| `API_URL` | `https://api.example.com/scrape` | Endpoint API tujuan |

### Langkah 3 — Setup Secrets (Data Sensitif)

Masuk ke **repository → Settings → Secrets and variables → Actions → tab Secrets → New repository secret**:

| Name | Keterangan |
|---|---|
| `API_KEY` | Bearer token API (kosongkan jika tidak perlu) |
| `TIKTOK_COOKIES_B64` | Cookies TikTok dalam base64 — lihat cara mendapatkannya di bawah |
| `THREADS_COOKIES_B64` | Cookies Threads dalam base64 — lihat cara mendapatkannya di bawah |

### Langkah 4 — Upload Cookies ke GitHub Secrets

Setelah login berhasil di lokal (Langkah Login di atas), jalankan:

```bash
python export_cookies.py
```

Output akan tampil seperti ini:

```
============================================================
GitHub Secret untuk TIKTOK
============================================================
Name : TIKTOK_COOKIES_B64
Value:
eyJjb29raWVzIjogW3sibmFtZSI6ICJ0dGlkIiwgInZhbHVlIjogIi4uLiJ9XX0=
============================================================
```

**Copy seluruh teks panjang di bagian Value** (mulai dari `eyJ...` hingga akhir), lalu:

1. Buka **repository → Settings → Secrets and variables → Actions**
2. Klik **New repository secret**
3. Name: `TIKTOK_COOKIES_B64`
4. Value: paste teks panjang tadi
5. Klik **Add secret**
6. Ulangi untuk `THREADS_COOKIES_B64`

**Ilustrasi alur cookies:**

```
Komputer Lokal                    GitHub
──────────────────────────────────────────────────────
1. python login.py
   → cookies tersimpan di cookies/*.json

2. python export_cookies.py
   → tampil teks base64            

3. Copy teks base64          →   Settings → Secrets
                                  TIKTOK_COOKIES_B64
                                  THREADS_COOKIES_B64

                              ↓
                    Setiap CI run:
                    decode secret → cookies/*.json
                    python main.py (pakai cookies)
```

> **Refresh cookies:** Setiap 1–3 bulan, ulangi langkah Login → `export_cookies.py` → update secret di GitHub.

---

## 🎮 Cara Trigger Manual di GitHub

1. Buka repository di GitHub
2. Klik tab **Actions**
3. Pilih **Social Media Scraper** di sidebar kiri
4. Klik tombol **Run workflow** (kanan atas)
5. Isi form yang muncul:

| Field | Keterangan | Contoh |
|---|---|---|
| **Platform** | Pilih platform yang mau di-scrape | `tiktok threads` |
| **Keyword pencarian** | Kosongkan = pakai keyword dari Settings | `automation test` |
| **Maksimal hasil** | Berapa postingan per platform | `50` |
| **Jumlah scroll TikTok** | Lebih banyak = lebih banyak hasil | `6` |

6. Klik **Run workflow**

### Melihat Hasil

Setelah workflow selesai (biasanya 5–15 menit):

1. Klik nama run di daftar workflow
2. Scroll ke bawah ke bagian **Artifacts**
3. Klik **scrape-result-XXXXX** untuk download
4. File ZIP berisi:
   - `output_*.json` — data hasil scraping
   - `screenshots/` — foto kondisi browser per langkah (untuk debug)

### Jadwal Otomatis

Scraper berjalan otomatis setiap hari **jam 20:00 WIB** menggunakan keyword dari `SEARCH_QUERY` variable di Settings.

---

## 📦 Format Data yang Dihasilkan

```json
{
  "query": "automation",
  "scraped_at": "2026-05-29T13:00:00+00:00",
  "results": {
    "tiktok": [
      {
        "platform": "tiktok",
        "post_id": "7380123456789",
        "username": "john.doe",
        "display_name": "John Doe",
        "caption": "Workflow automation tips #automation",
        "like_count": 12500,
        "comment_count": 340,
        "share_count": 89,
        "view_count": 250000,
        "post_url": "https://www.tiktok.com/@john.doe/video/7380123456789",
        "timestamp": "2026-05-20T10:30:00+00:00",
        "hashtags": ["automation"]
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
        "hashtags": []
      }
    ]
  },
  "summary": {
    "tiktok_count": 20,
    "threads_count": 15,
    "total_count": 35
  }
}
```

---

## ⚙️ Pengaturan Lanjutan

### Semua Variabel Konfigurasi (file `.env`)

| Variable | Default | Keterangan |
|---|---|---|
| `SEARCH_QUERY` | `automation` | Keyword pencarian default |
| `TIKTOK_ENABLED` | `true` | Aktif/nonaktifkan TikTok |
| `THREADS_ENABLED` | `true` | Aktif/nonaktifkan Threads |
| `TIKTOK_MAX_RESULTS` | `20` | Maks postingan TikTok |
| `THREADS_MAX_RESULTS` | `20` | Maks postingan Threads |
| `TIKTOK_SCROLL_COUNT` | `6` | Jumlah scroll TikTok (makin banyak = makin banyak hasil) |
| `HEADLESS` | `true` | `false` = browser tampil (berguna saat debug) |
| `SLOW_MO` | `500` | Kecepatan aksi browser dalam ms (makin besar = makin lambat tapi stabil) |
| `TIKTOK_COOKIES_FILE` | `cookies/tiktok_cookies.json` | Path file cookies TikTok |
| `THREADS_COOKIES_FILE` | `cookies/threads_cookies.json` | Path file cookies Threads |
| `API_URL` | — | URL API tujuan (**wajib diisi**) |
| `API_KEY` | — | Bearer token API (opsional) |
| `API_TIMEOUT` | `30` | Timeout koneksi ke API (detik) |

### Variabel Khusus Login (file `.env`, tidak dikirim ke mana pun)

| Variable | Keterangan |
|---|---|
| `TIKTOK_USERNAME` | Username/email TikTok |
| `TIKTOK_PASSWORD` | Password TikTok |
| `THREADS_USERNAME` | Username Instagram (untuk Threads) |
| `THREADS_PASSWORD` | Password Instagram (untuk Threads) |

---

## 🔧 Troubleshooting

### TikTok tidak mendapat data (0 hasil)

**Penyebab:** Bot detection atau cookies expired.

**Solusi:**
```bash
# Login ulang
python login.py --platform tiktok

# Upload ulang cookies ke GitHub Secrets
python export_cookies.py
# → copy TIKTOK_COOKIES_B64 → update di GitHub Settings
```

### TikTok muncul "Something went wrong"

**Penyebab:** TikTok memblok Chromium otomatis. Scraper sudah ada auto-reload, tapi bisa gagal jika cookies tidak ada.

**Solusi:** Pastikan cookies tersedia dan belum expired (lihat di atas).

### Threads hasil tidak relevan dengan keyword

**Penyebab:** Data ter-capture dari halaman lain (bukan halaman search).

**Solusi:** Download artifact dan cek screenshot `threads_04_results_loaded.png` — pastikan halaman search yang ter-capture bukan homepage.

### Login gagal / browser tidak bisa klik tombol

**Penyebab:** Captcha atau 2FA muncul, atau UI platform berubah.

**Solusi:**
1. Buka terminal, jalankan `python login.py`
2. Saat browser terbuka, selesaikan captcha/2FA secara manual
3. Tekan Enter di terminal setelah selesai

### Muncul error `ModuleNotFoundError`

**Penyebab:** Virtual environment belum aktif.

**Solusi:**
```bash
source venv/bin/activate
# Lalu jalankan ulang perintah sebelumnya
```

### Cookies di GitHub Actions tidak terbaca

**Penyebab:** Secret `TIKTOK_COOKIES_B64` / `THREADS_COOKIES_B64` belum diset atau nilai tidak valid.

**Solusi:**
1. Jalankan ulang `python export_cookies.py`
2. Copy ulang nilai base64 (pastikan tidak ada spasi/enter di tengah)
3. Update secret di GitHub

---

## 📁 Struktur File Project

```
jambu-air/
├── scrapers/
│   ├── tiktok.py          # Logic scraping TikTok
│   └── threads.py         # Logic scraping Threads
├── cookies/               # Tersimpan lokal, tidak di-upload ke GitHub
│   ├── tiktok_cookies.json
│   └── threads_cookies.json
├── screenshots/           # Screenshot debug, dibuat otomatis saat scraping
├── models.py              # Struktur data postingan
├── config.py              # Membaca konfigurasi dari .env
├── sender.py              # Mengirim data ke API
├── main.py                # Program utama (entry point)
├── login.py               # Script login untuk generate cookies
├── export_cookies.py      # Script encode cookies untuk GitHub Secrets
├── debug_inspect.py       # Script debug jika scraper bermasalah
├── requirements.txt       # Daftar library yang dibutuhkan
├── .env.example           # Template konfigurasi
└── .github/workflows/
    └── scraper.yml        # Konfigurasi otomasi GitHub Actions
```
