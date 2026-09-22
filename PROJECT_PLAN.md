# Projektplan: personlig nyhetstjänst

Version 1, 20 september 2026. Läroprojekt för nybörjare.

## 1. Mål och ramar

| | |
|---|---|
| **Steg 1** | Nyhetsbrev via mail, **dagligen kl ~08:00** (beslutat 2026-09-21, ursprungsplanen var veckovis→dagligt) med *nya* artiklar på teman jag är intresserad av |
| **Steg 2** | Interaktiv app eller hemsida för att djupdyka i nyheterna. Form avgörs senare |
| **Kategorier** | Sex kategorier, definitioner uppdaterade 2026-09-20 (namn **Jobb** och **Ekonomi** satta 2026-09-20, tidigare "Arbete"/"Investeringar och privatekonomi"): **Jobb** (handskriven, ej från surfhistorik) — jobbar med teknik och affärsutveckling; stora nyheter/rapporter om H&M och konkurrenter: vad de satsar på, hur det går (resultat), hur marknaden reagerar. Konkurrenter har två trösklar (bekräftat 2026-09-20): primära konkurrenter (lägre tröskel, vanliga rapporter räknas) och sekundära (hög tröskel, bara riktigt stora nyheter) — se `config/interests.yaml`. **Ekonomi** — privata investeringar + relevant ekonomi. **Politik** = makroekonomi och policy, globalt/EU/Sverige/Stockholm — inte allmän partipolitik. **Nöje** = teknik, bilar, hantverk. **AI** — hur företag applicerar/transformerar verksamhet med AI, stora kapabilitetsnyheter, praktiska tricks att lära sig själv, allmän utveckling. **Skvaller** — kändis-/kriminaljournalistik i stil med Aftonbladet/Expressen/Nyheter24. Se `config/interests.yaml` för detaljer (gitignorerad) |
| **Aldrig** | Sammanfatta sådant jag redan läst. Intresseprofilen styr *vilka teman*, inte vad som återberättas |
| **Kurering** | Dynamiskt antal, uppdaterat 2026-09-20: upp till 15 nyheter per kategori, men färre om inget nytt hänt sen sist — inte en fast kvot som tvingar fram fyllnadsnyheter. Varje nyhet med en rad om varför jag får den. Bra att ha med alla källor (bredd, se avsnitt 6 "Kandidatkälla") |
| **Trend** | Nyheter som är viktiga eller på väg upp just nu, vägda mot mina intressen |
| **Fördjupning** | Djupdykning i en nyhet som kombinerar flera källor: olika medier, marknadsdata, primärkällor och uttalanden från personer jag bevakar. Format-inspiration (2026-09-20): Omni - korta nyheter/rubriker först, med möjlighet att fördjupa (inklusive källor) per objekt |
| **Ramar** | Inga licenser utöver Claude Pro. Bara gratis och öppna nyhetskällor. Läroprojekt: förstå varje steg innan nästa |

## 2. Arkitektur

```
KÄLLOR (lokalt på Macen, Python)
  Takeout-baslinje (engångs, ev. ny senare)
  Lokala Chrome-historiken (varje vecka, launchd)
  interests.yaml (personer, ämnen, uteslutningar, skrivs för hand)
        |
        |  1. Bygg intresseprofil (teman + vikt, nyare väger tyngre)
        |  2. Hämta nya artiklar brett (Google Nyheter RSS + finance-news-MCP),
        |     ranka mot profilen, källdiversifiering, dynamiskt antal per kategori
        v
  profile.json + candidates/{kategori}.json   (lokalt i projektmappen)
        |
        |  LÄSER DIREKT UR PROJEKTMAPPEN - se rättelse nedan
        v
CLAUDE (schemalagd uppgift/routine, körs som Claude Code-session lokalt)
  läser candidates/ + profile.json, dublettdetektering, källvinkel-
  bedömning, motargument, nyhetsbrev via Gmail, skriver brev per
  kategori, skapar Gmail-utkast (eller skickar) till mig
        |
        v
  Steg 2: djupdykning (se avsnitt 6)
```

**Rättelse 2026-09-20 — arkitekturen var mer komplicerad än nödvändigt:** ursprunglig plan antog att schemalagda uppgifter körs isolerat i molnet utan filåtkomst, så Google Drive skulle användas som mellanhand. **Bekräftat felaktigt**, verktygsbeskrivningen för schemalagda uppgifter (`scheduled-tasks`-MCP:n) säger uttryckligen att en körning startar *"as a NEW Claude Code session in the task's working folder"* - alltså en vanlig session med full filåtkomst till projektmappen, ingen Drive-synk behövs. Enda begränsningen: Claude-appen måste vara öppen - annars körs uppgiften vid nästa app-start istället för exakt på schemat (samma "missad vecka tas igen"-princip som launchd/Fas 3, fast på app-nivå istället för dator-nivå).

