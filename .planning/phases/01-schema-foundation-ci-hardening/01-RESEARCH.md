# Phase 1: Schema Foundation & CI Hardening - Research

**Researched:** 2026-04-01
**Domain:** Python data pipeline, GitHub Actions CI, static site catalog schema
**Confidence:** HIGH

---

## Summary

Phase 1 establishes the foundation that all subsequent v1.1 phases depend on. The work is contained entirely in Python scripts and one GitHub Actions workflow YAML — no frontend changes, no Node.js, no backend.

Four changes are needed. First, add `coopScore` (int 1-3, nullable) to the catalog schema: the field must appear in `games.js`, propagate through `catalog_data.py` into both JSON exports, and be preserved across CI round-trips. Second, protect manually curated fields — including `coopScore`, `mini_review_it`, `mini_review_en`, and affiliate data — from being silently overwritten or dropped by the daily CI run. Third, remove `continue-on-error: true` from the build steps in `update.yml` so that a failing build actually blocks the deploy. Fourth, add canonical `coopMode` vocabulary enforcement to `validate_catalog.py`, treating any value other than `online`, `local`, `sofa` as a hard error.

**Primary recommendation:** Make all four changes in a single coordinated pass across `catalog_data.py`, `auto_update.py`, `validate_catalog.py`, and `.github/workflows/update.yml`. The changes are small and low-risk individually but must be done together to avoid a CI run that drops data between steps.

---

## Project Constraints (from CLAUDE.md)

- No backend. No Express, Flask, FastAPI, or any server. The site is and remains static.
- No npm/Node. `package.json` must not exist. No npm dependencies.
- GitHub Pages compatibility — everything must work on pure static hosting.
- Targeted changes only — touch only the files necessary for the task.
- Do NOT commit or push autonomously — propose changes, wait for user confirmation.
- Preserve game IDs — numeric IDs in `games.js` are fixed. Do not renumber or remove.
- Update `AI_COLLABORATION.md` after non-trivial changes.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCH-01 | Add `coopScore` (int 1-3, nullable) to schema in `catalog_data.py`; propagate to `catalog.games.v1.json` and `catalog.public.v1.json` | `catalog_data.py` has `normalize_game()`, `build_catalog_artifact()`, `build_public_catalog_export()`, and `write_legacy_games_js()` — all four need updating |
| SCH-02 | Protect manually curated fields (`coopScore`, `mini_review_it`, `mini_review_en`, `igUrl`, `igDiscount`, `gbUrl`, `gbDiscount`) from CI overwrite | `load_games()` does not read `mini_review_*` or `coopScore`; `write_legacy_games_js()` does not write them — both gaps must be fixed |
| SCH-03 | Remove `continue-on-error: true` from `build_static_pages.py` and `build_hub_pages.py` steps in `update.yml` | Two steps in `update.yml` lines 62-66 currently have `continue-on-error: true` |
| SCH-04 | `validate_catalog.py` reports error for any `coopMode` value outside `online`, `local`, `sofa` | Current catalog uses `split` (210 games) instead of `sofa`; this means either the canonical value must be decided (`split` or `sofa`) and enforced, or both must coexist — see pitfall below |
</phase_requirements>

---

## Standard Stack

This phase uses only what already exists in the project. No new libraries needed.

### Core
| Component | Version | Purpose | Notes |
|-----------|---------|---------|-------|
| Python | 3.11 (CI), local varies | Data pipeline | Already installed in CI via `setup-python@v5.6.0` |
| `catalog_data.py` | project-local | Schema I/O layer | Primary file to modify for SCH-01, SCH-02 |
| `validate_catalog.py` | project-local | Catalog validation | Primary file to modify for SCH-04 |
| `update.yml` | GitHub Actions | CI workflow | Primary file to modify for SCH-03 |
| `auto_update.py` | project-local | Daily CI update script | Reads and writes `games.js`; must preserve protected fields |

**Installation:** None required. All dependencies already present.

---

## Architecture Patterns

### Current Data Flow

```
games.js  (source of truth, ~589 games)
    |
    v catalog_data.load_games()         ← reads specific fields via ef() regex parser
    |                                      does NOT read: mini_review_it, mini_review_en, coopScore
    |
    v catalog_data.normalize_game()     ← adds canonical fields (slug, capabilities, etc.)
    |
    v auto_update.py                    ← mutates: ccu, trending, rating, coopMode, crossplay, genres, maxPlayers
    |                                      does NOT read: mini_review_it, mini_review_en
    |
    v catalog_data.write_legacy_games_js()  ← writes hardcoded field list BACK to games.js
    |                                           DROPS: mini_review_it, mini_review_en (not in template)
    |                                           DROPS: coopScore (not yet in schema)
    |
    v catalog_data.write_catalog_artifact()   → data/catalog.games.v1.json
    v catalog_data.write_public_catalog_export() → data/catalog.public.v1.json
```

