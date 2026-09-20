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
- [ ] Fas 1: integritetsgrind (domänlista bort innan något annat bearbetas — enheter filtreras inte)
- [ ] Fas 2: baslinjeprofil (`profile.json`)
