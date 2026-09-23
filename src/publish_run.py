"""Kör publiceringsstegen i det dagliga kureringsjobbet i ett enda anrop:
sammanställ brief-JSON från utkasten, ladda upp till Supabase och spara
tidsstämpeln för nästa körnings "sedan sist"-jämförelse.

Tidsstämpeln skrivs bara om uppladdningen lyckats, så en misslyckad
körning inte får nästa körning att tro att brevet redan publicerats.
"""

import datetime
import json
from pathlib import Path

import save_brief
import upload_brief

LAST_RUN_FILE = Path("data/profile/last_brief_run.json")


def main() -> None:
    save_brief.main()
    upload_brief.main()
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    LAST_RUN_FILE.write_text(json.dumps({"tid": now}), encoding="utf-8")
    print(f"Tidsstämpel sparad: {now}")


if __name__ == "__main__":
    main()
