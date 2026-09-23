# Datastruktur: brevet (för hemsidan, Supabase, Fas 6/7)

## En nyhet (`data/profile/brief/<datum>.json` → `kategorier.<kategori>[]`)

```json
{
  "id": "a3f9c1e2b7d4",
  "rubrik": "Riksbanken höjer inte i september",
  "sammanfattning": "Inflationen kom in lägre än väntat, vilket fick marknaden att nästan helt prisa ut en höjning inför mötet.",
  "las_mer": "En kuraterad text (~30 sekunders läsning, ~100-130 ord) som väver ihop ALLA källor i `kallor` nedan - inte bara den första. Ska läsas som en sammanhållen artikel, inte en lista av separata källsammanfattningar: vad som hänt, eventuella olika vinklar mellan källorna, och varför det är läsvärt. Om bara en källa finns blir texten i praktiken enkällig - inget att sammanställa, det är förväntat, inte ett fel.",
  "varfor_viktigt": "En rad om varför just den här personen får den här nyheten - kopplat till profilen (t.ex. 'matchar ditt intresse för Riksbanken/makroekonomi').",
  "kallor": [
    { "kalla": "Dagens industri", "lank": "https://..." },
    { "kalla": "Riksbanken (pressmeddelande)", "lank": "https://..." }
  ],
  "publicerad": "2026-09-21T08:00:00+02:00",
  "kategori": "politik",
  "nyhetsbrev": false,
  "stort_utomlands_ej_sverige": false,
  "motargument": false
}
```

**`sammanfattning`** - 1 mening, max ~25 ord (ändrat 2026-09-22 från ~3 meningar - anpassat till Omnis nivå-ett-längd: en kort krok som gör att man vill klicka, inte en fullständig bild i sig själv - den fullständiga bilden ligger i `las_mer`).

**Hård regel:** `las_mer` MÅSTE vara längre än `sammanfattning` och innehålla genuint nytt - fler detaljer, siffror, kontext eller konsekvenser - aldrig en kortare omskrivning eller upprepning av sammanfattningen. Poängen med att klicka är att få mer, inte mindre (bugg hittad och fixad 2026-09-22: flera `las_mer`-texter var kortare än den nya 3-menings-sammanfattningen efter att bara `sammanfattning` utökades).

**`id`** = de första 12 tecknen av SHA-256(länken i `kallor[0].lank`, den primära/först hittade källan), hex. Deterministiskt - samma primärlänk ger alltid samma id, ingen databas eller state behövs för att räkna ut det. Gör det möjligt att koppla ett betyg till en artikel även om den dyker upp igen en annan vecka. Om `kallor[0]` byts (t.ex. en bättre källa hittas i efterhand) byts även id:t - accepterad avvägning, samma princip som redan gäller för länkbaserade id:n.

**`kallor`** (tidigare enskilda fälten `kalla`/`lank`) - lista med minst ett objekt `{kalla, lank}`. Flera poster när dublettdetekteringen i kureringen (avsnitt 6 i `PROJECT_PLAN.md`) hittar samma händelse hos flera källor - då slås de ihop till EN nyhet med flera källor istället för flera separata nyheter. Sidan visar länkar till samtliga i den expanderade vyn.

**`nyhetsbrev` / `stort_utomlands_ej_sverige` / `motargument`** - booleska flaggor, redan beräknade av `fetch_candidates.py`/`merge_candidates.py`. Sidan visar en badge för dessa istället för att gissa.

**Bilder borttagna helt (beslut 2026-09-24).** Fältet `bild` och `src/fetch_og_images.py` är borttagna: låg träffsäkerhet (3 av 30 länkar i en mätning) och det var det långsammaste skriptet i körningen (~2,6 s per länk). Kolumnen `bild` i Supabase-tabellen `brief_items` finns kvar men lämnas tom.

## Brevet i sin helhet

```json
{
  "genererad": "2026-09-21T09:00:00+02:00",
  "kategorier": {
    "jobb": [ ... ],
    "ekonomi": [ ... ],
    "politik": [ ... ],
    "noje": [ ... ],
    "ai": [ ... ],
    "skvaller": [ ... ]
  }
}
```

Tomma kategorier har en tom lista `[]`, inte utelämnade helt (enklare för sidan att loopa över alla sex konsekvent).

## Betyg (Supabase-tabell)

```sql
create table ratings (
  id uuid primary key default gen_random_uuid(),
  item_id text not null,        -- matchar "id" ovan (hash av länken)
  betyg text not null check (betyg in ('upp', 'ner')),  -- enkelt, inte 1-5 (Fas 7: "Enkelt betyg per artikel")
  kategori text,                -- sparat VID betygstillfället, se motivering nedan
  kalla text,                   -- sparat VID betygstillfället, se motivering nedan
  skapad timestamptz default now()
);
```

Enkelt tumme upp/ner, enligt planens Fas 7-beskrivning ("Enkelt betyg per artikel"). En rad per betyg (inte en uppdaterad kolumn), så historik bevaras även om man ändrar sig.

**`kategori`/`kalla`** (tillagda 2026-09-22, Fas 7-implementationen) - `brief_items` rensas och skrivs om varje dag (se `src/upload_brief.py`), så ett betyg som bara pekar på ett `item_id` blir meningslöst i efterhand: ingen `join` mot den ursprungliga nyheten är möjlig när den raden är borta. Sidan skickar därför med kategori och primärkälla direkt vid betygstillfället, denormaliserat, så `src/read_ratings_summary.py` kan aggregera ("källa X får ofta nedröstningar") utan att bero på att den ursprungliga nyheten fortfarande finns kvar.

## Feedback (Supabase-tabell, planerad - se PROJECT_PLAN.md avsnitt 7)

```sql
create table feedback (
  id uuid primary key default gen_random_uuid(),
  text text not null,
  status text not null default 'ny' check (status in ('ny', 'hanterad')),
  skapad timestamptz default now(),
  hanterad_at timestamptz
);
```

`status` gör att en Claude Code-session bara behöver fråga efter `status = 'ny'` istället för att läsa allt varje gång, och kan sätta `hanterad`/`hanterad_at` på det som faktiskt åtgärdats i den sessionen - så feedbacken fungerar som en enkel att-göra-lista snarare än en logg som växer obegränsat.
