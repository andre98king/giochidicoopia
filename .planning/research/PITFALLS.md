# Domain Pitfalls — v1.1 Co-op Quality Scoring & Data Audit

**Domain:** Game catalog with co-op quality scoring, API-driven tag audit, classic game discovery
**Researched:** 2026-04-01
**Context:** Adding `coopScore` (1-3) to 589 existing games, auditing coopMode tags via Steam/IGDB, adding classic games, running bulk fixes through CI pipeline

---

## Quick Reference Table

| # | Pitfall | Risk | Phase to Address |
|---|---------|------|-----------------|
| 1 | coopScore default stomps manual overrides in subsequent CI runs | CRITICAL | Phase 1 — before any scoring logic |
| 2 | Three catalog copies diverge silently after bulk field add | CRITICAL | Phase 1 — establish single source of truth first |
| 3 | Steam `categories` API co-op flag is unreliable (self-reported by devs) | HIGH | Phase 2 — audit methodology |
| 4 | IGDB `game_modes` field missing or stale on ~30% of catalog | HIGH | Phase 2 — audit methodology |
| 5 | Auto-update CI overwrites coopScore with NULL on every weekly run | HIGH | Phase 1 — field protection strategy |
| 6 | Classic games have year=0 / no steamUrl — validator blocks deploy | HIGH | Phase 3 — classic discovery |
| 7 | coopMode terminology inconsistency (split vs sofa, CLAUDE.md vs actual data) | MEDIUM | Phase 1 — before scoring |
| 8 | ID gaps in catalog (IDs 4, 62, 78… missing) break page count validation | MEDIUM | Phase 1 — before adding games |
| 9 | bulk script runs on CI hit Steam API rate limit (200 req/day undocumented) | MEDIUM | Phase 2 — audit tooling |
| 10 | IGDB OAuth token expires mid-run, partial audit leaves data inconsistent | MEDIUM | Phase 2 — audit tooling |
| 11 | coopScore 1 games remain in catalog and hurt "co-op purity" brand | MEDIUM | Phase 2 — scoring semantics |
| 12 | continue-on-error in CI hides build failures silently | MEDIUM | Phase 1 — CI hardening |
| 13 | `git pull --rebase -X ours` in CI silently discards manual local edits | LOW | Phase 1 — workflow review |
| 14 | 66 games with releaseYear=0 cause bad SEO on classic game pages | LOW | Phase 3 — classic discovery |

---

## Critical Pitfalls

### Pitfall 1: coopScore Default Silently Overwritten by CI

**What goes wrong:** The weekly `auto_update.py` run fetches fresh data from Steam/IGDB and rebuilds game entries. If the update script sets `coopScore` to `null` or omits it entirely when the field is absent from the API response, every manually-assigned score gets erased on the next Monday run.

**Why it happens:** The existing pipeline merges fresh API data into catalog entries. Any field not explicitly "protected" gets overwritten. The current `auto_update.py` has no concept of fields that are human-curated.

**Consequences:** Hours of scoring work lost silently. Regression only discovered when the scoring UI shows blank values.

**Prevention:**
- Before writing any scoring logic, add a "locked fields" mechanism in `catalog_data.py`: fields in a designated list (`coopScore`, `mini_review_it`, `mini_review_en`, `personalNote`) are only written if the incoming value is not null AND the current value is already null.
- Alternative: store coopScore in a separate sidecar file (`data/coopscore_overrides.json`) and merge it after the auto-update, never letting the update script touch it.
- Validate in `validate_catalog.py`: if any game that had a coopScore now has `null`, fail the build.

**Detection:** Add a pre-commit check that counts games with coopScore set and errors if count drops.

---

### Pitfall 2: Three Catalog Copies Diverge After Bulk Field Add

**What goes wrong:** The project has three copies of game data: `assets/games.js` (~20k lines), `data/catalog.games.v1.json` (private, all fields), and `data/catalog.public.v1.json` (public, subset of fields). Adding `coopScore` to the private JSON but forgetting to propagate it to `games.js` means the frontend (which still loads from `games.js` based on `app.js`) shows no scoring UI. Adding it to `catalog.public.v1.json` but not building it into the static pages means game pages are stale.

