# Axel News

Personlig nyhetstjänst — läroprojekt. Full plan i [PROJECT_PLAN.md](PROJECT_PLAN.md).
Regler för Claude, särskilt läsförbudet på rådata, i [CLAUDE.md](CLAUDE.md).

## Struktur

- `src/` — kod
- `config/` — `interests.yaml` och annan handskriven konfiguration
- `data/` — rådata och genererade profiler (git-ignorerad, aldrig committad)
  - `data/raw/takeout/<datum>/zips/` — original-zip från Google Takeout
  - `data/raw/takeout/<datum>/extracted/` — uppackad Takeout
- `logs/` — körloggar (git-ignorerad)

## Status

- [x] Fas 0: mappstruktur, git-repo, `.gitignore`, läsförbud i `CLAUDE.md`
- [x] Takeout-baslinje (2026-09-20) uppackad i `data/raw/takeout/2026-09-20/`
- [x] Fas 1: schemautforskning (ingen filtrering — inget exkluderas, varken enheter eller domäner)
- [x] Fas 2: baslinjeprofil (`profile.json`, sex kategorier: Jobb, Ekonomi, Politik, Nöje, AI, Skvaller)
- [x] "Tunn skiva": första manuella testbrevet kört och godkänt
- [x] Fas 5 (v1): nyhetsinsamling + poängsättning + källdiversifiering, alla sex kategorier — se `src/fetch_candidates.py`, `src/merge_candidates.py`
- [x] Fas 3: lokal veckovis historikläsning + schemaläggning (launchd, söndagar 09:00) — se `src/build_weekly_history_snapshot.py`
- [ ] Fas 4b: LinkedIn-import (valfri)
- [x] Fas 6: schemalagd uppgift `axel-news-brief` — kör dagligen ~07:14 (cron `0 7 * * *`), klar ~07:45, se `/Users/axel/.claude/scheduled-tasks/axel-news-brief/SKILL.md`. Kräver att Claude-appen är öppen vid körningstillfället
- [ ] Fas 7: feedback-loop

## Köra Fas 5 manuellt

```bash
.venv/bin/python3 src/fetch_candidates.py <kategori>   # jobb/ekonomi/politik/noje/ai/skvaller
.venv/bin/python3 src/merge_candidates.py <kategori>   # om internationella kandidater hämtats också
```

## Fas 3: veckoskriptet

Körs automatiskt varje söndag 09:00 via launchd (`com.axelnews.weeklyhistory`,
installerad i `~/Library/LaunchAgents/`). Kräver Full Disk Access för
Claude-appen (System­inställningar → Sekretess och integritet →
Fullständig diskåtkomst) — både huvudappen och en inbäddad
`claude-code`-app behöver läggas till separat.

```bash
launchctl list | grep axelnews          # kolla status
.venv/bin/python3 src/build_weekly_history_snapshot.py   # kör manuellt
```
