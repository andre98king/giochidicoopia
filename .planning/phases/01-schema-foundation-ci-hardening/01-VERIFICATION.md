---
phase: 01-schema-foundation-ci-hardening
verified: 2026-04-01T11:45:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 1: Schema Foundation & CI Hardening — Verification Report

**Phase Goal:** Il catalogo ha un campo `coopScore` protetto e la pipeline CI non può sovrascrivere dati curati manualmente
**Verified:** 2026-04-01T11:45:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ogni gioco in `games.js` ha il campo `coopScore: null` (o int 1-3) e il campo compare anche in entrambi i JSON | VERIFIED | 589/589 games have `coopScore` key; both JSON exports have 589 entries with `coopScore`; confirmed via Python load_games() |
| 2 | Un valore `coopScore` assegnato manualmente non viene sovrascritto dal CI giornaliero | VERIFIED | `auto_update.py` calls `load_legacy_catalog_bundle()` (reads coopScore) then `write_legacy_games_js(existing_games)` (writes it back unchanged); no code in auto_update.py sets or clears coopScore |
| 3 | Un errore in `build_static_pages.py` o `build_hub_pages.py` fa fallire il workflow CI | VERIFIED | `.github/workflows/update.yml` lines 60-64: both build steps have no `continue-on-error`; only 5 `continue-on-error` lines remain, all on affiliate price-fetch steps (lines 37, 41, 47, 53, 57) |
| 4 | `validate_catalog.py` segnala come errore qualsiasi coopMode diverso da `online`, `local`, `sofa` — zero errori sul catalogo corrente | VERIFIED | `CANONICAL_COOP_MODES = {"online", "local", "sofa"}` at line 21; hard error appended to `errors` list at line 306; 0 non-canonical values found in current catalog |