### Required Data Flow After Phase 1

```
games.js  (source of truth)
    |
    v catalog_data.load_games()         ← ADDED: reads coopScore, mini_review_it, mini_review_en
    |
    v catalog_data.normalize_game()     ← ADDED: coopScore passes through to output
    |
    v auto_update.py                    ← ADDED: preserve coopScore if already set (skip if not None)
    |                                      ADDED: preserve mini_review_it/en (never touch)
    |
    v catalog_data.write_legacy_games_js()  ← ADDED: coopScore, mini_review_it, mini_review_en in template
    |
    v write_catalog_artifact()          ← coopScore present in games array (via normalize_game)
    v write_public_catalog_export()     ← coopScore present in public export
```

### Pattern 1: Read-then-preserve for protected fields

For any field that is set manually and must not be overwritten by CI:

1. `ef()` parser in `load_games()` must extract it
2. `normalize_game()` must pass it through (or place it in a canonical location)
3. `auto_update.py` must NOT touch it (or touch it only when it is `None`/falsy)
4. `write_legacy_games_js()` must include it in the write template

If ANY of the four steps is missing, the field is silently dropped on next CI run.

**Current gap:** `mini_review_it` and `mini_review_en` are missing from steps 1 and 4. They exist in `games.js` but are never read by `load_games()` and never written by `write_legacy_games_js()`. This means the next CI run that calls `auto_update.py` will **silently erase all 17 existing mini-reviews**. This is a pre-existing data loss bug that SCH-02 must fix.

### Pattern 2: Nullable field with overwrite guard

For `coopScore` specifically:
- Default value when absent: `null` (not 0, not empty string — `null` means "not yet scored")
- In `games.js` JS syntax: `coopScore: null` or `coopScore: 2`
- The `ef()` regex parser in `catalog_data.py` currently only handles strings, arrays, booleans, and integers — it does NOT handle `null`. The parser needs extending.
- Overwrite guard logic: `if g.get('coopScore') is None: pass  # don't assign`

### Pattern 3: coopMode vocabulary decision

The canonical vocabulary per REQUIREMENTS.md is `online`, `local`, `sofa`.

Current state of catalog:
- `online`: present, correct
- `local`: present, correct
- `split`: present in **210 games** — this value is NOT in the canonical set
- `sofa`: zero occurrences anywhere in the codebase

The code in `build_static_pages.py` uses `"split"` (line 399, 477, 810) and `app.js` similarly uses `"split"`. The SCH-04 requirement says canonical values are `online`, `local`, `sofa`.

**This is a vocabulary alignment decision.** Two valid approaches:
- Option A: Rename `split` → `sofa` everywhere (catalog data, `build_static_pages.py`, `app.js`, `catalog_data.py` derive_coop_modes output)
- Option B: Add `split` to the canonical set alongside `sofa`, treating them as synonyms

The REQUIREMENTS.md says `sofa` is the canonical value. Option A is the correct path but requires touching `build_static_pages.py` and `app.js` (frontend files). Option B would leave the canonical set inconsistent with the stated requirements.

**Recommendation:** Use Option A. The rename from `split` to `sofa` is a search-and-replace across a known set of files. It is lower risk than letting a non-canonical value exist in validated data.

### Anti-Patterns to Avoid

- **Adding `continue-on-error: true` to affiliate price steps:** Those steps already have it correctly — the flag is appropriate for optional scraping steps that depend on external APIs. Only the BUILD steps (`build_static_pages.py`, `build_hub_pages.py`) should have it removed.
- **Setting `coopScore` default to `0` instead of `null`:** Zero is ambiguous. Null explicitly means "not yet scored" and allows filtering for games needing scoring in Phase 2.
- **Using `or 0` fallback for coopScore in load_games:** The `ef()` parser returns `None` when a field is absent. `coopScore` should stay `None` when absent, not be coerced to `0`.
- **Writing coopScore to the public export without null handling:** `json.dumps(None)` correctly serializes to `null` in JSON — no special handling needed, but be explicit.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parsing `null` from JS source | Custom null-aware regex | Extend existing `ef()` function | One change in one place; consistent with all other field parsing |
| Field preservation in CI | A separate "protected fields" JSON sidecar file | Read and round-trip through existing `load_games` / `write_legacy_games_js` | Adding a sidecar introduces a new artifact to maintain and sync |
| coopMode validation | A separate validation script | Add to existing `validate_catalog.py` | Already runs in CI; adding 5 lines is simpler than a new script |

