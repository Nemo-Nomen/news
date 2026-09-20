# Projektplan: personlig nyhetstjänst

Version 1, 20 september 2026. Läroprojekt för nybörjare.

## 1. Mål och ramar

| | |
|---|---|
| **Steg 1** | Nyhetsbrev via mail (först veckovis, sedan ev. dagligt) med *nya* artiklar på teman jag är intresserad av |
| **Steg 2** | Interaktiv app eller hemsida för att djupdyka i nyheterna. Form avgörs senare |
| **Kategorier** | Arbete, Investeringar och privatekonomi, Politik, Nöje (bilar, elektronik m.m.) |
| **Aldrig** | Sammanfatta sådant jag redan läst. Intresseprofilen styr *vilka teman*, inte vad som återberättas |
| **Kurering** | Få, utvalda nyheter per kategori med en rad om varför jag får dem. Inte en flod av träffar |
| **Trend** | Nyheter som är viktiga eller på väg upp just nu, vägda mot mina intressen |
| **Fördjupning** | Djupdykning i en nyhet som kombinerar flera källor: olika medier, marknadsdata, primärkällor och uttalanden från personer jag bevakar |
| **Ramar** | Inga licenser utöver Claude Pro. Bara gratis och öppna nyhetskällor. Läroprojekt: förstå varje steg innan nästa |

## 2. Arkitektur

```
KÄLLOR (lokalt på Macen, Python)
  Takeout-baslinje (engångs, ev. ny senare)
  Lokala Chrome-historiken (varje vecka)
  interests.yaml (personer, ämnen, uteslutningar, skrivs för hand)
        |
        |  1. Filtrera bort jobbenheter och uteslutna domäner  <-- integritetsgrind
        |  2. Bygg intresseprofil (teman + vikt, nyare väger tyngre)
        |  3. Hämta nya artiklar via RSS, ta bort sådant jag redan läst,
        |     ranka mot profilen, behåll topp N per kategori
        v
  profile.json + candidates.json   (inga personliga URL:er, bara teman och publika artikellänkar)
        |
        |  synk via Google Drive for Desktop
        v
CLAUDE PRO: schemalagd uppgift (körs i molnet)
  läser Drive-mappen, skriver highlights per kategori,
  skapar Gmail-utkast (eller skickar) till mig
        |
        v
  Steg 2: djupdykning (se avsnitt 6)
```

**Varför uppdelningen:**
- "Redan läst"-filtret kräver historiken, så det görs lokalt och historiken lämnar aldrig Macen.
- Ingen kod anropar Claude direkt. API-anrop ingår inte i Pro, så det enda som kräver en modell är den schemalagda uppgiften.
- Schemalagda uppgifter körs enligt hjälpcentret i molnet och kan inte kopplas till en mapp på datorn. Därför går data via Google Drive.

## 3. Beslut, förbehåll och obekräftat

| Område | Läge |
|---|---|
| **Jobbenheter i Chrome-synken** | Chrome-inloggningen är privat i webbläsare och på mobil, men jobbdator och jobbtelefon ingår i synken under den privata inloggningen. Fas 1 är fortfarande en obligatorisk grind som tar bort besök från jobbenheterna, eftersom de kan innehålla interna sidor. Kontrollera H&M:s IT- och användarpolicy för privat konto på jobbutrustning, det kan jag inte bedöma |
| **Tillägg och program** | Inget installeras på jobbdatorn utöver det som är standard där. Skript och eventuella spårare körs bara på privat utrustning |
| **Tid på sida** | En svag signal bland flera (se avsnitt 6), aldrig ensam grund. ActivityWatch läggs till på privat dator först om ett test visar behov |
| **Arbetskategorin** | Definieras för hand i `interests.yaml`, inte från surfhistorik |
| **Schemalagda uppgifter på Pro** | Hjälpcentret säger att Cowork på Pro rullas ut. Kontrollera att "Scheduled" finns i din sidomeny |
| **Mailutskick från uppgift** | Obekräftat om det går utan godkännande. Börja med Gmail-utkast |
| **Enhets-ID i Takeout-JSON** | Obekräftat. Fas 1 kontrollerar det |
| **Tid på sida för synkade besök** | Obekräftat. Räkna mobil och andra enheter på antal besök |
| **Läsförbud i Claude Code** | Finns troligen som inställning, men kontrollera i dokumentationen |
| **Steg 2** | Uppskjutet |

## 4. Faser

Varje fas ska köras och förstås innan nästa. Storlek: S = en kväll, M = några kvällar, L = flera veckor.

