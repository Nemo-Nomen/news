"""Sammanställer det dagliga brevets strukturerade JSON
(data/profile/brief/<datum>.json, se config/brief_schema.md) från
kategorivisa utkast som Fas 6 skriver under kureringen
(data/profile/brief_draft/<kategori>.json).

Räknar ut deterministiska id:n (SHA-256 av kallor[0]['lank'], se
brief_schema.py) mekaniskt - Claude ska aldrig räkna hashar för hand,
opålitligt och onödigt när det redan finns kod för det.

Körs lokalt, gratis, ingen Claude behövs för själva sammanställningen
(bara för att skriva utkasten i föregående steg).
"""

import datetime
import json
from pathlib import Path

from brief_schema import CATEGORIES, empty_brief, make_id

DRAFT_DIR = Path("data/profile/brief_draft")
OUT_DIR = Path("data/profile/brief")


def load_draft(category: str) -> list:
    path = DRAFT_DIR / f"{category}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    now = datetime.datetime.now().astimezone()
    brief = empty_brief(now.isoformat(timespec="seconds"))

    for category in CATEGORIES:
        items = load_draft(category)
        for item in items:
            if not item.get("kallor"):
                raise ValueError(f"Nyhet utan kallor i {category}: {item.get('rubrik')}")
            item["id"] = make_id(item["kallor"][0]["lank"])
            item["kategori"] = category
        brief["kategorier"][category] = items

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{now.date().isoformat()}.json"
    out_file.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(len(v) for v in brief["kategorier"].values())
    print(f"Sparat: {out_file} ({total} nyheter totalt)")


if __name__ == "__main__":
    main()
