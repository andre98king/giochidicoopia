# Technology Stack — v1.1 Additions

**Project:** coophubs.net — Database Quality & Co-op Purity milestone
**Researched:** 2026-04-01
**Scope:** Only NEW capabilities needed for v1.1. Existing stack (requests, httpx, beautifulsoup4, lxml, feedparser, deep-translator, tenacity) is unchanged.

---

## Existing Pipeline State (Do Not Re-add)

The pipeline already has:
- `igdb_catalog_source.py` — full IGDB enrichment and discovery (Twitch OAuth, multiplayer_modes, external_games)
- `steam_catalog_source.py` — Steam appdetails, SteamSpy, rating/CCU/coopMode derivation
- `discover_backfill.py` — SteamSpy tag-based historical candidate finder
- `catalog_data.py` — JSON catalog I/O with normalized schema
- 427/589 games already have `igdbId`; 0/589 have `coopScore`

---

## Capability 1: Co-op Tag Audit (Verify coopMode Accuracy)

### Problem
`coopMode` on 589 games was derived from SteamSpy tag names (string matching), not from Steam's authoritative category IDs. This causes false positives (e.g., competitive games tagged "Multiplayer" making it in as "online" co-op).

### What's Already Available

| Source | Data | How Accessed | Status |
|--------|------|--------------|--------|
| Steam appdetails | `categories[]` array with `id` + `description` | `SteamCatalogSource.fetch_steam_desc()` — already returns full `steam_data` dict | **Existing** — `steam_data['categories']` is already fetched but `id` field is discarded |
| IGDB multiplayer_modes | `onlinecoop`, `offlinecoop`, `splitscreen`, `lancoop`, `dropin` booleans + maxPlayers | `IgdbCatalogSource.fetch_multiplayer_modes()` | **Existing** — already used in enrichment |
| SteamSpy tag data | Co-op tag presence per appid | `SteamCatalogSource.fetch_json()` with tag endpoint | **Existing** |

### Steam Category IDs for Co-op Verification (HIGH confidence — confirmed in existing codebase)

| ID | Description | Co-op Signal |
|----|-------------|--------------|
| 9  | Co-op | Weak — Steam uses this loosely |
| 38 | Online Co-op | Strong — explicit online co-op |
| 39 | Local Co-op | Strong — explicit local co-op |
| 37 | Local Multi-Player | Weak — may be competitive |
| 1  | Multi-player | Weak — includes PvP |

### New Script Needed: `audit_coop_tags.py`

No new libraries required. Uses existing `SteamCatalogSource` and `IgdbCatalogSource`.

**Pattern:**
1. Load catalog JSON
2. For each game with `steamUrl`: call appdetails, extract `categories[].id`
3. Cross-reference with IGDB `multiplayer_modes` (already fetched for 427 games)
4. Flag mismatches: game has `coopMode=['online']` but no category 38/39 in Steam AND no `onlinecoop=true` in IGDB
5. Output `data/audit_coop_results.json` with three buckets: `confirmed`, `flagged`, `missing_data`

**Integration point:** Runs standalone. Output is JSON reviewed manually before applying fixes via `catalog_data.py`.

**Rate limiting:** Reuse existing `SteamCatalogSource(delay=1.5)` + `tenacity` retry. No new rate limit logic needed.

---

## Capability 2: coopScore Field Generation

### Problem
`coopScore` (1=marginal, 2=solid, 3=co-op core) does not exist on any game yet. Needs semi-automatic generation: algorithmic scoring with human review gate before writing.

### Signal Inventory (All Existing, No New APIs)

| Signal | Field | Weight Rationale |
|--------|-------|------------------|
| IGDB `onlinecoop` / `offlinecoop` booleans | `capabilities.onlineCoop`, `capabilities.localCoop` | HIGH — authoritative DB, manually curated |
| IGDB `lancoop` | derived via `igdb_catalog_source._parse_multiplayer_modes()` | MEDIUM |
| Steam category 38 (Online Co-op) or 39 (Local Co-op) | from appdetails audit above | HIGH |
| Steam category 9 only (no 38/39) | from appdetails | LOW — "Co-op" label is vague |
| `coopMode` includes `local` or `split` | existing field | MEDIUM |
| `maxPlayers` >= 4 | existing field | MEDIUM |
| Genre: `survival`, `factory`, `roguelike` | often co-op-first design | LOW — genre hint only |

### Scoring Algorithm (No ML, No New Libraries)

