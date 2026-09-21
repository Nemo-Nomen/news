"""Hämtar kända nyhetsbrevs-RSS-flöden (config/newsletter_feeds.yaml) och
sparar dem som en egen "alltid med"-pool per kategori - de konkurrerar
inte om poängtröskeln, de väger starkast av alla signaler (se
PROJECT_PLAN.md avsnitt 6, "Nyhetsbrev/prenumerationer").

Körs lokalt i Fas 5, ingen Claude/Gmail behövs för flöden som har RSS.
"""

import datetime
import json
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

FEEDS_FILE = Path("config/newsletter_feeds.yaml")
RAW_DIR = Path("data/profile/candidates_raw")
LOOKBACK_DAYS = 7


def fetch_feed(url: str) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AxelNews RSS-läsare)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date_raw = item.findtext("pubDate", "")
        try:
            pub_date = parsedate_to_datetime(pub_date_raw)
        except (TypeError, ValueError):
            pub_date = None
        items.append({"title": title, "link": link, "pub_date": pub_date})
    return items


def main() -> None:
    feeds = yaml.safe_load(FEEDS_FILE.read_text(encoding="utf-8")) or []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=LOOKBACK_DAYS)

    by_category: dict = {}
    for feed in feeds:
        if not feed.get("url"):
            print(f"Hoppar över {feed['namn']} - inget RSS-flöde konfigurerat än")
            continue
        print(f"Hämtar: {feed['namn']} ({feed['url']})")
        items = fetch_feed(feed["url"])
        recent = [i for i in items if i["pub_date"] and i["pub_date"] >= cutoff]
        category = feed["kategori"]
        for item in recent:
            by_category.setdefault(category, []).append(
                {
                    "title": item["title"],
                    "link": item["link"],
                    "source": feed["namn"],
                    "pub_date": item["pub_date"].isoformat(),
                    "nyhetsbrev": True,
                }
            )
        print(f"  {len(recent)} nya poster senaste {LOOKBACK_DAYS} dagarna")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for category, items in by_category.items():
        out_file = RAW_DIR / f"{category}_nyhetsbrev.json"
        out_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Sparat: {out_file}")


if __name__ == "__main__":
    main()
