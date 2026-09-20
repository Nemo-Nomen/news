"""Fas 2: slå ihop interests.yaml + alla aggregat i data/profile/ till en
enda profile.json, strukturerad per kategori (Jobb, Ekonomi, Politik,
Nöje, AI, Skvaller).

Allt som skrivs ut/sparas här är redan diskuterat öppet i konversationen
(ämnesetiketter, domännamn+antal, kanalnamn+antal) - inga nya råa detaljer.
"""

import json
from pathlib import Path

import yaml

PROFILE_DIR = Path("data/profile")
OUTPUT = PROFILE_DIR / "profile.json"

CATEGORIES = ["jobb", "ekonomi", "politik", "noje", "ai", "skvaller"]

# news_domains.yaml- och youtube_channels.yaml-grupper -> de sex kategorierna
GROUP_TO_CATEGORY = {
    "ekonomi": "ekonomi",
    "politik_makro": "politik",
    "politik_makro_aggregator": "politik",
    "skvaller": "skvaller",
    "noje_teknik": "noje",
    "noje_bilar": "noje",
    "noje_hantverk": "noje",
}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def domains_per_category(news_domains: dict, domain_counts: dict) -> dict:
    counts = dict(domain_counts.get("domains", []))
    result = {cat: [] for cat in CATEGORIES}
    for group, domains in news_domains.items():
        category = GROUP_TO_CATEGORY.get(group)
        if not category:
            continue
        for domain in domains:
            if domain in counts:
                result[category].append({"domän": domain, "besök": counts[domain]})
    for cat in result:
        result[cat].sort(key=lambda d: -d["besök"])
    return result


def channels_per_category(youtube_channels: dict, channel_counts: dict, by_content: dict) -> dict:
    """Innehållsbaserat (youtube_by_content.json, YouTubes egen videokategori
    per video) är förstahandskälla för ekonomi/politik/noje - se beslut
    2026-09-20 ("kategorisera baserat på innehåll istället för kanal").
    Manuell kanallista (youtube_channels.yaml) fyller bara på för grupper
    som inte täcks av en YouTube-kategori-mappning (hantverk, skvaller).
    """
    counts = dict(channel_counts.get("channels", []))
    result = {cat: [] for cat in CATEGORIES}

    for cat, channels in by_content.items():
        if cat in result:
            result[cat].extend({"kanal": ch, "videor": n, "kalla": "innehåll"} for ch, n in channels)

    CONTENT_COVERED_GROUPS = {"ekonomi", "politik_makro", "politik_makro_aggregator", "noje_teknik", "noje_bilar"}
    for group, channels in youtube_channels.items():
        if group in CONTENT_COVERED_GROUPS:
            continue  # ersatt av innehållsbaserad kategorisering ovan
        category = GROUP_TO_CATEGORY.get(group)
        if not category:
            continue
        for channel in channels:
            if channel in counts:
                result[category].append({"kanal": channel, "videor": counts[channel], "kalla": "kanal (manuell)"})

    for cat in result:
        result[cat].sort(key=lambda d: -d["videor"])
    return result


def words_per_category(news_titles: dict) -> dict:
    raw = news_titles.get("words_per_category", {})
    result = {cat: {} for cat in CATEGORIES}
    for group, words in raw.items():
        category = GROUP_TO_CATEGORY.get(group)
        if not category:
            continue
        for word, count in words:
            result[category][word] = result[category].get(word, 0) + count
    return {cat: sorted(words.items(), key=lambda w: -w[1])[:15] for cat, words in result.items()}


def main() -> None:
    interests = load_yaml(Path("config/interests.yaml"))
    news_domains = load_yaml(Path("config/news_domains.yaml"))
    youtube_channels = load_yaml(Path("config/youtube_channels.yaml"))
    domain_counts = load_json(PROFILE_DIR / "domain_counts_filtered.json")
    channel_counts = load_json(PROFILE_DIR / "youtube_channel_counts.json")
    news_titles = load_json(PROFILE_DIR / "news_titles_analysis.json")
    by_content = load_json(PROFILE_DIR / "youtube_by_content.json")

    domaner = domains_per_category(news_domains, domain_counts)
    kanaler = channels_per_category(youtube_channels, channel_counts, by_content)
    ord_per_kategori = words_per_category(news_titles)

    # interests.yaml-nycklar matchar inte alltid visningsnamnen 1:1
    interests_key_map = {"jobb": "jobb", "ekonomi": "ekonomi", "politik": "politik_makro", "noje": "noje", "ai": "ai", "skvaller": "skvaller"}

    profile = {}
    for cat in CATEGORIES:
        interests_entry = interests.get(interests_key_map[cat], {})
        profile[cat] = {
            "amnen_handskrivna": interests_entry.get("amnen", []),
            "extra": {k: v for k, v in interests_entry.items() if k not in ("amnen", "uteslutningar")},
            "topp_ord_nyhetssajter": ord_per_kategori.get(cat, []),
            "domaner": domaner.get(cat, []),
            "youtube_kanaler": kanaler.get(cat, []),
        }

    profile["nyhetsbrev_personer"] = interests.get("nyhetsbrev_personer", [])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Skrev {OUTPUT}\n")
    for cat in CATEGORIES:
        p = profile[cat]
        print(f"{cat}: {len(p['amnen_handskrivna'])} handskrivna ämnen, "
              f"{len(p['domaner'])} domäner, {len(p['youtube_kanaler'])} YouTube-kanaler, "
              f"{len(p['topp_ord_nyhetssajter'])} toppord")


if __name__ == "__main__":
    main()