```
score = 1  # marginal default

# Score 3 (co-op core): game is designed around co-op
if (steam_cat_38 OR steam_cat_39) AND igdb_onlinecoop AND maxPlayers >= 2:
    score = 3
elif igdb_lancoop AND (steam_cat_38 OR steam_cat_39):
    score = 3

# Score 2 (solid co-op): co-op is a primary mode
elif (steam_cat_38 OR steam_cat_39) OR igdb_onlinecoop:
    score = 2

# Score 1 (marginal): only vague signals
# (steam cat 9 only, or coopMode derived from tag name matching)
```

This is pure Python logic on existing data. No new libraries needed.

**Semi-automatic workflow:**
1. Run score computation, write to `data/coop_score_candidates.json`
2. Human reviews flagged cases (score=1 or missing signals)
3. Approved scores written back to catalog via `catalog_data.py`

**Integration point:** New script `scripts/generate_coop_scores.py`. Reads from catalog JSON + audit output. Does NOT auto-write to catalog — outputs a review file.

---

## Capability 3: Classic/Underrated Co-op Discovery

### Problem
`discover_backfill.py` uses SteamSpy tag + rating filter. It covers Steam games from 2021+. Need to surface quality co-op games from all eras (pre-2020, console classics now on PC, niche titles).

### New Patterns Needed

#### Pattern A: IGDB Historical Range Query

IGDB `first_release_date` is a Unix timestamp. Supports range queries. Existing `IgdbCatalogSource._post()` already handles the HTTP layer.

**New query pattern** (no new library, extend existing `IgdbCatalogSource`):

```python
# Era buckets: 2000-2009, 2010-2015, 2016-2019
era_start = int(datetime(year, 1, 1).timestamp())
era_end = int(datetime(year+1, 1, 1).timestamp())
query = (
    "fields id, name, rating, rating_count, "
    "game_modes, platforms, first_release_date, "
    "external_games.uid, external_games.category; "
    f"where game_modes = ({IGDB_COOP_MODE}) "
    f"& platforms = ({IGDB_PC_PLATFORM}) "
    f"& first_release_date >= {era_start} "
    f"& first_release_date < {era_end} "
    f"& rating >= 70 & rating_count > 20; "
    "sort rating desc; limit 50;"
)
```

This extends the existing `discover_coop_games()` method — no structural change needed.

#### Pattern B: SteamSpy `top100forever` for Ownership-Based Discovery

SteamSpy already exposes `top100forever` (top 100 by cumulative players since 2009). Existing pipeline only uses `top100in2weeks`. Cross-referencing `top100forever` against catalog finds beloved older titles not yet included.

No new library. One extra `fetch_json()` call.

#### Pattern C: SteamSpy `all` Endpoint with Era Filter

SteamSpy `all` returns 1,000 games/page sorted by owners. Combined with a `releaseYear` filter and co-op tag cross-check, this surfaces high-ownership older titles missed by the existing pipeline.

Rate limit: 1 request/60 seconds for this endpoint. Must be respected in script design.

### New Script: `discover_classics.py`

Standalone script (not part of weekly CI). Outputs `data/classic_candidates.json` for manual review.

**No new libraries needed.** Reuses `IgdbCatalogSource`, `SteamCatalogSource`, `catalog_data`.

---

## Capability 4: Bulk Data Quality Fix Tooling

### Problem
66 games have `releaseYear=0`. Many games have `maxPlayers=4` (default, not verified). Some have empty `coopMode=[]` or inconsistent `players` labels.

### New Library: `rapidfuzz` (for title deduplication during bulk fixes)

| Library | Version | Purpose | Why Not Alternatives |
|---------|---------|---------|---------------------|
| `rapidfuzz` | `>=3.9.0` (current: 3.14.3) | Fuzzy title matching to catch near-duplicates when bulk-adding data | `difflib.SequenceMatcher` is slower (2500 vs 1000 pairs/sec); `fuzzywuzzy` depends on `python-Levenshtein` which has C build complexity; `rapidfuzz` is pure Python wheel, no build step |

**Use case:** When bulk-patching 66 games with `releaseYear=0` from Steam appdetails, detect if a patched title might be a near-duplicate of an existing entry (title changed slightly on Steam). Prevents silent catalog corruption.

**Integration point:** Import in `catalog_data.py` or a new `scripts/fix_missing_data.py`. Single function: `check_near_duplicate(title, existing_titles, threshold=90)`.

### No New Library Needed For

