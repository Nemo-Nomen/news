"""Laddar upp det senaste dagliga brevet (data/profile/brief/<datum>.json,
skrivet av save_brief.py) till Supabase-tabellen brief_items, skyddad
av en RLS-policy som bara tillåter `select` för inloggade användare
(se docs/index.html - sidan läser tabellen direkt efter inloggning).

Skriver med service_role-nyckeln, som förbigår RLS helt - den nyckeln
får ALDRIG exponeras i klientkod eller committas till git (sparas i
config/.supabase_service_key, gitignorerad, samma mönster som
config/.youtube_api_key).

Rensar tabellen och skriver om den helt vid varje körning - sajten
visar bara det senaste brevet, ingen historik i UI:t än.

Körs lokalt (eller av det schemalagda kureringsjobbet), gratis, bara
enkla HTTP-anrop mot Supabases REST-API (PostgREST) - ingen extra
dependency.
"""

import datetime
import json
import urllib.request
from pathlib import Path

SUPABASE_URL = "https://obefdjxlvgjddwysqhum.supabase.co"
SERVICE_KEY_FILE = Path("config/.supabase_service_key")
BRIEF_DIR = Path("data/profile/brief")


def load_service_key() -> str:
    if not SERVICE_KEY_FILE.exists():
        raise SystemExit(
            f"Saknar {SERVICE_KEY_FILE} - spara service_role-nyckeln där först "
            "(se PROJECT_PLAN.md avsnitt 7)."
        )
    return SERVICE_KEY_FILE.read_text(encoding="utf-8").strip()


def latest_brief_file() -> Path:
    files = sorted(BRIEF_DIR.glob("*.json"))
    if not files:
        raise SystemExit(f"Ingen brief-fil hittad i {BRIEF_DIR} - kör save_brief.py först.")
    return files[-1]


def request(method: str, path: str, service_key: str, body=None) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", service_key)
    req.add_header("Authorization", f"Bearer {service_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "return=minimal")
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()


def main() -> None:
    service_key = load_service_key()
    brief_path = latest_brief_file()
    brev_datum = brief_path.stem  # filnamnet är redan YYYY-MM-DD
    brief = json.loads(brief_path.read_text(encoding="utf-8"))

    rows = []
    for kategori, items in brief["kategorier"].items():
        for item in items:
            rows.append(
                {
                    "id": item["id"],
                    "kategori": kategori,
                    "rubrik": item["rubrik"],
                    "sammanfattning": item["sammanfattning"],
                    "las_mer": item["las_mer"],
                    "varfor_viktigt": item["varfor_viktigt"],
                    "kallor": item["kallor"],
                    "publicerad": item["publicerad"],
                    "nyhetsbrev": item["nyhetsbrev"],
                    "stort_utomlands_ej_sverige": item["stort_utomlands_ej_sverige"],
                    "motargument": item["motargument"],
                    "brev_datum": brev_datum,
                }
            )

    # Rensa hela tabellen (id kan aldrig vara null, så filtret matchar
    # alla rader) - sajten visar bara det senaste brevet, inte flera
    # dagar samtidigt.
    request("DELETE", "brief_items?id=not.is.null", service_key)

    if rows:
        request("POST", "brief_items", service_key, body=rows)

    print(f"Uppladdat: {len(rows)} nyheter från {brev_datum} till brief_items")


if __name__ == "__main__":
    main()
