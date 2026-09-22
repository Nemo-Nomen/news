"""Hämtar Hacker News toppstories (officiella Firebase-API:et, gratis,
ingen nyckel) och sparar AI-relaterade träffar i samma pool som andra
internationella källor (data/profile/candidates_raw/ai_internationellt.json).

Det här är den "kollaborativa signalen" PROJECT_PLAN.md avsnitt 6
efterlyste - komplement till trendsignalen (hur många MEDIER skrivit
om något) med hur många MÄNNISKOR brydde sig (HN:s poäng/uppröstningar).
Reddit undersöktes samtidigt (2026-09-22) men publik JSON utan inloggning
gav 403 - kräver en registrerad OAuth-app för att komma åt numera,
inte lika enkelt gratis som HN. Pausat, se PROJECT_PLAN.md.

Bara relevant för AI-kategorin - HN domineras av amerikansk tech/
startup-kultur, inte Jobb/Politik/Skvaller. Ett enkelt nyckelordsfilter
på titeln håller nere bruset (HN:s förstasida är brett, inte bara AI).

Körs lokalt, gratis, ingen Claude behövs.
"""

import datetime
import json
import re
import urllib.request
from pathlib import Path

HN_API = "https://hacker-news.firebaseio.com/v0"
OUT_FILE = Path("data/profile/candidates_raw/ai_internationellt.json")
MIN_SCORE = 100  # bara stories med tydligt community-intresse
STORY_LIMIT = 150  # hur många av dagens toppstories vi går igenom

AI_KEYWORDS = re.compile(
    r"\b(ai|artificial intelligence|gpt|llm|openai|anthropic|claude|gemini|"
    r"chatgpt|neural|machine learning|deep learning|transformer|agentic)\b",
    re.IGNORECASE,
)


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AxelNews HN-läsare)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_existing() -> list:
    if not OUT_FILE.exists():
        return []
    return json.loads(OUT_FILE.read_text(encoding="utf-8"))


def main() -> None:
    top_ids = fetch_json(f"{HN_API}/topstories.json")[:STORY_LIMIT]
    existing = load_existing()
    seen_links = {i["link"] for i in existing}
    new_count = 0

    for story_id in top_ids:
        try:
            item = fetch_json(f"{HN_API}/item/{story_id}.json")
        except Exception:
            continue
        if not item or item.get("type") != "story":
            continue
        title = item.get("title", "")
        url = item.get("url")
        score = item.get("score", 0)
        if not url or score < MIN_SCORE or not AI_KEYWORDS.search(title):
            continue
        if url in seen_links:
            continue
        seen_links.add(url)
        pub_date = datetime.datetime.fromtimestamp(item["time"], tz=datetime.timezone.utc)
        existing.append(
            {
                "title": title,
                "link": url,
                "source": "Hacker News",
                "pub_date": pub_date.isoformat(),
                "description": f"{score} poäng, {item.get('descendants', 0)} kommentarer på Hacker News.",
            }
        )
        new_count += 1
        print(f"  ✓  [{score}p] {title[:60]}")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sparat: {OUT_FILE} ({new_count} nya, {len(existing)} totalt)")


if __name__ == "__main__":
    main()
