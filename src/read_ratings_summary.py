"""Sammanfattar betyg (ratings-tabellen i Supabase) per källa och
kategori, för att mata in i kureringen (Fas 7 - se PROJECT_PLAN.md).

Skriver INTE tillbaka något - bara ett skrivskyddat sammandrag Claude
läser i början av Steg 5 (kurering) i det schemalagda jobbet, för att
kunna nedprioritera källor/kategorier som ofta får "ner" och behålla
sådant som ofta får "upp".

Använder service_role-nyckeln (samma som upload_brief.py) eftersom
ratings-tabellens RLS bara tillåter insert, ingen select, för vanliga
klienter - ett lokalt skript som läser för att förbättra kureringen är
en annan sak än att exponera andras data publikt.

Kör lokalt, gratis, bara HTTP mot Supabases REST-API.
"""

import json
import urllib.request
from collections import defaultdict
from pathlib import Path

SUPABASE_URL = "https://obefdjxlvgjddwysqhum.supabase.co"
SERVICE_KEY_FILE = Path("config/.supabase_service_key")
LOOKBACK_ROWS = 500  # senaste betygen, oavsett datum - enkel gräns istället för tidsfönster


def load_service_key() -> str:
    if not SERVICE_KEY_FILE.exists():
        raise SystemExit(f"Saknar {SERVICE_KEY_FILE} - inget att sammanfatta, hoppa över steget.")
    return SERVICE_KEY_FILE.read_text(encoding="utf-8").strip()


def fetch_ratings(service_key: str) -> list:
    url = (
        f"{SUPABASE_URL}/rest/v1/ratings"
        f"?select=betyg,kategori,kalla&order=skapad.desc&limit={LOOKBACK_ROWS}"
    )
    req = urllib.request.Request(url)
    req.add_header("apikey", service_key)
    req.add_header("Authorization", f"Bearer {service_key}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    service_key = load_service_key()
    rows = fetch_ratings(service_key)

    if not rows:
        print("Inga betyg sparade än - inget att sammanfatta.")
        return

    per_kalla = defaultdict(lambda: {"upp": 0, "ner": 0})
    per_kategori = defaultdict(lambda: {"upp": 0, "ner": 0})

    for row in rows:
        betyg = row.get("betyg")
        if betyg not in ("upp", "ner"):
            continue
        kalla = row.get("kalla") or "(okänd källa)"
        kategori = row.get("kategori") or "(okänd kategori)"
        per_kalla[kalla][betyg] += 1
        per_kategori[kategori][betyg] += 1

    print(f"Sammanfattning av {len(rows)} senaste betygen:\n")

    print("Per källa (nettoresultat, sorterat mest negativt->positivt):")
    kalla_sorted = sorted(per_kalla.items(), key=lambda kv: kv[1]["upp"] - kv[1]["ner"])
    for kalla, counts in kalla_sorted:
        netto = counts["upp"] - counts["ner"]
        print(f"  {kalla}: {counts['upp']} upp / {counts['ner']} ner (netto {netto:+d})")

    print("\nPer kategori:")
    for kategori, counts in sorted(per_kategori.items()):
        netto = counts["upp"] - counts["ner"]
        print(f"  {kategori}: {counts['upp']} upp / {counts['ner']} ner (netto {netto:+d})")


if __name__ == "__main__":
    main()