**Varför uppdelningen ändå kvarstår (lokalt vs. schemalagt):**
- "Redan läst"-filtret kräver historiken, så det görs lokalt och historiken lämnar aldrig Macen.
- Fas 5 (RSS-insamling, poängsättning) är billig och körs utan Claude/kvot - bara den sista kurateringen (dublett/källvinkel/motargument/brevskrivning) kostar kvot, så den delen hålls avgränsad till den schemalagda uppgiften.

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
| **Schemalagda uppgifter på Pro** | **Bekräftat 2026-09-20**: `mcp__scheduled-tasks__*`-verktygen finns och fungerar. Uppgiften körs som en vanlig lokal Claude Code-session i projektmappen (inte molnisolerad), med samma verktygsåtkomst (inkl. MCP) som en vanlig session - se rättelsen i avsnitt 2 |
| **Mailutskick från uppgift** | Fortfarande obekräftat om det går utan godkännande. Börjar med Gmail-utkast enligt plan |
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
| **3. Veckoskript (M) — ✅ klar 2026-09-20** | Läs lokala `History` (skrivskyddat, kopia), lägg till veckoaggregat, dubblettskydd. Schemalagt med launchd, söndagar 09:00. Krävde Full Disk Access för Claude-appen (två separata TCC-behörigheter - huvudappen och en inbäddad claude-code-app, se `src/build_weekly_history_snapshot.py`) | Schemaläggning, idempotens (två körningar ger samma resultat) | Skriptet testat två gånger i rad - andra körningen räknade 0 nya besök (bekräftad idempotens). `launchctl list` visar jobbet laddat. launchd förväntas komma ikapp missade veckor vid nästa uppvaknande, men skyddet mot missade veckor ligger egentligen i idempotensen själv (vattenstämpel), inte i launchd:s pålitlighet |
| **4. Manuell config (S)** | `interests.yaml`: personer, ämnen per kategori, uteslutningar | Konfigurationsfiler | Nya ämnen slår igenom i nästa profil utan kodändring |
| **4b. LinkedIn-import (S, valfri)** | Begär LinkedIns dataarkiv, läs bara filerna över företag och personer du följer och lägg dem som förslag i `interests.yaml` som du själv gallrar. Läs inga andra filer i arkivet | CSV-filer, gallring | Du har en gallrad lista på företag och personer som styr bevakningen |
| **5. Nyhetsinsamling (L) — ✅ v1 klar 2026-09-20** | Gratis RSS per kategori (Google Nyheter-sök, brett), gruppera rubriker om samma händelse (trendsignal, känt grov), ranka på intressematch × trend × färskhet, källdiversifiering, brus-exkludering, topp N (dynamiskt, upp till 15) per kategori till `data/profile/candidates/{kategori}.json`. Internationellt komplement via `finance-news`-MCP (`merge_candidates.py`, kräver Claude interaktivt). **Ej klart:** "sortera bort det du redan läst" - kräver Fas 3:s lokala historikläsning, som inte finns än. Görs i Fas 3/6 istället | HTTP, RSS, rankning | Fungerande kandidatlistor för alla sex kategorier. Kända kvarstående brister: grov lokal dublettgruppering (Fas 6 gör det riktiga jobbet), Jobb/Skvaller har litet urval, tröskelvärden empiriska - inte långtidstestade |
| **6. Brevet (M) — ✅ klar 2026-09-21, schemalagd dagligen** | Schemalagd uppgift (`axel-news-brief`) som läser projektmappen direkt (ingen Drive behövs, se rättelsen i avsnitt 2), kör Fas 5, applicerar all kurering (dublett/källvinkel/motargument/nyhetsbrev via RSS), skapar Gmail-utkast. Testkörd 2026-09-20 med lyckat resultat (alla MCP-verktyg fungerade). Schema: dagligen ~07:14 (cron `0 7 * * *`, launchd/schemaläggaren lägger på några minuters förskjutning), klar med god marginal till kl 08:00 (testkörningen tog ~29 min) | Promptdesign, kopplingar | Ett brev anländer som Gmail-utkast varje dag. **Krav för pålitlig 08:00-leverans**: Claude-appen måste vara öppen och datorn vaken vid körningstillfället - annars körs uppgiften vid nästa app-start istället (samma begränsning som launchd/Fas 3, men på app-nivå) |
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
| Nyhetsbrev/prenumerationer via mejl | Gmail (sökt av Claude i Fas 6, "sedan sist"-tidsstämpel - se nedan) | **Starkast av alla, uttryckligt** — beslut 2026-09-20: väger tyngre än den kollaborativa/virala popularitetssignalen (se nedan). En nyhet du fått i ett nyhetsbrev du valt att prenumerera på slår en generiskt viral nyhet vid konkurrens om samma plats |
| Ordpar/bigram i sökningar och titlar (fångar sammansatta namn som enskilda ord missar, t.ex. "maui jim") | `Chrome/Historik.json` | Medel — kompletterar ordfrekvens, avslöjar produktnamn och hela frågor |
| Shopping-/varumärkessökningar tolkade som smaksignal för Nöje (inte bortkastade, inte heller likställda med bilar/teknik/hantverk) | Google-sökbigram, `config/interests.yaml` (`noje.varumarken_smak`) | Svag, balanserad — beslut 2026-09-20: Nöje har begränsat antal platser (max 3-5), varumärkessmak konkurrerar om samma platser, tar inte över. Se även "Repetitiv smal sökning" nedan - vikten skalar *inte* med frekvens |
| **Repetitiv smal sökning kring en och samma produkt** (t.ex. "new balance 990" i många varianter/sökningar) | Alla sökkällor | **Omvänt** mot övriga signaler — beslut 2026-09-20: hög frekvens på en *smal, specifik* produkt/fråga tyder på pris-jämförelse ("var köper jag den billigast"), inte eskalerande intresse. Vikta ner, oavsett hur högt antalet är — räkna som *förekomst* (fanns/fanns inte), inte skalat med frekvens. Skiljs från bred repetition över *olika* saker i samma tema (t.ex. många olika bilkanaler) som fortfarande är en äkta intressesignal |
| **Korroboreringstest: gammal/specifik modell vs. nytt/genuint intresse** (generaliserad princip, exempel bilar 2026-09-20) | Domänvolym över källtyper | Beslut 2026-09-20: när en signal är tvetydig mellan "shoppar en specifik sak" och "genuint intresserad av kategorin", jämför volymen på dedikerade nyhets-/specsajter mot volymen på köp-/transaktionssajter (försäkring, leasing, register, marknadsplats). Är transaktionsvolymen klart högre = shopping, exkludera. Är nyhets-/specvolymen klart högre eller jämförbar = genuint intresse, behåll. Testat på bilar: nyhetssajter (vibilagare.se m.fl.) hade 8-39 besök mot köpklustret (biluppgifter.se, kvd.se, bilförsäkring, leasing) på upp till 131 - talade för shopping, hela klustret exkluderat |
| **Kanal vs. innehåll** (samma princip som "Domän vs. innehåll", en nivå ner) | YouTube-kanalnamn | Upptäckt 2026-09-20: att kategorisera YouTube-kanaler genom att *känna igen namnet* missar kanaler vars namn inte "låter" tematiska. SveaKanal (89/119 videor, 75%) och Felix Nordqvist (32/55, 58%) hade i praktiken mest ekonomiinnehåll men uteslöts helt i den manuella genomgången. Fixat genom nyckelordssökning i titlar över *alla* kanaler (inte bara redan kategoriserade) - samma metod som för domäner. Gör om i Fas 3, lita inte på kanalnamn ensamt |
| **Video-nivå, inte kanal-nivå: officiell YouTube-kategori per video** | YouTube Data API v3 (`videos.list`, `part=snippet`), `src/fetch_youtube_metadata.py` | Beslut 2026-09-20: gratis API-nyckel (config/.youtube_api_key, gitignorerad) ger YouTubes egen videokategori per video - träffsäkrare än nyckelordsgissning. Löste komplikationen att SveaKanal officiellt är 100% "News & Politics": eftersom Ekonomi och Politik hör ihop innehållsmässigt (se `config/youtube_category_mapping.yaml`) mappas "News & Politics" till **båda** kategorierna, istället för att tvinga in kanalen i en enda. Generellt: en kanal kan nu bidra olika mycket till olika kategorier beroende på vad enskilda videor faktiskt handlar om (`src/categorize_youtube_by_content.py`), inte en fast kanal->kategori-etikett |
| Videobeskrivningar (nivå 1) | Samma API | Låg signal i praktiken - domineras av sociala länkar/affiliate-boilerplate (com, www, instagram, amzn, follow), inte innehåll. Inte använd som signal |
| Kapitelrubriker i beskrivningen (nivå 3, om kreatören lagt in dem) | Samma API, regex-parsning av tidsstämplade rader | Bra signal där de finns (~300 kanaler) - t.ex. "gold", "debt", "silver", "money" lyste igenom tydligt. Sparad i `data/profile/youtube_metadata.json`, inte ännu inbakad i `profile.json` |
| Direkt inskriven adress kontra klick på länk | `transition`-fältet i `History` | Medel |
| Hur nyligt (avtagande vikt) | `History`, Takeout | Medel |
| Tid på sida (`visit_duration`) | `History` | Svag, valideras mot verkligheten |

