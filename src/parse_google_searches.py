"""Extraherar sökord ur Google-sökningar i Chrome/Historik.json.

Domänen google.com i sig säger inget om intressen (alla använder Google
till allt) - men själva sökordet gör det. Skriptet plockar ut "q"-
parametern ur sök-URL:er, räknar ordfrekvens och skriver aldrig ut
enskilda sökningar, bara aggregat.
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import yaml

SOURCE = Path("data/raw/takeout/2026-09-20/extracted/Takeout/Chrome/Historik.json")
EXCLUSIONS_FILE = Path("config/search_word_exclusions.yaml")
OUTPUT = Path("data/profile/google_search_words.json")
TOP_N_PRINTED = 40

STOPWORDS = {
    "och", "att", "det", "som", "för", "med", "den", "på", "av", "en", "ett",
    "är", "till", "om", "du", "jag", "vi", "de", "han", "hon", "man", "kan",
    "inte", "har", "var", "ska", "hur", "vad", "vem", "när", "vart", "eller",
    "mig", "finns", "the", "a", "an", "of", "to", "in", "for", "on", "and",
    "is", "with", "you", "your", "how", "what", "why", "from", "com", "new",
}
WORD_RE = re.compile(r"[a-zA-ZåäöÅÄÖ0-9]{2,}")


def load_word_exclusions() -> set:
    if not EXCLUSIONS_FILE.exists():
        return set()
    with EXCLUSIONS_FILE.open(encoding="utf-8") as f:
        groups = yaml.safe_load(f) or {}
    return {word for words in groups.values() for word in words}


def extract_query(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if "google." not in parsed.netloc:
        return None
    if not parsed.path.startswith("/search"):
        return None
    q = parse_qs(parsed.query).get("q")
    return q[0] if q else None


def main() -> None:
    excluded_words = load_word_exclusions()

    with SOURCE.open(encoding="utf-8") as f:
        data = json.load(f)

    word_counts: Counter[str] = Counter()
    total_visits = 0
    total_searches = 0

    for entry in data.get("Browser History", []):
        total_visits += 1
        query = extract_query(entry.get("url", ""))
        if not query:
            continue
        total_searches += 1
        for word in WORD_RE.findall(query.lower()):
            if word not in STOPWORDS and word not in excluded_words:
                word_counts[word] += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {"total_visits": total_visits, "total_searches": total_searches, "words": word_counts.most_common(500)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"{total_searches} Google-sökningar hittade (av {total_visits} besök totalt).")
    print(f"Fullständigt resultat: {OUTPUT}\n")
    print(f"Topp {TOP_N_PRINTED} sökord:")
    for word, count in word_counts.most_common(TOP_N_PRINTED):
        print(f"  {count:5d}  {word}")


if __name__ == "__main__":
    main()
