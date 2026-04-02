# Pipeline Workflow -- Full Analysis

> Last updated: 2026-04-02

## Overview

The project runs **3 GitHub Actions workflows** that automate the entire data pipeline: catalog updates, price fetching, page generation, quality auditing, and free game tracking. Everything is static -- no backend, no database server -- just Python scripts that read/write JSON and JS files, committed directly to `main`.

---

## Workflow 1: Update Games Database (`update.yml`)

**Schedule:** Daily at 06:00 UTC + manual dispatch

### Pipeline Steps (sequential)

```
checkout + python 3.11 setup
        |
        v
auto_update.py                 [CORE - ~10 min]
  - Reads assets/games.js (legacy catalog bundle)
  - Fetches CCU/rating from SteamSpy (top100in2weeks)
  - Fetches co-op candidates from SteamSpy (4 tag queries)
  - Fetches new releases from Steam store API
  - Discovers games via IGDB API (cross-platform)
  - Discovers GOG-only titles
  - Optionally fetches itch.io games (if ITCH_IO_KEY set)
  - Deduplicates by igdbId + Steam AppID + title
  - Verifies co-op via quality_gate.py
  - Updates trending flags (MIN_CCU_TRENDING = 10000)
  - Picks featured indie of the week
  - Writes back assets/games.js + data/catalog.*.json
        |
        v
fetch_affiliate_prices.py      [continue-on-error]
  - Instant Gaming (httpx + BeautifulSoup scraping)
  - GameBillet (httpx + BeautifulSoup scraping)
  - Kinguin (CJ deep link wrapping, no search)
  - GAMIVO (CJ deep link wrapping, no search)
        |
        v
fetch_gameseal_prices.py       [continue-on-error]
  - Gameseal + Kinguin via CJ API
  - Requires CJ_API_TOKEN secret
        |
        v
fetch_gamivo_prices.py          [continue-on-error]
  - GAMIVO via CJ API
  - Requires CJ_API_TOKEN secret
        |
        v
fetch_k4g_prices.py             [continue-on-error]
  - K4G price fetching
        |
        v
fetch_gmg_prices.py             [continue-on-error]
  - Green Man Gaming via Impact.com
        |
        v
build_static_pages.py           [CRITICAL]
  - Generates games/<id>.html for every game (IT + EN)
  - Generates sitemap.xml, sitemap-main.xml, sitemap-hubs.xml
  - Applies SEO overrides from data/seo_overrides.json
        |
        v
build_hub_pages.py              [CRITICAL]
  - Generates SEO hub pages:
    - migliori-giochi-coop-2026.html
    - giochi-coop-local.html
    - giochi-coop-2-giocatori.html
    - giochi-coop-free.html
    - giochi-coop-indie.html
    - + horror, survival, offline, indie category pages
  - Uses editorial data from data/hub_editorial.json
        |
        v
validate_catalog.py             [GATE]
  - Structural validation of catalog
        |
        v
git commit + push to main
  - Tracked files: assets/games.js, games/, sitemap*.xml,
    data/catalog.*.json, index.html, assets/i18n.js
```

### Secrets Required

| Secret | Used By |
|--------|---------|
| `STEAM_API_KEY` | auto_update.py |
| `IGDB_CLIENT_ID` | auto_update.py |
| `IGDB_CLIENT_SECRET` | auto_update.py |
| `ITCH_IO_KEY` | auto_update.py (optional) |
| `CJ_API_TOKEN` | fetch_gameseal_prices.py, fetch_gamivo_prices.py |

### Key Config (catalog_config.py)

| Constant | Value | Purpose |
|----------|-------|---------|
| `DELAY` | 1.5s | Rate limit between API calls |
| `MAX_NEW_GAMES` | 30 | Max new SteamSpy games per run |
| `MAX_IGDB_DISCOVERY` | 30 | Max new IGDB games per run |
| `MAX_GOG_GAMES` | 10 | Max new GOG-only games per run |
| `MAX_STEAM_NEW` | 20 | Max new Steam releases per run |
| `MIN_CCU_TRENDING` | 10000 | CCU threshold for trending badge |