**Poängmodell per artikel (Fas 5–6):** `poäng = intressematch × trend/viktighet × färskhet`. Sådant du redan läst filtreras bort innan poängsättningen.

| Del | Hur | Var |
|---|---|---|
| **Intressematch** | Likhet mellan artikelns ämne och profilens teman och `interests.yaml` (personer, ämnen) | Lokalt |
| **Trendsignal** | Antal oberoende medier som rapporterar samma händelse de senaste 24–72 timmarna. Marknadsnyheter kan även vägas mot kursrörelser | Lokalt (gruppering av rubriker) eller i den schemalagda uppgiften |
| **Färskhet** | Publiceringstid, med avtagande vikt | Lokalt |
| **Kurering** | Uppdaterat 2026-09-20: dynamiskt, upp till 15 objekt per kategori - färre om inget nytt hänt sen sist (inte en fast kvot). Vart och ett med en rad om varför du får det. Format-inspiration: Omni - korta rubriker/nyheter först, fördjupning (inkl. källor) per objekt på begäran | Schemalagd uppgift |
| **Utforskning** | Ett objekt per kategori utanför profilen, så att tjänsten upptäcker nya intressen i stället för att bara bekräfta gamla | Schemalagd uppgift |

**Vald kureringsmetod (beslut 2026-09-20).** Diskuterade fyra metodfamiljer (viktad poängformel, regelbaserad tröskel, utforskningsplats, LLM-slutgranskning) och landade i en kombination, olika per kategori:

