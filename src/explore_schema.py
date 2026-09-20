"""Fas 1: skriv ut bara fältnamn/struktur för Takeout-filer, aldrig värden."""

import csv
import json
import sys
from pathlib import Path

SKIP_SUFFIXES = {".html", ".ics", ".mbox"}


def json_key_paths(obj, prefix="") -> set[str]:
    paths: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            paths.add(path)
            paths |= json_key_paths(value, path)
    elif isinstance(obj, list):
        for item in obj[:5]:
            paths |= json_key_paths(item, f"{prefix}[]")
    return paths


def explore(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                with path.open(encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[JSON] {rel}")
                for key_path in sorted(json_key_paths(data)):
                    print(f"    {key_path}")
            elif suffix == ".csv":
                with path.open(encoding="utf-8", newline="") as f:
                    header = next(csv.reader(f), [])
                print(f"[CSV]  {rel}")
                print(f"    kolumner: {header}")
            elif suffix in SKIP_SUFFIXES:
                size = path.stat().st_size
                print(f"[{suffix.lstrip('.').upper()}]  {rel}  ({size} bytes — ostrukturerad, hoppas över i Fas 1)")
            else:
                print(f"[?]    {rel}  (filtyp {suffix!r} hanteras inte ännu)")
        except Exception as exc:
            print(f"[FEL]  {rel}: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/takeout/2026-09-20/extracted/Takeout")
    explore(target)
