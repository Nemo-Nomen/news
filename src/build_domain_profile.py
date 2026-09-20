"""Fas 2 (tunn skiva): räkna besök per domän från Chrome/Historik.json.

Domännamn + antal räknas som aggregat (inte rå URL/titel), så resultatet
får visas för Claude. Hela listan sparas i data/ (git-ignorerad); bara
toppen skrivs ut i terminalen.
"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import yaml

SOURCE = Path("data/raw/takeout/2026-09-20/extracted/Takeout/Chrome/Historik.json")
EXCLUSIONS_FILE = Path("config/domain_exclusions.yaml")
OUTPUT_RAW = Path("data/profile/domain_counts.json")
OUTPUT_FILTERED = Path("data/profile/domain_counts_filtered.json")
TOP_N_PRINTED = 25


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def load_exclusions() -> set[str]:
    if not EXCLUSIONS_FILE.exists():
        return set()
    with EXCLUSIONS_FILE.open(encoding="utf-8") as f:
        groups = yaml.safe_load(f) or {}
    return {domain for domains in groups.values() for domain in domains}


def main() -> None:
    with SOURCE.open(encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("Browser History", [])
    counts: Counter[str] = Counter()
    skipped = 0
    for entry in entries:
        url = entry.get("url", "")
        domain = domain_of(url)
        if domain:
            counts[domain] += 1
        else:
            skipped += 1

    ranked = counts.most_common()
    excluded = load_exclusions()
    filtered = [(domain, count) for domain, count in ranked if domain not in excluded]
    excluded_visits = sum(count for domain, count in ranked if domain in excluded)

    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_RAW.open("w", encoding="utf-8") as f:
        json.dump(
            {"total_visits": len(entries), "skipped": skipped, "domains": ranked},
            f,
            ensure_ascii=False,
            indent=2,
        )
    with OUTPUT_FILTERED.open("w", encoding="utf-8") as f:
        json.dump(
            {"excluded_domains": sorted(excluded), "excluded_visits": excluded_visits, "domains": filtered},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Totalt {len(entries)} besök, {len(ranked)} unika domäner, {skipped} utan giltig domän.")
    print(f"{len(excluded)} domäner exkluderade från profilen ({excluded_visits} besök): {sorted(excluded)}")
    print(f"Rådata (oexkluderad): {OUTPUT_RAW}")
    print(f"Profil-redo (exkluderad): {OUTPUT_FILTERED}")
    print(f"\nTopp {TOP_N_PRINTED} domäner (efter exkludering):")
    for domain, count in filtered[:TOP_N_PRINTED]:
        print(f"  {count:6d}  {domain}")


if __name__ == "__main__":
    main()