**Key insight:** The project already has the right architecture — `catalog_data.py` as a single I/O layer. All four SCH requirements are fixed by extending this layer, not by adding new infrastructure.

---

## Common Pitfalls

### Pitfall 1: The `ef()` parser does not handle `null`

**What goes wrong:** Adding `coopScore: null` to `games.js` and then calling `ef(block, "coopScore")` returns `None` — but so does calling `ef()` for any absent field. There is no way to distinguish "coopScore is null" from "coopScore field not present" with the current parser.

**Why it happens:** The `ef()` regex pattern is:
```python
r'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|-?\d+)'
```
It does not match the literal `null` value.

**How to avoid:** Extend the regex to also match `null`:
```python
r'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|null|-?\d+)'
```
And in the value handler:
```python
if value == "null":
    return None
```
Then in `load_games()`, use `ef(block, "coopScore")` — it returns `None` for both `coopScore: null` and absent `coopScore`, which is the correct behavior (both mean "not yet scored").

**Warning signs:** `coopScore` always appears as `0` or is silently missing after a CI round-trip.

### Pitfall 2: mini_review_it/en will be erased by the next CI run

**What goes wrong:** The 17 existing `mini_review_it`/`mini_review_en` entries in `games.js` are invisible to the CI pipeline. `load_games()` never reads them; `write_legacy_games_js()` never writes them. The next time `auto_update.py` runs and writes `games.js`, all 17 mini-reviews are silently deleted.

**Why it happens:** `write_legacy_games_js()` has a hardcoded field template. Fields not in the template are dropped on every write. `mini_review_it` was added to `games.js` manually after the write function was written.

**How to avoid:** 
1. Add `mini_review_it` and `mini_review_en` to the `ef()` calls in `load_games()`
2. Add them to the write template in `write_legacy_games_js()` — as optional fields (only write the line if the value is non-empty, or always write with empty-string default)

**Warning signs:** After `auto_update.py` runs locally, `grep "mini_review" assets/games.js` returns nothing.

### Pitfall 3: Removing `continue-on-error` from affiliate steps

**What goes wrong:** The `update.yml` has `continue-on-error: true` on BOTH the build steps AND the affiliate price fetch steps. Removing it from affiliate steps would cause a network failure (external API down, rate-limited) to block the entire CI and prevent games.js from being updated.

**Why it happens:** Both sets of steps are visually adjacent in the YAML and the flag looks like a blanket "tolerate errors" setting.

**How to avoid:** Remove `continue-on-error: true` only from:
- Line 62: `Build static game pages` (calls `build_static_pages.py`)
- Line 66: `Build hub pages SEO` (calls `build_hub_pages.py`)

Keep `continue-on-error: true` on all affiliate price fetch steps (lines 37-58). These call external APIs and should not block CI.

**Warning signs:** CI fails on a day when an affiliate API is rate-limited, preventing `games.js` from being updated.

### Pitfall 4: `split` vs `sofa` vocabulary mismatch

**What goes wrong:** SCH-04 adds validation that rejects any `coopMode` value not in `{online, local, sofa}`. The current catalog has 210 games with `coopMode: ["split"]`. Running the validator immediately after adding this check will produce 210 errors.

**Why it happens:** The codebase uses `"split"` internally (set by `derive_coop_modes()` in `steam_catalog_source.py`, referenced in `build_static_pages.py` and `app.js`). The REQUIREMENTS.md specifies `"sofa"` as the canonical value.

**How to avoid:** The vocabulary migration and the validation addition must happen in the same plan. Either:
- Rename `split` → `sofa` in ALL locations before adding the validator, then validate
- OR validate `{online, local, split}` initially and rename later (contradicts requirements)

The correct path per requirements is to rename, then validate. Files to update:
1. `scripts/catalog_data.py` — `normalize_game()` capabilities block references `"split"`
2. `scripts/steam_catalog_source.py` — `derive_coop_modes()` returns `"split"`
3. `scripts/build_static_pages.py` — label dict and conditional checks use `"split"`
4. `assets/app.js` — references `"split"` in filter/display logic
5. All 210 games in `assets/games.js` — `coopMode` field values
6. `data/catalog.games.v1.json` and `data/catalog.public.v1.json` — regenerated after pipeline fix, no manual edit needed

### Pitfall 5: Validate step runs before build artifacts exist

**What goes wrong:** In `update.yml`, `validate_catalog.py` is run AFTER the build steps. If both build steps have `continue-on-error: true` removed and one fails, the validate step still runs — but it validates against stale static pages from a previous run, producing misleading results.