| Fas | Innehåll | Du lär dig | Klart när |
|---|---|---|---|
| **0. Förberedelse (S)** | Python, Git, Terminal, mappstruktur, Claude Code installerat. Privat Git-repo med `.gitignore` för `data/` | Terminalen, mappar, versionshantering | Ett "hello world"-skript körs, repot finns och råfiler kan inte committas |
| **1. Integritetsgrind (M)** | Skriptet skriver ut *bara fältnamn* i Takeout-JSON. Om enhets-ID finns: gruppera domäner per enhet och peka ut jobbenheterna. I lokala `History`: gruppera på `originator_cache_guid`. Uteslut jobbenheter helt, plus domänlista (bank, hälsa, familj, jobb) | JSON, SQLite, gruppering | Jobbenheter är borttagna innan något annat behandlas. Om enheter inte går att skilja åt: filtrera på domän och starta profilen från veckoskriptet |
| **2. Baslinjeprofil (M)** | Läs Takeout (Chrome, Min aktivitet, YouTube-historik), aggregera per domän och tema, viktning per antal besök | Datarensning, aggregering | `profile.json` med toppteman skapas från filtrerad data |
| **Tunn skiva** | Kör en första brief manuellt i chatten med `profile.json` som underlag | Se om profilen ger relevanta teman | Du har läst ett första brev och vet vad som är fel |
| **3. Veckoskript (M)** | Läs lokala `History` (skrivskyddat, kopia), lägg till veckoaggregat, dubblettskydd, ny profil. Schemalägg med launchd | Schemaläggning, idempotens (två körningar ger samma resultat) | Skriptet körs själv varje vecka och en missad vecka tas igen |
| **4. Manuell config (S)** | `interests.yaml`: personer, ämnen per kategori, uteslutningar | Konfigurationsfiler | Nya ämnen slår igenom i nästa profil utan kodändring |
| **4b. LinkedIn-import (S, valfri)** | Begär LinkedIns dataarkiv, läs bara filerna över företag och personer du följer och lägg dem som förslag i `interests.yaml` som du själv gallrar. Läs inga andra filer i arkivet | CSV-filer, gallring | Du har en gallrad lista på företag och personer som styr bevakningen |
| **5. Nyhetsinsamling (L)** | Gratis RSS per kategori, sortera bort det du redan läst (URL mot historik), gruppera rubriker om samma händelse (trendsignal), ranka på intressematch × trend × färskhet, topp N per kategori till `candidates.json` | HTTP, RSS, rankning | `candidates.json` innehåller nya, relevanta artiklar utan sådant du läst |
| **6. Brevet (M)** | Schemalagd uppgift som läser Drive-mappen och skapar brev per kategori med länkar och 1–2 meningars highlights | Promptdesign, kopplingar | Ett brev anländer som utkast, sedan som mail, utan manuell körning |
| **7. Feedback (M)** | Enkelt betyg per artikel som skriptet läser tillbaka in i profilen | Återkopplingsloopar | Betygen påverkar nästa veckas ranking |

## 5. Best practice

1. **Tunn skiva först.** Ett fungerande brev för en kategori är bättre än fem halva delar.
2. **Testdata.** Bygg med syntetisk data. Claude Code ska aldrig läsa råfilerna. Sätt läsförbud på `data/` och skriv regeln i projektets `CLAUDE.md`.
3. **Kör själv på riktiga filer.** Dela bara aggregerade teman med Claude, inte URL:er eller titlar.
4. **Git.** Privat repo. Aldrig råfiler, nycklar eller konfiguration med personuppgifter i repot.
5. **Struktur:** `src/` för kod, `config/` för `interests.yaml`, `data/` (ej i Git) för råfiler och profiler, `logs/` för körloggar.
6. **Dry-run och loggar.** Varje skript ska kunna köras utan att ändra något och tydligt säga vad det gjorde.
7. **Idempotens.** Dubblettnyckel: tid, URL-hash och enhet. Då kan en ny Takeout slås ihop utan dubbelräkning.
8. **Versionera profilen.** Spara veckosnapshots. Låt nyare veckor väga tyngre så att långsiktiga intressen skiljs från tillfälliga.
9. **README.** Skriv vad varje del gör. Det är dokumentation åt framtida dig.
10. **Mät.** Notera kvotförbrukning per körning och brevets relevans.
11. **Rensa.** Radera eller kryptera råfiler efter bearbetning, och slå på FileVault.

## 6. Kurering, trend och fördjupning

