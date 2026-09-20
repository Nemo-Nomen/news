"""Läser Chrome/Historik.json, filtrerar besök på kända nyhetsdomäner
(config/news_domains.yaml) och räknar ord i sidtitlarna - per kategori och
per domän. Samma mönster som parse_youtube_history.py: avsändare (domän)
och ämne (ordfrekvens) som separata dimensioner.

Skriver bara ut aggregat (besöksantal, ordfrekvens) - aldrig enskilda
titlar eller URL:er.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import yaml

SOURCE = Path("data/raw/takeout/2026-09-20/extracted/Takeout/Chrome/Historik.json")
NEWS_DOMAINS_FILE = Path("config/news_domains.yaml")
OUTPUT = Path("data/profile/news_titles_analysis.json")
TOP_N_PRINTED = 20

STOPWORDS = {
    "och", "att", "det", "som", "för", "med", "den", "på", "av", "en", "ett",
    "är", "till", "om", "du", "jag", "vi", "de", "han", "hon", "man", "kan",
    "inte", "har", "var", "ska", "blir", "denna", "detta", "dessa", "min",
    "din", "sin", "vår", "eller", "men", "så", "här", "där", "när", "vad",
    "hur", "nya", "nytt", "gör", "får", "från", "vid", "över", "under", "ny",
    "efter", "utan", "mot", "flera", "kommer", "tar", "blev", "vill", "ger",
    "the", "a", "an", "of", "to", "in", "for", "on", "and", "is", "with",
    "you", "your", "this", "that", "are", "how", "what", "why", "from",
    "have", "has", "just", "his", "her", "can", "out", "new", "it", "its",
    "at", "as", "by", "be", "was", "were", "will", "not", "but", "all",
    "we", "they", "he", "she", "my", "me", "who", "when", "which", "do",
    "does", "did", "our", "us", "about", "into", "than", "then", "now",
    "more", "most", "one", "two", "com", "here",
}
WORD_RE = re.compile(r"[a-zA-ZåäöÅÄÖ]{3,}")


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def load_news_domains() -> dict[str, str]:
    with NEWS_DOMAINS_FILE.open(encoding="utf-8") as f:
        groups = yaml.safe_load(f) or {}
    return {domain: category for category, domains in groups.items() for domain in domains}


def main() -> None:
    domain_to_category = load_news_domains()

    with SOURCE.open(encoding="utf-8") as f:
        data = json.load(f)

    visits_per_domain: Counter[str] = Counter()
    words_per_domain: dict[str, Counter[str]] = defaultdict(Counter)
    matched_titles = 0

    for entry in data.get("Browser History", []):
        domain = domain_of(entry.get("url", ""))
        if domain not in domain_to_category:
            continue
        title = (entry.get("title") or "").strip()
        if not title or title == domain:
            continue
        visits_per_domain[domain] += 1
        matched_titles += 1
        for word in WORD_RE.findall(title.lower()):
            if word not in STOPWORDS:
                words_per_domain[domain][word] += 1

    # Ord som förekommer i mer än hälften av en domäns titlar är sajtens
    # eget namn/tagline (boilerplate), inte ett artikelämne - filtrera bort
    # dem per domän innan orden slås ihop till kategori-nivå.
    words_per_category: dict[str, Counter[str]] = defaultdict(Counter)
    words_total: Counter[str] = Counter()
    for domain, counter in words_per_domain.items():
        threshold = visits_per_domain[domain] * 0.3
        category = domain_to_category[domain]
        for word, count in counter.items():
            if count > threshold:
                continue
            words_per_category[category][word] += count
            words_total[word] += count

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "matched_titles": matched_titles,
                "visits_per_domain": visits_per_domain.most_common(),
                "words_total": words_total.most_common(300),
                "words_per_category": {cat: c.most_common(100) for cat, c in words_per_category.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"{matched_titles} besök med titel på {len(visits_per_domain)} kända nyhetsdomäner.")
    print(f"Fullständigt resultat: {OUTPUT}\n")

    print("Besök per domän:")
    for domain, count in visits_per_domain.most_common():
        print(f"  {count:5d}  {domain}  ({domain_to_category[domain]})")

    print(f"\nTopp {TOP_N_PRINTED} ord totalt:")
    for word, count in words_total.most_common(TOP_N_PRINTED):
        print(f"  {count:5d}  {word}")

    for category, counter in words_per_category.items():
        print(f"\nTopp 10 ord — {category}:")
        for word, count in counter.most_common(10):
            print(f"  {count:5d}  {word}")


if __name__ == "__main__":
    main()