**Why it happens:** The validate step (line 69) checks that generated `.html` pages match the game count. If `build_static_pages.py` fails mid-run, some pages may exist from the previous run but not be in sync with the current `games.js`.

**How to avoid:** This is acceptable behavior post-fix — if `build_static_pages.py` fails, the CI job fails at that step and validate never runs (since failure stops execution without `continue-on-error`). Document this in the plan as the intended outcome.

---

## Code Examples

### Extend `ef()` to handle null (for coopScore support)

```python
# Source: catalog_data.py — current ef() function, extend the regex and value handler
def ef(block: str, field: str):
    match = re.search(
        rf'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|null|-?\d+)',
        block,
        re.DOTALL,
    )
    if not match:
        return None
    value = match.group(1)
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":          # NEW: handle null literal
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("["):
        return re.findall(r'"([^"]+)"', value)
    return re.sub(r"\\(.)", r"\1", value.strip('"'))
```

### Add coopScore to load_games()

```python
# In the game dict inside load_games():
"coopScore": ef(block, "coopScore"),   # Returns None if absent or null — correct default
```

### Add coopScore to write_legacy_games_js() template

```python
# In the f-string template, after the existing fields:
f"    coopScore: {json.dumps(game.get('coopScore'))},\n"
# json.dumps(None) → "null", json.dumps(2) → "2" — correct JS syntax
```

### Add mini_review fields to load_games()

```python
# In the game dict inside load_games():
"mini_review_it": ef(block, "mini_review_it") or "",
"mini_review_en": ef(block, "mini_review_en") or "",
```

### Add mini_review fields to write_legacy_games_js() template

```python
# These are optional — only write if non-empty to keep games.js clean
# But safer to always write (empty string), consistent with other optional fields
f'    mini_review_it: "{js_esc(game.get("mini_review_it", ""))}",\n'
f'    mini_review_en: "{js_esc(game.get("mini_review_en", ""))}",\n'
```

### Add coopScore to normalize_game()

```python
# In the return dict of normalize_game(), pass coopScore through:
"coopScore": raw_game.get("coopScore"),   # None means not yet scored
```

### Add coopScore to build_public_catalog_export()

```python
# In public_games.append() dict:
"coopScore": game.get("coopScore"),   # None → null in JSON output
```

### Add coopMode validation to validate_catalog.py

```python
CANONICAL_COOP_MODES = {"online", "local", "sofa"}

# In the per-game loop:
invalid_coop_modes = []
for game in games:
    modes = set(game.get("coopMode") or [])
    bad = modes - CANONICAL_COOP_MODES
    if bad:
        invalid_coop_modes.append(f"{game['id']} ({game.get('title')}): {sorted(bad)}")

if invalid_coop_modes:
    errors.append(f"Non-canonical coopMode values: {short_list(invalid_coop_modes)}")
```

### Remove continue-on-error from build steps in update.yml

```yaml
# BEFORE:
- name: Build static game pages
  continue-on-error: true
  run: python3 scripts/build_static_pages.py

- name: Build hub pages SEO
  continue-on-error: true
  run: python3 scripts/build_hub_pages.py

# AFTER:
- name: Build static game pages
  run: python3 scripts/build_static_pages.py

- name: Build hub pages SEO
  run: python3 scripts/build_hub_pages.py
```

### Overwrite guard for coopScore in auto_update.py

```python
# When updating existing games — do NOT touch coopScore:
# (No code needed — auto_update.py simply doesn't assign coopScore at all)
# For new games added by auto_update.py, set the default:
new_game = {
    ...
    'coopScore': None,   # Not yet scored
    ...
}
```

---

## State of the Art

| Old Approach | Current Approach | Correct Approach After Phase 1 |
|--------------|------------------|-------------------------------|
| `continue-on-error: true` on build steps | Exists today — build errors silently swallowed | Remove from build steps only; keep for affiliate steps |
| No `coopScore` field | Not in schema | `coopScore: null` default for all 589 games |
| `mini_review_it/en` not round-tripped | Written manually in `games.js`, silently dropped by CI | Read by `load_games()`, written by `write_legacy_games_js()` |
| `split` as coopMode value | Used in 210 games | Renamed to `sofa` everywhere; `split` treated as error by validator |

---

## Environment Availability

Step 2.6: No new external dependencies. Phase 1 touches only Python files and a YAML file that are already part of the project. All tools (Python 3.11, GitHub Actions) are already available.

---

## Validation Architecture

No dedicated test framework detected (no pytest.ini, no tests/ directory, no test files).

The project uses `validate_catalog.py` as its functional validation gate, run in CI. For Phase 1, the validation approach is:

