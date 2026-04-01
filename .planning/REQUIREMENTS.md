# REQUIREMENTS.md — Milestone v1.1: Database Quality & Co-op Purity
*Last updated: 2026-04-01*

---

## Active Requirements

### Schema & CI Hardening

- [x] **SCH-01**: Il campo `coopScore` (int 1-3, nullable) è aggiunto allo schema in `catalog_data.py` e propagato a `catalog.games.v1.json` e `catalog.public.v1.json`
- [x] **SCH-02**: I campi curati manualmente (`coopScore`, `mini_review_it`, `mini_review_en`, `igUrl`, `igDiscount`, `gbUrl`, `gbDiscount`) sono protetti dal CI giornaliero e non vengono sovrascritti dagli update automatici
- [x] **SCH-03**: Il flag `continue-on-error: true` è rimosso da `build_static_pages.py` nel workflow CI, così un errore di build blocca il deploy invece di silenziarlo
- [x] **SCH-04**: Il vocabolario `coopMode` è canonicalizzato: i valori accettati sono solo `online`, `local`, `sofa` — qualsiasi altro valore è segnalato come errore dalla pipeline

### Tag Audit & coopScore

- [x] **AUD-01**: Lo script `audit_coop_tags.py` legge il catalogo, interroga Steam e IGDB per ogni gioco con `steamUrl` o `igdbId`, e scrive un report `data/coop_audit_report.json` con le discrepanze trovate (read-only, non modifica mai il catalogo direttamente)
- [x] **AUD-02**: Il report di audit distingue almeno tre categorie: `tag_mismatch` (coopMode nel catalogo non corrisponde alle API), `missing_fields` (maxPlayers/coopMode/crossplay assenti), `suspect_coop` (gioco probabilmente non co-op secondo le API)
- [x] **AUD-03**: Lo script `generate_coop_score.py` assegna `coopScore` 1-3 a ogni gioco usando regole basate su segnali IGDB + Steam (`multiplayer_modes`, categorie co-op, player count), con calibrazione su un campione di 20-30 giochi verificati manualmente prima dell'applicazione bulk
- [x] **AUD-04**: Lo script `apply_fixes.py` legge un file `data/pending_fixes.json` (generato dall'utente dopo revisione del report) e applica le correzioni al catalogo in modo sicuro, con backup prima di ogni modifica

### Classic Game Discovery

- [x] **CLS-01**: Lo script `discover_classics.py` interroga IGDB (con filtro per `first_release_date` e `multiplayer_modes`) e SteamSpy (`top100forever`) per trovare giochi co-op rilevanti non ancora presenti nel catalogo — output: `data/classic_candidates.json` per revisione manuale
- [x] **CLS-02**: Il report candidati classici include almeno: titolo, anno, genere, coopMode rilevato, rating Steam, perché è candidato — così la revisione manuale è informata
- [x] **CLS-03**: I giochi classici approvati manualmente dall'utente vengono aggiunti al catalogo con `coopScore` pre-assegnato e senza `steamUrl` mancante (o con nota esplicita se non disponibile su Steam)

### Bulk Data Fixes

- [x] **FIX-01**: I giochi con `maxPlayers` palesemente errato (valori > 64 come 65535, 255) vengono corretti con il valore reale o impostati a `null` se non verificabile
- [x] **FIX-02**: I giochi con `rating: 0` che hanno una pagina Steam attiva vengono aggiornati con il rating reale, oppure marcati esplicitamente come "non disponibile" invece di mostrare 0
- [x] **FIX-03**: Il campo `crossplay` è verificato per i giochi con `crossplay: true` che non hanno evidenza API di supporto crossplay — i falsi positivi vengono corretti a `false`
- [x] **FIX-04**: La pipeline di validazione (`validate_catalog.py`) è aggiornata per segnalare: `coopScore` mancante, `coopMode` con valori non canonici, `maxPlayers` anomali

---

## Future Requirements (deferred)

- Badge `coopScore` visibile nell'UI (filtro o icona sulle card) — rinviato a milestone successiva
- Hub page "Classici Co-op" con editoriale — rinviato
- Mini-recensioni per i nuovi classici aggiunti — rinviato
- Deprecazione definitiva di `assets/games.js` in favore di solo JSON — rinviato
- Audit giochi senza né `steamUrl` né `igdbId` (187 giochi) — rinviato, richiede ricerca manuale

---

## Out of Scope (questa milestone)

- Nuove feature UX (filtri nuovi, redesign, quiz) — focus esclusivo sulla qualità dati
- Backend o Node.js di qualsiasi tipo — stack invariato
- Integrazione nuovi store affiliate — rinviato
- Automazione completa del coopScore nel CI settimanale — richiede validazione manuale prima

---

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| SCH-01 | Phase 1 | Complete |
| SCH-02 | Phase 1 | Complete |
| SCH-03 | Phase 1 | Complete |
| SCH-04 | Phase 1 | Complete |
| AUD-01 | Phase 2 | Complete |
| AUD-02 | Phase 2 | Complete |
| AUD-03 | Phase 2 | Complete |
| AUD-04 | Phase 2 | Complete |
| CLS-01 | Phase 3 | Complete |
| CLS-02 | Phase 3 | Complete |
| CLS-03 | Phase 3 | Complete |
| FIX-01 | Phase 4 | Complete |
| FIX-02 | Phase 4 | Complete |
| FIX-03 | Phase 4 | Complete |
| FIX-04 | Phase 4 | Complete |
