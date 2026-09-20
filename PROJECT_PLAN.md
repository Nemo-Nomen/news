# Projektplan: personlig nyhetstjänst

Version 1, 20 september 2026. Läroprojekt för nybörjare.

## 1. Mål och ramar

| | |
|---|---|
| **Steg 1** | Nyhetsbrev via mail (först veckovis, sedan ev. dagligt) med *nya* artiklar på teman jag är intresserad av |
| **Steg 2** | Interaktiv app eller hemsida för att djupdyka i nyheterna. Form avgörs senare |
| **Kategorier** | Sex kategorier, definitioner uppdaterade 2026-09-20 (namn **Jobb** och **Ekonomi** satta 2026-09-20, tidigare "Arbete"/"Investeringar och privatekonomi"): **Jobb** (handskriven, ej från surfhistorik) — jobbar med teknik och affärsutveckling; stora nyheter/rapporter om H&M och konkurrenter: vad de satsar på, hur det går (resultat), hur marknaden reagerar. Konkurrenter har två trösklar (bekräftat 2026-09-20): primära konkurrenter (lägre tröskel, vanliga rapporter räknas) och sekundära (hög tröskel, bara riktigt stora nyheter) — se `config/interests.yaml`. **Ekonomi** — privata investeringar + relevant ekonomi. **Politik** = makroekonomi och policy, globalt/EU/Sverige/Stockholm — inte allmän partipolitik. **Nöje** = teknik, bilar, hantverk. **AI** — hur företag applicerar/transformerar verksamhet med AI, stora kapabilitetsnyheter, praktiska tricks att lära sig själv, allmän utveckling. **Skvaller** — kändis-/kriminaljournalistik i stil med Aftonbladet/Expressen/Nyheter24. Se `config/interests.yaml` för detaljer (gitignorerad) |
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
        |  1. Bygg intresseprofil (teman + vikt, nyare väger tyngre)
        |  2. Hämta nya artiklar via RSS, ta bort sådant jag redan läst,
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
| **Exkludering i rådata (Fas 1)** | Beslut 2026-09-20: inget exkluderas ur rådatan. Varken jobbenheter (jobbdator/jobbtelefon i Chrome-synken) eller en domänlista (bank, hälsa, familj, jobb) filtreras bort där. All data i Takeout och lokal historik behandlas lika och sparas orört i `data/`. Fas 1 innehåller därför ingen filtrering, bara schemautforskning |
| **Domäner som signal i profilen (Fas 2, annat lager än ovan)** | Beslut 2026-09-20: jobbdomäner (`hennesandmauritz.sharepoint.com`, `hm.hrmcloud.se`, `performancemanager5.successfactors.eu`, `login.microsoftonline.com`) och shoppingdomäner (`blocket.se`, `amazon.se`, `prisjakt.nu`, `arket.com`, `vinted.se`, `tradera.com`, `www2.hm.com`) räknas inte som signal när `profile.json` byggs. Rådatan i `data/profile/domain_counts.json` påverkas inte — listan i `config/domain_exclusions.yaml` filtrerar bara vid profilbygget |
| **Domän vs. innehåll som signal** | Insikt 2026-09-20: domänbesök räcker inte som signal för domäner med blandat innehåll (t.ex. YouTube — kan vara bilar, teknik, nyheter, musik om vartannat). För sådana domäner behöver profilen bygga på sidtitlar/innehåll, inte bara besöksantal. Se avsnitt 6 |
| **Nyhetsmail som signal** | Insikt 2026-09-20: nyhetsbrev/prenumerationer som kommer via mejl är också en intressesignal. Hanteras senare via `E-post`-mboxen eller Gmail-etiketter — inte implementerat än |
| **Tillägg och program** | Inget installeras på jobbdatorn utöver det som är standard där. Skript och eventuella spårare körs bara på privat utrustning |
| **Tid på sida** | En svag signal bland flera (se avsnitt 6), aldrig ensam grund. ActivityWatch läggs till på privat dator först om ett test visar behov |
| **Arbetskategorin** | Definieras för hand i `interests.yaml`, inte från surfhistorik |
| **Schemalagda uppgifter på Pro** | Hjälpcentret säger att Cowork på Pro rullas ut. Kontrollera att "Scheduled" finns i din sidomeny |
| **Mailutskick från uppgift** | Obekräftat om det går utan godkännande. Börja med Gmail-utkast |
| **Tid på sida för synkade besök** | Obekräftat. Räkna mobil och andra enheter på antal besök |
| **Läsförbud i Claude Code** | Finns troligen som inställning, men kontrollera i dokumentationen |
| **Steg 2** | Uppskjutet |

