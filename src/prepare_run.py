"""Kör alla mekaniska förberedelsesteg i det dagliga kureringsjobbet i ett
enda anrop: kandidathämtning, internationella källor, Hacker News,
nyhetsbrev, sammanslagning för ALLA sex kategorier och
betygssammanfattningen.

Ett anrop istället för ~20 separata sparar Claude-turer och minskar
risken att körningen hänger på en behörighetsfråga för ett nytt
kommando. Ett steg som misslyckas stoppar inte resten - felen listas
sist.

Förutsätter att Claude redan skrivit eventuella finance-news-träffar
till data/profile/candidates_raw/<kategori>_mcp.json (läses av
merge_candidates.py).
"""

import traceback

import fetch_candidates
import fetch_hackernews
import fetch_newsletter_feeds
import fetch_trusted_international
import merge_candidates
import read_ratings_summary
from brief_schema import CATEGORIES


def run(label: str, fn, *args, failures: list) -> None:
    print(f"\n=== {label} ===")
    try:
        fn(*args)
    except (Exception, SystemExit) as exc:
        print(f"MISSLYCKADES: {exc}")
        traceback.print_exc()
        failures.append(f"{label}: {exc}")


def main() -> None:
    failures: list = []

    for category in CATEGORIES:
        run(f"Kandidater (Google Nyheter): {category}", fetch_candidates.main, category, failures=failures)
    run("Betrodda internationella källor", fetch_trusted_international.main, failures=failures)
    run("Hacker News (AI)", fetch_hackernews.main, failures=failures)
    run("Nyhetsbrev", fetch_newsletter_feeds.main, failures=failures)
    for category in CATEGORIES:
        run(f"Sammanslagning: {category}", merge_candidates.main, category, failures=failures)
    run("Betygssammanfattning", read_ratings_summary.main, failures=failures)

    print("\n=== Klart ===")
    if failures:
        print("Steg som misslyckades (fortsätt ändå, notera i slutsammanfattningen):")
        for f in failures:
            print(f"  - {f}")
    else:
        print("Alla steg lyckades.")


if __name__ == "__main__":
    main()
