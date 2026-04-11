#!/usr/bin/env python3
"""
Generate coopScore candidates based on audit report data.

This script reads data/coop_audit_report.json and assigns coopScore 1-3:
- 3 = Co-op Core (co-op is the central design pillar)
- 2 = Co-op Solid (co-op is a main mode but not the only purpose)
- 1 = Co-op Marginale (co-op exists but is secondary/limited)
- null = No API data to score on

Output: data/coop_score_candidates.json for human review.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import catalog_data


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CANDIDATES_PATH = DATA_DIR / "coop_score_candidates.json"


def calculate_coop_score(
    steam_categories: list,
    igdb_modes: dict | None,
    title: str,
    passed: bool,
) -> tuple[int | None, str, dict]:
    """
    Calculate coopScore based on audit report data.

    Returns: (score, reason, signals)
    """
    signals = {}

    steam_cat_ids = set(steam_categories)
    signals["steam_categories"] = list(steam_cat_ids)

    has_steam_coop = bool(steam_cat_ids & {9, 38, 39, 24, 48, 44})
    signals["steam_coop"] = has_steam_coop

    igdb_online = False
    igdb_offline = False
    igdb_split = False
    igdb_max = 0

    if igdb_modes:
        igdb_online = igdb_modes.get("onlinecoop", False)
        igdb_offline = igdb_modes.get("offlinecoop", False)
        igdb_split = igdb_modes.get("splitscreen", False)
        igdb_max = igdb_modes.get("maxPlayers", 0)
        signals["igdb_onlinecoop"] = igdb_online
        signals["igdb_offlinecoop"] = igdb_offline
        signals["igdb_splitscreen"] = igdb_split
        signals["igdb_max_players"] = igdb_max

    title_lower = title.lower()
    coop_keywords = [
        "co-op",
        "co op",
        "coop",
        "together",
        "duo",
        "multiplayer",
        "versus",
    ]
    has_coop_brand = any(kw in title_lower for kw in coop_keywords)
    has_pvp_brand = any(
        kw in title_lower for kw in ["versus", "pvp", "battle", "arena", "competitive"]
    )
    signals["coop_brand"] = has_coop_brand
    signals["pvp_brand"] = has_pvp_brand

    if not steam_categories and not igdb_modes:
        return None, "No API data available", signals

    if (igdb_online and igdb_max >= 2) or (igdb_split and igdb_offline):
        return (
            3,
            "IGDB onlinecoop=True with max>=2 or splitscreen with offline",
            signals,
        )

    if has_steam_coop and has_coop_brand and not has_pvp_brand:
        return 3, "Steam co-op + co-op branding (not PvP)", signals

    if passed and has_steam_coop:
        return 2, "Passed audit with Steam co-op categories", signals

    if (igdb_online or igdb_offline) and igdb_max >= 2:
        return 2, "IGDB multiplayer modes with max>=2", signals

    if has_steam_coop:
        return 2, "Steam co-op category present", signals

    if has_steam_coop and not igdb_modes:
        return 1, "Steam co-op but no IGDB data", signals

    return None, "Insufficient data for scoring", signals


def main() -> int:
    print("Loading catalog...")
    games = catalog_data.load_games()
    games_by_id = {g["id"]: g for g in games}

    audit_report_path = DATA_DIR / "coop_audit_report.json"
    if not audit_report_path.is_file():
        print("ERROR: coop_audit_report.json not found. Run audit_coop_tags.py first.")
        return 1

    print("Loading audit report...")
    with open(audit_report_path, encoding="utf-8") as f:
        audit = json.load(f)

    passed_games = {g["game_id"]: g for g in audit.get("passed", [])}
    tag_mismatch_games = {g["game_id"]: g for g in audit.get("tag_mismatch", [])}
    missing_fields_games = {g["game_id"]: g for g in audit.get("missing_fields", [])}
    suspect_coop_games = {g["game_id"]: g for g in audit.get("suspect_coop", [])}

    all_audited = {
        **passed_games,
        **tag_mismatch_games,
        **missing_fields_games,
        **suspect_coop_games,
    }

    games_to_score = [
        g for g in games if g.get("steamUrl") or ((g.get("igdbId") or 0) > 0)
    ]
    print(f"Scoring {len(games_to_score)} games with identifiers...")

    candidates = []
    score_counts = {1: 0, 2: 0, 3: 0, None: 0}

    for i, game in enumerate(games_to_score):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/{len(games_to_score)}")

        game_id = game["id"]
        title = game.get("title", "")

        audit_entry = all_audited.get(game_id, {})
        steam_categories = audit_entry.get("steam_categories", [])
        igdb_modes = audit_entry.get("igdb_modes")

        is_passed = game_id in passed_games
        is_suspect = game_id in suspect_coop_games

        score, reason, signals = calculate_coop_score(
            steam_categories, igdb_modes, title, is_passed
        )

        if is_suspect and score and score >= 2:
            score = 1
            reason = "Marked suspect_coop - reducing score"

        if score is not None:
            score_counts[score] += 1
        else:
            score_counts[None] += 1

        candidates.append(
            {
                "game_id": game_id,
                "title": title,
                "coopScore": score,
                "reason": reason,
                "signals": signals,
            }
        )

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidates": candidates,
        "stats": {
            "total_candidates": len(candidates),
            "score_3": score_counts[3],
            "score_2": score_counts[2],
            "score_1": score_counts[1],
            "null": score_counts[None],
        },
    }

    DATA_DIR.mkdir(exist_ok=True)
    CANDIDATES_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"\nScoring complete!")
    print(f"  Total candidates: {report['stats']['total_candidates']}")
    print(f"  Score 3 (Co-op Core): {report['stats']['score_3']}")
    print(f"  Score 2 (Co-op Solid): {report['stats']['score_2']}")
    print(f"  Score 1 (Co-op Marginale): {report['stats']['score_1']}")
    print(f"  Null (no data): {report['stats']['null']}")
    print(f"\nCandidates written to: {CANDIDATES_PATH}")

    print("\n=== Calibration Sample ===")
    print("Review these games to calibrate scoring logic:")

    sample_size = 5
    for score_val in [3, 2, 1]:
        games_with_score = [c for c in candidates if c.get("coopScore") == score_val]
        sample = games_with_score[:sample_size]
        print(f"\nScore {score_val} ({len(games_with_score)} total):")
        for c in sample:
            print(f"  - {c['title']}: {c['reason']}")

    null_games = [c for c in candidates if c.get("coopScore") is None]
    if null_games:
        print(f"\nNull ({len(null_games)} total):")
        for c in null_games[:sample_size]:
            print(f"  - {c['title']}: {c['reason']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