| Metod | Används för | Hur |
|---|---|---|
| **A — Poängformel** | Ekonomi, Politik, Nöje, Skvaller | Baslinjen: `poäng = intressematch × trend × färskhet` (se ovan). Bred, kontinuerlig matchning passar kategorier med vida teman |
| **B — Regelbaserad tröskel, snävt ("overfittat")** | Jobb, AI | Uttryckligt val: för dessa två ska urvalet vara *snävt* mot de exakta ämnena i `interests.yaml` (H&M + namngivna konkurrenter med sina två trösklar; AI:s fyra specifika vinklar), inte löst nyckelordsmatchat. Motivering: bred intressematch riskerar dra in "AI" eller "affärsnyheter" som tekniskt matchar men inte är relevanta - hellre för smalt än för brett här |
| **C — Utforskning + källdiversifiering** | Alla kategorier | Utökad utforskningsplats: inte bara ett ämne utanför profilen, utan även aktiv **källdiversifiering** - undvik att alltid välja från samma toppdomäner (t.ex. alltid di.se för Ekonomi). Konkret mekanism att implementera i Fas 5: mild nedviktning av en domän som användes i senaste brevet/veckorna, så att andra källor får chansen |
| **D — LLM-slutgranskning** | Alla kategorier | Fokus specifikt på **dublettdetektering**: när flera kandidater handlar om samma händelse, känna igen det och slå ihop/välja bästa vinkel - inte en fullständig omprövning av poängen. Bekräftat 2026-09-20: görs av Claude i Fas 6, inte en lokal nyckelords-/entitetsregel i Fas 5 - kvoten räckt bekräftades vara liten nog (se nedan) |

**Fyra metodfrågor avgjorda (beslut 2026-09-20):**

1. **Dublettdetektering** (samma som Metod D ovan): LLM-bedömning i Fas 6, inte en lokal regel. Motivering: kvotkostnad bedömd som liten (en Fas 6-körning är betydligt mindre än en utforskande chattsession - se resonemang i konversationen, mätning sker på riktigt när Fas 6 finns).
2. **"Vänster/socialistisk vinkel"-bedömning för Politik**: löpande LLM-bedömning i Fas 6, inte en handskriven källista. Samma kvotresonemang som ovan - flexibelt, ingen lista att underhålla.
3. **"Aktuell tes" för Ekonomi-motargumentsregeln**: mekaniskt, härlett automatiskt från profilens riktning (t.ex. dominerande bullish/bearish-källor i `profile.json` avgör vilken tes som ska motargumenteras) - inte manuellt inskrivna teser i `interests.yaml`.
4. **"Hänt något"-tröskel för dynamisk kurering**: en poängtröskel i formeln (`intressematch × trend × färskhet`) - allt under en bestämd lägstanivå räknas som brus och utesluts, oavsett takets 15 platser. Exakt tröskelvärde sätts empiriskt när Fas 5 körs på riktig data.

**Känd svaghet i den lokala grupperingsheuristiken (upptäckt 2026-09-20, beslut: accepterad).** `group_key_of()` (de tre första betydande orden i bokstavsordning) är för skör för att hitta riktiga dubbletter - testat med påhittade rubriker om exakt samma händelse ("Fed sänker räntan" vs "Federal Reserve räntesänkning"), som INTE matchade pga "cuts"/"cut"-böjning och "Fed"/"Federal Reserve"-synonymi. Beslut: accepteras som en grov, billig lokal approximation - inte förbättrad till ordlikhet/Jaccard nu, eftersom Fas 6:s LLM-baserade dublettdetektering (se "Fyra metodfrågor avgjorda") gör det riktiga jobbet ändå. Den lokala trend-signalen i Fas 5 ska alltså tolkas som svag/ungefärlig, inte auktoritativ.

**Internationellt genombrott-detektering (ny, 2026-09-20).** Utöver att internationella källor kompletterar bredden (se ovan): `src/merge_candidates.py` flaggar specifikt kandidater vars ämnesgrupp har **minst två oberoende internationella källor men ingen svensk källa** - "stort utomlands, ännu inte i Sverige". Byggt och testat (ingen träff i det första, lilla urvalet - rimligt givet grupperingsheuristikens skörhet ovan, kräver troligen större datavolym från en fullskalig Fas 5-körning för att träffa).

