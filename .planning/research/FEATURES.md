# Feature Landscape — Co-op Game Database Quality (v1.1)

**Domain:** Co-op PC game catalog / directory
**Researched:** 2026-04-01
**Milestone target:** Database quality, co-op purity, classic discovery

---

## 1. Co-op Quality Signal Taxonomy

### What the ecosystem uses

**Co-Optimus** (co-optimus.com) is the primary reference site for co-op game quality. Their 5-point scale is the industry benchmark:

| Score | Label | Definition |
|-------|-------|------------|
| 5/5 | Exceptional | Top-tier co-op experience, excels on numerous levels, incredible with friends — may still have minor imperfections |
| 4/5 | Great | Some missing co-op features or minor flaws, but overall doesn't hurt the experience |
| 3/5 | Decent | Annoying quirks in co-op: bad save system, poor split-screen implementation, lack of player balance |
| 2/5 | Poor | Falls short on expected co-op features; key things missing or broken |
| 1/5 | Marginal | Barely qualifies as co-op |

Key insight: Co-Optimus rates **co-op experience specifically**, not overall game quality. A 90/100 game can score 2/5 on co-op if the mode was bolted on.

**Steam tag taxonomy** is unreliable for data quality. Steam has four tags that developers use inconsistently:
- `Co-op` — generic, often means "at least one co-op element exists"
- `Online Co-Op` — frequently misused (some devs tag LAN-only as this)
- `Local Co-Op` — sometimes means same-PC, sometimes means LAN
- `Shared/Split Screen` — relatively consistent

**IGDB multiplayer_modes** fields (from API): `onlinecoop`, `lancoop`, `offlinecoop`, `splitscreen`, `onlinecoopmax`, `offlinecoopmax` — more granular than Steam tags, but requires API access.

### Quality signals that distinguish true co-op from afterthought co-op

Based on game design research and community consensus:

**POSITIVE signals (true co-op):**
- Shared campaign/story mode built for multiple players
- Asymmetric or complementary roles (each player has distinct function)
- Mechanics that require communication to progress
- Difficulty tuned for team play (not just "extra health for player 2")
- Revive/rescue mechanics (Left 4 Dead model)
- Shared resource pool or joint decision-making
- Drop-in/drop-out support that doesn't break the game
- Dedicated co-op content (not just "player 2 follows player 1")

**NEGATIVE signals (afterthought co-op):**
- Second player is just a "guest" following main player
- Story/narrative ignores the second player entirely
- Co-op locked to a separate mode, campaign is solo-only
- No voice/ping/communication tools in a game that requires coordination
- Heavy frame-rate degradation in local co-op
- Campaign timer/save system that penalizes the slower player
- Player 2 can only join specific sections
- "Drop-in online" with severe desync or broken progression

**BOUNDARY cases to flag for manual review:**
- Games where co-op is an optional mode on a primarily PvP game
- "Co-op story" that is a linear escort where one player controls and one watches
- MMO-style games where co-op is incidental (you can group up but nothing requires it)
- Horde/wave modes on an otherwise solo game (Dead Space Extraction model)

---

## 2. coopScore 1-3 Definition Criteria

Simplified 3-point scale adapted from Co-Optimus for the catalog:

### Score 3 — Co-op Core
*"This game was made for co-op."*

**Criteria (needs 3+ of these):**
- Campaign/primary game mode is co-op by design, not adaptation
- Roles or mechanics that only make sense with a partner
- Requires communication or coordination to succeed
- Would be significantly worse (not just shorter) without a partner
- Dedicated co-op narrative or asymmetric design
- Developer explicitly designed around co-op first

**Examples:** Portal 2 (co-op campaign), It Takes Two, A Way Out, Overcooked!, Split Fiction, Don't Starve Together, Deep Rock Galactic, Left 4 Dead 2

### Score 2 — Co-op Solid
*"The game has proper, well-integrated co-op that enhances the experience."*

**Criteria (needs 2+ of these):**
- Full campaign playable co-op with meaningful adjustments for multiple players
- Co-op mode is substantial (not just a side mode)
- Balance tuned for team play
- The co-op experience is documented and intentional
- Minor issues but nothing that breaks the mode

**Examples:** Diablo IV, Borderlands 2, Terraria, Valheim, Minecraft, Risk of Rain 2, Helldivers 2, Monster Hunter World, Baldur's Gate 3

### Score 1 — Co-op Marginal
*"You can play with others, but it was clearly designed as solo first."*

**Criteria (any of these):**
- Co-op is a tacked-on mode with no design changes
- Only specific sections or modes support co-op
- Co-op presence is technically there but creates a worse experience
- Heavy bugs or limitations in the co-op implementation
- PvPvE where players happen to be on the same side

