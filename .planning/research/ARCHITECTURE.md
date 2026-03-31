# Architecture Patterns — v1.1 Data Quality Milestone

**Project:** Co-op Games Hub (coophubs.net)
**Domain:** Static co-op game catalog with Python data pipeline
**Researched:** 2026-04-01
**Overall confidence:** HIGH (based on direct codebase inspection)

---

## Current Data Flow (Baseline)

```
assets/games.js  (source of truth, 589 games, hand-maintained JS)
       |
       v
catalog_data.py::load_games()      ← parses JS with regex, normalises
       |
       +--> data/catalog.games.v1.json    (full admin catalog)
       +--> data/catalog.public.v1.json   (public subset, consumed by app.js)
       |
       v
build_static_pages.py              ← reads catalog.games.v1.json
       |
       +--> games/<id>.html (589 static pages)
       +--> sitemap.xml
```

The key constraint: `games.js` is the **write target** for the pipeline. All scripts that
modify game data call `catalog_data.write_legacy_games_js()` to persist back to `games.js`,
then the export functions regenerate both JSON files. No script writes directly to
`catalog.games.v1.json` — that file is always derived.

---

## Capability 1: coopScore Field

### What it is
An integer 1-3 per game expressing how central co-op is to the experience:
- `1` — co-op present but marginal (PvP-first game with a wave mode, MMO with group content)
- `2` — co-op is a supported and complete mode
- `3` — co-op is the primary design intent

### Integration Point: catalog_data.py

`coopScore` belongs in `games.js` (and therefore `catalog.games.v1.json`) as a first-class
field. It does NOT belong only in the audit output — it is editorial metadata that persists.

**Files to change:**

| File | Change |
|------|--------|
| `scripts/catalog_data.py` | Add `coopScore` to `LEGACY_RUNTIME_FIELDS` tuple; add to `normalize_game()` pass-through; add to `write_legacy_games_js()` serialiser |
| `scripts/catalog_data.py` | Add to `build_public_catalog_export()` so the field reaches the frontend |
| `assets/games.js` | Field added per-game (integer, default `null`/absent until scored) |
| `data/catalog.games.v1.json` | Derived — regenerated automatically after games.js update |
| `data/catalog.public.v1.json` | Derived — regenerated automatically |

**Schema addition in normalize_game():**
```python
"coopScore": raw_game.get("coopScore") or None,  # 1-3 or None if unscored
```

**In write_legacy_games_js() serialiser:**
```python
coop_score = game.get("coopScore")
score_line = f"    coopScore: {coop_score},\n" if coop_score else "    coopScore: null,\n"
```

**In build_public_catalog_export():**
```python
"coopScore": game.get("coopScore") or None,
```

**Frontend impact:** `app.js` can read `coopScore` from `catalog.public.v1.json` without
any backend. A future filter "Co-op purity" is possible client-side with no pipeline changes.

### Default for existing games
All 589 existing games ship with `coopScore: null` until the audit script populates them.
The frontend must treat `null` as "unscored" and render no badge, not as score 0.

---

## Capability 2: Co-op Tag Audit Script

### Purpose
Read the catalog, query Steam API (and optionally IGDB), compare reported `coopMode` /
`categories` with authoritative source data, and output a report of suspected errors.

### New file: `scripts/audit_coop_tags.py`

**Does NOT modify games.js** — output only. A human reviews the report and applies fixes
via the bulk-fix tool (Capability 4) or manually.

### Data flow

```
data/catalog.games.v1.json
          |
          v
audit_coop_tags.py
          |
          +--> Steam API /appdetails (per steamAppId, rate-limited)
          +--> IGDB API (optional, fallback for non-Steam games)
          |
          v
data/coop_audit_report.json      ← machine-readable findings
stdout                           ← human-readable summary
```

### Output schema: `data/coop_audit_report.json`

