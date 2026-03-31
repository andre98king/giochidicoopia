# Research Summary — v1.1 Database Quality & Co-op Purity

**Synthesized:** 2026-04-01
**Milestone:** v1.1 — Database Quality & Co-op Purity
**Source files:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Executive Summary

coophubs.net is a static catalog of 589 co-op PC games. The v1.1 milestone exists because the catalog's co-op claims are built on unreliable foundations: `coopMode` fields were derived from Steam tag string matching (not from authoritative category IDs), no game has a `coopScore` field, and the daily CI pipeline has no protection for human-curated fields. The core promise of the site — "la fonte più affidabile di giochi veramente co-op" — cannot be kept until the data quality problems are fixed.

The recommended approach is conservative and incremental: no new infrastructure, no new APIs, and only one new dependency (`rapidfuzz` for title deduplication). All four v1.1 capabilities (tag audit, coopScore generation, classic discovery, bulk fixes) reuse existing pipeline components — `SteamCatalogSource`, `IgdbCatalogSource`, `catalog_data.py`. The single biggest risk is not technical: it is the daily CI run overwriting manually-assigned scores within 24 hours of them being written. That protection must exist in the codebase before any scoring work begins.

The feature set is straightforward. `coopScore` 1-3 is the differentiating feature that no other co-op catalog has. Classic game discovery surfaces titles the current SteamSpy-based pipeline misses entirely. All new scripts output JSON review files; nothing auto-applies to the catalog. This manual review gate is intentional and must be preserved.

---

## Stack Additions

| Item | Version | Purpose |
|------|---------|---------|
| `rapidfuzz` | `>=3.9.0` | Fuzzy title matching to detect near-duplicates during bulk data fixes |

All other capabilities use the existing stack: `requests`, `tenacity`, `httpx`, `igdb_catalog_source.py`, `steam_catalog_source.py`, `catalog_data.py`.

**APIs already integrated (no new auth needed):**
- Steam `appdetails` — category IDs 9 (Co-op), 38 (Online Co-op), 39 (Local Co-op) already fetched but `id` field currently discarded
- IGDB `multiplayer_modes` — `onlinecoop`, `offlinecoop`, `lancoop`, `splitscreen` booleans already used in enrichment
- SteamSpy — `top100in2weeks` used; `top100forever` endpoint is available and unused, useful for classic discovery

**What NOT to add:** pandas, SQLite, aiohttp, any LLM API, Node/npm. The pipeline is Python-only on a JSON catalog. None of these add value at 589 games scale.

---

## Feature Table Stakes

Features that must ship in v1.1 for the milestone to deliver its goal:

| Feature | Why Required | Script |
|---------|-------------|--------|
| `coopScore` 1-3 on all 589 games | Core differentiator; catalog has no quality signal today | `generate_coop_scores.py` + manual review |
| `audit_coop_tags.py` | Identifies games that are not actually co-op; prerequisite for scoring | New script, read-only |
| `discover_classics.py` | Surfaces pre-2020 co-op games missed by SteamSpy pipeline | New script, outputs candidates JSON |
| `fix_missing_data.py` / `apply_fixes.py` | Bulk-applies corrections to `maxPlayers`, `coopMode`, `crossplay`, `coopScore` | New script, dry-run by default |
| CI field protection in `catalog_data.py` | Prevents daily CI from overwriting coopScore | Patch to existing file |

**coopScore semantics (decided before implementation):**
- Score 3: Co-op Core — game was designed around co-op (Portal 2, It Takes Two, Deep Rock Galactic)
- Score 2: Co-op Solid — full co-op is present and well-integrated (Valheim, Borderlands 2, BG3)
- Score 1: Co-op Marginal — co-op exists but was clearly not the design intent; hidden from default view
- `null`: Unscored — renders no badge; most games will be null until manual review passes

**Classic game priority candidates (likely missing from catalog):**
Left 4 Dead 2, Portal 2, Payday 2, Trine series, Castle Crashers, Magicka, Stardew Valley, Divinity: Original Sin 2, Don't Starve Together (verify), Dungeon Defenders

**Deferred to v1.2+:**
- Co-op sub-type field (`coopType: campaign|horde|survival|puzzle|sandbox`) — high audit effort
- Full mini-review coverage — progressive, start with Score 3 games only
- `steamUrl` backfill for 187 games without it — separate pipeline task
- `gbUrl` expansion (currently 4/589 games)

---

## Architecture Summary

**Single source of truth:** `assets/games.js` — all pipeline writes go here via `catalog_data.write_legacy_games_js()`. The two JSON files (`catalog.games.v1.json`, `catalog.public.v1.json`) are always derived. Writing coopScore to JSON only will cause it to be lost on the next pipeline run.