**Kollaborativ signal (ny, 2026-09-20).** Uttryckligt önskemål: inte bara fortsätta bekräfta det jag redan läser/tittar på (ren innehållsbaserad matchning), utan också vad "såna som jag" gillar - en kompletterande signal utöver den egna historiken. Trendsignalen ovan mäter *redaktionell täckning* (hur många medier skriver om det), inte *läsarpopularitet*. Konkreta källor att undersöka i Fas 5: "mest lästa"-listor hos enskilda sajter, Reddit-uppröstningar, Hacker News-poäng (särskilt relevant för AI/teknik). Obekräftat om alla dessa är gratis/skrapbara - kontrolleras i Fas 5.
**Viktprioritet, bekräftad 2026-09-20:** nyhetsbrev (ovan) väger tyngre än den här kollaborativa/virala signalen. Om en nyhetsbrevsartikel och en generiskt viral artikel konkurrerar om samma plats i brevet, vinner nyhetsbrevet.

**Nyhetsbrev: RSS istället för Gmail (uppdaterat 2026-09-21).** Ursprungsbeslutet (2026-09-20) var Gmail-sökning för alla nyhetsbrev. Bättre lösning hittad: om avsändaren publicerar ett eget RSS-flöde går det att hämta **lokalt i Fas 5** (gratis, ingen Claude/Gmail behövs alls) istället för att läsa inkorgen. **Båda kända nyhetsbrev har bekräftade RSS-flöden**: Fernando del Pino Calvo-Sotelo (`https://www.fpcs.es/feed/`) och Kortsikt (`https://kortsikt.com/feed/`, länk given av användaren) - byggt och testat i `src/fetch_newsletter_feeds.py`. Fernando del Pinos flöde gav samma artikel som Gmail-sökningen hittade kvällen innan - bra korsvalidering av att metoden fungerar. `config/newsletter_feeds.yaml` listar flödena; Gmail-sökning finns kvar som fallback i den schemalagda uppgiften om ett framtida nyhetsbrev saknar RSS. Nyhetsbrevsposter konkurrerar inte om poängtröskeln i `merge_candidates.py` - de tas alltid med, väger starkast av alla signaler.

**Kandidatkälla: historik som utgångspunkt, källor brett (rättat 2026-09-20).** Första versionen av det här beslutet (samma dag) föreslog att begränsa kandidatkällorna till de ~30 domäner som redan syns i `news_domains.yaml` (trusted-source curation). Rättat efter tydlig instruktion: historiken ska bara användas för att **förstå profilen** (ämnen, vikter, entiteter) - den ska *inte* begränsa vilka sajter eller sökord som får leta fram nyheter. Motivering: jag hinner inte besöka alla relevanta sajter själv, så själva poängen med tjänsten är att den täcker bredare än min egen historik, inte bara bekräftar den.
Konkret för Fas 5: samla in brett per kategori - RSS från fler nyhetssajter än bara de historiskt bekräftade (t.ex. sök upp etablerade RSS-flöden per ämne: ekonomi/börs, makro/politik, teknik, bilar osv., inte begränsat till listan i `news_domains.yaml`), eventuellt kombinerat med nyckelordssökning brett över öppna nyhetskällor. Poängmodellen (Metod A) rankar sedan hela det bredare flödet mot profilen. `news_domains.yaml` fortsätter vara värdefull som *profilkälla* (vad historiken visar) men blir inte samtidigt en hård begränsning på *sökkällorna* i Fas 5.

**Explore/exploit formaliserat (beslut 2026-09-20).** Metod C:s "utforskningsplats" görs om till en epsilon-greedy-liknande regel istället för en fast "ett objekt": en bestämd andel av platserna per kategori (förslag: ~15-20%, testas och justeras) är alltid utforskande (slumpad från trusted-source-flödet eller från popularitetssignalen), resten rankas av poängmodellen. Grundat i den klassiska kontextuella bandit-metoden för nyhetsrekommendation (Yahoo/LinUCB).

