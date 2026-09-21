"""Berikar direktkälle-kandidater (nyhetsbrev, betrodda internationella
källor) med en artikelbild, hämtad via og:image-metataggen på
artikelsidan. Fungerar INTE för Google Nyheter-sökta kandidater - deras
länkar pekar på Googles JS-baserade omdirigeringssidor, ingen riktig
artikel-URL att skrapa. Se PROJECT_PLAN.md/config/brief_schema.md.

Hotlinkar bilden (sparar bara URL:en, laddar aldrig ner/lagrar filen
själv) - samma princip som en vanlig länkförhandsvisning.
"""

import json
import re
import urllib.request
from pathlib import Path

RAW_DIR = Path("data/profile/candidates_raw")
TIMEOUT = 8
PLACEHOLDER_MARKERS = ("blank.jpg", "avatar", "gravatar")

OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
    r'|content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\'])',
    re.IGNORECASE,
)


def fetch_og_image(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read(150_000).decode("utf-8", errors="ignore")
    except Exception:
        return None
    m = OG_IMAGE_RE.search(html)
    if not m:
        return None
    image_url = m.group(1) or m.group(2)
    if any(marker in image_url.lower() for marker in PLACEHOLDER_MARKERS):
        return None
    return image_url


def enrich_file(path: Path) -> None:
    if not path.exists():
        return
    items = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for item in items:
        if "bild" in item:
            continue  # redan berikad
        image = fetch_og_image(item["link"])
        item["bild"] = image
        changed = True
        print(f"  {'✓' if image else '·'}  {item['title'][:60]}")
    if changed:
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    for pattern in ("*_nyhetsbrev.json", "*_internationellt.json"):
        for path in sorted(RAW_DIR.glob(pattern)):
            print(f"{path.name}:")
            enrich_file(path)


if __name__ == "__main__":
    main()