**Why it happens:** The CONCERNS.md explicitly flags this triple-copy problem. The field list already differs: `catalog.games.v1.json` has 15 fields not in `catalog.public.v1.json` (including `gmgDiscount`, `taxonomy`, `igdbId`, `editorial`, etc.).

**Consequences:** Feature works in one context, broken in another. Hard to debug because all three files are valid JSON/JS.

**Prevention:**
- Decide in Phase 1 which file is the single source of truth for `coopScore`. Recommended: `catalog.games.v1.json` only (private), synced to `catalog.public.v1.json` by the build script, then baked into static pages by `build_static_pages.py`.
- Add `coopScore` to the public catalog explicitly only when the UI needs it. Do not add it to `games.js` until `games.js` is deprecated.
- The validate step should assert: if coopScore exists in catalog.games.v1.json, it must also exist identically in catalog.public.v1.json for the same game ID.

**Detection:** A post-update diff between private and public catalog fields catches this immediately.

---

## High Pitfalls

### Pitfall 3: Steam API Co-op Tag Is Self-Reported and Unreliable

**What goes wrong:** The Steam `appdetails` API returns a `categories` array that includes entries like `"Multi-player"`, `"Online Co-op"`, `"Local Co-op"`. These tags are set by the game developer in Steamworks — they are not verified by Valve. Developers routinely:
- Tag asymmetric multiplayer games as "Co-op" (one player is a monster/boss)
- Tag "Co-op vs AI" modes as full co-op
- Miss tags entirely for indie games that never updated their Steamworks page
- Over-tag (mark game as co-op when the mode was removed in a patch)

The Steam community itself has flagged this: discussions exist asking to "remove co-op tags" because they are "meaningless" without further qualification.

**Why it happens:** The audit script will call `ISteamApps/GetAppDetails` and trust the `categories` field. The audit goal is precisely to fix this, but the source used to fix it has the same problem.

**Consequences:** The audit legitimizes bad Steam data instead of correcting it. co-op purity gets worse, not better.

**Prevention:**
- Use Steam categories as a signal, not a verdict. Treat `"Online Co-op"` tag as one input.
- Cross-reference with IGDB `game_modes` (which has community editing and is less dev-controlled).
- For games where Steam and IGDB disagree, flag for manual review rather than auto-resolving.
- Co-optimus.com data (if accessible) is more reliable for co-op specifics — consider scraping the search results for the 100 most popular games to spot-check the Steam data.

**Detection:** Any game where Steam says co-op but IGDB says single-player only should be flagged automatically.

---

### Pitfall 4: IGDB `game_modes` Missing or Stale on Many Games

**What goes wrong:** IGDB's `game_modes` field (which has values like `Co-operative`, `Multiplayer`, `Single player`) is community-maintained. For older games, indie games, and games not on major platforms, this field is often null, empty, or reflects only the original launch modes (not modes added by updates or DLC).

**Why it happens:** IGDB has ~250k games but active contributors focus on mainstream titles. The 589 games in this catalog include many indie games (itch.io sourced) and games without Steam pages — exactly the ones IGDB coverage is worst for.

**Consequences:** The audit script finds no IGDB data for ~20-30% of games, leaving those games with unaudited coopMode tags. The audit appears complete but has silent gaps.

**Prevention:**
- Log every game where IGDB returned null/empty game_modes. Produce a "needs manual review" list.
- Do not treat IGDB null as "co-op confirmed" or "co-op denied". It means "unknown".
- For the 187 games without steamUrl (confirmed from catalog analysis), IGDB is the only API source — treat these as all-manual-review candidates.

**Detection:** Build a coverage report: % of games audited via Steam API, % via IGDB, % requiring manual review.

---

### Pitfall 5: Auto-Update CI Runs Daily and Will Overwrite New Fields