## 4. Faser

Varje fas ska köras och förstås innan nästa. Storlek: S = en kväll, M = några kvällar, L = flera veckor.

| Fas | Innehåll | Du lär dig | Klart när |
|---|---|---|---|
| **0. Förberedelse (S)** | Python, Git, Terminal, mappstruktur, Claude Code installerat. Privat Git-repo med `.gitignore` för `data/` | Terminalen, mappar, versionshantering | Ett "hello world"-skript körs, repot finns och råfiler kan inte committas |
| **1. Schemautforskning (S)** | Skriptet skriver ut *bara fältnamn* i Takeout-JSON, för att förstå formatet. Ingen filtrering — inget exkluderas (varken enheter eller domäner, beslut 2026-09-20) | JSON, SQLite, gruppering | Takeout- och `History`-formatens fält är kartlagda och redo för Fas 2 |
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

**Dimensionsmodell (2026-09-20, grundat i forskning om nyhetsrekommendation).** En besökt sida/video beskrivs inte med en enda siffra, utan längs flera dimensioner samtidigt — vikten byggs per *kombination*, inte per dimension var för sig (t.ex. "kanalen Mat Armstrong + ämnet bilar" väger tyngre än att bara räkna youtube.com-besök):

| Dimension | Vad den fångar | Exempel hos oss |
|---|---|---|
| **Ämne/tema** | Vad innehållet handlar om | bilar, ekonomi, politik |
| **Entitet/avsändare** | Vem som publicerat/skapat det | YouTube-kanal (t.ex. Mat Armstrong), tidning, journalist |
| **Källa/domän** | Vilken plattform | youtube.com, di.se |
| **Tid (färskhet)** | Hur nyligen, avtagande vikt | `time_usec` i `History` |
| **Engagemang** | Hur du interagerade | klick, upprepade besök, betyg, lästid |