---

## Workflow 2: Catalog Quality Audit (`catalog_audit.yml`)

**Schedule:** Weekly, Sundays at 03:00 UTC + manual dispatch

### Pipeline Steps

```
checkout + python 3.11 setup
        |
        v
catalog_audit.py --fast --apply
  - Iterates ALL games in catalog (~590+)
  - For each game: checks Steam categories for real co-op signal
  - Uses quality_gate.py (multi-source: Steam/IGDB/GOG/RAWG)
  - --fast mode: Steam-only (~2-3 min, 4 parallel workers)
  - --apply: auto-removes high-confidence false co-op entries
  - Outputs:
    - data/audit_rejected.json (confirmed false co-op)
    - data/audit_needs_review.json (ambiguous cases)
    - data/audit_state.json (resume checkpoint)
        |
        v
build_static_pages.py
  - Rebuilds pages if games were removed
        |
        v
validate_catalog.py
  - Re-validates after cleanup
        |
        v
git commit + push to main
```

### Secrets Required

| Secret | Used By |
|--------|---------|
| `IGDB_CLIENT_ID` | catalog_audit.py |
| `IGDB_CLIENT_SECRET` | catalog_audit.py |
| `RAWG_API_KEY` | catalog_audit.py |

### Quality Gate Logic (quality_gate.py)

The quality gate checks multiple sources in priority order:

1. **Steam categories** (primary) -- always checked
   - Auto-approve if categories 9, 38, 39, or 48 found (strong co-op signal)
   - PvP categories (49, 36, 37, 47) flag for review
2. **IGDB game_modes** (secondary) -- if credentials available
3. **GOG catalog features** (tertiary) -- by title search
4. **RAWG tags** (quaternary) -- additional confirmation

Verdicts: `approve` / `reject` / `needs_review`

---

## Workflow 3: Update Free Games (`free_games.yml`)

**Schedule:** Daily at 07:00 UTC (1 hour after main update) + manual dispatch

### Pipeline Steps

```
checkout + python 3.11 setup
  - Note: installs only requests + beautifulsoup4 (not full requirements.txt)
        |
        v
fetch_free_games.py
  - Fetches active free game offers from multiple stores
  - Defensive: if all stores fail, keeps previous file
  - Partial failure: preserves previous entries for failed stores
  - Removes expired offers before writing
  - Stores disabled: humble (unreliable source)
  - Output: assets/free_games.js
        |
        v
validate_free_games.py
  - Validates the free games feed
        |
        v
git commit + push to main
```

### Secrets Required

None -- all sources are public.

---

## Data Flow Diagram

```
                     External APIs
          +---------+---------+---------+
          |         |         |         |
       SteamSpy  Steam    IGDB     GOG/itch
          |         |         |         |
          +----+----+----+----+----+----+
               |              |
               v              v
         auto_update.py   catalog_audit.py
               |              |
               v              v
          assets/games.js  (removes false co-op)
               |
      +--------+--------+
      |        |        |
      v        v        v
  fetch_*    build_    build_
  prices    static    hub_pages
      |     pages        |
      v        |         v
  games.js     v     hub HTML pages
  (prices)  games/
            <id>.html
               |
               v
         validate_catalog.py
               |
               v
         git push to main
               |
               v
         GitHub Pages (via Cloudflare)
```

### Catalog Data Layers

| File | Purpose | Consumer |
|------|---------|----------|
| `assets/games.js` | Legacy JS bundle (runtime) | Frontend `app.js` (fallback) |
| `data/catalog.public.v1.json` | Public JSON catalog | Frontend `app.js` (primary) |
| `data/catalog.games.v1.json` | Full catalog with admin fields | Pipeline scripts |
| `assets/free_games.js` | Free game offers feed | `free.html` page |
| `games/<id>.html` | Pre-rendered game pages | Google crawler, direct links |

---

## Script Dependency Graph