Källor: [A Contextual-Bandit Approach to Personalized News Article Recommendation](https://arxiv.org/pdf/1003.0146), [Personalized News Recommendation: Methods and Challenges](https://arxiv.org/pdf/2106.08934), [Surprise me! A longitudinal user study on serendipitous recommendation](https://ceur-ws.org/Vol-4027/paper6.pdf).

**Internationellt komplement via MCP (beslut 2026-09-20).** `finance-news`-MCP:n (Bloomberg/WSJ/CNBC/MarketWatch/Seeking Alpha/FT) ger renare källor än Google Nyheter-skrapningen men saknar helt svensk vinkel (Riksbanken, svenska aktier, Stockholms bostadsmarknad) och har egna brister (flödestest gav 9/10 träffar från en enda Qatar-konferens, ingen inbyggd färskhetsbegränsning, falska positiver på substrängsnivå precis som vår egen "Börsen"-bugg). Används som **komplement**, inte ersättning: `src/merge_candidates.py` slår ihop svenska (`fetch_candidates.py`, lokalt skript) och internationella kandidater (`data/profile/candidates_raw/{kategori}_internationellt.json`) innan trend/poängsättning körs på hela poolen tillsammans.
**Arkitekturnotis:** MCP-verktyg som `finance-news` är bara tillgängliga för Claude, inte för ett fristående Python-skript. Den internationella filen måste alltså hämtas av Claude (interaktivt, eller i Fas 6 om kopplade verktyg visar sig fungera där - fortfarande obekräftat, se avsnitt 3). Fas 5:s svenska insamling förblir ett rent lokalt skript utan Claude/kvot inblandad.
`avanza` och `fin-data`-MCP:erna används istället för **Fördjupning** (redan planerat i avsnitt 6 sedan tidigare) - marknadsdata/kurser att korsreferera mot en nyhet, inte för kandidatinsamling.

**Ekonomi: aktivt motargument mot min egen tes (beslut 2026-09-20).** Om profilen visar att jag konsumerat mycket av en viss riktning (t.ex. flera källor om att guldpriset ska stiga), ska brevet också aktivt leta upp och inkludera trovärdiga motargument - inte bara det som redan bekräftar tesen. Tröskel för att en motartikel ska räknas: **stor spridning** (samma trendsignal som redan finns i poängmodellen) **och/eller** **hög ethos och logos** - klassisk retorik: ethos = källans trovärdighet/auktoritet (etablerad analytiker, erkänd institution), logos = argumentets logiska styrka (inte bara en rubrik som säger motsatsen, ett faktiskt underbyggt resonemang). Skiljer sig från den generella utforskningsplatsen (Metod C) genom att vara **riktad** - leta specifikt efter motsatsen till den egna tesen, inte slumpmässig bredd. Implementeras i Fas 5: identifiera "aktuell tes" per ämne från profilens riktning, sök separat efter motsatt vinkel, applicera samma ethos/logos-tröskel innan inkludering.

**Politik: undvik vänster/socialistisk vinkel (beslut 2026-09-20).** Till skillnad från Ekonomi-regeln ovan (som handlar om att aktivt visa båda sidor av en sakfråga) är det här en explicit **uteslutningsregel** på källnivå: när kandidatkällor väljs ut för Politik (makroekonomi/policy) ska källor/kommentatorer med tydlig vänster- eller socialistisk redaktionell vinkel undvikas eller nedprioriteras. Implementeras i Fas 5 som en del av källurvalet (vilka RSS-flöden/kommentatorer som ingår i kandidatpoolen för Politik), inte som ett filter på enskilda artiklar i efterhand.

**Fördjupning som kombinerar källor** (per nyhet, på begäran):

| Källtyp | Exempel | Gratis? |
|---|---|---|
| Flera medier | Samma händelse i olika tidningar, med skillnader i vinkel | Ja, öppna källor |
| Marknadsdata | Kurser, valuta och räntor, korsrefererade mot minst två källor | Ja, via kopplade verktyg i Claude (t.ex. Avanza och finansdata) |
| Primärkällor | Bolagsrapporter, myndighetsdata, statistik | Ja, öppna |
| Personer du bevakar | Senaste uttalanden och intervjuer, som Dalio/Gave-körningen | Ja, webbsökning |
| Din egen historik | Vad du redan läst om ämnet, så att fördjupningen bygger vidare | Lokalt, som profiluppgift |

Fördjupningen körs som en Claude-konversation (projekt). Varje objekt i brevet får en färdig "Djupdyk"-prompt som du kopierar. Kopplade verktyg finns i chatten. Att de fungerar i schemalagda molnuppgifter är obekräftat.

## 7. Steg 2: beslutat 2026-09-21

Ursprungliga alternativ (A: Claude-publicerad Artefakt, B: lokal statisk sida, C: egen webbapp med live-Claude-anrop, kostar API) - **D, en ny variant, valdes istället** efter diskussion om cross-device-åtkomst, lärosyfte och betygsättning (Fas 7-synergin):

**D. Statisk sida (GitHub Pages) + Supabase som databas, ev. Lovable som frontend-generator senare.**

| Del | Lösning | Kostnad |
|---|---|---|
| Hosting | GitHub Pages (helt statisk, GitHub-konto krävs) | Gratis |
| Betyg/data-lagring | Supabase (Postgres + auto-genererat API, anropas direkt från webbläsarens JavaScript) | Gratis (Supabase-konto krävs) |
| Fördjupning ("Läs mer"/"Varför viktigt") | Förberett av Fas 6 (har redan Claude-tillgång), inbäddat i sidans data - INTE ett live Claude-anrop från sidan | Ingen extra kostnad, kräver inget API |
| Frontend, v1 | Jag bygger (HTML/CSS/JS) | - |
| Frontend, v2 (senare, valfritt) | Lovable (separat AI-verktyg, bygger mot samma Supabase-projekt) - en annan AI skriver den koden, inte Claude | Gratis nivå har begränsad kvot |

**Varför D istället för A:** Artefakt-varianten (A) skulle skicka fördjupningsfrågor till Claude-chatten, inte visa dem inbäddat på sidan - matchade inte önskemålet om en sammanhängande, app-liknande upplevelse. D löser det genom att låta Fas 6 förbereda fördjupningstexterna i förväg istället för att generera dem live.

**Cross-device:** löst utan extra kostnad - GitHub Pages-sidan är redan nåbar från vilken enhet som helst med internetuppkoppling, ingen Tailscale/domän-fråga kvarstår för just den här varianten (till skillnad från en lokalt körd lösning).

**Lösenordsskydd:** inte löst än - sidan visar kurerad profil och betyg (personlig preferensdata), bör inte vara helt öppen. Löses när sidan faktiskt byggs, inte en plattformsfunktion utan kod vi skriver själva/via Supabase Auth.

**Börsticker (design-prototypen, beslutat 2026-09-21):** tre varianter testade. 1) Eget schemalagt Claude Code-jobb som skrev en JSON-fil några gånger/dag - fungerande, men beroende av att Axels dator och Claude Code är igång, precis som Fas 6-begränsningen. 2) TradingViews gratis klientsidan-widget, inbäddad direkt i sidan - uppdaterades i besökarens egen webbläsare utan server, men gick inte att styla likt WSJ-originalets smala rad (eget typsnitt/ikoner/"D"-märkning låsta i en iframe). **Landade i en tredje variant:** samma egna, WSJ-styliserade ticker-design som i (1), men datakällan (`src/fetch_ticker.py`, samma fria nyckelfria API:er: Yahoo, Frankfurter.app, CoinGecko) körs nu av ett GitHub Actions-schemalagt jobb (`.github/workflows/update-ticker.yml`, var 4:e timme) istället för ett lokalt Claude Code-jobb - på GitHub:s servrar, inte Axels dator. Sidans JS läser `web/ticker.json` (samma ursprung, ingen CORS-fråga) och faller tillbaka till fröade/simulerade värden om filen inte är nåbar (Claude-artefaktens sandlåda, eller innan sajten är deployad). Symboler: OMXS30, H&M, USD/SEK, EUR/SEK, GULD, BTC.