Källor: [Personalized News Recommendation: Methods and Challenges](https://arxiv.org/pdf/2106.08934), [Multi-view knowledge representation learning](https://pmc.ncbi.nlm.nih.gov/articles/PMC11707356/), [A global user profile framework](https://link.springer.com/article/10.1007/s11042-023-17436-w). Det här är "feature-baserad" användarmodellering (handskrivna regler/dimensioner) snarare än deep learning — matchar läroprojektets nivå.

Praktiskt: samma logik gäller nyhetssajter som YouTube — det är inte bara *att* du klickade på di.se, utan *vilken artikel* och *vilken skribent/rubrik-ämne* som är den starka signalen.

**Intressesignaler till profilen.** Ingen enskild signal är sanning. Profilen vägs samman av flera. Vikterna nedan är förslag som justeras efter test:

| Signal | Källa | Föreslagen vikt |
|---|---|---|
| Egna tillägg (personer, ämnen) | `interests.yaml` | Starkast, uttryckligt |
| Följda ämnen, källor, orter, tidskrifter i Google Nyheter | Takeout: `Nyheter/*.txt` | Starkt, uttryckligt — flera dimensioner (topic/source/location/magazine) hålls isär, inte slås ihop till en enda lista, så profilen kan vikta dem olika |
| Sökfrågor | Takeout, Min aktivitet | Stark |
| Följda personer och företag | LinkedIn-arkivet, efter gallring | Stark |
| Betyg på brevets objekt | Feedback (Fas 7) | Stark |
| Återkommande besök på samma ämne eller domän | `History`, Takeout | Stark för renodlade domäner. Jobb- och shoppingdomäner exkluderade från profilen, se `config/domain_exclusions.yaml` och avsnitt 3 |
| Sidtitlar för domäner med blandat innehåll (t.ex. YouTube) | `History`, `Chrome/Historik.json` | Stark — domänen ensam räcker inte som signal där, se avsnitt 3 ("Domän vs. innehåll") |
| Avsändare/kanal (YouTube-kanal, tidning, skribent) — egen dimension, skild från ämne | `YouTube och YouTube Music/historik/visningshistorik.html` (kanalnamn per video), artikel-URL:er på nyhetssajter | Stark — se dimensionsmodellen ovan |
| Nyhetsbrev/prenumerationer via mejl | Takeout `E-post` (mbox) eller Gmail-etiketter | Stark, uttryckligt — inte implementerat än |
| Ordpar/bigram i sökningar och titlar (fångar sammansatta namn som enskilda ord missar, t.ex. "maui jim") | `Chrome/Historik.json` | Medel — kompletterar ordfrekvens, avslöjar produktnamn och hela frågor |
| Shopping-/varumärkessökningar tolkade som smaksignal för Nöje (inte bortkastade, inte heller likställda med bilar/teknik/hantverk) | Google-sökbigram, `config/interests.yaml` (`noje.varumarken_smak`) | Svag, balanserad — beslut 2026-09-20: Nöje har begränsat antal platser (max 3-5), varumärkessmak konkurrerar om samma platser, tar inte över. Se även "Repetitiv smal sökning" nedan - vikten skalar *inte* med frekvens |
| **Repetitiv smal sökning kring en och samma produkt** (t.ex. "new balance 990" i många varianter/sökningar) | Alla sökkällor | **Omvänt** mot övriga signaler — beslut 2026-09-20: hög frekvens på en *smal, specifik* produkt/fråga tyder på pris-jämförelse ("var köper jag den billigast"), inte eskalerande intresse. Vikta ner, oavsett hur högt antalet är — räkna som *förekomst* (fanns/fanns inte), inte skalat med frekvens. Skiljs från bred repetition över *olika* saker i samma tema (t.ex. många olika bilkanaler) som fortfarande är en äkta intressesignal |
| **Korroboreringstest: gammal/specifik modell vs. nytt/genuint intresse** (generaliserad princip, exempel bilar 2026-09-20) | Domänvolym över källtyper | Beslut 2026-09-20: när en signal är tvetydig mellan "shoppar en specifik sak" och "genuint intresserad av kategorin", jämför volymen på dedikerade nyhets-/specsajter mot volymen på köp-/transaktionssajter (försäkring, leasing, register, marknadsplats). Är transaktionsvolymen klart högre = shopping, exkludera. Är nyhets-/specvolymen klart högre eller jämförbar = genuint intresse, behåll. Testat på bilar: nyhetssajter (vibilagare.se m.fl.) hade 8-39 besök mot köpklustret (biluppgifter.se, kvd.se, bilförsäkring, leasing) på upp till 131 - talade för shopping, hela klustret exkluderat |
| Direkt inskriven adress kontra klick på länk | `transition`-fältet i `History` | Medel |
| Hur nyligt (avtagande vikt) | `History`, Takeout | Medel |
| Tid på sida (`visit_duration`) | `History` | Svag, valideras mot verkligheten |

**Poängmodell per artikel (Fas 5–6):** `poäng = intressematch × trend/viktighet × färskhet`. Sådant du redan läst filtreras bort innan poängsättningen.

| Del | Hur | Var |
|---|---|---|
| **Intressematch** | Likhet mellan artikelns ämne och profilens teman och `interests.yaml` (personer, ämnen) | Lokalt |
| **Trendsignal** | Antal oberoende medier som rapporterar samma händelse de senaste 24–72 timmarna. Marknadsnyheter kan även vägas mot kursrörelser | Lokalt (gruppering av rubriker) eller i den schemalagda uppgiften |
| **Färskhet** | Publiceringstid, med avtagande vikt | Lokalt |
| **Kurering** | Max 3–5 objekt per kategori, vart och ett med en rad om varför du får det | Schemalagd uppgift |
| **Utforskning** | Ett objekt per kategori utanför profilen, så att tjänsten upptäcker nya intressen i stället för att bara bekräfta gamla | Schemalagd uppgift |

**Vald kureringsmetod (beslut 2026-09-20).** Diskuterade fyra metodfamiljer (viktad poängformel, regelbaserad tröskel, utforskningsplats, LLM-slutgranskning) och landade i en kombination, olika per kategori:

| Metod | Används för | Hur |
|---|---|---|
| **A — Poängformel** | Ekonomi, Politik, Nöje, Skvaller | Baslinjen: `poäng = intressematch × trend × färskhet` (se ovan). Bred, kontinuerlig matchning passar kategorier med vida teman |
| **B — Regelbaserad tröskel, snävt ("overfittat")** | Jobb, AI | Uttryckligt val: för dessa två ska urvalet vara *snävt* mot de exakta ämnena i `interests.yaml` (H&M + namngivna konkurrenter med sina två trösklar; AI:s fyra specifika vinklar), inte löst nyckelordsmatchat. Motivering: bred intressematch riskerar dra in "AI" eller "affärsnyheter" som tekniskt matchar men inte är relevanta - hellre för smalt än för brett här |
| **C — Utforskning + källdiversifiering** | Alla kategorier | Utökad utforskningsplats: inte bara ett ämne utanför profilen, utan även aktiv **källdiversifiering** - undvik att alltid välja från samma toppdomäner (t.ex. alltid di.se för Ekonomi). Konkret mekanism att implementera i Fas 5: mild nedviktning av en domän som användes i senaste brevet/veckorna, så att andra källor får chansen |
| **D — LLM-slutgranskning** | Alla kategorier | Fokus specifikt på **dublettdetektering**: när flera kandidater handlar om samma händelse, känna igen det och slå ihop/välja bästa vinkel - inte en fullständig omprövning av poängen |

**Kollaborativ signal (ny, 2026-09-20).** Uttryckligt önskemål: inte bara fortsätta bekräfta det jag redan läser/tittar på (ren innehållsbaserad matchning), utan också vad "såna som jag" gillar - en kompletterande signal utöver den egna historiken. Trendsignalen ovan mäter *redaktionell täckning* (hur många medier skriver om det), inte *läsarpopularitet*. Konkreta källor att undersöka i Fas 5: "mest lästa"-listor hos enskilda sajter, Reddit-uppröstningar, Hacker News-poäng (särskilt relevant för AI/teknik). Obekräftat om alla dessa är gratis/skrapbara - kontrolleras i Fas 5.

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
| Jobbdata hamnar i profilen | Accepterad risk (beslut 2026-09-20): inget exkluderas, varken enheter eller domäner. Arbetskategorin i `interests.yaml` skrivs ändå för hand, så jobbrelaterat kan hållas utanför nyhetsbrevets kategorier även om det finns i rådatan |
| Pro-kvoten tar slut | Lokal förfiltrering ger få kandidater. Mät per körning och börja veckovis |
| Schemalagd uppgift misslyckas utan varning | Kontrollera "Scheduled" i sidomenyn under första veckorna |
| Macen är avstängd | Veckoskriptet tar igen missade veckor |
| Historiken rensas av Chrome | Spara veckoaggregat, förlita dig inte på att läsa bakåt |
| Takeout-formatet ändras | Läsaren ska ge tydliga fel och ha tester |