**Examples:** Games where "co-op" means joining someone's open-world session with no shared objectives, basic "drop-in" that bypasses core mechanics, or horde modes on primarily solo games

### Assignment rules

- Default to Score 2 when uncertain and the game has standard, working co-op
- Score 3 requires at least one design element that only exists because of co-op
- Score 1 should be reserved for cases where the co-op mode is clearly secondary — or for games that may not belong in the catalog at all
- Games with maxPlayers=2 online-only: audit individually — 21 games in current catalog fit this pattern

---

## 3. Landmark Classic Co-op Games by Genre/Era

These titles are community-validated as defining the genre. They represent "classic" co-op: pre-2018, high reputation, strong community consensus across multiple sources.

### Arcade / Beat 'em Up (pre-2000)

| Title | Year | Platform | Why Landmark |
|-------|------|----------|--------------|
| Gauntlet | 1985 | Arcade/PC | Pioneered drop-in/drop-out co-op, 4-player dungeon crawl |
| Double Dragon | 1987 | Arcade | Defined sidescrolling co-op beat 'em up |
| Contra | 1987 | Arcade/NES | Run-and-gun co-op template, still referenced |
| TMNT Turtles in Time | 1991 | Arcade | 4-player beat 'em up peak of the era |
| Streets of Rage 2 | 1992 | Sega Genesis | Best beat 'em up of the genre |
| Doom | 1993 | PC | First major LAN co-op campaign on PC |
| Diablo | 1996 | PC | Online co-op dungeon crawl, Battle.net template |
| StarCraft | 1998 | PC | LAN/online co-op RTS, shaped PC online gaming |

### FPS / Action (2000-2010)

| Title | Year | Platform | Why Landmark |
|-------|------|----------|--------------|
| Halo: Combat Evolved | 2001 | Xbox/PC | Campaign co-op on consoles, split-screen standard |
| Resident Evil 5 | 2009 | PC | AAA co-op campaign with asymmetric resource management |
| Left 4 Dead | 2008 | PC | Gold standard of co-op survival — rescue mechanics |
| Left 4 Dead 2 | 2009 | PC | Perfected L4D formula, still active community |
| Borderlands | 2009 | PC | Defined co-op looter-shooter genre |
| Call of Duty: World at War | 2008 | PC | Introduced Nazi Zombies / horde mode concept |
| Castle Crashers | 2008 | PC | Revived beat 'em up with online co-op, co-op trolling |

### Survival / Sandbox (2009-2015)

| Title | Year | Platform | Why Landmark |
|-------|------|----------|--------------|
| Minecraft | 2011 | PC | Server co-op building, crowdsourced creativity |
| Terraria | 2011 | PC | 2D sandbox co-op, still receives major updates |
| Don't Starve Together | 2013 | PC | Cooperative survival with permadeath |
| Diablo III | 2012 | PC | 4-player co-op ARPG, polished co-op UI |
| Magicka | 2011 | PC | Comedy co-op spellcasting with friendly fire |
| Dungeon Defenders | 2011 | PC | Tower defense + co-op action hybrid |

### Puzzle / Narrative (2010-2018)

| Title | Year | Platform | Why Landmark |
|-------|------|----------|--------------|
| Portal 2 | 2011 | PC | Redefined co-op puzzle design, dual portal mechanics |
| Trine | 2009 | PC | Physics puzzle co-op with complementary classes |
| Brothers: A Tale of Two Sons | 2013 | PC | Story-first co-op design influence |
| A Way Out | 2018 | PC | Narrative co-op, split-screen throughout |
| Overcooked! | 2016 | PC | Local co-op chaos cooking, accessible design |

### Action / RPG (2010-2018)

| Title | Year | Platform | Why Landmark |
|-------|------|----------|--------------|
| Gears of War (series) | 2007+ | Xbox/PC | Campaign + Horde mode co-op standard |
| Borderlands 2 | 2012 | PC | Improved co-op looter-shooter, community benchmark |
| Payday 2 | 2013 | PC | Heist co-op, long-lived community |
| Deep Rock Galactic | 2018 | PC | Class-based teamwork, community darling |
| Monster Hunter: World | 2018 | PC | Co-op hunting with unique join mechanics |
| Warhammer: Vermintide 2 | 2018 | PC | L4D-style melee co-op, still active |

### Titles to prioritize for catalog addition (pre-2018, potentially missing)

Games that appear across multiple "best co-op" lists but may be absent from the current 589-game catalog:
- Gauntlet: Slayer Edition (2014, PC) — modern revival, 4-player
- Trine series (2009/2011/2015) — puzzle co-op series
- Payday 2 (2013) — heist co-op, enormous player base
- Castle Crashers (2008) — beat 'em up classic
- Magicka (2011) — comedy co-op
- Dungeon Defenders (2011) — tower defense co-op
- Brothers: A Tale of Two Sons (2013) — narrative
- Stardew Valley (2016) — farming co-op, crossplay
- Full Metal Furies (2017) — underrated co-op RPG
- Divinity: Original Sin 2 (2017) — co-op CRPG benchmark
- Nex Machina (2017) — arcade co-op shooter