```
catalog_config.py          (constants, env vars, tag mappings)
       |
catalog_data.py            (load/save games.js + JSON catalogs)
       |
  +----+-----+------+------+-------+
  |          |      |      |       |
auto_     build_  build_  fetch_  catalog_
update    static  hub_    *       audit
  |       pages   pages   prices    |
  |                                 |
  +--- steam_catalog_source --------+
  +--- igdb_catalog_source          |
  +--- gog_catalog_source           |
  +--- itch_catalog_source          |
  +--- steam_new_releases_source    |
  |                                 |
  +--- quality_gate.py -------------+
```

All scripts share the same `catalog_data.py` module for reading/writing the catalog, ensuring consistent format.

---

## Risks and Issues

### 1. Direct commits to main

All three workflows push directly to `main` without PRs. A bad auto-update could break the live site immediately. There is no rollback mechanism beyond `git revert`.

**Severity:** High
**Mitigation options:**
- Push to a staging branch, validate, then fast-forward main
- Add a smoke test step (check sitemap is valid XML, game pages return 200)

### 2. Price fetchers use `continue-on-error: true`

All 5 price-fetching steps silently swallow failures. If an API is down for days, stale prices accumulate with no alert.

**Severity:** Medium
**Mitigation options:**
- Add a summary step that checks how many price fetchers succeeded
- Post a GitHub issue or Slack notification if >2 fetchers fail

### 3. No caching between workflow steps

Each price fetcher reloads `games.js` from disk independently. If the file is large, this is wasted I/O. More importantly, if two fetchers write to the same file, the last writer wins (though currently they write to different fields).

**Severity:** Low (works correctly today, but fragile)

### 4. Free games workflow uses partial dependencies

`free_games.yml` installs only `requests` and `beautifulsoup4` instead of the full `requirements.txt`. This means any refactor that adds a shared import to `fetch_free_games.py` will break silently.

**Severity:** Medium
**Mitigation:** Use `pip install -r scripts/requirements.txt` consistently across all workflows.

### 5. No test suite

There are no unit tests for any pipeline script. `validate_catalog.py` does structural checks, but there is no test for:
- Tag mapping correctness
- Deduplication logic
- Quality gate edge cases
- Price parsing accuracy

**Severity:** High for long-term maintenance

### 6. Sequential price fetching

The 5 price-fetch steps run sequentially. Since each has `continue-on-error`, they could run in parallel as separate jobs or as async tasks in a single script.

**Severity:** Low (time optimization only)
**Potential saving:** ~5-10 minutes per run

### 7. Audit runs in --fast mode only

The weekly audit only uses Steam data (`--fast`). Games that have incorrect Steam data but correct IGDB/RAWG data could be wrongly flagged. The `--full` mode exists but is not scheduled.

**Severity:** Low (conservative -- only removes high-confidence rejections)

---

## Recommendations (prioritized)

| # | Recommendation | Impact | Effort | Priority |
|---|----------------|--------|--------|----------|
| 1 | Add smoke tests after build (validate HTML, sitemap) | High | Low | P0 |
| 2 | Unify dependency installation across all workflows | Medium | Low | P0 |
| 3 | Add failure alerting for price fetchers | Medium | Low | P1 |
| 4 | Add unit tests for quality_gate.py and catalog_data.py | High | Medium | P1 |
| 5 | Parallelize price fetching steps | Low | Medium | P2 |
| 6 | Consider staging branch for auto-updates | High | Medium | P2 |
| 7 | Schedule monthly --full audit run | Low | Low | P3 |

---

## Timing Summary

| Workflow | Schedule | Duration (est.) | Frequency |
|----------|----------|------------------|-----------|
| Update Games DB | 06:00 UTC daily | ~15-20 min | Daily |
| Free Games | 07:00 UTC daily | ~2-3 min | Daily |
| Catalog Audit | 03:00 UTC Sunday | ~3-5 min (fast) | Weekly |

The audit intentionally runs before the daily update (Sunday 03:00 vs 06:00) so any removed games are not re-added by the same day's update.