**Score: 4/4 truths verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/catalog_data.py` | ef() handles null, load_games reads coopScore+mini_review_*, write_legacy_games_js writes them, public export includes coopScore | VERIFIED | `coopScore` at lines 278, 371, 462; ef() null handling confirmed; 17 mini_review_it values preserved through round-trip |
| `assets/games.js` | All 589 games have coopScore field | VERIFIED | 589 occurrences of `coopScore`; 210 games have `"sofa"` coopMode; 0 games with `"split"` |
| `.github/workflows/update.yml` | Build steps fail-fast (no continue-on-error) | VERIFIED | Exactly 5 `continue-on-error` lines, all on affiliate fetch steps; build steps at lines 60-64 have none |
| `scripts/validate_catalog.py` | CANONICAL_COOP_MODES enforcement as hard error | VERIFIED | Constant defined at line 21; violation appends to `errors` (not `warnings`) at line 306 |
| `scripts/steam_catalog_source.py` | Outputs `sofa` instead of `split` | VERIFIED | `modes.append("sofa")` at line 158 |
| `scripts/igdb_catalog_source.py` | Outputs `sofa` instead of `split` | VERIFIED | `coop_modes.append("sofa")` at line 329 |
| `scripts/itch_catalog_source.py` | Outputs `sofa` instead of `split` | VERIFIED | `"split-screen": ["local", "sofa"]` in tag mapping; `is_local` check uses `"sofa"` |
| `assets/app.js` | Frontend filter uses `sofa` | VERIFIED | `{ id: 'mode_split', field: 'coopMode', value: 'sofa' }` at line 46 |
| `data/catalog.games.v1.json` | coopScore on every game | VERIFIED | 589 `"coopScore"` occurrences |
| `data/catalog.public.v1.json` | coopScore on every game | VERIFIED | 589 `"coopScore"` occurrences |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `catalog_data.py ef()` | `games.js coopScore: null` | regex handles null literal | WIRED | `ef('coopScore: null', 'coopScore')` returns Python None; confirmed programmatically |
| `catalog_data.py write_legacy_games_js()` | `assets/games.js` | template includes coopScore, mini_review_it, mini_review_en | WIRED | Lines 462-465 in write template include all three fields |
| `auto_update.py` | `coopScore` preserved through CI | load_games reads value, write_legacy writes it back | WIRED | Round-trip confirmed: load reads coopScore; update loop only modifies ccu/rating/trending/description_en; write emits unchanged coopScore |
| `steam/igdb/itch sources` | `validate_catalog.py CANONICAL_COOP_MODES` | sources output "sofa", validator accepts "sofa" | WIRED | All three sources confirmed to output "sofa"; CANONICAL_COOP_MODES includes "sofa" |
| `.github/workflows/update.yml build steps` | CI failure on build error | no continue-on-error | WIRED | Confirmed: lines 60-64 have no continue-on-error; workflow will fail if build scripts exit non-zero |

---

### Data-Flow Trace (Level 4)

Not applicable — no dynamic rendering components introduced in this phase. All artifacts are data pipeline scripts and CI configuration.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ef() handles null literal | `python3 -c "import sys; sys.path.insert(0,'scripts'); import catalog_data; assert catalog_data.ef('coopScore: null', 'coopScore') is None"` | No assertion error | PASS |
| ef() preserves int values | `python3 -c "... assert catalog_data.ef('coopScore: 2', 'coopScore') == 2"` | Returns 2 | PASS |
| All 589 games have coopScore key | `load_games()` + `all('coopScore' in g for g in games)` | True | PASS |
| Zero non-canonical coopMode values | `load_games()` + set difference check | 0 games | PASS |
| 17 mini_review_it values survived | `len([g for g in games if g.get('mini_review_it')])` | 17 | PASS |
| validate_catalog.py: 0 coopMode errors | Run validate script, check for "Non-canonical coopMode" in output | Absent | PASS |
| CI build steps have no continue-on-error | `grep -n "continue-on-error" update.yml` | Lines 37,41,47,53,57 only (affiliate steps) | PASS |
| JSON exports have coopScore | `grep -c '"coopScore"' catalog.games.v1.json` | 589 | PASS |
| Zero "split" coopMode in games.js | `grep -c '"split"' assets/games.js` | 0 | PASS |
| 210 "sofa" values in games.js | `grep -c '"sofa"' assets/games.js` | 210 | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCH-01 | 01-01 | `coopScore` field in schema, propagated to JSON exports | SATISFIED | 589/589 games in games.js and both JSON exports have `coopScore` |
| SCH-02 | 01-01 | Curated fields protected from CI overwrite | SATISFIED | `auto_update.py` round-trip preserves coopScore; `mini_review_it/en` now in load/write cycle; 17 values verified intact |
| SCH-03 | 01-01 | `continue-on-error` removed from build steps | SATISFIED | update.yml lines 60-64: both build steps have no `continue-on-error`; 5 remain on affiliate steps only |
| SCH-04 | 01-02 | coopMode vocabulary canonicalized to {online, local, sofa} | SATISFIED | CANONICAL_COOP_MODES enforced as hard error; 210 "split" renamed to "sofa"; 0 non-canonical values in current catalog |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | - | - | - | - |

The only "empty" values (`coopScore: null`) are intentional and documented — null means "not yet scored", which is the correct semantic for Phase 1. Phase 2 will assign values.

---

### Human Verification Required

None. All four success criteria were verifiable programmatically with full confidence.

The pre-existing `validate_catalog.py` sitemap URL error ("Missing sitemap URLs" for 1182+ URLs) is unrelated to Phase 1 scope and documented in both SUMMARYs as deferred. It does not block this phase's goal.

---

### Gaps Summary

No gaps. All four success criteria are fully achieved:

1. `coopScore` is present on all 589 games in games.js, catalog.games.v1.json, and catalog.public.v1.json.
2. The CI round-trip in auto_update.py reads and writes coopScore without modification — any manually assigned value survives.
3. Both build steps fail-fast in CI (no `continue-on-error`).
4. CANONICAL_COOP_MODES = {"online", "local", "sofa"} is enforced as a hard error in validate_catalog.py, with zero violations on the current catalog.

**Commits verified:** ce6ae3b6, 0d46a7e0, 9126f2a9, 3208eb66 — all exist in git history with correct content.

---

_Verified: 2026-04-01T11:45:00Z_
_Verifier: Claude (gsd-verifier)_