**coopScore must be added to 4 locations in `catalog_data.py`:**
1. `LEGACY_RUNTIME_FIELDS` tuple
2. `normalize_game()` pass-through
3. `write_legacy_games_js()` serialiser
4. `build_public_catalog_export()` (so frontend can read it)

**New files:**

| File | Type | Writes to |
|------|------|-----------|
| `scripts/audit_coop_tags.py` | New script | `data/coop_audit_report.json` only |
| `scripts/discover_classics.py` | New script | `data/classic_candidates.json` only |
| `scripts/apply_fixes.py` | New script | `assets/games.js` (only with `--apply` flag) |
| `data/pending_fixes.json` | Human-edited input | Consumed by `apply_fixes.py` |

**Modified files:** `catalog_data.py`, `validate_catalog.py`, `catalog_config.py`, `assets/games.js`

**Not changed:** `app.js`, `index.html`, `build_static_pages.py`, GitHub Actions workflows, all game HTML pages.

---

## Critical Warnings

### 1. Daily CI Will Overwrite coopScore Within 24 Hours

The CI runs daily (cron `0 6 * * *`), not weekly as CLAUDE.md states. `auto_update.py` rebuilds catalog entries from API data. Any field not explicitly protected gets overwritten. coopScore MUST be added to a protected/locked field list in `catalog_data.py` before any scoring work begins. Mechanism: locked editorial fields (`coopScore`, `mini_review_it`, `mini_review_en`) are only overwritten if the incoming value is not null AND the current value is already null.

### 2. Steam Co-op Tags Are Self-Reported and Unreliable

Steam `categories` are set by developers in Steamworks without Valve verification. Common problems: asymmetric multiplayer tagged as co-op, modes removed by patches still shown as active, indie games that never updated Steamworks tags. The audit must treat Steam categories as one signal, not a verdict. Cross-reference with IGDB `game_modes` is mandatory; disagreements go to manual review, not auto-resolution.

### 3. 187 Games Have No steamUrl — Steam Audit Impossible for These

187 games in the catalog have no `steamUrl` and therefore no Steam App ID. The tag audit script cannot call Steam appdetails for these games. For this subset, IGDB is the only API source, and IGDB coverage for indie/small games is ~70%. These 187 games should be explicitly listed as "manual review only" in the audit output.

### 4. `continue-on-error: true` Must Be Removed from Build Steps Before New Features

`build_static_pages.py` and `build_hub_pages.py` currently run with `continue-on-error: true`. This means a Python exception in either script deploys stale pages silently with no CI failure. Before adding coopScore rendering to build scripts, remove `continue-on-error` from these steps. Keep it only on affiliate price-fetch steps (those are genuinely optional).

### 5. coopScore Thresholds Need Calibration Before Bulk Application

The rule-based scoring algorithm assigns scores based on Steam category IDs and IGDB booleans. Before running it on all 589 games, manually score 20-30 representative games and verify the algorithm agrees. Focus calibration on: Score 3 boundary (IGDB says co-op but is it really core?), Score 1 boundary (high-player-count games where co-op is incidental), and the `coopMode = ['online']` only with low CCU pattern.

---

## Suggested Phase Order

### Phase 1: Schema Foundation + CI Hardening
**Prerequisite for all other phases. Must be complete before writing a single line of scoring logic.**

Deliverables:
- `coopScore: null` field added to all 589 games in `games.js` (via `catalog_data.py` update)
- Editorial field protection implemented in `auto_update.py` and `catalog_data.py`
- `continue-on-error: true` removed from build steps in `update.yml`
- Canonical `coopMode` values defined in `catalog_config.py` (resolve `split` vs `sofa` inconsistency)
- `coopScore` semantics documented (Score 1 = hidden by default, not removed)
- `validate_catalog.py` updated to report coopScore coverage stats

Rationale: Without this, any work in Phase 2 or 3 can be silently destroyed by the next CI run.

Research flag: No research needed — all changes are mechanical additions to existing files.

---

### Phase 2: Tag Audit + coopScore Generation
**Depends on Phase 1. Cannot start until field protection is live.**

Deliverables:
- `audit_coop_tags.py`: reads catalog, calls Steam appdetails + IGDB, outputs `coop_audit_report.json` with `confirmed/flagged/missing_data` buckets and severity levels
- `generate_coop_scores.py`: reads catalog + audit report, outputs `coop_score_candidates.json` for manual review
- Manual review pass on all Score 3 candidates (~50 games) and Score 1 candidates (~50-80 games)
- `pending_fixes.json` populated from audit findings
- `apply_fixes.py` with dry-run default — apply corrections to `games.js`

