# data/ — Tassonomia dei file JSON

38 file in questa cartella. Questa guida spiega cosa è "vivo", cosa è un artefatto
temporaneo, e cosa non va toccato durante la CI.

---

## Stato dei file

### LIVE — Scritti e letti dalla CI (non spostare, non rinominare)

| File | Scritto da | Letto da | Commit in git? |
|------|-----------|---------|---------------|
| `catalog.games.v1.json` | `catalog_data.py` | `catalog_data.py` | ✅ Sì (CI) |
| `catalog.public.v1.json` | `catalog_data.py` | `catalog_data.py` | ✅ Sì (CI) |

> `catalog.games.v1.json` = catalogo completo (con campi privati)
> `catalog.public.v1.json` = versione ridotta per uso pubblico

---

### EDITORIALE — Curati manualmente, letti dalla CI

| File | Letto da | Contenuto |
|------|---------|-----------|
| `hub_editorial.json` | `build_hub_pages.py` | Testi intro, meta, CTA per le 8 hub pages |
| `game_reviews.json` | (futuro) | Mini-recensioni curate |
| `seo_overrides.json` | `build_static_pages.py` | Override manuali di title/desc SEO per giochi specifici |

> ⚠️ Modifica questi file con cura — influenzano direttamente le pagine HTML generate.

---

### PIPELINE — Output del quality gate e ingest

Scritti da `catalog_ingest.py` dopo ogni run. Non committati in git.

| File | Contenuto | Prossima azione |
|------|-----------|----------------|
| `approved_candidates.json` | Giochi passati il quality gate → pronti per `--apply` | Revisione + `catalog_ingest.py --apply` |
| `rejected_candidates.json` | Giochi rifiutati (solo PvP, DLC, tool) | Nessuna (log di riferimento) |
| `needs_review_candidates.json` | Co-op + PvP misti, revisione manuale richiesta | Revisione manuale |
| `audit_state.json` | Stato persistente dell'audit co-op | Usato da `catalog_audit.py` |
| `audit_needs_review.json` | Output audit: giochi con tag dubbi | Revisione manuale |
| `audit_rejected.json` | Output audit: giochi da rimuovere | Approvazione manuale prima di rimuovere |
| `coop_audit_report.json` | Report completo ultimo audit | Lettura/analisi |

---

### DISCOVERY — Candidati per espansione catalogo

Prodotti da scrapers e cross-reference. Non committati in git.

| File | Prodotto da | Contenuto |
|------|------------|-----------|
| `steam_coop_games.json` | `steam_scraper.py` | Lista grezza giochi co-op Steam |
| `igdb_coop_games.json` | `igdb_scraper.py` | Lista grezza giochi co-op IGDB |
| `rawg_coop_games.json` | `rawg_scraper.py` | Lista grezza giochi co-op RAWG |
| `gog_coop_games.json` | `gog_scraper.py` | Lista grezza giochi co-op GOG |
| `cooptimus_games.json` | `cooptimus_scraper.py` | Lista Co-Optimus (scraper bloccato) |
| `multi_cross_reference.json` | `multi_cross_reference.py` | 289 candidati cross-validati (4 fonti) |
| `cross_reference_results.json` | `cross_reference.py` | Match Steam↔catalogo |
| `coop_games_to_add.json` | Manuale / pipeline | Candidati in attesa di validazione |
| `new_games_to_add.json` | Manuale | Candidati aggiuntivi |
| `new_games_entries.json` | Manuale / `add_new_games.py` | Entry legacy ID 618-628 |
| `new_games_detailed.json` | Pipeline | Versione arricchita di new_games_entries |
| `backfill_candidates.json` | `discover_backfill.py` | Giochi con dati mancanti |
| `classic_candidates.json` | `discover_classics.py` | Giochi classici co-op da aggiungere |
| `approved_classics.json` | Manuale | Classici approvati per `add_classics.py` |

---

### ARTEFATTI TEMPORANEI — Fix e patch pendenti

| File | Contenuto | Azione richiesta |
|------|-----------|-----------------|
| `pending_fixes.json` | Fix generici in attesa | `apply_fixes.py` |
| `pending_coopscore_fixes.json` | Correzioni co-op score | `generate_coop_score.py` |
| `pending_maxplayers_fixes.json` | Correzioni maxPlayers errati | `apply_fixes.py` |
| `_nocoop_flagged.json` | Giochi segnalati come non-co-op | Revisione → rimozione o mantenimento |
| `coop_discrepancies.json` | Discrepanze tag co-op rilevate | Revisione manuale |
| `coop_score_candidates.json` | Candidati per scoring | `generate_coop_score.py` |
| `coop_classification_results.json` | Output classificatore AI | Analisi |
| `no_steam_audit.json` | Giochi senza steamUrl | Arricchimento manuale |

---

### DATABASE LOCALE — Versione validata per query locali

| File | Contenuto |
|------|-----------|
| `validated_db.json` | Snapshot catalogo validato (prodotto da `validate_catalog.py`) |
| `steam_coop_details.json` | Dati dettagliati Steam per cross-reference |
| `steam_url_enrichments.json` | Mapping titolo → steamUrl per giochi senza URL |

---

### LOG

| File | Contenuto |
|------|-----------|
| `scraper_log.jsonl` | Log strutturato delle ultime run scrapers (JSONL, una entry per riga) |

---

## File nascosti

| File | Contenuto |
|------|-----------|
| `.audit_steam_cache.json` | Cache chiamate Steam API durante gli audit (evita rate limit) |

---

## Cosa NON spostare

I file `catalog.games.v1.json` e `catalog.public.v1.json` sono referenziati direttamente
in `.github/workflows/update.yml` (git add) e in `catalog_data.py` via `DATA_DIR`.
Spostarli romperebbe la CI senza aggiornare entrambi i file.

`hub_editorial.json` e `seo_overrides.json` sono referenziati con path hardcoded in
`build_hub_pages.py` e `build_static_pages.py`.
