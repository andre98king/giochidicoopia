# scripts/ — Indice completo

Tutti i 45 script Python organizzati per dominio funzionale.
Questo file è la mappa di navigazione per AI e collaboratori umani.

---

## Livello 0 — Moduli condivisi (leggere PRIMA di toccare qualsiasi altro script)

| Script | Ruolo | Dipendenze |
|--------|-------|-----------|
| `catalog_config.py` | Costanti globali: DELAY, limiti, TAG_MAP, BLACKLIST_APPIDS, env keys | `os` |
| `catalog_data.py` | Layer I/O per `assets/games.js` ↔ `data/catalog.*.json`. Legge/scrive il catalogo | `pathlib`, `json`, `re` |
| `quality_gate.py` | Valida se un gioco è co-op: chiama Steam API, restituisce APPROVE/REVIEW/REJECT | `urllib`, `json` |

> **Regola**: Qualsiasi script che tocca il catalogo importa `catalog_data`. Qualsiasi script che valida nuovi giochi importa `quality_gate`.

---

## Livello 1 — Pipeline CI (eseguiti da `.github/workflows/update.yml`)

Ordine di esecuzione nel workflow:

```
auto_update.py
  → fetch_affiliate_prices.py   (continue-on-error)
  → fetch_gameseal_prices.py    (continue-on-error)
  → fetch_gamivo_prices.py      (continue-on-error)
  → fetch_k4g_prices.py         (continue-on-error)
  → fetch_gmg_prices.py         (continue-on-error)
  → build_static_pages.py
  → build_hub_pages.py
  → validate_catalog.py
```

| Script | Ruolo | Input | Output |
|--------|-------|-------|--------|
| `auto_update.py` | Pipeline principale: aggiorna CCU/rating, scopre nuovi giochi, arricchisce, scrive games.js | `assets/games.js`, API Steam/IGDB/GOG/RAWG | `assets/games.js`, `data/catalog.*.json` |
| `build_static_pages.py` | Genera `games/<id>.html` + `sitemap*.xml` per SEO | `assets/games.js`, `data/seo_overrides.json` | `games/*.html`, `sitemap*.xml` |
| `build_hub_pages.py` | Genera hub pages IT (`giochi-coop-*.html`) | `assets/games.js`, `data/hub_editorial.json` | `giochi-coop-*.html` |
| `validate_catalog.py` | Controlla integrità post-build: ID duplicati, campi mancanti, sitemap | `assets/games.js`, `games/*.html`, `sitemap*.xml` | stdout (errori fatali fanno fallire CI) |

---

## Livello 2 — Fetch prezzi affiliate (parte CI, continue-on-error)

| Script | Fonte | Dati letti | Dati scritti |
|--------|-------|-----------|-------------|
| `fetch_affiliate_prices.py` | Instant Gaming + GameBillet (scraping async) | `assets/games.js` | `assets/games.js` (aggiorna `igUrl`, `igDiscount`, `gbUrl`, `gbDiscount`) |
| `fetch_gameseal_prices.py` | Gameseal + Kinguin via CJ API | `assets/games.js` | `assets/games.js` |
| `fetch_gamivo_prices.py` | GAMIVO via CJ API | `assets/games.js` | `assets/games.js` |
| `fetch_k4g_prices.py` | K4G (scraping) | `assets/games.js` | `assets/games.js` |
| `fetch_gmg_prices.py` | Green Man Gaming (Impact.com) | `assets/games.js` | `assets/games.js` |

---

## Livello 3 — Fetch dati non-prezzi

| Script | Fonte | Ruolo |
|--------|-------|-------|
| `fetch_free_games.py` | Epic, Steam, GOG RSS | Aggiorna `assets/free_games.js` con giochi gratis della settimana |
| `fetch_analytics.py` | Google Search Console + Cloudflare | Scarica metriche SEO localmente per analisi |
| `fetch_youtube_videos.py` | YouTube Data API | Associa trailer YouTube ai giochi del catalogo |

---

## Livello 4 — Build supplementari (esecuzione manuale)

| Script | Ruolo | Nota |
|--------|-------|------|
| `generate_hub_pages_en.py` | Genera hub pages EN (`en/*.html`) | Eseguire dopo modifiche alle hub IT |
| `apply_fixes.py` | Applica patch da `data/pending_fixes.json` al catalogo | Uso occasionale |

---

## Livello 5 — Fonti dati (adapters, usati da `auto_update.py`)

| Script | API/Fonte | Co-op rilevante |
|--------|-----------|----------------|
| `steam_catalog_source.py` | Steam Store + SteamSpy | Categorie 9/38/39/24/48/44 |
| `steam_new_releases_source.py` | Steam new releases feed | Ultimi 100 giochi rilasciati |
| `igdb_catalog_source.py` | IGDB API (Twitch auth) | `game_modes: co-operative` |
| `rawg_catalog_source.py` | RAWG API | `tags: co-op` |
| `gog_catalog_source.py` | GOG Store scraping | Sezione multiplayer GOG |
| `itch_catalog_source.py` | itch.io RSS | Feed co-op/local-multiplayer |

