---
phase: 1
slug: schema-foundation-ci-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none — project uses `validate_catalog.py` as functional gate + Python one-liners |
| **Config file** | none |
| **Quick run command** | `cd scripts && python3 validate_catalog.py` |
| **Full suite command** | `cd scripts && python3 validate_catalog.py` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 scripts/validate_catalog.py`
- **After every plan wave:** Run `python3 scripts/validate_catalog.py`
- **Before `/gsd:verify-work`:** Full suite must be green (0 errors)
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Req | Wave | Test Type | Automated Command | Status |
|---------|-----|------|-----------|-------------------|--------|
| ef-null-parser | SCH-01 | 1 | unit one-liner | `python3 -c "from scripts.catalog_data import ef; assert ef('coopScore: null', 'coopScore') is None"` | ⬜ pending |
| coopScore-load | SCH-01 | 1 | functional | `python3 -c "import sys; sys.path.insert(0,'scripts'); import catalog_data; g=catalog_data.load_games(); assert 'coopScore' in g[0], 'coopScore missing from load_games output'"` | ⬜ pending |
| coopScore-json | SCH-01 | 1 | file check | `python3 -c "import json; d=json.load(open('data/catalog.games.v1.json')); assert 'coopScore' in d['games'][0], 'coopScore missing from catalog JSON'"` | ⬜ pending |
| mini-review-load | SCH-02 | 1 | functional | `python3 -c "import sys; sys.path.insert(0,'scripts'); import catalog_data; games=catalog_data.load_games(); mr=[g for g in games if g.get('mini_review_it')]; print('Games with mini_review_it:', len(mr)); assert len(mr) >= 17, f'Expected >= 17 mini reviews, got {len(mr)}'"` | ⬜ pending |
| ci-yaml-fix | SCH-03 | 1 | file check | `grep -n "continue-on-error" .github/workflows/update.yml` (build steps must NOT appear) | ⬜ pending |
| sofa-rename | SCH-04 | 1 | grep check | `python3 -c "import sys; sys.path.insert(0,'scripts'); import catalog_data; games=catalog_data.load_games(); bad=[g for g in games if set(g.get('coopMode',[])) - {'online','local','sofa'}]; print('Non-canonical:', len(bad)); assert len(bad)==0"` | ⬜ pending |
| validate-clean | SCH-04 | 2 | functional | `python3 scripts/validate_catalog.py` (must exit 0, 0 errors) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

No new test framework needed. Existing `validate_catalog.py` covers functional validation. All per-task verifications above are Python one-liners runnable without a test framework.

*Existing infrastructure covers all phase requirements — no Wave 0 setup needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Protected fields survive actual CI run | SCH-02 | Requires GitHub Actions execution | After merge, verify in next CI run that `mini_review_it` count in `games.js` is still ≥ 17 |
| Build failure blocks CI deploy | SCH-03 | Requires a failing build to test the gate | Verify by reading the YAML diff — `continue-on-error: true` absent from build steps |
| `coopScore` not overwritten by CI | SCH-02 | Requires CI run with a manually-set value | Set one game to `coopScore: 2` locally, run `auto_update.py` locally, verify value unchanged |