---

## 4. Table Stakes vs Differentiators for Co-op Quality System

### Table Stakes
Features users expect in any co-op catalog. Missing = catalog feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Status |
|---------|--------------|------------|--------|
| `coopMode` field (online/local/split) | Basic filtering need | Low | Done (needs audit) |
| `maxPlayers` accurate | Users plan sessions around this | Low | Done (needs cleanup for values like 65535) |
| Co-op type distinguishable | Is co-op the main mode or optional? | Medium | Missing — this is `coopScore` |
| Correct crossplay data | Cross-platform sessions require this | Low | Done (108 games have it, needs verification) |
| Games actually being co-op | Catalog credibility | High | Needs audit (`_nocoop_flagged.json` exists) |
| Classic/landmark titles present | Users expect well-known titles | Medium | Needs audit |

### Differentiators
Features that set coophubs.net apart from Steam search or other lists.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `coopScore` 1-3 | Only site that rates co-op quality, not game quality | Medium | No current field, needs scoring logic + Python script |
| Classic games flagged | "Hidden gems" and "timeless classics" discovery | Medium | Needs `isClassic` flag or `era` tag |
| Underrated/undiscovered flag | Surfacing games with low CCU but high co-op quality | Medium | Could derive from ccu + rating + coopScore combination |
| Co-op type taxonomy | `campaign`, `horde`, `survival`, `puzzle` as sub-modes | High | Would require new sub-field, significant audit effort |
| Mini-reviews on co-op quality | Context beyond a score — "why is this co-op worth it?" | High | 0/589 have mini-reviews currently |
| Editor-curated playlists | "Best co-op for 2 players", "Relaxed co-op" | Low | Can be done as hub pages without data changes |

### Anti-Features
Explicitly avoid.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| 5-point co-op score (like Co-Optimus) | Too granular for catalog context, hard to assign consistently to 589 games | Use 1-3 scale — faster to assign, clearer for users |
| Automated coopScore from Steam tags | Steam tags are unreliable — documented inconsistency | Manual or semi-manual assignment with Steam API cross-check |
| Co-op sub-types as mandatory field | Requires full catalog re-audit, high maintenance | Optional/progressive enrichment, not blocking |
| Removing games based on coopScore alone | Co-op score 1 doesn't mean "remove from catalog" — some users want marginal co-op | Flag with score, let users filter |
| Large maxPlayers values without cap | 65535, 255 confuse users — Factorio and Terraria have unlimited players | Cap display at "unlimited" above threshold (e.g., >64) |

---

## 5. Fields to Audit and Fix

### Priority 1 — Blocking for v1.1

| Field | Issue | Scope | Action |
|-------|-------|-------|--------|
| `coopScore` | Does not exist | 589 games | Create field, write scoring script, manual review |
| `maxPlayers` suspicious values | 65535 (Factorio), 255 (Terraria, Neverwinter), 70, 100 | 8 games confirmed, ~10 total | Cap or set to meaningful value (e.g., `null` = "unlimited") |
| `coopMode` accuracy | Steam tags are inconsistent; online-only games (300) and local co-op games without steamUrl (150) are unverified | ~450 games | Cross-check against Co-Optimus + Steam store page |
| `rating` = 0 | 186 games have rating=0, likely "not yet released" or "no Steam data" | 186 games | Distinguish "unreleased" from "unrated" — add `releaseStatus` or handle in display |

### Priority 2 — Quality improvement

| Field | Issue | Scope | Action |
|-------|-------|-------|--------|
| `crossplay` | 108 marked true — verify these are real crossplay (not just "available on multiple platforms") | 108 games | Spot-check top 20 by rating, fix outliers |
| `steamUrl` | 187 games missing steamUrl — these can't get affiliate links or Steam data | 187 games | Batch-fill using title search on Steam API |
| `mini_review_it` / `mini_review_en` | 0/589 have reviews | All games | Start with Score 3 games + top classics |
| Classic indicator | No way to surface "timeless" vs "new" | All pre-2015 games | Add `isClassic: true` to landmark titles |

### Priority 3 — Progressive enrichment

| Field | Issue | Scope | Action |
|-------|-------|-------|--------|
| `gbUrl` | Only 4/589 games have GameBillet links | 589 games | Expand GameBillet affiliate coverage |
| Co-op sub-type | No distinction between campaign co-op, horde mode, survival sandbox | All games | Optional field `coopType: ["campaign"|"horde"|"survival"|"puzzle"|"sandbox"]` |
| `description_en` | Not audited for quality | All games | Verify non-empty, sensible for top 50 games by CCU |

