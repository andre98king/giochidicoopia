# Roadmap: Co-op Games Hub

## Milestones

- ✅ **v1.0 Stabilizzazione** - Fasi precedenti (shipped 2026-03-31)
- 🚧 **v1.1 Database Quality & Co-op Purity** - Phases 1-4 (in progress)

---

## Phases

<details>
<summary>✅ v1.0 Stabilizzazione (Fasi precedenti) - SHIPPED 2026-03-31</summary>

### Milestone 1.1: Cache Optimization
- Cache hit rate migliorato da 6.9% a 15.3% via `_headers`

### Milestone 1.2: Gameseal Fix
- Sconto default 15% invece di 0%, API Gameseal non ritorna salePrice

### Milestone 1.3: SEO Base
- Title/meta aggiornati per 589 giochi, keywords "coop online games"
- 8 hub pages IT + 8 EN con contenuto editoriale
- 17 mini-recensioni su giochi trending
- Sitemap split in 5 file, sottomessa a GSC

### Milestone 2.1: Nuovi Partner Affiliate
- GAMIVO (346 link), K4G (402 link), GMG Impact.com (402 link)
- Workflow automatico alle 06:00, script catalog ripristinati

</details>

---

### 🚧 v1.1 Database Quality & Co-op Purity (In Progress)

**Milestone Goal:** Trasformare il catalogo nella fonte più affidabile di giochi veramente co-op — schema corretto, CI protetto, audit tag completo, coopScore 1-3, classici scoperti, dati anomali corretti.

## Phase Details

### ✅ Phase 1: Schema Foundation & CI Hardening — VERIFIED 2026-04-01
**Goal**: Il catalogo ha un campo `coopScore` protetto e la pipeline CI non può sovrascrivere dati curati manualmente
**Depends on**: Nothing (first phase of v1.1)
**Requirements**: SCH-01, SCH-02, SCH-03, SCH-04
**Success Criteria** (what must be TRUE):
  1. Ogni gioco in `games.js` ha il campo `coopScore: null` (o intero 1-3) e il campo compare anche in `catalog.games.v1.json` e `catalog.public.v1.json`
  2. Un valore `coopScore` assegnato manualmente non viene sovrascritto dal successivo run CI giornaliero — un campo con valore esistente non viene toccato dall'update automatico
  3. Un errore in `build_static_pages.py` o `build_hub_pages.py` fa fallire il workflow CI invece di essere ignorato silenziosamente (niente `continue-on-error: true` sui build step)
  4. `validate_catalog.py` segnala come errore qualsiasi valore di `coopMode` diverso da `online`, `local`, `sofa` — zero errori sul catalogo corrente significa che tutti i valori sono gia canonici
**Plans:** 2/2 plans complete
Plans:
- [x] 01-01-PLAN.md — Schema I/O: add coopScore field, protect mini_review fields, harden CI build steps
- [x] 01-02-PLAN.md — Vocabulary: rename split to sofa, add canonical coopMode validation

### Phase 2: Tag Audit & coopScore Generation
**Goal**: Ogni gioco con `steamUrl` o `igdbId` ha un audit del tag coopMode completato, e un `coopScore` proposto e validato manualmente e pronto per l'applicazione bulk
**Depends on**: Phase 1
**Requirements**: AUD-01, AUD-02, AUD-03, AUD-04
**Success Criteria** (what must be TRUE):
  1. Lo script `audit_coop_tags.py` produce `data/coop_audit_report.json` con tre categorie di discrepanze: `tag_mismatch`, `missing_fields`, `suspect_coop` — lo script non modifica mai il catalogo
  2. Il report identifica esplicitamente i giochi senza `steamUrl` come "manual review only" e li separa dai giochi con audit completo
  3. Lo script `generate_coop_score.py` produce `data/coop_score_candidates.json` con score proposti calibrati su un campione verificato manualmente di 20-30 giochi prima dell'applicazione bulk
  4. Lo script `apply_fixes.py` legge `data/pending_fixes.json`, fa backup automatico, e applica le correzioni a `games.js` solo con flag `--apply` esplicito — senza il flag produce solo un dry-run report
**Plans**: TBD

### Phase 3: Classic Game Discovery
**Goal**: I giochi co-op classici non presenti nel catalogo vengono identificati e i candidati approvati vengono aggiunti con dati completi
**Depends on**: Phase 1
**Requirements**: CLS-01, CLS-02, CLS-03
**Success Criteria** (what must be TRUE):
  1. Lo script `discover_classics.py` produce `data/classic_candidates.json` con candidati trovati via IGDB (query con filtro `first_release_date` pre-2020 e `multiplayer_modes`) e SteamSpy `top100forever`, deduplicati rispetto al catalogo esistente
  2. Ogni candidato nel report include almeno: titolo, anno, genere, coopMode rilevato, rating Steam, motivo della candidatura — informazioni sufficienti per una decisione di inclusione senza ricerca aggiuntiva
  3. I classici approvati dall'utente vengono aggiunti al catalogo con `coopScore` pre-assegnato, `releaseYear` valorizzato, e URL di acquisto attivo (Steam, GOG o itch.io) oppure nota esplicita "no active purchase URL" se assente
**Plans**: TBD

### Phase 4: Bulk Data Fixes & Validation
**Goal**: Le anomalie sui dati esistenti sono corrette e `validate_catalog.py` certifica la qualita del catalogo completo prima della chiusura della milestone
**Depends on**: Phase 2
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04
**Success Criteria** (what must be TRUE):
  1. Nessun gioco nel catalogo ha `maxPlayers` con valori impossibili (65535, 255 come bug noti) — corretti al valore reale o impostati a `null` con nota
  2. Nessun gioco con pagina Steam attiva mostra `rating: 0` — aggiornato al valore reale o marcato esplicitamente come non disponibile anziche 0
  3. I giochi con `crossplay: true` senza evidenza API sono corretti a `false` dopo spot-check verificato
  4. Un singolo run di `validate_catalog.py` produce un report con: percentuale giochi con `coopScore` assegnato, conteggio `coopMode` non canonici (target: 0), conteggio `maxPlayers` anomali (target: 0)
**Plans**: TBD

---

## Progress

**Execution Order:** 1 → 2 e 3 in parallelo (entrambi dipendono da Phase 1) → 4

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Schema Foundation & CI Hardening | v1.1 | 2/2 | Verified | 2026-04-01 |
| 2. Tag Audit & coopScore Generation | v1.1 | 0/? | Not started | - |
| 3. Classic Game Discovery | v1.1 | 0/? | Not started | - |
| 4. Bulk Data Fixes & Validation | v1.1 | 0/? | Not started | - |