**"Tyck till"-feedbackruta (design-prototypen, tillagd 2026-09-21, Supabase-plan samma dag):** en fritextruta längst ned på sidan sparar just nu bara till `localStorage` (samma mönster som betygsknapparna), med en "Kopiera allt"-knapp som manuell brygga till nästa Claude Code-session. **Planerat nästa steg, när Supabase kopplas in (steg 5 nedan):**

- Ny tabell `feedback` i Supabase (schema i `config/brief_schema.md`) med kolumnerna `text`, `status` (`ny`/`hanterad`), `skapad`, `hanterad_at`.
- Sidans JS byter från ren `localStorage`-skrivning till att `insert`:a direkt i `feedback`-tabellen via samma Supabase-klient som betygsknapparna redan kommer använda (samma anon-nyckel, samma init). `localStorage` behålls som lokal offline-kö/fallback om insert misslyckas (ingen uppkoppling) - försöker synka igen nästa sidladdning.
- En liten skript, `src/fetch_feedback.py` (samma mönster som `fetch_ticker.py` - fria HTTP-anrop, ingen extra dependency), frågar Supabases REST-API efter rader med `status = 'ny'` i början av en underhålls-session i Claude Code. Det ersätter "Kopiera allt"-bryggan - jag slipper klistra in något manuellt.
- Efter att ha åtgärdat (eller medvetet valt bort) punkter i en session: `update feedback set status = 'hanterad', hanterad_at = now() where id in (...)` för de posterna, så nästa körning bara ser nytt.
- "Kopiera allt"-knappen i UI:t behålls ändå som redundant fallback (kostar inget, funkar även om Supabase är nere).

## 8. Risker

| Risk | Åtgärd |
|---|---|
| Jobbdata hamnar i profilen | Accepterad risk (beslut 2026-09-20): inget exkluderas, varken enheter eller domäner. Arbetskategorin i `interests.yaml` skrivs ändå för hand, så jobbrelaterat kan hållas utanför nyhetsbrevets kategorier även om det finns i rådatan |
| Pro-kvoten tar slut | Lokal förfiltrering ger få kandidater. Mät per körning och börja veckovis |
| Schemalagd uppgift misslyckas utan varning | Kontrollera "Scheduled" i sidomenyn under första veckorna |
| Macen är avstängd | Veckoskriptet tar igen missade veckor |
| Historiken rensas av Chrome | Spara veckoaggregat, förlita dig inte på att läsa bakåt |
| Takeout-formatet ändras | Läsaren ska ge tydliga fel och ha tester |
| **Datahygien** (tillagd 2026-09-20) | Rådatan (inkl. 3 GB mejl-mbox) ligger okrypterad utöver diskkryptering i `data/raw/takeout/`. FileVault bekräftat påslaget (kollat 2026-09-20: `fdesetup status` → On), vilket skyddar vid stöld/borttappad dator. Kvarstår: ingen fjärrkopia av repot (git har ingen remote) - en förlustrisk, inte en exponeringsrisk, om datorn dör. Best practice #11 ("Radera eller kryptera råfiler efter bearbetning") inte genomförd än |
| **Kvot/tokenrisk för Fas 6** (tillagd 2026-09-20) | Fas 6:s omfattning växte under sessionen (dublettdetektering + källvinkel-bedömning + motargumentslogik + internationellt komplement + Gmail-sökning, alla LLM-baserade) jämfört med den enkla uppskattningen som gjordes tidigare ("några procent av veckokvoten"). Åtgärd: mät verkligt utfall från första skarpa körningen, inte bara uppskatta i förväg |

## 9. Backlog