Key constraints:
- Audit must run in batches of max 80 games per run (Steam rate limits)
- Resumable via tracked IDs in output file
- IGDB token refreshed at start of every run
- Disable scheduled CI during the audit window to prevent `git pull --rebase -X ours` conflicts

Research flag: Patterns are well-documented in existing codebase. No phase research needed.

---

### Phase 3: Classic Game Discovery
**Independent from Phase 2 — can be built in parallel. Requires Phase 1 schema to be complete.**

Deliverables:
- `discover_classics.py`: IGDB era-range queries (pre-2020) + SteamSpy `top100forever` cross-reference
- `classic_candidates.json`: structured output for manual review
- Manual review of candidates — verify active purchase URL exists (GOG, Steam, itch.io)
- Approved classics added via `apply_fixes.py` with IDs assigned as `max(existing_ids) + 1`
- One-time fix: `releaseYear=0` on 66 existing games patched from IGDB or Steam data

Key constraints:
- Only add classics with an active purchase URL — define policy before running the script
- Never reuse gap IDs from deleted games
- Require `releaseYear` as mandatory field in discovery output
- SteamSpy `all` endpoint: 1 request/60 seconds rate limit — respect in script design

Research flag: No phase research needed. IGDB query patterns and SteamSpy endpoints are confirmed in STACK.md.

---

### Phase 4: Bulk Data Fixes + Validation
**Depends on Phase 2 audit findings. Final cleanup pass before milestone is declared complete.**

Deliverables:
- `maxPlayers` suspicious values fixed (65535, 255, 70, 100 — at least 8 confirmed bad values)
- `rating=0` handling: display "Unreleased" badge instead of "0"
- `crossplay: true` spot-check on top 20 by rating
- Final `validate_catalog.py` run with coopScore coverage report
- `build_static_pages.py` updated to render coopScore badge on game pages

Rationale: Audit findings from Phase 2 define what needs fixing. Phase 4 applies those fixes at scale and validates the complete catalog state.

Research flag: No phase research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (new deps) | HIGH | Only one new library. All existing API integrations verified in codebase. |
| Feature scope | HIGH | coopScore semantics well-defined. Classic game lists cross-validated across multiple sources. |
| Architecture | HIGH | Based on direct codebase inspection. Data flow confirmed. `games.js` as write target verified. |
| Pitfalls | HIGH | PITFALLS.md sourced directly from codebase files, not inference. CI schedule discrepancy (daily not weekly) confirmed from `update.yml`. |
| coopScore algorithm | MEDIUM | Rule logic is sound; thresholds need calibration on real data before bulk application. |
| IGDB coverage depth | MEDIUM | ~30% of games may have null `game_modes` — exact number unconfirmed until audit runs. |

**Gaps that need attention during planning:**
- Exact count of games where both Steam and IGDB data is unavailable (187 without steamUrl, but how many of those also have no `igdbId`?) — check `data/catalog.games.v1.json` field intersection
- coopScore visibility rule for Score 1 games needs a frontend decision (hide by default = filter UI change in `app.js`)
- `_nocoop_flagged.json` existing contents should be reviewed before Phase 2 — these are the highest-confidence Score 1 candidates

---

## Aggregated Sources

- [SteamSpy API endpoints](https://steamspy.com/api.php) — `top100forever`, `tag`, `all` confirmed
- [IGDB API Documentation](https://api-docs.igdb.com/) — `game_modes`, `multiplayer_modes`, `first_release_date` range queries
- [RapidFuzz 3.14.3](https://rapidfuzz.github.io/RapidFuzz/) — current stable, pure Python wheel
- [Co-Optimus Review Scale](https://www.co-optimus.com/review-scores.php) — co-op quality rating reference
- [PCGamesN Best Co-op Games 2026](https://www.pcgamesn.com/best-co-op-games) — current editorial list
- [Co-op Games That Shaped Modern Gaming — DualShockers](https://www.dualshockers.com/co-op-games-that-shaped-modern-gaming-more-than-players-realized/)
- [Game Developer: 5 Problems with Co-op Game Design](https://www.gamedeveloper.com/design/5-problems-with-co-op-game-design-and-possible-solutions-)
- [Schema evolution best practices — dataengineeracademy.com](https://dataengineeracademy.com/module/best-practices-for-managing-schema-evolution-in-data-pipelines/)
- Internal codebase: `scripts/catalog_data.py`, `scripts/validate_catalog.py`, `scripts/catalog_config.py`, `scripts/discover_backfill.py`, `scripts/steam_catalog_source.py`, `.github/workflows/update.yml`, `data/catalog.games.v1.json`