- Fixing `releaseYear=0`: already `parse_release_year()` in `steam_catalog_source.py` — just run it against the appdetails response
- Fixing `maxPlayers`: already `IgdbCatalogSource.fetch_multiplayer_modes()` — run enrichment selectively on un-enriched games
- Fixing `players` label: already `derive_players_label()` in `steam_catalog_source.py`

---

## Updated requirements.txt Addition

```
# Fuzzy title matching for deduplication (bulk data quality fixes)
rapidfuzz>=3.9.0
```

Only one new library. All other v1.1 capabilities use existing dependencies.

---

## What NOT to Add

| Rejected Item | Reason |
|---------------|--------|
| `pandas` | Overkill for 589-game dataset. Plain dicts + list comprehensions are sufficient and faster to iterate. |
| `sqlalchemy` / SQLite | No persistence layer needed. JSON catalog is the source of truth. Adding a DB creates sync complexity with `games.js`. |
| `aiohttp` / async pattern | IGDB and Steam APIs both require rate limiting (0.35s, 1.5s delays). Async would require semaphore logic with no net throughput gain given the enforced delays. |
| `openai` / LLM API for scoring | coopScore logic is deterministic from structured data. LLM adds cost, latency, non-reproducibility, and a new external dependency. |
| `rich` / `tabulate` for audit output | Scripts run in CI and locally. JSON output files are sufficient — human review happens in an editor/diff tool, not a terminal table. |
| Node/npm anything | Static site constraint. Pipeline is Python only. |

---

## Integration Map: New Scripts and Existing Pipeline

```
catalog.games.v1.json  (source of truth)
        │
        ├── audit_coop_tags.py
        │       ├── reads: catalog JSON
        │       ├── calls: SteamCatalogSource (appdetails categories)
        │       ├── calls: IgdbCatalogSource (multiplayer_modes for missing igdbIds)
        │       └── writes: data/audit_coop_results.json  [reviewed manually]
        │
        ├── generate_coop_scores.py
        │       ├── reads: catalog JSON + audit_coop_results.json
        │       └── writes: data/coop_score_candidates.json  [reviewed manually]
        │
        ├── discover_classics.py
        │       ├── reads: catalog JSON (existing igdbIds, steamAppIds, titles)
        │       ├── calls: IgdbCatalogSource (era-ranged discovery queries)
        │       ├── calls: SteamCatalogSource (top100forever, appdetails verification)
        │       └── writes: data/classic_candidates.json  [reviewed manually]
        │
        └── fix_missing_data.py  (or integrated into auto_update.py)
                ├── reads: catalog JSON (games where releaseYear=0, maxPlayers=4 unverified)
                ├── calls: SteamCatalogSource (appdetails for missing releaseYear)
                ├── calls: IgdbCatalogSource (multiplayer_modes for un-enriched games)
                ├── uses: rapidfuzz (duplicate check before writing)
                └── writes: data/data_quality_fixes.json  [reviewed] → catalog JSON
```

**All new scripts output JSON review files. No script auto-writes to the catalog without a separate apply step. This preserves the manual review gate.**

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Existing API capabilities (IGDB, Steam) | HIGH | Verified against existing working scripts in codebase |
| Steam category IDs (9, 38, 39) | HIGH | Present in existing `discover_backfill.py:COOP_CATEGORY_IDS` |
| IGDB `first_release_date` timestamp range queries | MEDIUM | Confirmed in IGDB API docs structure; specific syntax from existing query patterns |
| SteamSpy `top100forever` for classic discovery | HIGH | Confirmed from official SteamSpy API docs at steamspy.com/api.php |
| `rapidfuzz` 3.14.3 as current stable | HIGH | Confirmed from PyPI and official docs |
| coopScore algorithm (rule-based) | MEDIUM | Logic designed from signal inventory; thresholds will need calibration on real data |

---

## Sources

- [SteamSpy API endpoints](https://steamspy.com/api.php) — official, confirmed `top100forever`, `tag`, `all` endpoints
- [IGDB API Getting Started](https://api-docs.igdb.com/) — official Twitch/IGDB documentation
- [RapidFuzz 3.14.3 docs](https://rapidfuzz.github.io/RapidFuzz/) — current stable version confirmed
- [RapidFuzz PyPI](https://pypi.org/project/RapidFuzz/) — install details
- Existing codebase: `scripts/igdb_catalog_source.py`, `scripts/steam_catalog_source.py`, `scripts/discover_backfill.py` — verified integration patterns
