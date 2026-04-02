# Co-op Games Hub — Istruzioni per AI

Questo file è letto automaticamente da Claude Code e da Aider (via `.aider.conf.yml`).
Contiene tutto ciò che serve per lavorare correttamente su questo progetto.

---

## Navigazione rapida per AI

> Leggi SOLO i file che servono al tuo task. Non caricare tutto.

```
Task UI/frontend?
  → Leggi: assets/app.js, assets/style.css, index.html
  → Template: .claude/TASK_TEMPLATE.md

Task pipeline Python / nuovi giochi?
  → Leggi: scripts/INDEX.md       (mappa 45 script, dipendenze, ordine CI)
  → Leggi: scripts/catalog_config.py, scripts/catalog_data.py
  → Non toccare: .github/workflows/ senza approvazione

Task dati JSON?
  → Leggi: data/README.md         (tassonomia 38 file, stato live/pipeline/legacy)
  → Schema campi: data/schema.json (contratto dati, tipi, vincoli — leggero)
  → Esempio record: data/sample.json (1 record sintetico completo)
  → MAI caricare catalog.games.v1.json intero (574 giochi, troppo grande)

Task SEO / pagine statiche?
  → Leggi: scripts/build_static_pages.py, scripts/build_hub_pages.py
  → Override SEO: data/seo_overrides.json, data/hub_editorial.json

Non sai da dove iniziare?
  → Leggi: .claude/AI_COLLABORATION.md    (log sessioni precedenti, stato attuale)
  → Leggi: .planning/STATE.md     (stato roadmap)
```

### Struttura cartelle

```
/
├── assets/
│   ├── app.js          ← logica principale frontend (~600 righe)
│   ├── games.js        ← 589 giochi come oggetti JS (~94K token — NON passare intero ad aider)
│   ├── free_games.js   ← giochi gratis settimana corrente
│   ├── i18n.js         ← stringhe IT/EN
│   ├── style.css       ← tutto il CSS
│   └── particles.js    ← animazione sfondo
├── games/              ← 589 pagine HTML statiche (auto-generate, non editare)
├── en/                 ← 8 hub pages in inglese
├── scripts/
│   ├── INDEX.md        ← MAPPA COMPLETA 45 script (leggi prima di tutto)
│   ├── catalog_config.py   ← costanti globali pipeline
│   ├── catalog_data.py     ← I/O catalogo
│   ├── auto_update.py      ← pipeline CI principale
│   ├── build_static_pages.py
│   ├── build_hub_pages.py
│   ├── quality_gate.py
│   └── [42 altri script → vedi INDEX.md]
├── data/
│   ├── README.md               ← TASSONOMIA 38 JSON (live / pipeline / editoriale / log)
│   ├── schema.json             ← CONTRATTO DATI: tutti i campi, tipi, vincoli (leggero)
│   ├── sample.json             ← 1 record sintetico completo (riferimento strutturale)
│   ├── catalog.games.v1.json   ← catalogo completo 574 giochi (NON caricare intero)
│   ├── hub_editorial.json      ← testi hub pages (editoriale)
│   ├── seo_overrides.json      ← override SEO manuali
│   └── [35 altri file → vedi README.md]
├── .github/workflows/  ← update.yml (ogni giorno) + free_games.yml (giornaliero)
├── .claude/
│   ├── TASK_TEMPLATE.md    ← USA QUESTO prima di ogni task
│   └── settings.json
├── .planning/          ← roadmap, requisiti, stato progetto
├── CLAUDE.md           ← questo file
└── .claude/AI_COLLABORATION.md ← log sessioni AI
```

---

## Cos'è il progetto

Sito statico **coophubs.net** — catalogo di videogiochi cooperativi per PC.
Hosting: **GitHub Pages** + Cloudflare (DNS, proxy, HTTPS). Dominio già configurato e funzionante.

**Titolare**: Metalink Application S.r.l.s (P.IVA: 04739980615)

Stack: HTML + CSS + JavaScript puro, Python per la pipeline dati automatica.
Nessun backend. Nessun framework. Nessun runtime Node in produzione.

---

## File principali

| File | Ruolo |
|------|-------|
| `index.html` | Homepage con catalogo e filtri |
| `app.js` | Logica filtri, rendering card, routing verso pagine statiche |
| `games.js` | Database giochi (589 giochi), oggetti JS |
| `games/<id>.html` | 589 pagine statiche per ogni gioco (SEO) |

## Pipeline Python