---

## Livello 6 — Discovery e cross-reference (uso locale/occasionale)

| Script | Ruolo | Input | Output |
|--------|-------|-------|--------|
| `cross_reference.py` | Match Steam↔catalogo su titolo/appid | `data/steam_coop_games.json`, `data/steam_coop_details.json` | `data/cross_reference_results.json` |
| `multi_cross_reference.py` | Match multi-fonte (Steam+IGDB+RAWG+GOG) | `data/*_coop_games.json` | `data/multi_cross_reference.json` |
| `discover_backfill.py` | Trova giochi con steamUrl ma senza altri dati | `assets/games.js` | `data/backfill_candidates.json` |
| `discover_classics.py` | Cerca giochi classici co-op mancanti | Steam API | `data/classic_candidates.json` |
| `add_classics.py` | Aggiunge classici approvati al catalogo | `data/approved_classics.json` | `assets/games.js` |
| `add_new_games.py` | Aggiunge manualmente nuovi giochi | JSON manuale | `assets/games.js` |

---

## Livello 7 — Scrapers standalone (raccolta dati grezza, output in data/)

| Script | Fonte | Output |
|--------|-------|--------|
| `steam_scraper.py` | Steam Store | `data/steam_coop_games.json` |
| `igdb_scraper.py` | IGDB API | `data/igdb_coop_games.json` |
| `rawg_scraper.py` | RAWG API | `data/rawg_coop_games.json` |
| `gog_scraper.py` | GOG Store | `data/gog_coop_games.json` |
| `cooptimus_scraper.py` | Co-Optimus (bloccato Cloudflare) | N/A — non funziona |

---

## Livello 8 — Validazione e auditing (uso locale)

| Script | Ruolo |
|--------|-------|
| `validate_catalog.py` | Anche standalone: `python3 scripts/validate_catalog.py` |
| `validate_free_games.py` | Valida `assets/free_games.js` |
| `game_validator.py` | Validatore singolo gioco (usato da catalog_ingest) |
| `catalog_audit.py` | Audit completo co-op tags su tutto il catalogo |
| `audit_coop_tags.py` | Verifica coerenza tag co-op con Steam API |

---

## Livello 9 — Pipeline ingest manuale (workflow consigliato per aggiungere giochi)

```bash
# 1. Raccogli candidati da fonti
python3 scripts/steam_scraper.py && python3 scripts/igdb_scraper.py

# 2. Cross-reference e deduplicazione
python3 scripts/multi_cross_reference.py

# 3. Dry-run quality gate
python3 scripts/catalog_ingest.py --input data/multi_cross_reference.json

# 4. Applica giochi approvati
python3 scripts/catalog_ingest.py --apply

# 5. Rebuild pagine statiche
python3 scripts/build_static_pages.py && python3 scripts/build_hub_pages.py
```

| Script | Ruolo |
|--------|-------|
| `catalog_ingest.py` | Orchestratore pipeline: valida → arricchisce → aggiunge al catalogo |
| `catalog_enricher.py` | Arricchisce un gioco con dati Steam + SteamSpy + RAWG |
| `generate_coop_score.py` | Calcola punteggio co-op composito per sorting |

---

## Livello 10 — Classificatori AI/ML (sperimentale)

| Script | Ruolo | Stato |
|--------|-------|-------|
| `coop_classifier.py` | Classifica co-op via keyword matching | Funzionante |
| `coop_classifier_v2.py` | Versione migliorata con scoring | Funzionante |

> Config modello Ollama: `Modelfile.coop-classifier` nella root del progetto.

---

## File non-Python in scripts/

| File | Ruolo |
|------|-------|
| `requirements.txt` | Dipendenze pip per CI e locale |
| `local/` | Script locali non committati / esperimenti |

---

## Dipendenze tra script (grafo semplificato)

```
catalog_config.py ←── auto_update.py
catalog_data.py   ←── auto_update.py, build_static_pages.py, build_hub_pages.py,
                       validate_catalog.py, catalog_ingest.py, fetch_affiliate_prices.py
quality_gate.py   ←── auto_update.py, catalog_ingest.py
catalog_enricher  ←── catalog_ingest.py
igdb_catalog_src  ←── auto_update.py
gog_catalog_src   ←── auto_update.py
itch_catalog_src  ←── auto_update.py
rawg_catalog_src  ←── auto_update.py
steam_catalog_src ←── auto_update.py
steam_new_rel_src ←── auto_update.py
build_static_pg   ←── validate_catalog.py (import diretto)
```

> **NON spostare gli script in sottocartelle**: usano bare imports (`import catalog_data`)
> che funzionano solo se tutti i file sono nella stessa directory.
