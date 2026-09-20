"""Läser Takeout/Nyheter/*.txt och skriver ett granskningsbart utkast till config/interests_draft.yaml.

Skriptet läser rådata, men skriver bara ut antal rader per fil till terminalen
- aldrig innehållet. Granska och gallra draft-filen själv innan något av det
förs över till den riktiga config/interests.yaml.
"""

from pathlib import Path

SOURCE_DIR = Path("data/raw/takeout/2026-09-20/extracted/Takeout/Nyheter")
OUTPUT = Path("config/interests_draft.yaml")

FILES = {
    "followed_topics": "followed_topics.txt",
    "followed_sources": "followed_sources.txt",
    "followed_locations": "followed_locations.txt",
    "magazines": "magazines.txt",
    "articles": "articles.txt",
}


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    sections = {key: read_lines(SOURCE_DIR / filename) for key, filename in FILES.items()}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# Utkast importerat från Google Takeout (Nyheter), 2026-09-20.\n")
        f.write("# Oredigerad dump - granska och flytta det du vill spara till\n")
        f.write("# interests.yaml (kategoriserat per Arbete/Investeringar/Politik/Nöje), ta bort resten.\n\n")
        for key, lines in sections.items():
            f.write(f"{key}:\n")
            if not lines:
                f.write("  []\n")
            else:
                for line in lines:
                    f.write(f"  - {line}\n")
            f.write("\n")

    print("Skrev config/interests_draft.yaml. Antal rader per sektion (inte innehållet):")
    for key, lines in sections.items():
        print(f"  {key}: {len(lines)}")


if __name__ == "__main__":
    main()
