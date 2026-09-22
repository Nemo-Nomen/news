"""Fas 5, tunn skiva: hämta nyhetskandidater brett via Google Nyheter RSS-sök
(inte begränsat till historiskt bekräftade källor), poängsätt mot profilen
och skriv en rankad kandidatlista.

poäng = intressematch x trend x färskhet (se PROJECT_PLAN.md avsnitt 6).
Kandidaterna är publika nyhetsrubriker, inte personlig data - inget
läsförbud gäller dem.
"""

import json
import math
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

PROFILE_FILE = Path("data/profile/profile.json")
QUERIES_FILE = Path("config/rss_queries.yaml")
SOURCE_EXCLUSIONS_FILE = Path("config/candidate_source_exclusions.yaml")
OUTPUT_DIR = Path("data/profile/candidates")

POANG_TROSKEL = 0.03  # "hänt något"-tröskel, empiriskt startvärde - justeras
FARSKHET_HALVERINGSTID_TIMMAR = 48
MAX_KANDIDATER = 10  # sänkt från 15 (beslut 2026-09-22, se PROJECT_PLAN.md)
MAX_PER_KALLA = 2  # källdiversifiering (Metod C) - tak per utgivare per körning

STOPWORDS = {
    "och", "att", "det", "som", "för", "med", "den", "på", "av", "en", "ett",
    "är", "till", "om", "du", "jag", "vi", "de", "har", "kan", "inte", "var",
    "the", "a", "an", "of", "to", "in", "for", "on", "and", "is", "with",
}
WORD_RE = re.compile(r"[a-zA-ZåäöÅÄÖ]{3,}")
HM_RE = re.compile(r"\bH\s*&\s*M\b", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """H&M innehåller '&' som annars delar upp det i två för korta
    tokens ('H', 'M') - normalisera till ett matchbart ord innan
    ordextraktion, både för profiltext och kandidattitlar."""
    return HM_RE.sub("HANDM", text)  # min 3 tecken krävs av WORD_RE, "HM" är för kort


def flatten_text(value) -> list:
    """Plockar ut alla strängar ur godtyckligt nästlade dict/list-strukturer
    (t.ex. extra.konkurrenter.primara/sekundara), inte bara toppnivåfälten."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        parts = []
        for v in value.values():
            parts += flatten_text(v)
        return parts
    if isinstance(value, list):
        parts = []
        for v in value:
            parts += flatten_text(v)
        return parts
    return []


def profile_words(category: dict) -> set:
    text_parts = list(category.get("amnen_handskrivna", []))
    text_parts += [w for w, _ in category.get("topp_ord_nyhetssajter", [])]
    text_parts += flatten_text(category.get("extra", {}))
    words = set()
    for part in text_parts:
        words |= set(WORD_RE.findall(normalize_text(part).lower()))
    return words - STOPWORDS


def significant_words(title: str) -> set:
    return set(WORD_RE.findall(normalize_text(title).lower())) - STOPWORDS


PREFIX_LEN = 4  # fångar svenska sammansättningar (guld+pris, börs+fall) utan full stemmer


def word_overlap(profile_word_set: set, title_words: set) -> int:
    """Matchar på prefix (minst PREFIX_LEN tecken) istället för hela ordet,
    så "guldpris"/"guldkantad" räknas som träff mot profilordet "guld"."""
    profile_prefixes = {w[:PREFIX_LEN] for w in profile_word_set if len(w) >= PREFIX_LEN}
    matched = {w for w in title_words if len(w) >= PREFIX_LEN and w[:PREFIX_LEN] in profile_prefixes}
    return len(matched)


RECENCY_WINDOW = "when:3d"  # begränsa Google Nyheter till senaste 3 dygnen


def fetch_google_news_rss(query: str) -> list:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} {RECENCY_WINDOW}", "hl": "sv", "gl": "SE", "ceid": "SE:sv"}
    )
    with urllib.request.urlopen(url, timeout=15) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall("./channel/item"):
        title_raw = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date_raw = item.findtext("pubDate", "")
        source_el = item.find("source")
        source = source_el.text if source_el is not None else None
        # Google Nyheter formaterar ofta titeln som "Rubrik - Källa"
        title = title_raw.rsplit(" - ", 1)[0] if " - " in title_raw else title_raw
        try:
            pub_date = parsedate_to_datetime(pub_date_raw)
        except (TypeError, ValueError):
            pub_date = None
        items.append({"title": title, "link": link, "source": source, "pub_date": pub_date})
    return items


def score(title: str, pub_date, profile_word_set: set, trend_group_sources: dict) -> dict:
    words = significant_words(title)
    matches = word_overlap(profile_word_set, words)
    intressematch = min(1.0, matches / 3)

    if pub_date is not None:
        import datetime

        hours_old = (datetime.datetime.now(datetime.timezone.utc) - pub_date).total_seconds() / 3600
        farskhet = math.exp(-hours_old / FARSKHET_HALVERINGSTID_TIMMAR)
    else:
        farskhet = 0.5  # okänt datum - varken straffa eller gynna hårt

    group_key = tuple(sorted(words)[:3])  # enkel, billig grupperingsnyckel
    # Trend = antal OBEROENDE källor i samma grupp, inte antal artiklar -
    # annars räknas en enskild källas upprepade inlägg som "trend"
    trend = min(1.0, len(trend_group_sources.get(group_key, set())) / 3)

    return {
        "intressematch": round(intressematch, 3),
        "trend": round(trend, 3),
        "farskhet": round(farskhet, 3),
        "poang": round(intressematch * trend * farskhet, 4),
    }


def build_trend_groups(items: list) -> dict:
    trend_group_sources: dict = {}
    for item in items:
        words = significant_words(item["title"])
        key = tuple(sorted(words)[:3])
        trend_group_sources.setdefault(key, set()).add(item["source"])
    return trend_group_sources


def group_key_of(title: str) -> tuple:
    return tuple(sorted(significant_words(title))[:3])


def rank_and_select(items: list, profile_word_set: set) -> list:
    """Grupperar för trend, poängsätter, filtrerar på tröskel och
    källdiversifiering. items: dicts med title/link/source/pub_date
    (pub_date som datetime eller None). Återanvänds av main() och av
    merge_candidates.py (svenska + internationella källor ihopslagna)."""
    trend_group_sources = build_trend_groups(items)

    scored = []
    for item in items:
        s = score(item["title"], item["pub_date"], profile_word_set, trend_group_sources)
        scored.append({**item, "pub_date": item["pub_date"].isoformat() if item["pub_date"] else None, **s})

    scored.sort(key=lambda x: -x["poang"])
    over_threshold = [c for c in scored if c["poang"] >= POANG_TROSKEL]

    # Källdiversifiering (Metod C): tak per källa så att en enda
    # högfrekvent utgivare inte kan fylla hela listan.
    per_source_count: Counter = Counter()
    selected = []
    for c in over_threshold:
        if per_source_count[c["source"]] >= MAX_PER_KALLA:
            continue
        selected.append(c)
        per_source_count[c["source"]] += 1
        if len(selected) >= MAX_KANDIDATER:
            break
    return selected


def load_source_exclusions() -> set:
    if not SOURCE_EXCLUSIONS_FILE.exists():
        return set()
    groups = yaml.safe_load(SOURCE_EXCLUSIONS_FILE.read_text(encoding="utf-8")) or {}
    return {source.lower() for sources in groups.values() for source in sources}


def main() -> None:
    category = sys.argv[1] if len(sys.argv) > 1 else "ekonomi"

    profile = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    queries = yaml.safe_load(QUERIES_FILE.read_text(encoding="utf-8")).get(category, [])
    if not queries:
        raise SystemExit(f"Inga sökfrågor för kategorin '{category}' i {QUERIES_FILE}")

    profile_word_set = profile_words(profile[category])

    excluded_sources = load_source_exclusions()

    all_items = []
    seen_links = set()
    skipped_noise = 0
    for query in queries:
        print(f"Hämtar: {query}")
        for item in fetch_google_news_rss(query):
            if item["link"] in seen_links:
                continue
            seen_links.add(item["link"])
            if item["source"] and item["source"].lower() in excluded_sources:
                skipped_noise += 1
                continue
            all_items.append(item)
    if skipped_noise:
        print(f"({skipped_noise} artiklar från exkluderade brus-källor hoppades över)")

    # Spara hela råpoolen (inte bara slutresultatet) så internationella
    # kandidater kan slås ihop med den innan trend/rankning i merge_candidates.py.
    raw_dir = OUTPUT_DIR.parent / "candidates_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / f"{category}_sverige.json"
    raw_file.write_text(
        json.dumps(
            [{**i, "pub_date": i["pub_date"].isoformat() if i["pub_date"] else None} for i in all_items],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    candidates = rank_and_select(all_items, profile_word_set)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{category}.json"
    output_file.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{len(all_items)} unika artiklar hämtade (sparade i {raw_file}).")
    print(f"Topp {len(candidates)} sparade till {output_file}:\n")
    for c in candidates:
        print(f"  {c['poang']:.3f}  ({c['intressematch']}/{c['trend']}/{c['farskhet']})  {c['title']}  [{c['source']}]")


if __name__ == "__main__":
    main()