```json
{
  "generatedAt": "2026-04-01T...",
  "summary": {
    "total": 589,
    "checked": 400,
    "flagged": 23,
    "skipped": 189
  },
  "flags": [
    {
      "id": 42,
      "title": "Game Title",
      "steamAppId": "12345",
      "currentCoopMode": ["online"],
      "currentCategories": ["action"],
      "steamCoopCategories": [],
      "igdbCoopModes": [],
      "issue": "no_coop_evidence",
      "severity": "high",
      "suggestedAction": "remove_from_catalog",
      "notes": "Steam appdetails shows no co-op category IDs (9, 38, 39)"
    }
  ],
  "disputed": [...],
  "verified_ok": [...]
}
```

**Severity levels:**
- `high` — no co-op evidence from any source → candidate for removal
- `medium` — source disagrees with tag (e.g., has `local` but Steam shows online-only)
- `low` — incomplete data (missing maxPlayers, empty coopMode array)

### Integration with validate_catalog.py

`validate_catalog.py` already reads `data/coop_validation_report.json` (lines 312-323).
The new audit script should write to `data/coop_audit_report.json` (separate file, different
schema). `validate_catalog.py` can be extended to also read the new report and emit warnings,
following the same pattern already in place.

### Rate limiting strategy

The existing `catalog_config.py` already defines `MAX_CROSSVAL = 80` and `MAX_VERIFY = 80`.
The audit script should respect the same pattern: accept `--max-games N` CLI arg (default 80),
resume from where it left off by tracking checked IDs in the output file.

**Resumable pattern** (already used by other scripts):
```python
existing = load_existing_report()  # reads coop_audit_report.json if present
already_checked = {f["id"] for f in existing.get("flags", []) + existing.get("verified_ok", [])}
to_check = [g for g in games if g["id"] not in already_checked]
```

---

## Capability 3: Classic Game Discovery Script

### Purpose
Find co-op PC games from all eras (pre-2015, 2015-2020) that are not in the catalog.
Output a structured candidate list for manual review — similar to `discover_backfill.py`
but focused on older games and using a broader search strategy.

### New file: `scripts/discover_classics.py`

**Relationship to discover_backfill.py:**
`discover_backfill.py` covers 2020-present via SteamSpy tag queries.
`discover_classics.py` covers pre-2020 games, uses IGDB as primary source (better historical
data than SteamSpy), falls back to Steam tag queries with year filters.

### Data flow

```
IGDB API  ──────────────┐
Steam SteamSpy API  ────┤──> discover_classics.py
data/catalog.games.v1.json (existing IDs to exclude)
                         |
                         v
data/classic_candidates.json   ← output file
```

### Output schema: `data/classic_candidates.json`

```json
{
  "generatedAt": "2026-04-01T...",
  "query": { "minYear": 1990, "maxYear": 2019, "maxCandidates": 100 },
  "candidates": [
    {
      "title": "Dungeon Siege II",
      "steamAppId": "39200",
      "releaseYear": 2005,
      "steamRating": 82,
      "steamReviews": 4200,
      "igdbRating": 78,
      "coopModes": ["online", "local"],
      "maxPlayers": 4,
      "genre": ["rpg", "action"],
      "source": "igdb",
      "notes": "Classic co-op RPG, 4-player LAN/online campaign",
      "alreadyInCatalog": false
    }
  ]
}
```

### Discovery strategy

Primary: IGDB API query
```
fields name, first_release_date, aggregated_rating, game_modes, multiplayer_modes;
where game_modes = (3)  // 3 = Co-operative
and first_release_date < 2020-01-01
and platforms = (6)  // 6 = PC
sort aggregated_rating desc;
limit 500;
```

Secondary: SteamSpy tag queries with year filter (same approach as discover_backfill.py
but with `--min-year 1990 --max-year 2019`).

Filter before output: exclude any `steamAppId` already in `BLACKLIST_APPIDS` from
`catalog_config.py`, exclude any game already in the catalog (check by steamAppId and title).

**Output is always candidates for human review — no auto-add to catalog.**