---

## 6. Implementation Notes for coopScore

### Recommended approach: semi-automated + manual review

1. **Write Python script** that assigns a preliminary score based on heuristics:
   - Score 3 candidates: games in landmark list above, or with `coopMode` containing multiple modes + `maxPlayers` <= 4
   - Score 1 candidates: `maxPlayers` > 50, single `coopMode: ["online"]`, low CCU (<1000), or in `_nocoop_flagged.json`
   - Score 2: everything else

2. **Manual review pass** on:
   - All Score 3 candidates (~50 games) — confirm each deserves it
   - All Score 1 candidates (~50-80 games) — confirm or escalate to removal
   - Flagged games from `_nocoop_flagged.json`

3. **Display logic**:
   - Score 3: badge "Co-op Core" (highlight color)
   - Score 2: no badge (default, majority of catalog)
   - Score 1: badge "Co-op optional" (neutral, not negative)
   - Filterable: users can exclude Score 1 games

### Heuristic signals for the script

```python
def estimate_coop_score(game):
    score = 2  # default
    
    # Strong signals for Score 3
    coop3_titles = {"Portal 2", "It Takes Two", "A Way Out", "Overcooked!", 
                    "Left 4 Dead 2", "Deep Rock Galactic", "Don't Starve Together",
                    "Split Fiction", "Helldivers 2", ...}
    if game['title'] in coop3_titles:
        return 3
    
    # Structural signals for Score 3
    modes = set(game.get('coopMode', []))
    if len(modes) >= 2 and game.get('maxPlayers', 0) <= 4:
        score = max(score, 3)  # candidate, needs review
    
    # Signals for Score 1
    if game.get('maxPlayers', 0) > 64:  # MMO-scale, co-op is incidental
        score = min(score, 1)
    if modes == {'online'} and game.get('ccu', 0) < 500:
        score = min(score, 1)  # low-activity online-only game
    
    return score
```

---

## Sources

- [Co-Optimus Review Score Explanation](https://www.co-optimus.com/review-scores.php) — Rating scale reference (MEDIUM confidence — 403 on direct fetch, extracted from search snippet)
- [58 Best Co-Op Games of All Time — Gameranx](https://gameranx.com/features/id/292975/article/30-best-co-op-games-of-all-time/) — Community-validated list (MEDIUM confidence)
- [PCGamesN Best Co-op Games 2026](https://www.pcgamesn.com/best-co-op-games) — Current editorial list (HIGH confidence)
- [Co-op Games That Shaped Modern Gaming — DualShockers](https://www.dualshockers.com/co-op-games-that-shaped-modern-gaming-more-than-players-realized/) — Historical landmark analysis (HIGH confidence)
- [Cooperative Video Game — Wikipedia](https://en.wikipedia.org/wiki/Cooperative_video_game) — Genre taxonomy and history (HIGH confidence)
- [5 Problems with Co-op Game Design — Game Developer](https://www.gamedeveloper.com/design/5-problems-with-co-op-game-design-and-possible-solutions-) — Design quality signals (MEDIUM confidence)
- [Steam Co-op Tag Discussion](https://steamcommunity.com/discussions/forum/10/412449508292033203/) — Tag reliability analysis (HIGH confidence for the problem, community source)
- [Co-op Games from Every Console Generation — DualShockers](https://www.dualshockers.com/best-co-op-games-from-every-console-generation/) — Era-based landmark list (MEDIUM confidence)
- Catalog analysis: internal data from `data/catalog.public.v1.json` — field completeness stats (HIGH confidence)

---

## Feature Dependencies

```
coopScore field → requires: catalog audit pass (coopMode accuracy first)
classic game discovery → requires: coopScore (Score 3 games + isClassic flag)
mini-reviews → requires: coopScore (review Score 3 games first)
steamUrl backfill → enables: affiliate links + data enrichment for 187 games
maxPlayers cleanup → required for: coopScore heuristics to work correctly
```

## MVP Recommendation for v1.1

Prioritize in this order:
1. **maxPlayers cleanup** (8 known bad values, fast fix, unblocks coopScore heuristics)
2. **coopScore field + Python scoring script** (core of the milestone)
3. **Manual review pass** on Score 3 + Score 1 candidates (~100 games total)
4. **Classic games audit** — check which landmark titles from the list above are missing from the 589
5. **rating=0 handling** — display "Unreleased" badge rather than showing "0" as a score

Defer:
- co-op sub-type field (high effort, low immediate user value)
- Full mini-review coverage (progressive, start with top 20 classics)
- steamUrl backfill for 187 games (separate pipeline task)
