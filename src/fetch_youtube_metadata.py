"""Nivå 1-3: hämta YouTubes egen kategori, beskrivning och kapitelrubriker
per video via YouTube Data API v3 - mycket rikare än titel+kanal, men
fortfarande bara metadata, ingen transkribering.

Skriver bara ut aggregat (kategori-antal, ordfrekvens från beskrivningar/
kapitel) - aldrig enskilda beskrivningar.

Kräver en gratis API-nyckel i config/.youtube_api_key (en rad, ingen
nyrad på slutet behövs). Filen är gitignorerad.
"""

import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

SOURCE = Path(
    "data/raw/takeout/2026-09-20/extracted/Takeout/YouTube och YouTube Music/historik/visningshistorik.html"
)
API_KEY_FILE = Path("config/.youtube_api_key")
OUTPUT = Path("data/profile/youtube_metadata.json")
BATCH_SIZE = 50
API_BASE = "https://www.googleapis.com/youtube/v3"

STOPWORDS = {
    "och", "att", "det", "som", "för", "med", "den", "på", "av", "en", "ett",
    "är", "till", "om", "du", "jag", "vi", "de", "här", "har", "kan",
    "the", "a", "an", "of", "to", "in", "for", "on", "and", "is", "with",
    "you", "your", "this", "that", "video", "youtube", "http", "https",
}
WORD_RE = re.compile(r"[a-zA-ZåäöÅÄÖ]{3,}")
CHAPTER_LINE_RE = re.compile(r"^\s*(?:\d{1,2}:)?\d{1,2}:\d{2}\s+(.+)$")
VIDEO_ID_RE = re.compile(r"[?&]v=([A-Za-z0-9_-]{11})")


def is_unavailable_placeholder(title: str) -> bool:
    lowered = title.strip().lower()
    return lowered.endswith("här") or lowered.startswith("http")


def load_api_key() -> str:
    if not API_KEY_FILE.exists():
        raise SystemExit(
            f"Hittar ingen API-nyckel i {API_KEY_FILE}. Skapa filen med nyckeln som enda innehåll."
        )
    return API_KEY_FILE.read_text(encoding="utf-8").strip()


def api_get(path: str, params: dict, api_key: str) -> dict:
    params = {**params, "key": api_key}
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def fetch_category_names(api_key: str) -> dict:
    data = api_get("videoCategories", {"part": "snippet", "regionCode": "SE"}, api_key)
    return {item["id"]: item["snippet"]["title"] for item in data.get("items", [])}


def extract_watch_entries(html_path: Path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    for cell in soup.select("div.content-cell"):
        links = cell.find_all("a")
        if not links:
            continue
        title = links[0].get_text(strip=True)
        href = links[0].get("href", "")
        channel = links[1].get_text(strip=True) if len(links) > 1 else None
        if is_unavailable_placeholder(title):
            continue
        match = VIDEO_ID_RE.search(href)
        if not match:
            continue
        yield match.group(1), channel


def extract_chapter_titles(description: str) -> list:
    titles = []
    for line in description.splitlines():
        m = CHAPTER_LINE_RE.match(line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def main() -> None:
    api_key = load_api_key()
    category_names = fetch_category_names(api_key)

    video_ids = []
    id_to_channel = {}
    for video_id, channel in extract_watch_entries(SOURCE):
        if video_id not in id_to_channel:
            video_ids.append(video_id)
            id_to_channel[video_id] = channel

    print(f"{len(video_ids)} unika videor att slå upp via API ({BATCH_SIZE} per anrop).")

    category_counts: Counter = Counter()
    category_by_channel: dict = defaultdict(Counter)
    description_words: Counter = Counter()
    chapter_words: Counter = Counter()
    not_found = 0

    for i in range(0, len(video_ids), BATCH_SIZE):
        batch = video_ids[i : i + BATCH_SIZE]
        data = api_get("videos", {"part": "snippet", "id": ",".join(batch)}, api_key)
        found_ids = set()
        for item in data.get("items", []):
            found_ids.add(item["id"])
            snippet = item["snippet"]
            category_id = snippet.get("categoryId", "")
            category = category_names.get(category_id, f"okänd ({category_id})")
            channel = id_to_channel.get(item["id"])

            category_counts[category] += 1
            if channel:
                category_by_channel[channel][category] += 1

            description = snippet.get("description", "")
            for word in WORD_RE.findall(description.lower()):
                if word not in STOPWORDS:
                    description_words[word] += 1
            for chapter_title in extract_chapter_titles(description):
                for word in WORD_RE.findall(chapter_title.lower()):
                    if word not in STOPWORDS:
                        chapter_words[word] += 1

        not_found += len(batch) - len(found_ids)
        print(f"  {min(i + BATCH_SIZE, len(video_ids))}/{len(video_ids)}")
        time.sleep(0.05)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "total_videos": len(video_ids),
                "not_found": not_found,
                "category_counts": category_counts.most_common(),
                "category_by_channel": {ch: c.most_common() for ch, c in category_by_channel.items()},
                "description_words": description_words.most_common(300),
                "chapter_words": chapter_words.most_common(300),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nSkrev {OUTPUT}")
    print(f"{not_found} videor hittades inte (privata/borttagna sen historiken sparades).")
    print("\nKategorifördelning (alla videor):")
    for cat, count in category_counts.most_common(20):
        print(f"  {count:5d}  {cat}")


if __name__ == "__main__":
    main()