---

## Capability 4: Bulk Data Fix Tooling

### Purpose
Efficiently update `maxPlayers`, `coopMode`, `crossplay`, and `coopScore` for many games
at once, driven by a structured input file rather than hand-editing `games.js`.

### New file: `scripts/apply_fixes.py`

### Input format: `data/pending_fixes.json`

This file is the human-edited manifest of changes to apply:

```json
{
  "fixes": [
    {
      "id": 42,
      "title": "Game Title",
      "reason": "Audit found: no local co-op, only online",
      "changes": {
        "coopMode": ["online"],
        "coopScore": 2,
        "maxPlayers": 4
      }
    },
    {
      "id": 99,
      "title": "Another Game",
      "reason": "Remove: not actually co-op",
      "action": "remove"
    }
  ]
}
```

Supported `action` values:
- absent / `"update"` — apply `changes` fields to the game
- `"remove"` — move game from catalog to `data/_nocoop_flagged.json`
- `"set_score"` — shorthand for only updating `coopScore`

### Data flow

```
data/pending_fixes.json   (human-edited)
          |
          v
apply_fixes.py
          |
          +--> reads assets/games.js via catalog_data.load_games()
          +--> applies changes in memory
          +--> dry-run print by default
          +--> catalog_data.write_legacy_games_js()  (--apply flag required)
          +--> catalog_data.write_catalog_artifact()
          +--> catalog_data.write_public_catalog_export()
          |
          v
assets/games.js  (updated)
data/catalog.games.v1.json  (regenerated)
data/catalog.public.v1.json  (regenerated)
```

**Dry-run by default** — the script prints what it would change and exits 0. Pass `--apply`
to actually write. This prevents accidental mass edits.

**Removal handling** — removed games move to `data/_nocoop_flagged.json` with a timestamp
and the `reason` field, matching the existing convention for that file.

---

## Component Map: New vs Modified

| Component | Status | File | Notes |
|-----------|--------|------|-------|
| `coopScore` field in schema | NEW | `scripts/catalog_data.py` | Add to 4 locations in the file |
| `coopScore` in games.js serialiser | NEW | `scripts/catalog_data.py` | write_legacy_games_js() |
| `coopScore` in public export | NEW | `scripts/catalog_data.py` | build_public_catalog_export() |
| `audit_coop_tags.py` | NEW | `scripts/audit_coop_tags.py` | Read-only, outputs report |
| `discover_classics.py` | NEW | `scripts/discover_classics.py` | Read-only, outputs candidates |
| `apply_fixes.py` | NEW | `scripts/apply_fixes.py` | Writes games.js only with --apply |
| `coop_audit_report.json` | NEW | `data/coop_audit_report.json` | Generated by audit script |
| `classic_candidates.json` | NEW | `data/classic_candidates.json` | Generated by discover_classics |
| `pending_fixes.json` | NEW | `data/pending_fixes.json` | Human-edited input for apply_fixes |
| `validate_catalog.py` | MODIFIED | `scripts/validate_catalog.py` | Add coopScore stats; read audit report |
| `catalog_config.py` | MODIFIED | `scripts/catalog_config.py` | Add COOP_SCORE thresholds constants |
| `games.js` | MODIFIED | `assets/games.js` | coopScore field added per game |
| `catalog.games.v1.json` | DERIVED | `data/catalog.games.v1.json` | Auto-regenerated |
| `catalog.public.v1.json` | DERIVED | `data/catalog.public.v1.json` | Auto-regenerated |

**NOT changed:** `app.js`, `index.html`, `build_static_pages.py`, GitHub Actions workflows,
all game HTML pages. The static site constraint is fully respected.

---

## Build Order Recommendation

The four capabilities have data dependencies that dictate build order:

