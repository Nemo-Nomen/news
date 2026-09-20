"""Kategoriserar YouTube-kanaler per projektkategori baserat på videons
faktiska innehåll (YouTubes egen videokategori, från fetch_youtube_metadata.py)
istället för att gissa utifrån kanalnamnet eller tvinga in hela kanalen
i en enda kategori.

En kanal kan bidra olika många videor till olika kategorier - t.ex. en
kanal som är 80% Autos & Vehicles och 20% Science & Technology räknas
in i Nöje på båda grunderna (de mappar till samma projektkategori här,
men principen gäller generellt).
"""

import json
from collections import defaultdict
from pathlib import Path

import yaml

METADATA_FILE = Path("data/profile/youtube_metadata.json")
MAPPING_FILE = Path("config/youtube_category_mapping.yaml")
OUTPUT = Path("data/profile/youtube_by_content.json")


def main() -> None:
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    mapping = yaml.safe_load(MAPPING_FILE.read_text(encoding="utf-8")) or {}

    channels_per_category: dict = defaultdict(lambda: defaultdict(int))
    unmapped_counts: dict = defaultdict(int)

    for channel, category_counts in metadata["category_by_channel"].items():
        for yt_category, count in category_counts:
            project_categories = mapping.get(yt_category)
            if not project_categories:
                unmapped_counts[yt_category] += count
                continue
            for project_category in project_categories:
                channels_per_category[project_category][channel] += count

    result = {
        cat: sorted(channels.items(), key=lambda kv: -kv[1])
        for cat, channels in channels_per_category.items()
    }

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Skrev {OUTPUT}\n")
    for cat, channels in result.items():
        total = sum(c for _, c in channels)
        print(f"{cat}: {len(channels)} kanaler, {total} videor totalt")
        for channel, count in channels[:8]:
            print(f"    {count:4d}  {channel}")

    print("\nOmappade YouTube-kategorier (ingen projektkategori tilldelad):")
    for yt_cat, count in sorted(unmapped_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {count:5d}  {yt_cat}")


if __name__ == "__main__":
    main()
