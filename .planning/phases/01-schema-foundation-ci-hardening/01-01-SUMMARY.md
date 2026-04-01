---
phase: 01-schema-foundation-ci-hardening
plan: 01
subsystem: database
tags: [catalog_data, games.js, json, ci, github-actions, python, schema]

# Dependency graph
requires: []
provides:
  - "coopScore field (nullable int 1-3) in games.js, catalog.games.v1.json, and catalog.public.v1.json for all 589 games"
  - "mini_review_it and mini_review_en fields preserved through CI round-trips via load_games/write_legacy_games_js"
  - "ef() parser handles null literals for nullable fields"
  - "CI build steps (build_static_pages, build_hub_pages) fail-fast instead of silently ignoring errors"
affects: [02-coop-audit-scoring, 03-classic-discovery, 04-data-gaps-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ef() regex pattern: extends to handle null, true, false, int, string, array literals"
    - "Nullable field convention: coopScore uses None (not 0 or '') to distinguish unscored from scored"
    - "JSON round-trip safety: new fields added to both load_games() and write_legacy_games_js() atomically"

key-files:
  created: []
  modified:
    - "scripts/catalog_data.py"
    - "assets/games.js"
    - "data/catalog.games.v1.json"
    - "data/catalog.public.v1.json"
    - ".github/workflows/update.yml"

key-decisions:
  - "coopScore uses None/null (not 0) to distinguish unscored games from games with score=0 — preserving scoring semantics for Phase 2"
  - "public catalog export now includes gmgUrl, gmgDiscount (previously missing) alongside coopScore"
  - "validate_catalog.py sitemap URL errors are pre-existing and out of scope — deferred, not blocking"

patterns-established:
  - "ef() null handling: always check value == 'null' after bool checks, before int check"
  - "New game fields must be added in both load_games() and write_legacy_games_js() to survive CI round-trips"

requirements-completed: [SCH-01, SCH-02, SCH-03]

# Metrics
duration: 8min
completed: 2026-04-01
---

# Phase 01 Plan 01: Schema Foundation & CI Hardening Summary

**coopScore nullable field added to all 589 games via catalog_data.py I/O extension, mini_review data loss bug fixed, and CI build steps hardened to fail-fast**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-01T10:41:00Z
- **Completed:** 2026-04-01T10:49:02Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Extended `ef()` parser in catalog_data.py to handle `null` JavaScript literals (returning Python `None`)
- Added `coopScore` (nullable), `mini_review_it`, `mini_review_en` to `load_games()` and `write_legacy_games_js()` — fixing a pre-existing data loss bug where 17 mini-reviews would be silently erased on next CI run
- Added `coopScore`, `gmgUrl`, `gmgDiscount` to `build_public_catalog_export()` (gmg fields were previously missing from public export)
- Round-tripped all 589 games through updated I/O: every game now has `coopScore: null` in games.js and both JSON exports
- Removed `continue-on-error: true` from "Build static game pages" and "Build hub pages SEO" CI steps — build errors now fail the workflow

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend catalog_data.py schema for coopScore and mini_review fields** - `ce6ae3b6` (feat)
2. **Task 2: Add coopScore to all games, regenerate JSON exports, harden CI YAML** - `0d46a7e0` (feat)

## Files Created/Modified
- `scripts/catalog_data.py` - ef() null handling, load_games() 3 new fields, build_public_catalog_export() coopScore+gmg, write_legacy_games_js() template extended
- `assets/games.js` - All 589 games now have coopScore: null, mini_review_it: "", mini_review_en: "" (or preserved values)
- `data/catalog.games.v1.json` - Regenerated with coopScore field on every game
- `data/catalog.public.v1.json` - Regenerated with coopScore, gmgUrl, gmgDiscount fields
- `.github/workflows/update.yml` - Removed continue-on-error from 2 build steps (5 remain on affiliate steps)

## Decisions Made
- `coopScore` uses `None`/`null` as default (not `0`) to distinguish "not yet scored" from scored games — critical for Phase 2 audit scoring workflow
- `gmgUrl` and `gmgDiscount` were missing from the public catalog export and were added alongside `coopScore` (Rule 2: missing field in export)
- pre-existing `validate_catalog.py` sitemap URL errors are out of scope — deferred to `deferred-items.md`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added gmgUrl and gmgDiscount to public catalog export**
- **Found during:** Task 1 (reading build_public_catalog_export())
- **Issue:** gmgUrl and gmgDiscount fields present in games.js and catalog.games.v1.json but missing from catalog.public.v1.json — inconsistency that would break any public API consumer
- **Fix:** Added both fields to the public export dict alongside coopScore
- **Files modified:** scripts/catalog_data.py
- **Verification:** `python3 -c "import json; d=json.load(open('data/catalog.public.v1.json')); print('gmgUrl' in d['games'][0])"` prints True
- **Committed in:** ce6ae3b6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** gmgUrl/gmgDiscount addition was necessary for public export consistency. No scope creep.

## Issues Encountered
- `python3 scripts/validate_catalog.py` reports `ERROR: Missing sitemap URLs` — this is a pre-existing issue unrelated to this plan's changes. The validator checks if all sitemap URLs map to existing files, but those files (game pages, hub pages) exist and were not regenerated by this plan. Deferred.

## Known Stubs
None — coopScore is intentionally `null` for all games at this stage. Scoring is the purpose of Phase 2. This is tracked and expected.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 (coop-audit-scoring) can now read/write coopScore via catalog_data.load_games() and write_legacy_games_js()
- Phase 3 (classic-discovery) similarly benefits from the extended schema
- CI now fails loudly on build script errors — any broken build_static_pages.py will be immediately visible

## Self-Check: PASSED

- FOUND: scripts/catalog_data.py
- FOUND: assets/games.js
- FOUND: data/catalog.games.v1.json
- FOUND: data/catalog.public.v1.json
- FOUND: .github/workflows/update.yml
- FOUND: .planning/phases/01-schema-foundation-ci-hardening/01-01-SUMMARY.md
- FOUND commit: ce6ae3b6 (Task 1)
- FOUND commit: 0d46a7e0 (Task 2)
- FOUND commit: 21f28eb7 (metadata)

---
*Phase: 01-schema-foundation-ci-hardening*
*Completed: 2026-04-01*
