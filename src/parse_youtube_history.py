"""Läser YouTube-visningshistorik (Takeout-HTML) och delar upp varje post i
kanal (avsändare) och titel som separata dimensioner, istället för fri text.

Skriver bara ut aggregat (kanalräkning, ordfrekvens i titlar) - aldrig
enskilda videotitlar.
"""

import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

SOURCE = Path(
    "data/raw/takeout/2026-09-20/extracted/Takeout/YouTube och YouTube Music/historik/visningshistorik.html"
)
OUTPUT_CHANNELS = Path("data/profile/youtube_channel_counts.json")
OUTPUT_WORDS = Path("data/profile/youtube_title_words.json")
TOP_N_PRINTED = 25

STOPWORDS = {
    # svenska
    "och", "att", "det", "som", "för", "med", "den", "på", "av", "en", "ett",
    "är", "till", "om", "du", "jag", "vi", "de", "han", "hon", "man", "kan",
    "inte", "har", "var", "ska", "blir", "denna", "detta", "dessa", "min",
    "din", "sin", "vår", "eller", "men", "så", "här", "där", "när", "vad",
    "hur", "nya", "gör", "får", "från", "vid", "över", "under",
    # engelska (vanliga hjälpord)
    "the", "a", "an", "of", "to", "in", "for", "on", "and", "is", "with",
    "video", "youtube", "you", "your", "this", "that", "are", "how", "what",
    "why", "from", "have", "has", "just", "his", "her", "can", "out", "new",
    "full", "it", "its", "at", "as", "by", "be", "was", "were", "will",
    "not", "but", "all", "we", "they", "he", "she", "i", "my", "me", "who",
    "when", "which", "these", "those", "do", "does", "did", "our", "us",
    "about", "into", "than", "then", "now", "more", "most", "one", "two",
    "ep", "part", "vs", "official", "here", "com", "net", "org",
}
URL_RE = re.compile(r"https?://\S+|www\.\S+|youtu\.be/\S+")
WORD_RE = re.compile(r"[a-zA-ZåäöÅÄÖ]{3,}")


def is_unavailable_placeholder(title: str) -> bool:
    # Borttagna/privata videor: Google skriver en platshållartext som
    # slutar på "här" istället för en riktig titel, eller bara URL:en.
    lowered = title.strip().lower()
    return lowered.endswith("här") or lowered.startswith("http")


def parse_entries(html_path: Path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    for cell in soup.select("div.content-cell"):
        links = cell.find_all("a")
        if not links:
            continue
        title = links[0].get_text(strip=True)
        channel = links[1].get_text(strip=True) if len(links) > 1 else None
        yield title, channel


def main() -> None:
    channel_counts: Counter[str] = Counter()
    word_counts: Counter[str] = Counter()
    total = 0
    without_channel = 0
    unavailable = 0

    for title, channel in parse_entries(SOURCE):
        total += 1
        if is_unavailable_placeholder(title):
            unavailable += 1
            continue
        if channel:
            channel_counts[channel] += 1
        else:
            without_channel += 1
        cleaned = URL_RE.sub(" ", title.lower())
        for word in WORD_RE.findall(cleaned):
            if word not in STOPWORDS:
                word_counts[word] += 1

    OUTPUT_CHANNELS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CHANNELS.write_text(
        __import__("json").dumps(
            {
                "total_videos": total,
                "unavailable_placeholder": unavailable,
                "without_channel": without_channel,
                "channels": channel_counts.most_common(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    OUTPUT_WORDS.write_text(
        __import__("json").dumps(dict(word_counts.most_common(500)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Totalt {total} videoposter, varav {unavailable} borttagna/privata (ingen titel att analysera).")
    print(f"Av de {total - unavailable} återstående saknar {without_channel} identifierat kanalnamn.")
    print(f"Kanaler: {OUTPUT_CHANNELS}")
    print(f"Ordfrekvens i titlar: {OUTPUT_WORDS}")
    print(f"\nTopp {TOP_N_PRINTED} kanaler:")
    for channel, count in channel_counts.most_common(TOP_N_PRINTED):
        print(f"  {count:5d}  {channel}")
    print(f"\nTopp {TOP_N_PRINTED} ord i titlar:")
    for word, count in word_counts.most_common(TOP_N_PRINTED):
        print(f"  {count:5d}  {word}")


if __name__ == "__main__":
    main()
