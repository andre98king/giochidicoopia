---
phase: 01-schema-foundation-ci-hardening
plan: 02
subsystem: database
tags: [catalog_data, games.js, json, python, schema, coopMode, vocabulary]

# Dependency graph
requires: ["01-01"]
provides:
  - "coopMode vocabulary canonicalized: only {online, local, sofa} accepted"
  - "210 former 'split' coopMode values renamed to 'sofa' in games.js and JSON exports"
  - "validate_catalog.py enforces CANONICAL_COOP_MODES as hard error"
  - "All pipeline sources (Steam, IGDB, itch.io) produce 'sofa' instead of 'split'"
  - "Frontend app.js filter uses 'sofa' value"
affects: [02-coop-audit-scoring, 03-classic-discovery, 04-data-gaps-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CANONICAL_COOP_MODES constant in validate_catalog.py — single source of truth for accepted coopMode values"
    - "Vocabulary rename via sed for bulk JS data file changes (safe when value is unambiguous)"

key-files:
  created: []
  modified:
    - "scripts/steam_catalog_source.py"
    - "scripts/igdb_catalog_source.py"
    - "scripts/itch_catalog_source.py"
    - "scripts/catalog_data.py"
    - "scripts/build_static_pages.py"
    - "scripts/build_hub_pages.py"
    - "scripts/validate_catalog.py"
    - "assets/app.js"
    - "assets/games.js"
    - "data/catalog.games.v1.json"
    - "data/catalog.public.v1.json"

key-decisions:
  - "coopMode vocabulary is now canonical: {online, local, sofa} — 'split' is permanently removed from the data schema"
  - "validate_catalog.py CANONICAL_COOP_MODES is the enforcing contract — any future source adding non-canonical values will be caught as a hard error"
  - "Steam source variable has_split kept as-is (reads Steam's API category strings which say 'split') — only the OUTPUT value was changed to 'sofa'"

patterns-established:
  - "Vocabulary rename pattern: update sources first (Task 1), then bulk-rename data files (Task 2), then regenerate exports"
  - "CANONICAL_COOP_MODES = {set} in validator — extend this set when adding new coopMode values"

requirements-completed: [SCH-04]

# Metrics
duration: 10min
completed: 2026-04-01
---

# Phase 01 Plan 02: coopMode Vocabulary Canonicalization Summary

**coopMode vocabulary renamed from 'split' to 'sofa' across all 11 files — 210 games updated, canonical validator added, zero non-canonical values remain**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-01T11:15:00Z
- **Completed:** 2026-04-01T11:25:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Updated all 8 Python scripts and app.js to use `"sofa"` instead of `"split"` as the coopMode data value (Task 1)
- Added `CANONICAL_COOP_MODES = {"online", "local", "sofa"}` constant to validate_catalog.py with a hard-error check that rejects any non-canonical coopMode values (Task 1)
- Bulk-renamed 210 `"split"` coopMode values to `"sofa"` in assets/games.js via sed (Task 2)
- Regenerated both JSON exports (catalog.games.v1.json, catalog.public.v1.json) — 0 games with "split", 210 games with "sofa" (Task 2)
- validate_catalog.py runs with 0 non-canonical coopMode errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Rename split to sofa in all Python scripts and app.js** - `9126f2a9` (feat)
2. **Task 2: Rename split to sofa in games.js data and regenerate JSON exports** - `3208eb66` (feat)

## Files Created/Modified

- `scripts/steam_catalog_source.py` - `modes.append("sofa")` instead of `"split"`
- `scripts/igdb_catalog_source.py` - `coop_modes.append("sofa")` instead of `"split"`
- `scripts/itch_catalog_source.py` - tag mapping `"split-screen": ["local", "sofa"]` and is_local check updated
- `scripts/catalog_data.py` - splitScreen/sharedScreen capability flags use `"sofa" in coop_modes`
- `scripts/build_static_pages.py` - label dict key `"sofa"` and two JSON-LD play_modes conditionals updated
- `scripts/build_hub_pages.py` - both `_mode_label` and `_mode_label_en` dicts use `"sofa"` key
- `scripts/validate_catalog.py` - adds `CANONICAL_COOP_MODES`, updates sync checks, adds hard-error loop for non-canonical values
- `assets/app.js` - `mode_split` filter object: `value: 'sofa'` instead of `'split'`
- `assets/games.js` - 210 `"split"` coopMode values renamed to `"sofa"` via sed
- `data/catalog.games.v1.json` - regenerated, 0 games with `"split"` coopMode
- `data/catalog.public.v1.json` - regenerated, 0 games with `"split"` coopMode

## Decisions Made

- `coopMode` vocabulary is now canonical: `{online, local, sofa}`. "split" is permanently retired from the data schema. All pipeline sources and validators enforce this.
- Steam source keeps internal variable `has_split` (reads Steam's own API category strings which contain the word "split") — only the OUTPUT value was renamed. This is intentional and documented.
- `CANONICAL_COOP_MODES` in validate_catalog.py is the single authoritative contract — adding new coopMode values requires updating this constant.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `python3 scripts/validate_catalog.py` exits with code 1 due to pre-existing "Missing sitemap URLs" error — this is identical to what was documented in 01-01-SUMMARY.md and is out of scope for this plan. The new CANONICAL_COOP_MODES check found 0 violations.
- 34 coopMode/categories sync warnings exist (games with "splitscreen" category but no "sofa" coopMode) — these are pre-existing data quality gaps, not introduced by this plan. They were warnings before and remain warnings.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 (coop-audit-scoring) can now use `"sofa"` as the canonical split-screen coopMode value
- validate_catalog.py will reject any future source that produces non-canonical coopMode values
- The frontend filter `mode_split` correctly targets `"sofa"` data values

## Self-Check: PASSED

- FOUND: scripts/steam_catalog_source.py (modes.append("sofa") at line 158)
- FOUND: scripts/igdb_catalog_source.py (coop_modes.append("sofa") at line 329)
- FOUND: scripts/itch_catalog_source.py ("sofa" in tag mapping and is_local check)
- FOUND: scripts/catalog_data.py ("sofa" in splitScreen/sharedScreen)
- FOUND: scripts/build_static_pages.py ("sofa" in labels and JSON-LD conditionals)
- FOUND: scripts/build_hub_pages.py ("sofa" in both _mode_label functions)
- FOUND: scripts/validate_catalog.py (CANONICAL_COOP_MODES, validation loop)
- FOUND: assets/app.js (value: 'sofa' in mode_split filter)
- FOUND: assets/games.js (210 "sofa", 0 "split")
- FOUND: data/catalog.games.v1.json (0 games with "split" coopMode)
- FOUND: data/catalog.public.v1.json (0 games with "split" coopMode)
- FOUND commit: 9126f2a9 (Task 1)
- FOUND commit: 3208eb66 (Task 2)

---
*Phase: 01-schema-foundation-ci-hardening*
*Completed: 2026-04-01*