```
Phase 1: Schema Foundation
  └── Add coopScore to catalog_data.py (LEGACY_RUNTIME_FIELDS + normalize + serialize + export)
  └── Verify: python3 scripts/catalog_data.py writes games.js with coopScore: null per game
  └── Run validate_catalog.py to confirm no regressions

Phase 2: Audit Script (reads catalog, outputs report — no write risk)
  └── Build audit_coop_tags.py
  └── Run on full catalog: produces coop_audit_report.json
  └── Review report manually, identify high-severity flags

Phase 3: Bulk Fix Tooling (writes games.js — needs Phase 1 complete)
  └── Build apply_fixes.py with dry-run default
  └── Build pending_fixes.json from Phase 2 audit findings
  └── Apply fixes: python3 scripts/apply_fixes.py --apply
  └── Run validate_catalog.py + build_static_pages.py

Phase 4: Classic Discovery (independent, can run any time after Phase 1)
  └── Build discover_classics.py
  └── Run to generate classic_candidates.json
  └── Manual review + promotion to pending_fixes.json
```

**Phase 2 before Phase 3** is the critical dependency: you need to know what to fix before
building the bulk-fix tool. Phase 4 is independent — it can be built in parallel with Phase 2.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Writing coopScore Only to the JSON Files
**What:** Adding coopScore to `catalog.games.v1.json` directly without updating `games.js`.
**Why bad:** `catalog_data.py` always derives the JSON from `games.js`. Any direct JSON edit
is overwritten on the next pipeline run. `games.js` must remain the write target.

### Anti-Pattern 2: Auto-applying Audit Findings
**What:** Having `audit_coop_tags.py` write directly to `games.js` when it finds issues.
**Why bad:** The audit checks external APIs which can be wrong or have stale data. The
`VERIFIED_COOP_APPIDS` set in `catalog_config.py` exists precisely because Steam's own tags
are unreliable for some games. Human review is mandatory.

### Anti-Pattern 3: Running Audit in GitHub Actions on Every Push
**What:** Adding the audit script to the weekly `auto-update.yml` workflow.
**Why bad:** The audit queries the Steam API for up to 589 games — far above rate limits for
an automated run. Keep it as a manual CLI tool only.

### Anti-Pattern 4: Separate coopScore Storage
**What:** Storing coopScore in a separate `data/coop_scores.json` file and merging at
build time.
**Why bad:** Adds a merge step that can fall out of sync with `games.js`. The field belongs
in the game object, not in a sidecar file.

---

## Scalability Considerations

| Concern | Current (589 games) | Future (2000+ games) |
|---------|---------------------|----------------------|
| Audit script runtime | ~12 min at 1.3s/game (80 per run) | Same — resumable, run in batches |
| pending_fixes.json size | Tiny (tens of fixes) | Still tiny — one-time use per batch |
| coopScore null coverage | Many nulls initially | Reduces over time via audit runs |
| classic_candidates.json | ~100 candidates | Re-runnable, idempotent |

---

## Integration with Existing validate_catalog.py

`validate_catalog.py` should gain two additions (small, low risk):

1. **coopScore stats in the summary print block** — alongside the existing affiliate coverage
   summary, print: "coopScore coverage: X/589 scored (Y%)"

2. **Read coop_audit_report.json for high-severity flags** — mirror the existing pattern
   at lines 312-323 that reads `coop_validation_report.json`:
   ```python
   audit_report = catalog_data.DATA_DIR / "coop_audit_report.json"
   if audit_report.is_file():
       # emit warnings for high-severity flags not yet fixed
   ```

This keeps the validation gate informative without making it block on unfixed audit items.

---

## Sources

- Direct inspection of `scripts/catalog_data.py` (single source of truth for schema)
- Direct inspection of `scripts/validate_catalog.py` (existing validation patterns)
- Direct inspection of `scripts/catalog_config.py` (rate limits, blacklists, thresholds)
- Direct inspection of `scripts/discover_backfill.py` (pattern for discovery output)
- Direct inspection of `data/catalog.games.v1.json` (confirmed coopScore absent, 589 games)
- Confidence: HIGH — all findings from direct file reading, no inference needed