| Script | Ruolo |
|--------|-------|
| `auto_update.py` | Aggiornamento automatico giochi (GitHub Actions, lunedì) |
| `build_static_pages.py` | Genera `games/<id>.html` + `sitemap.xml` |
| `validate_catalog.py` | Valida il catalogo dopo il build |
| `fetch_free_games.py` | Aggiorna i giochi gratuiti (GitHub Actions, ogni giorno) |
| `steam_catalog_source.py` | Adapter Steam |
| `itch_catalog_source.py` | Adapter itch.io |
| `catalog_data.py` | Layer I/O dati catalogo |
| `catalog_config.py` | Configurazione pipeline |

## Database Integration (2026-04-01)

### Fonti dati testate e implementate

| Fonte | Status | Note |
|-------|--------|------|
| Steam Store | ✅ Funziona | 75 giochi, scraping con cloudscraper |
| IGDB API | ✅ Funziona | 30 giochi, API key in .env |
| RAWG API | ✅ Funziona | 217 giochi, API key in .env |
| GOG Store | ✅ Funziona | 91 giochi, scraping |
| Co-optimus | ❌ Bloccato | Cloudflare protection |
| SteamDB | ❌ Bloccato | 403 Forbidden |

### Script creati

```
scripts/
├── steam_scraper.py          # Steam Store scraping
├── igdb_scraper.py           # IGDB API
├── rawg_scraper.py           # RAWG API  
├── gog_scraper.py            # GOG Store
├── multi_cross_reference.py  # Cross-validazione fonti
├── add_new_games.py          # Prepara nuovi giochi (legacy)
├── quality_gate.py           # Validatore co-op multi-source (Steam + RAWG)
├── catalog_enricher.py       # Arricchimento dati da Steam + SteamSpy + RAWG
└── catalog_ingest.py         # Pipeline completa: valida → arricchisce → applica
```

### Ingest pipeline (workflow consigliato)

```bash
# Dry-run: valida candidati senza modificare nulla
python3 scripts/catalog_ingest.py --input data/coop_games_to_add.json

# Con cross-reference (289 candidati)
python3 scripts/catalog_ingest.py --input data/multi_cross_reference.json

# Applica i giochi approvati (aggiunge a games.js + enrich Steam)
python3 scripts/catalog_ingest.py --apply

# Solo validazione (più veloce, senza fetch dati Steam)
python3 scripts/catalog_ingest.py --no-enrich
```

**Quality gate logic:**
- ✓ APPROVE: ha categorie Steam co-op (9/38/39/24/48/44) senza PvP
- ⚠ REVIEW: co-op + PvP misti (eFootball, GTA-style)
- ✗ REJECT: solo PvP (CS2, PUBG) oppure nessuna categoria co-op

### Cross-reference risultati

- 124 giochi validati (match con catalogo esistente)
- 289 nuovi potenziali giochi trovati
- 9 nuovi giochi co-op aggiunti (ID 618-628, esclusi CS2 e Wuthering Waves)

### File dati creati

```
data/
├── steam_coop_games.json
├── igdb_coop_games.json
├── rawg_coop_games.json
├── gog_coop_games.json
├── multi_cross_reference.json
├── coop_games_to_add.json         # candidati da validare
├── new_games_entries.json         # entry legacy (ID 618-628)
├── approved_candidates.json       # output pipeline: approvati
├── rejected_candidates.json       # output pipeline: rifiutati
└── needs_review_candidates.json   # output pipeline: review manuale
```

---

## Regole obbligatorie

1. **Nessun backend** — niente Express, Flask, FastAPI o qualsiasi server. Il sito è e resta statico.
2. **Nessun npm/Node** — `package.json` non deve esistere. Nessuna dipendenza npm.
3. **Compatibilità GitHub Pages** — tutto deve funzionare su hosting statico puro.
4. **Modifiche mirate** — tocca solo i file necessari al task. Niente refactoring non richiesti.
5. **Non fare commit o push autonomamente** — proponi le modifiche, aspetta conferma dell'utente.
6. **Preserva gli ID giochi** — ogni gioco in `games.js` ha un ID numerico fisso. Non spostare, rinumerare o eliminare senza motivo esplicito.
7. **Aggiorna `.claude/AI_COLLABORATION.md`** dopo modifiche non banali — aggiungi una voce nel log con data e descrizione.

---

## Regole architetturali

- Tratta il progetto come un catalogo/directory statico.
- Evita logica duplicata tra file diversi.
- Usa HTML semantico.
- Mantieni CSS leggibile e organizzato in `style.css`.
- Mantieni JavaScript modulare e prevedibile.
- Se i dati sono in JSON o oggetti JS, mantieni struttura pulita e scalabile.

## Regole SEO

- Ogni pagina importante deve avere `title` e `meta description` sensati.
- Mantieni gerarchia corretta degli heading (un solo `h1` per pagina).
- Aggiungi `alt` text alle immagini rilevanti.
- File SEO statici: `robots.txt` e `sitemap.xml` già presenti e configurati.

## Regole UX

