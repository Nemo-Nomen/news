"""Hämtar kända internationella källors egna RSS-flöden
(config/trusted_international_feeds.yaml) och lägger till dem i samma
"internationellt"-pool som finance-news-MCP:n skriver till
(data/profile/candidates_raw/<kategori>_internationellt.json).

Till skillnad från nyhetsbreven (fetch_newsletter_feeds.py) går de här
genom NORMAL poängsättning i merge_candidates.py - allmänna
nyhetskällor, inte "alltid med"-signaler.

Körs lokalt, gratis, ingen Claude behövs.
"""

import datetime
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

FEEDS_FILE = Path("config/trusted_international_feeds.yaml")
RAW_DIR = Path("data/profile/candidates_raw")
LOOKBACK_DAYS = 3


ATOM_NS = "{http://www.w3.org/2005/Atom}"

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Källornas beskrivningsfält är ofta HTML (t.ex. SR Ekots <ul><li><p>...)
    - platta ut till text så den går att läsa/citera direkt utan extra
    WebFetch/WebSearch för att förstå vad artikeln handlar om (se
    PROJECT_PLAN.md "hastighetsanalys 2026-09-22")."""
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", text or "")).strip()


def _parse_rss2(root) -> list:
    items = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date_raw = item.findtext("pubDate", "")
        description = _strip_html(item.findtext("description", ""))
        try:
            pub_date = parsedate_to_datetime(pub_date_raw)
        except (TypeError, ValueError):
            pub_date = None
        items.append({"title": title, "link": link, "pub_date": pub_date, "description": description})
    return items


def _parse_atom(root) -> list:
    items = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title = entry.findtext(f"{ATOM_NS}title", "")
        link_el = entry.find(f'{ATOM_NS}link[@rel="alternate"]')
        if link_el is None:
            link_el = entry.find(f"{ATOM_NS}link")
        link = link_el.get("href", "") if link_el is not None else ""
        pub_date_raw = entry.findtext(f"{ATOM_NS}published") or entry.findtext(f"{ATOM_NS}updated", "")
        description = _strip_html(entry.findtext(f"{ATOM_NS}summary") or "")
        try:
            pub_date = datetime.datetime.fromisoformat(pub_date_raw.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            pub_date = None
        items.append({"title": title, "link": link, "pub_date": pub_date, "description": description})
    return items


def fetch_feed(url: str) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AxelNews RSS-läsare)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    # Vissa källor (SR Ekot, The Verge) ger Atom istället för RSS 2.0 -
    # roten heter då "feed" (med Atom-namespace) istället för "rss".
    if root.tag == f"{ATOM_NS}feed":
        return _parse_atom(root)
    return _parse_rss2(root)


def load_existing(path: Path) -> list:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    feeds_by_category = yaml.safe_load(FEEDS_FILE.read_text(encoding="utf-8")) or {}
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=LOOKBACK_DAYS)

    for category, feeds in feeds_by_category.items():
        out_file = RAW_DIR / f"{category}_internationellt.json"
        existing = load_existing(out_file)
        seen_links = {i["link"] for i in existing}

        for feed in feeds:
            print(f"[{category}] Hämtar: {feed['namn']} ({feed['url']})")
            try:
                items = fetch_feed(feed["url"])
            except Exception as exc:
                print(f"  Fel: {exc}")
                continue
            new_count = 0
            for item in items:
                if not item["pub_date"] or item["pub_date"] < cutoff:
                    continue
                if item["link"] in seen_links:
                    continue
                seen_links.add(item["link"])
                existing.append(
                    {
                        "title": item["title"],
                        "link": item["link"],
                        "source": feed["namn"],
                        "pub_date": item["pub_date"].isoformat(),
                        "description": item.get("description", ""),
                    }
                )
                new_count += 1
            print(f"  {new_count} nya senaste {LOOKBACK_DAYS} dagarna")

        RAW_DIR.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Sparat: {out_file} ({len(existing)} totalt)")


if __name__ == "__main__":
    main()
