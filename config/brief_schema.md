# Datastruktur: brevet (för hemsidan, Supabase, Fas 6/7)

## En nyhet (`data/profile/brief/<datum>.json` → `kategorier.<kategori>[]`)

```json
{
  "id": "a3f9c1e2b7d4",
  "rubrik": "Riksbanken höjer inte i september",
  "sammanfattning": "Inflationen kom in lägre än väntat - marknaden slutade nästan helt prisa in en höjning.",
  "las_mer": "En längre paragraf med mer sammanhang - vad som hänt, vilka källor som rapporterat det, eventuella olika vinklar.",
  "varfor_viktigt": "En rad om varför just den här personen får den här nyheten - kopplat till profilen (t.ex. 'matchar ditt intresse för Riksbanken/makroekonomi').",
  "kalla": "Dagens industri",
  "lank": "https://...",
  "publicerad": "2026-09-21T08:00:00+02:00",
  "kategori": "politik",
  "nyhetsbrev": false,
  "stort_utomlands_ej_sverige": false,
  "motargument": false
}
```

**`id`** = de första 12 tecknen av SHA-256(`lank`), hex. Deterministiskt - samma länk ger alltid samma id, ingen databas eller state behövs för att räkna ut det. Gör det möjligt att koppla ett betyg till en artikel även om den dyker upp igen en annan vecka.

**`nyhetsbrev` / `stort_utomlands_ej_sverige` / `motargument`** - booleska flaggor, redan beräknade av `fetch_candidates.py`/`merge_candidates.py`. Sidan kan visa en liten badge/ikon för dessa (📬, 🌍, ⚖️) istället för att gissa.

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
  skapad timestamptz default now()
);
```

Enkelt tumme upp/ner, enligt planens Fas 7-beskrivning ("Enkelt betyg per artikel"). En rad per betyg (inte en uppdaterad kolumn), så historik bevaras även om man ändrar sig.