### Phase Requirements → Validation Map

| Req ID | Behavior | Validation Method | Automated? |
|--------|----------|-------------------|------------|
| SCH-01 | `coopScore` field in all three data artifacts | Run `validate_catalog.py` locally; inspect JSON output | Semi (manual local run) |
| SCH-02 | Protected fields survive CI round-trip | Run `auto_update.py` locally in dry-run or on a copy; verify `mini_review` count after write | Manual spot-check |
| SCH-03 | Build failures block CI | Remove `continue-on-error`; verify YAML diff is correct | Manual review of YAML diff |
| SCH-04 | Non-canonical `coopMode` values cause error | Run `validate_catalog.py` after vocabulary rename; confirm 0 errors | `python3 scripts/validate_catalog.py` |

### Local Verification Commands

```bash
# Run from the scripts/ directory
cd /home/andrea/Progetto\ sito/giochidicoopia/scripts

# Verify coopScore propagation (SCH-01)
python3 -c "import catalog_data; g=catalog_data.load_games(); print('coopScore in first game:', g[0].get('coopScore')); print('Total games:', len(g))"

# Verify coopMode vocabulary (SCH-04) — should print 0 after rename
python3 -c "
import catalog_data
games = catalog_data.load_games()
bad = [(g['id'], g['coopMode']) for g in games if set(g['coopMode']) - {'online','local','sofa'}]
print('Games with non-canonical coopMode:', len(bad))
if bad: print('Sample:', bad[:3])
"

# Verify mini_review round-trip (SCH-02)
python3 -c "
import catalog_data
games = catalog_data.load_games()
with_mr = [g for g in games if g.get('mini_review_it')]
print('Games with mini_review_it after load:', len(with_mr))
"

# Full validation
python3 validate_catalog.py
```

### Wave 0 Gaps

No test framework setup needed — validation uses existing `validate_catalog.py` extended in SCH-04. No new test files required.

---

## Open Questions

1. **`split` → `sofa` rename scope in frontend files**
   - What we know: `build_static_pages.py` and `app.js` both reference the string `"split"` for display/logic
   - What's unclear: Whether renaming the data value requires simultaneous changes in `app.js` (frontend JS, affects live site rendering) or if the frontend can tolerate both values during the transition
   - Recommendation: Rename in all locations atomically. Since this is a static site committed to git and deployed together, there is no staging window where data and frontend are out of sync.

2. **`mini_review_it/en` format in `ef()` parser**
   - What we know: `ef()` uses a regex that captures strings via `"(?:[^"\\]|\\.)*"` — this handles escaped quotes correctly
   - What's unclear: Whether any existing mini_review values contain characters that would break the regex (e.g., unescaped double quotes or multi-line strings)
   - Recommendation: Inspect the 17 existing values before committing. A Python one-liner can verify all parse correctly.

3. **`igdbId` in `mini_review` — does `ef()` multiline flag matter?**
   - What we know: `ef()` is called with `re.DOTALL` — this is already present and handles multi-line field values
   - What's unclear: Whether `mini_review_it` values can be multi-line in `games.js`
   - Recommendation: Treat as single-line; mini-reviews in the source are written as single-line strings.

---

## Sources

### Primary (HIGH confidence)

- Direct inspection of `/home/andrea/Progetto sito/giochidicoopia/scripts/catalog_data.py` — confirmed: `ef()` parser does not handle null; `load_games()` and `write_legacy_games_js()` do not include `mini_review_*` or `coopScore`
- Direct inspection of `/home/andrea/Progetto sito/giochidicoopia/.github/workflows/update.yml` — confirmed: `continue-on-error: true` on lines 62 and 66 (build steps)
- Direct inspection of `/home/andrea/Progetto sito/giochidicoopia/scripts/validate_catalog.py` — confirmed: no `coopMode` vocabulary check exists
- Runtime check of `data/catalog.public.v1.json` — confirmed: `split` appears as coopMode value in 210 games; `sofa` has zero occurrences; `coopScore` field absent in all 589 games

### Secondary (MEDIUM confidence)

- Inspection of `auto_update.py` tail — confirmed: writes `games.js` via `catalog_data.write_legacy_games_js()` without any `coopScore` or `mini_review` handling
- Cross-reference of `build_static_pages.py` and `app.js` — confirmed: both reference `"split"` string, not `"sofa"`

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries, all inspection is direct code reading
- Architecture: HIGH — data flow traced end-to-end through actual source files
- Pitfalls: HIGH — all pitfalls confirmed by direct runtime checks, not inference

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable codebase; only invalidated if schema or CI workflow changes before planning is complete)