**What goes wrong:** The `update.yml` workflow runs **every day** (not weekly as CLAUDE.md says — the actual cron is `0 6 * * *`). Any new field added to the catalog gets processed by `auto_update.py` on the next daily run. If the update script does not explicitly preserve human-curated fields, they are wiped within 24 hours of being added.

**Why it happens:** The CI pipeline was designed for data freshness, not data protection. The `git add` at the end includes both catalog JSON files, so even a script that only modifies prices will commit the full catalog back.

**Consequences:** A coopScore audit done manually or by a semi-automated script is gone the next morning before anyone notices.

**Prevention:**
- Before adding coopScore to the catalog, patch `auto_update.py` to explicitly preserve all "editorial" fields (coopScore, mini_review_it, mini_review_en, personalNote, isFeaturedIndie).
- Use a merge strategy in the update: load existing catalog, update only non-protected fields from API data, write back.
- Add a CI assertion: count games with coopScore before and after update; fail if count decreases.

---

### Pitfall 6: Classic Games Without steamUrl Fail Existing Validators

**What goes wrong:** `validate_catalog.py` requires every game to have at least one valid store URL. Classic games (pre-2010) may only have an itch.io link, a GOG link, or no storefront link at all (abandonware-type games). The current validator will block the deploy.

**Why it happens:** The validator was written for the existing catalog where all games have at least a Steam URL or itch URL. Classic game discovery will find games that are no longer commercially sold.

**Consequences:** Adding a classic game causes CI to fail. Either the CI check gets weakened (bad) or the game entry is blocked (also bad).

**Prevention:**
- Define an explicit policy before the classic game discovery phase: only add classics that have an active purchase URL (GOG, itch.io, or a remaster on Steam).
- If the policy allows "notable" games without a purchase link, update the validator to allow exceptions with a `sourceMeta.noStorefront: true` flag, and require that this flag be set intentionally.
- Never lower the validator bar silently — document exceptions explicitly.

**Detection:** The validator already catches this. The pitfall is working around it incorrectly.

---

## Medium Pitfalls

### Pitfall 7: coopMode Terminology Inconsistency (split vs sofa)

**What goes wrong:** CLAUDE.md documents coopMode values as `online | local | sofa`. The actual catalog data uses `online | local | split` (210 games have `split`). The `capabilities` object uses `splitScreen`. No game has `sofa`. This is already inconsistent. Adding coopScore logic that treats `local + split` as different from `sofa + local` will produce wrong scores.

**Prevention:** Before writing the coopScore scoring function, define the canonical coopMode values in one place (a constant in `catalog_config.py`), update CLAUDE.md to match, and add a validator rule that rejects unknown coopMode values.

**Phase to address:** Phase 1, before any scoring logic.

---

### Pitfall 8: ID Gaps Will Confuse "New Game" ID Assignment

**What goes wrong:** The catalog has IDs 1-616 but only 589 games. There are gaps at IDs 4, 62, 78, 82, 84, 93, 95, 103, 107, 117 (and more). These gaps exist from previously removed games. When adding classic games, using `max(ids) + 1` is safe, but a script that tries to "fill gaps" would cause ID collisions with deleted games that may still have static HTML pages in `games/` directory.

**Prevention:** Always assign new IDs as `max(existing_ids) + 1`. Never reuse gap IDs. Add a note to `catalog_config.py` documenting that gaps are intentional.

**Phase to address:** Phase 1 (before adding any games), Phase 3 (classic discovery).

---

### Pitfall 9: Steam API Rate Limits Hit During Bulk Audit

**What goes wrong:** Steam's public API (`store.steampowered.com/api/appdetails`) has an undocumented rate limit. Community-documented behavior: approximately 200 requests per 5-minute window per IP; sustained use leads to temporary IP blocks (typically 10-60 minutes). Auditing all 589 games in one script run will trigger this.

**Why it happens:** The existing `steam_catalog_source.py` already handles this with `tenacity` retry logic and a 60-second wait on 429. But a new audit script written from scratch may not inherit this protection, and even with retries, a full 589-game audit run will be slow (30-90 minutes).