**Nyhetskort v2 (design-prototypen, backlog-post tillagd 2026-09-21):** fyra ändringar av nyhetskorten i `web/preview.html`, Omni-inspirerat.

1. **✅ Klart 2026-09-22. Längre förstanivå-sammanfattning.** `sammanfattning`-fältet (visas innan man klickar) är nu ~3 meningar istället för en rad. Uppdaterat i `config/brief_schema.md`, exempeldatan i `web/preview.html` och kureringsinstruktionen i det schemalagda jobbet (`axel-news-brief`).

2. **✅ Klart 2026-09-22. Sammanslagen `las_mer`-text över flera källor.** Vid klick: en kuraterad text som väver ihop alla källor som rapporterat om händelsen (inte bara en artikels sammanfattning), ~30 sekunders läsning (~100-130 ord). Datamodellen håller nu flera källor per nyhet (`kallor: [{kalla, lank}, ...]` istället för det gamla enda `kalla`+`lank`-paret). **Känd begränsning, kvarstår:** många kandidater har bara en källa - för dem blir "sammanslagen text" i praktiken samma som enkällig text, inget att bygga bort, bara att vänta sig.

3. **✅ Klart 2026-09-22. Länkar till alla underliggande källor** i den expanderade vyn - en `KÄLLOR (n)`-lista med länk till varje `kallor`-post, singular `KÄLLA` när det bara finns en.

4. **Ej byggd - hårt Supabase-beroende. "Följ ämne"-knapp**, bredvid Relevant/Skippa fler. Diskuterat två varianter:
   - *A (avfärdad):* begränsa till redan namngivna ämnen i `config/interests.yaml`. Tillför inget utöver befintlig intressepoängsättning - de ämnena är redan privilegierade av `poäng = intressematch × trend × färskhet`.
   - **B (vald):** låt Fas 6:s kurering LLM-tagga varje nyhet med ett kanoniskt ämnesnamn (kollat mot en växande registrering av tidigare använda taggar, troligen en utökning av den befintliga trend-grupperingslogiken i `merge_candidates.py`/avsnitt 6), så att godtyckliga/oplanerade ämnen (t.ex. en enskild stor nyhetshändelse) kan följas, inte bara fördefinierade intressen.
   
   **Hård beroende, samma som feedback-rutan (avsnitt 7):** följda ämnen sparas i webbläsaren (`localStorage`/senare Supabase), men Fas 6:s kurering körs som ett schemalagt jobb utan åtkomst till webbläsarens lagring. Kureringen behöver läsa listan över följda ämnen från Supabase vid varje körning och sätta en `foljt_amne: true`-flagga på matchande nyheter (samma mönster som `nyhetsbrev`/`motargument`-flaggorna) - fuzzy-matchningen görs alltså av Claude under kureringen, inte av klientkoden. **Kan därför inte byggas före Supabase-steget (5)** - bör sekvenseras tillsammans med feedback-rutans Supabase-koppling, inte separat.

**✅ Klart 2026-09-22. Källupptäckt via Omni:** Omni själv är INTE en bra källa att prenumerera på (se resonemang nedan) - men deras artiklar listar ofta "Källor: [tidning A, tidning B...]" under varje sammanfattning. Bläddrade igenom omni.se:s ekonomi- och tech-sidor och noterade återkommande primärkällor. De flesta (CNBC, Bloomberg, Barron's, WSJ/FT, The Verge-liknande) täcks redan via finance-news-MCP:n eller Google Nyheter. Två nya lades till i `config/trusted_international_feeds.yaml` som inte redan täcktes och hade fungerande flöden: **SR Ekot** (politik - saklig radionyhetsbevakning, lägre redaktionell-vinkel-risk än opinionssajter) och **The Verge** (ai - matchar "kapabilitetsnyheter"-vinkeln bättre). Båda ger Atom-format istället för RSS 2.0, vilket avslöjade att `fetch_trusted_international.py` bara klarade RSS 2.0 - uppdaterad samma dag att tolka båda formaten (regressionstestat mot Washington Post-flödena, fortsatt fungerande). Kört end-to-end: 20 nya SR Ekot-poster, 10 nya The Verge-poster hämtade och sparade.

**Varför Omni inte är en källa i sig (kollat 2026-09-22):** (1) Omni gör i huvudsak inte egen rapportering - de sammanfattar andra medieutgåvors nyheter, så att prenumerera på dem vore att kurera en kurator istället för att gå till primärkällor. (2) Ingen publik RSS finns (404 på alla vanliga sökvägar - modern app/JS-sajt, samma situation som Kvartal/Bulletin/100.se). (3) Omni ägs av Bonnier News (samma grupp som DN), vilket generellt ligger i den svenska medielandskapets center-vänster-mittfåra - skulle dra fel håll mot CLAUDE.md:s regel om att undvika vänster/socialistisk vinkel i politik-kategorin, särskilt efter att motvikter (Kvartal, Bulletin, 100.se, Epoch Times) nyligen lagts till. Omni är dock redan formatinspirationen för hela brevets struktur ("Omni-inspirerat" i Steg 6) - det är en annan, redan använd, oproblematisk sak.
