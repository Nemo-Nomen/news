"""Fas 2 (tunn skiva): räkna besök per domän från Chrome/Historik.json.

Domännamn + antal räknas som aggregat (inte rå URL/titel), så resultatet
får visas för Claude. Hela listan sparas i data/ (git-ignorerad); bara
toppen skrivs ut i terminalen.
"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

SOURCE = Path("data/raw/takeout/2026-09-20/extracted/Takeout/Chrome/Historik.json")
OUTPUT = Path("data/profile/domain_counts.json")
TOP_N_PRINTED = 25


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


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

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(
            {"total_visits": len(entries), "skipped": skipped, "domains": ranked},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Totalt {len(entries)} besök, {len(ranked)} unika domäner, {skipped} utan giltig domän.")
    print(f"Fullständig lista: {OUTPUT}")
    print(f"\nTopp {TOP_N_PRINTED} domäner:")
    for domain, count in ranked[:TOP_N_PRINTED]:
        print(f"  {count:6d}  {domain}")


if __name__ == "__main__":
    main()