**Prevention:**
- Reuse the existing rate-limited HTTP client from `steam_catalog_source.py`. Do not write a new one.
- Add a `--batch-size` flag to the audit script so it can be run in chunks (e.g., 100 games per run) spread across multiple days.
- Cache API responses locally in `data/audit_cache/` so repeated runs don't re-fetch unchanged games.

**Phase to address:** Phase 2 — audit tooling design.

---

### Pitfall 10: IGDB OAuth Token Expires Mid-Run

**What goes wrong:** IGDB API requires a Twitch OAuth client credentials token that expires after ~60 days. If the token expires during a multi-hour audit run (or if it was already expired when the run starts), the audit gets partial results — some games audited, some skipped. The catalog ends up with a mix of audited and unaudited entries with no clear marking of which is which.

**Prevention:**
- Refresh the IGDB token at the start of every audit run, not just when errors occur.
- Log which games were processed and which were skipped in a separate file (`data/audit_log.json`).
- Mark audited games with a `sourceMeta.lastAudit` timestamp so partial runs can be resumed.

**Phase to address:** Phase 2 — audit tooling design.

---

### Pitfall 11: coopScore 1 Games Undermine the "Co-op Purity" Brand

**What goes wrong:** If coopScore 1 means "co-op is marginal" (e.g., a game where co-op is an afterthought), showing these games in the main catalog contradicts the site's core promise ("fonte più affidabile di giochi veramente co-op"). Users will find games that technically co-op but feel like single-player, damaging trust.

**Why it happens:** A 1-3 scale assumes all three values remain in the catalog. But coopScore 1 games are arguably worse than not having them.

**Prevention:**
- Define semantics explicitly before implementation: does a coopScore 1 game stay in the catalog (visible but marked), get hidden from default view, or get removed entirely?
- Recommended: coopScore 1 = "marginal, hidden by default but accessible via filter". This preserves data integrity while protecting the default browsing experience.
- Align with the `_nocoop_flagged.json` file that already exists — games flagged there should likely become coopScore 1 candidates for review, not auto-removal.

**Phase to address:** Phase 1 — define scoring semantics before building the scoring field.

---

### Pitfall 12: `continue-on-error: true` Hides Build Failures

**What goes wrong:** The CI pipeline uses `continue-on-error: true` on 6 out of 10 steps (affiliate price fetches, `build_static_pages.py`, `build_hub_pages.py`). This means a broken `build_static_pages.py` will silently not regenerate game pages, but the workflow will succeed, commit, and push stale HTML.

**Why it happens:** `continue-on-error` was added to prevent affiliate API flakiness from blocking deploys. But it also masks real build errors.

**Consequences:** After adding coopScore rendering to `build_static_pages.py`, a Python exception in that code will silently deploy game pages without coopScore data. The only indicator is that pages look wrong — there is no CI failure alert.

