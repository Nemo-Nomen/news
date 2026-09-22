# Axel News — projektregler

Se `PROJECT_PLAN.md` för fullständig plan (mål, arkitektur, faser).

## Läsförbud på rådata

`data/` innehåller personlig rådata: Google Takeout (mejl, sökhistorik,
YouTube-historik, Chrome-bokmärken m.m.) och lokal Chrome-historik.

**Claude (i denna mapp) ska aldrig läsa filer under `data/` direkt** —
varken med Read, cat, grep på innehåll, eller genom att öppna dem i
kod som körs interaktivt. Tillåtet:

- Lista filnamn/struktur (`ls`, `find`, `unzip -l`) för att navigera.
- Skriva och köra skript (Python) som läser `data/` och skriver
  aggregerade resultat (t.ex. `data/profile.json`, `data/candidates.json`)
  — men Claude läser inte själva skriptets utdata om utdatan
  innehåller personliga URL:er, titlar eller rå text. Endast teman,
  antal och andra aggregat får visas/läsas.
- Läsa `config/interests.yaml` (skrivs för hand, inga personuppgifter
  om inte jag lagt dit dem själv).

Om en uppgift kräver att läsa rådata för att förstå formatet: skriv ett
skript som skriver ut *bara fältnamn/struktur* (schema), aldrig värden,
och läs den utskriften istället.

## Struktur

- `src/` — kod
- `config/` — `interests.yaml` och annan handskriven konfiguration
- `data/` — rådata och genererade profiler (git-ignorerad, aldrig committad)
- `logs/` — körloggar (git-ignorerad)
- `docs/` — hemsidan (GitHub Pages serveras från denna mapp, kräver namnet `docs` — se PROJECT_PLAN.md avsnitt 7)
- `.github/workflows/` — schemalagda GitHub Actions-jobb (t.ex. börstickerns kursuppdatering)
