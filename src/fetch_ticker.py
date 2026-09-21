"""Hämtar en handfull marknadskurser (index, aktie, valuta, guld, BTC)
till börstickern överst på hemsidan (web/ticker.json).

Tre fria källor utan nyckel, samma mönster som fetch_trusted_international.py:
- Yahoo Finance chart-endpoint (index/aktie/guld) - ingen nyckel, används
  redan indirekt av flera testverktyg i projektet.
- Frankfurter.app (ECB-kurser) för USD/SEK - uppdateras en gång per
  bankdag, vilket räcker gott för en ticker som inte behöver vara
  minutfärsk.
- CoinGecko publika pris-endpoint för BTC.

Tänkt att köras några gånger under dagen (inte varje minut) via ett
schemalagt Claude Code-jobb, separat från det dagliga brevet i Fas 6.
web/ticker.json committas till git och serveras statiskt av GitHub
Pages - sidans JS läser den filen istället för att anropa något API
direkt från webbläsaren (som annars stöter på CORS-problem för
aktie-/indexdata).
"""

import datetime
import json
import urllib.request
from pathlib import Path

OUT_FILE = Path("web/ticker.json")
UA = {"User-Agent": "Mozilla/5.0 (AxelNews ticker-läsare)"}
TIMEOUT = 10


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_yahoo(symbol: str) -> tuple:
    data = fetch_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d")
    meta = data["chart"]["result"][0]["meta"]
    return meta["regularMarketPrice"], meta["chartPreviousClose"]


def fetch_usd_sek() -> tuple:
    today = fetch_json("https://api.frankfurter.app/latest?from=USD&to=SEK")
    price = today["rates"]["SEK"]
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    try:
        # Frankfurter snappar automatiskt till senaste bankdag om datumet
        # infaller på en helg.
        prev = fetch_json(f"https://api.frankfurter.app/{yesterday}?from=USD&to=SEK")
        baseline = prev["rates"]["SEK"]
    except Exception:
        baseline = price
    return price, baseline


def fetch_btc() -> tuple:
    data = fetch_json(
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    )
    price = data["bitcoin"]["usd"]
    change_pct = data["bitcoin"]["usd_24h_change"]
    baseline = price / (1 + change_pct / 100)
    return price, baseline


SOURCES = [
    ("OMXS30", lambda: fetch_yahoo("%5EOMX"), 2),
    ("H&M", lambda: fetch_yahoo("HM-B.ST"), 2),
    ("USD/SEK", fetch_usd_sek, 2),
    ("GULD", lambda: fetch_yahoo("GC=F"), 2),
    ("BTC", fetch_btc, 0),
]


def main() -> None:
    items = []
    for symbol, fetcher, decimals in SOURCES:
        try:
            price, baseline = fetcher()
            items.append({"symbol": symbol, "price": round(price, 4), "baseline": round(baseline, 4), "decimals": decimals})
            print(f"  ✓  {symbol}: {price} (föregående: {baseline})")
        except Exception as exc:
            print(f"  ·  {symbol}: fel - {exc}")

    if not items:
        print("Inga kurser hämtades, skriver inte över ticker.json")
        return

    payload = {
        "updated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "items": items,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sparat: {OUT_FILE} ({len(items)} kurser)")


if __name__ == "__main__":
    main()