**Prevention:**
- Keep `continue-on-error: true` only on external API fetches (affiliate prices, which are optional).
- Remove `continue-on-error: true` from `build_static_pages.py` and `build_hub_pages.py` — these are required build steps.
- Add an explicit post-build check: if any `.html` file in `games/` is more than 7 days old, fail the build (it means build_static_pages.py didn't run).

**Phase to address:** Phase 1 — CI hardening before any new build logic.

---

## Minor Pitfalls

### Pitfall 13: `git pull --rebase -X ours` in CI Discards Local Edits

**What goes wrong:** The CI commit step runs `git pull --rebase -X ours origin main`. If a developer has pushed a local manual fix to a game entry between the CI run starting and the CI commit step, the `ours` strategy will silently discard the developer's change in favor of the CI-generated version.

**Prevention:** This is an existing risk, not new to v1.1. Be aware that any manual catalog edits should be done when the CI is not running (avoid pushing between 06:00-07:00 UTC). During the audit phase where many manual edits happen, consider temporarily disabling the scheduled workflow and running it manually after the audit.

**Phase to address:** Phase 2 — audit execution.

---

### Pitfall 14: 66 Games with releaseYear=0 Produce Bad SEO for Classic Pages

**What goes wrong:** 66 games in the catalog have `releaseYear: 0`. These are predominantly itch.io-sourced games and games without Steam pages. Adding classic games (which may also lack reliable release year data) will increase this count. Static pages for these games will have "Released: 0" or no year shown, which looks unprofessional and hurts structured data quality.

**Prevention:**
- Before the classic discovery phase, run a one-time fix: for all games with `releaseYear: 0`, attempt to pull the year from IGDB (if `igdbId` exists) or from the Steam page, and fall back to marking the field as `null` (which the page template can then hide) rather than `0`.
- For classic games being added, require `releaseYear` as a mandatory field in the discovery script's output.

**Phase to address:** Phase 3 — classic discovery, but fix the existing 0-year entries in Phase 2 as a data quality improvement.

---

## Phase-Specific Warning Matrix

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| Phase 1: Schema + CI prep | Adding coopScore field | Field overwritten by next daily CI run (Pitfall 1, 5) | Implement field protection in catalog_data.py FIRST |
| Phase 1: Schema + CI prep | Define coopMode canonical values | Scoring logic built on wrong assumptions (Pitfall 7) | Canonicalize coopMode vocabulary before scoring |
| Phase 1: Schema + CI prep | CI pipeline hardening | continue-on-error hides broken build steps (Pitfall 12) | Remove continue-on-error from build steps |
| Phase 2: Tag audit | Using Steam API as truth | Tags are dev self-reported, unreliable (Pitfall 3) | Cross-reference Steam + IGDB, flag disagreements for manual review |
| Phase 2: Tag audit | IGDB coverage gaps | 30%+ games may have null game_modes (Pitfall 4) | Log coverage gaps, produce manual review list |
| Phase 2: Tag audit | API rate limits | 589 games in one run hits Steam rate limit (Pitfall 9) | Batch processing, local response cache |
| Phase 2: Tag audit | IGDB token expiry | Partial audit leaves inconsistent state (Pitfall 10) | Refresh token at start, checkpoint progress |
| Phase 2: Tag audit | CI conflict | Manual audit edits overwritten by daily CI (Pitfall 13) | Disable scheduled CI during audit window |
| Phase 2: Scoring | coopScore 1 semantics | Score 1 games undermine catalog quality promise (Pitfall 11) | Define visibility rules for score 1 before implementing |
| Phase 3: Classic games | Store URL requirement | Classics without purchase link fail validator (Pitfall 6) | Define and document policy before discovery |
| Phase 3: Classic games | ID assignment | Gap IDs reused, collide with deleted game pages (Pitfall 8) | Always use max(ids)+1, never fill gaps |
| Phase 3: Classic games | Missing release years | releaseYear=0 on classic game pages (Pitfall 14) | Require releaseYear in discovery script output |
| All phases | Catalog triple-copy | coopScore added to one file, missing in others (Pitfall 2) | Establish single source of truth in Phase 1 |

---

## Sources

- Project codebase analysis: `data/catalog.games.v1.json` (589 games, field inventory, coopMode distribution)
- `.planning/codebase/CONCERNS.md` (triple-copy catalog debt, script coupling risks, API rate limit risks)
- `.github/workflows/update.yml` (daily CI schedule, continue-on-error usage, rebase strategy)
- `scripts/validate_catalog.py` (current validator rules, store URL requirement)
- `scripts/steam_catalog_source.py` (existing rate limit handling with tenacity)
- Steam community discussions on co-op tag reliability: [Remove "Co-op" Tags discussion](https://steamcommunity.com/discussions/forum/10/135510669595012004/)
- IGDB API documentation: [api-docs.igdb.com](https://api-docs.igdb.com/) — game_modes field is community-maintained
- Co-optimus.com as alternative co-op data source: noted in [steam-game-finder issue #2](https://github.com/Nebukam/steam-game-finder/issues/2)
- Schema evolution best practices: [dataengineeracademy.com](https://dataengineeracademy.com/module/best-practices-for-managing-schema-evolution-in-data-pipelines/)