**Intressesignaler till profilen.** Ingen enskild signal är sanning. Profilen vägs samman av flera. Vikterna nedan är förslag som justeras efter test:

| Signal | Källa | Föreslagen vikt |
|---|---|---|
| Egna tillägg (personer, ämnen) | `interests.yaml` | Starkast, uttryckligt |
| Sökfrågor | Takeout, Min aktivitet | Stark |
| Följda personer och företag | LinkedIn-arkivet, efter gallring | Stark |
| Betyg på brevets objekt | Feedback (Fas 7) | Stark |
| Återkommande besök på samma ämne eller domän | `History`, Takeout | Stark |
| Direkt inskriven adress kontra klick på länk | `transition`-fältet i `History` | Medel |
| Hur nyligt (avtagande vikt) | `History`, Takeout | Medel |
| YouTube-titlar | `History`, YouTube-historik | Medel |
| Tid på sida (`visit_duration`) | `History` | Svag, valideras mot verkligheten |

**Poängmodell per artikel (Fas 5–6):** `poäng = intressematch × trend/viktighet × färskhet`. Sådant du redan läst filtreras bort innan poängsättningen.

| Del | Hur | Var |
|---|---|---|
| **Intressematch** | Likhet mellan artikelns ämne och profilens teman och `interests.yaml` (personer, ämnen) | Lokalt |
| **Trendsignal** | Antal oberoende medier som rapporterar samma händelse de senaste 24–72 timmarna. Marknadsnyheter kan även vägas mot kursrörelser | Lokalt (gruppering av rubriker) eller i den schemalagda uppgiften |
| **Färskhet** | Publiceringstid, med avtagande vikt | Lokalt |
| **Kurering** | Max 3–5 objekt per kategori, vart och ett med en rad om varför du får det | Schemalagd uppgift |
| **Utforskning** | Ett objekt per kategori utanför profilen, så att tjänsten upptäcker nya intressen i stället för att bara bekräfta gamla | Schemalagd uppgift |

**Fördjupning som kombinerar källor** (per nyhet, på begäran):

| Källtyp | Exempel | Gratis? |
|---|---|---|
| Flera medier | Samma händelse i olika tidningar, med skillnader i vinkel | Ja, öppna källor |
| Marknadsdata | Kurser, valuta och räntor, korsrefererade mot minst två källor | Ja, via kopplade verktyg i Claude (t.ex. Avanza och finansdata) |
| Primärkällor | Bolagsrapporter, myndighetsdata, statistik | Ja, öppna |
| Personer du bevakar | Senaste uttalanden och intervjuer, som Dalio/Gave-körningen | Ja, webbsökning |
| Din egen historik | Vad du redan läst om ämnet, så att fördjupningen bygger vidare | Lokalt, som profiluppgift |

Fördjupningen körs som en Claude-konversation (projekt). Varje objekt i brevet får en färdig "Djupdyk"-prompt som du kopierar. Kopplade verktyg finns i chatten. Att de fungerar i schemalagda molnuppgifter är obekräftat.

## 7. Steg 2: alternativ (beslut skjuts)

| Alternativ | Innehåll | Kostnad och begränsning |
|---|---|---|
| **A. Sida som Claude publicerar** | Artefakt med kategorier och länkar, djupdykning i Claude-chatten eller ett projekt | Ryms i Pro. Djupdykningen sker i Claude, inte i själva sidan |
| **B. Lokal statisk sida** | Skriptet genererar en HTML-sida per vecka på Macen | Gratis. Ingen modell i sidan, bara sammanfattningar från brevet |
| **C. Egen webbapp med live-djupdykning** | Sidan anropar Claude direkt | Kräver API, som faktureras separat. Utanför ramen |

Rekommendation: A, eftersom fördjupningen som kombinerar källor kräver Claude med kopplade verktyg. B kan komplettera som lokal översiktssida över veckans brev. C först om du senare accepterar en API-kostnad.

## 8. Risker

| Risk | Åtgärd |
|---|---|
| Jobbdata hamnar i profilen | Fas 1-grinden. Arbetskategorin skrivs för hand |
| Pro-kvoten tar slut | Lokal förfiltrering ger få kandidater. Mät per körning och börja veckovis |
| Schemalagd uppgift misslyckas utan varning | Kontrollera "Scheduled" i sidomenyn under första veckorna |
| Macen är avstängd | Veckoskriptet tar igen missade veckor |
| Historiken rensas av Chrome | Spara veckoaggregat, förlita dig inte på att läsa bakåt |
| Takeout-formatet ändras | Läsaren ska ge tydliga fel och ha tester |
