"""Slår ihop svenska (Google Nyheter, fetch_candidates.py) och
internationella (finance-news MCP, hämtat av Claude interaktivt - se
data/profile/candidates_raw/{category}_internationellt.json) kandidater
innan trend/poängsättning, så en händelse som täcks av både svenska och
internationella källor får rätt trend-signal.

Den internationella filen skrivs för hand/av Claude just nu eftersom
finance-news bara är tillgängligt via MCP, inte från ett fristående
skript - se PROJECT_PLAN.md avsnitt 6 för arkitekturnotisen.
"""

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_candidates import PROFILE_FILE, profile_words, rank_and_select

RAW_DIR = Path("data/profile/candidates_raw")
OUTPUT_DIR = Path("data/profile/candidates")


def load_raw(path: Path) -> list:
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        if item.get("pub_date"):
            item["pub_date"] = datetime.datetime.fromisoformat(item["pub_date"])
        else:
            item["pub_date"] = None
    return items


def main() -> None:
    category = sys.argv[1] if len(sys.argv) > 1 else "ekonomi"

    profile = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    profile_word_set = profile_words(profile[category])

    sverige = load_raw(RAW_DIR / f"{category}_sverige.json")
    internationellt = load_raw(RAW_DIR / f"{category}_internationellt.json")
    combined = sverige + internationellt

    print(f"{len(sverige)} svenska + {len(internationellt)} internationella = {len(combined)} kandidater totalt.")

    candidates = rank_and_select(combined, profile_word_set)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{category}.json"
    output_file.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Topp {len(candidates)} (svenskt + internationellt ihopslaget) sparade till {output_file}:\n")
    for c in candidates:
        flagga = "🌍" if c["source"] in {i["source"] for i in internationellt} else "🇸🇪"
        print(f"  {flagga} {c['poang']:.3f}  ({c['intressematch']}/{c['trend']}/{c['farskhet']})  {c['title'][:65]}  [{c['source']}]")


if __name__ == "__main__":
    main()
