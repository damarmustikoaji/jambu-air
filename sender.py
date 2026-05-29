import json
import httpx
from models import ScrapeResult
from config import config


async def send_to_api(result: ScrapeResult) -> bool:
    """Kirim hasil scraping ke backend API. Return True jika berhasil."""
    payload = result.to_payload()

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    print(f"[Sender] Mengirim {payload['summary']['total_count']} post ke {config.api_url}")
    print(f"[Sender] Summary: TikTok={payload['summary']['tiktok_count']}, Threads={payload['summary']['threads_count']}")

    try:
        async with httpx.AsyncClient(timeout=config.api_timeout) as client:
            response = await client.post(config.api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"[Sender] Berhasil! Status: {response.status_code}")
            try:
                resp_json = response.json()
                print(f"[Sender] Response API: {json.dumps(resp_json, ensure_ascii=False)}")
            except Exception:
                print(f"[Sender] Response API (text): {response.text[:500]}")
            return True
    except httpx.HTTPStatusError as e:
        print(f"[Sender] HTTP error {e.response.status_code}: {e.response.text}")
        return False
    except httpx.RequestError as e:
        print(f"[Sender] Request error: {e}")
        return False


def save_to_file(result: ScrapeResult, output_file: str = "output.json"):
    """Simpan hasil ke file JSON (untuk debug atau backup)."""
    payload = result.to_payload()
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[Sender] Hasil disimpan ke {output_file}")