- Il mobile è prioritario.
- La navigazione deve restare chiara e immediata.
- Evita popup invasivi e monetizzazione aggressiva.
- Dai priorità a leggibilità, fiducia e utilità.

## Regole monetizzazione

- Monetizzazione leggera e non invasiva.
- CTA affiliate discrete, sezioni supporto/donazioni, blocchi utili.
- Niente banner aggressivi, autoplay o pulsanti ingannevoli.

## Programmi affiliate attivi (stato 2026-03-19)

| Store | Stato | Commissione | Note |
|-------|-------|-------------|------|
| **Instant Gaming** | Attivo | 3% | Link: `?igr=gamer-ddc4a8` — in `AFFILIATE.ig` (app.js) |
| **GameBillet** | Attivo | 5% | Link: `?affiliate=fb308ca0-...` — in `AFFILIATE.gb` (app.js) |
| **Green Man Gaming** | Approvato | 5%/2% | Impact.com username: coophubs |
| **MacGameStore** | Approvato | 5% | Stesso account di WinGameStore |
| **Gameseal** | Approvato (CJ) | varia | Non ancora integrato nel codice |
| **WinGameStore** | Link scaduto | 5% | Email support inviata 2026-03-18 |
| **GOG** | Application inviata | varia | Email a affiliate@gog.com 2026-03-18 |
| **CJ Affiliate** | Attivo | varia | Fanatical, G2A, GAMIVO, GOG INT, K4G, Kinguin (pending) |

### Architettura affiliate nel codice

- **`assets/app.js`** → oggetto `AFFILIATE` (riga ~585) + funzione `buildPriceCompare()` + `addUtm()`
- **`scripts/build_static_pages.py`** → costanti `AFFILIATE_*` (riga ~104) + `render_store_links()`
- Link "Prezzi alternativi" (IG + GameBillet) appaiono nel modal e nelle pagine statiche solo se il gioco ha `steamUrl`
- GOG: parametri già predisposti, attivabili riempiendo le costanti
- Epic rimosso (programma solo per creator, non per siti web)
- I link usano `rel="sponsored"` come da best practice SEO

## Tono del sito

- Indipendente, utile e affidabile.
- Testi chiari, sintetici, orientati all'utente.
- Niente linguaggio pompato o marketing finto.

---

## Struttura dati gioco (games.js)

```js
{
  id: 1,                          // ID fisso, non cambiare
  title: "Nome Gioco",
  categories: ["action", "indie"],// "free" e "indie" usati come categorie speciali
  genres: ["action"],
  coopMode: ["online", "local"],  // online | local | sofa
  maxPlayers: 4,
  crossplay: false,               // true solo se verificato con certezza
  players: "1-4",
  image: "https://shared.cloudflare.steamstatic.com/...",
  description: "...",             // italiano
  description_en: "...",          // inglese
  mini_review_it: "...",          // mini-recensione italiano (opzionale)
  mini_review_en: "...",          // mini-recensione inglese (opzionale)
  steamUrl: "https://store.steampowered.com/app/APPID/",
  rating: 74,                     // intero 0-100 (da Steam)
  ccu: 12000,                     // concurrent users (da SteamSpy)
  trending: false,                // true se in top trending
  igUrl: "...",                   // URL Instant Gaming con affiliato
  igDiscount: 40,                 // sconto % su IG
  gbUrl: "...",                   // URL GameBillet con affiliato
  gbDiscount: 25                  // sconto % su GB
}
```

> **Nota**: "free" e "indie" sono valori nell'array `categories`, NON campi boolean separati.
> Il filtro "Gratis" usa `categories.includes('free')`. Non esistono campi `isFree`/`isIndie`.

---

## Collaborazione AI

### Team

| Agente | Ruolo |
|--------|-------|
| **Claude Code** | Leader tecnico — decisioni architetturali, QA, review, fix mirati |
| **Aider + Ollama** (qwen2.5-coder:14b, GPU Vulkan) | Task delegati — coding ripetitivo, refactoring meccanico, generazione dati |
| Gemini CLI | Fallback — quota API limitata, usare Ollama come default |

### Setup locale Aider (config non in repo)

`.aider.conf.yml` e `.aider.model.settings.yml` sono gitignored — vanno creati in locale.
Crea `.aider.conf.yml` nella root del progetto con questo contenuto:

```yaml
model: ollama/qwen2.5-coder:14b      # oppure deepseek-coder-v2:16b
openai-api-base: http://localhost:11434/v1
openai-api-key: ollama
weak-model: ollama/qwen2.5-coder:7b
read:
  - CLAUDE.md
  - .claude/AI_COLLABORATION.md
auto-commits: false
auto-lint: false
pretty: true
show-model-warnings: false
```

