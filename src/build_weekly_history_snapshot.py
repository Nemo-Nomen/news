"""Fas 3: läser en kopia av lokala Chrome-historiken, aggregerar besök per
domän (samma exkluderingar som build_domain_profile.py) och slår ihop med
tidigare veckors aggregat - idempotent, bara nya besök sen förra körningen
räknas in.

Chrome sparar tid som mikrosekunder sedan 1601-01-01 (WebKit-epok), inte
unix-tid - konverteras innan jämförelse.

Skriver bara ut aggregat (domän + antal + total tittid) - aldrig enskilda
URL:er eller titlar.
"""

import datetime
import json
import shutil
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import yaml

CHROME_HISTORY = Path.home() / "Library/Application Support/Google/Chrome/Default/History"
SNAPSHOT_DIR = Path("data/raw/chrome_history")
EXCLUSIONS_FILE = Path("config/domain_exclusions.yaml")
STATE_FILE = Path("data/profile/weekly_history_state.json")
OUTPUT_FILE = Path("data/profile/weekly_domain_counts.json")

WEBKIT_EPOCH = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)


def webkit_to_datetime(webkit_us: int) -> datetime.datetime:
    return WEBKIT_EPOCH + datetime.timedelta(microseconds=webkit_us)


def datetime_to_webkit(dt: datetime.datetime) -> int:
    return int((dt - WEBKIT_EPOCH).total_seconds() * 1_000_000)


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def load_exclusions() -> set:
    if not EXCLUSIONS_FILE.exists():
        return set()
    groups = yaml.safe_load(EXCLUSIONS_FILE.read_text(encoding="utf-8")) or {}
    return {d for domains in groups.values() for d in domains}


def copy_snapshot() -> Path:
    today = datetime.date.today().isoformat()
    snapshot_dir = SNAPSHOT_DIR / today
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    dest = snapshot_dir / "History"
    shutil.copy2(CHROME_HISTORY, dest)
    return dest


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_processed_webkit_time": 0, "runs": []}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def load_existing_output() -> dict:
    if not OUTPUT_FILE.exists():
        return {}
    data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    return {d["domän"]: d for d in data.get("domaner", [])}


def main() -> None:
    excluded = load_exclusions()
    state = load_state()
    last_processed = state["last_processed_webkit_time"]

    snapshot_path = copy_snapshot()

    conn = sqlite3.connect(f"file:{snapshot_path}?mode=ro", uri=True)
    rows = conn.execute(
        """
        SELECT urls.url, visits.visit_time, visits.visit_duration
        FROM visits JOIN urls ON visits.url = urls.id
        WHERE visits.visit_time > ?
        """,
        (last_processed,),
    ).fetchall()
    conn.close()

    domain_counts: dict = load_existing_output()
    max_visit_time = last_processed
    new_visits = 0

    for url, visit_time, visit_duration in rows:
        domain = domain_of(url)
        if not domain or domain in excluded:
            continue
        entry = domain_counts.setdefault(domain, {"domän": domain, "besök": 0, "tittid_sekunder": 0})
        entry["besök"] += 1
        entry["tittid_sekunder"] += visit_duration // 1_000_000  # mikrosekunder -> sekunder
        new_visits += 1
        max_visit_time = max(max_visit_time, visit_time)

    ranked = sorted(domain_counts.values(), key=lambda d: -d["besök"])
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps({"uppdaterad": datetime.datetime.now().isoformat(), "domaner": ranked}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    state["last_processed_webkit_time"] = max_visit_time
    state["runs"].append({"tid": datetime.datetime.now().isoformat(), "nya_besök": new_visits})
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{new_visits} nya besök inräknade sen förra körningen.")
    print(f"Totalt {len(ranked)} domäner i det ackumulerade veckoaggregatet.")
    print(f"Sparat: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