Hardware disponibile (RX 9070 XT 16GB VRAM + 16GB RAM):
- `qwen2.5-coder:14b` — ~9GB VRAM, veloce, buono per file medi
- `deepseek-coder-v2:16b` — ~9GB VRAM, più preciso nell'editing
- `qwen3-coder:30b` — ~18GB VRAM+RAM, potente per task complessi

### Limiti operativi di Aider con Ollama

- `assets/games.js` (~94K token) è **troppo grande** — non passarlo mai ad aider, allucinaverifica i numeri
- File adatti: `app.js`, `style.css`, `i18n.js`, `particles.js`, script Python singoli
- Aider usa "whole file" format con Ollama — riscrive l'intero file, usare su file piccoli/medi
- Verifica sempre l'output prima di accettare modifiche

### Regole di collaborazione

- Leggere sempre `.claude/AI_COLLABORATION.md` prima di intervenire.
- Aggiornare `.claude/AI_COLLABORATION.md` dopo modifiche rilevanti (sezione log con data).
- Non sovrascrivere lavoro altrui senza prima leggere lo stato corrente.
- Non lasciare decisioni importanti solo in chat — salvarle nei file del progetto.
- Segnalare sempre se una conclusione è confermata o solo un'ipotesi.

### Cosa NON deve mai fare nessuna AI

- Creare `package.json`, `index.js`, `server.js` o qualsiasi file backend
- Installare pacchetti npm o avviare un server locale come soluzione permanente
- Fare commit o push senza conferma esplicita dell'utente
- Creare file con nomi placeholder (es. `path/to/filename.js`)
- Modificare `.github/workflows/` senza approvazione esplicita

---

## Checklist prima di modificare

- Funziona ancora su GitHub Pages?
- È più semplice o più manutenibile di prima?
- Migliora davvero SEO, UX, struttura o monetizzazione?
- Sto aggiungendo complessità inutile?

## Output atteso dopo un task

- Riassumi cosa hai cambiato
- Elenca i file toccati
- Segnala passaggi manuali rimasti
- Evidenzia tutto ciò che può influenzare deploy, SEO o dominio

---

## Stato SEO (2026-03-25)

- **SEO Audit**: 91/100 (Technical 92, Content 88, Schema 95, Sitemap 98, Mobile 95, GEO 82)
- **robots.txt**: Aggiornato — blocca AI training crawler (GPTBot, ClaudeBot, Google-Extended, Bytespider, PerplexityBot, CCBot), mantiene indexing per Googlebot/Bingbot
- **Sitemap**: 555+ URL con hreflang it/en/x-default
- **Schema**: VideoGame su game pages, WebSite+Organization+SearchAction su homepage
- **Performance**: Lazy loading (IntersectionObserver), sizes attribute, cache busting v=20260325
- **Security Headers**: Cloudflare Response Header Transform Rule configurata — X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. Score: **A** su securityheaders.com
- **MCP Google Search Console**: Configurato — progetto `coophubs-gsc`, proprietà `sc-domain:coophubs.net` (siteOwner). Credenziali: `/home/andrea/.claude/mcp-gsc/`

---

## Plugin AI Installati

### GSD (Get Shit Done)

Workflow management con context engineering. Documentazione: `.planning/PLUGIN_GUIDE.md`.

```bash
/gsd:new-project    # Inizializza progetto/feature
/gsd:map-codebase   # Analizza codebase
/gsd:quick <task>   # Task veloce
/gsd:progress       # Mostra stato
```

### Ralph

Autonomous AI agent loop per task ripetitivi. Script: `scripts/ralph/ralph.sh`.

### BMAD

Agile AI development con 34+ workflow. Skill: `bmad-help`, `bmad-party-mode`, `bmad-review-*`.

---

## Documentazione Planning

- `.planning/PROJECT.md` — Visione e obiettivi
- `.planning/REQUIREMENTS.md` — Requisiti v1-v3
- `.planning/ROADMAP.md` — Roadmap completa
- `.planning/STATE.md` — Stato attuale
- `.planning/codebase/` — Analisi codebase (7 documenti)
- `.planning/backlink_checklist.md` — Directory italiane per backlink

---

## Ultimo commit (2026-03-31 18:30)

**Commit**: `5a1ddf68` — "feat: add mini-reviews to trending games, improve SEO meta, add hub editorial content"

**Modifiche**:
1. SEO title/meta aggiornati (589 giochi, keywords "coop online games")
2. 5 hub pages con contenuto editoriale
3. 17 mini-recensioni su giochi trending (ID: 1,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34)
4. UI per mini-reviews in card/featured/modal
5. Checklist backlink directory italiane

**Prossimi passi**:
- Verificare indexing Google (24-48h)
- Contattare directory italiane per backlink
- Espansione catalogo
