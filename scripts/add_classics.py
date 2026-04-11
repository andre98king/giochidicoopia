#!/usr/bin/env python3
"""
Add approved classic games to the catalog.

Reads data/approved_classics.json and adds games to the catalog:
- Dry-run by default (no --apply flag = no changes)
- Assigns new IDs (max existing + 1)
- Validates required fields before adding
- Writes via catalog_data.write_legacy_games_js()
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import catalog_data


ROOT = Path(__file__).resolve().parent.parent
GAMES_JS = ROOT / "assets" / "games.js"
DATA_DIR = ROOT / "data"
DEFAULT_INPUT = DATA_DIR / "approved_classics.json"


REQUIRED_FIELDS = [
    "title",
    "description",
    "categories",
    "coopMode",
    "maxPlayers",
]


def validate_game(game: dict) -> tuple[bool, str]:
    """Validate that game has all required fields."""
    for field in REQUIRED_FIELDS:
        if field not in game or not game[field]:
            return False, f"Missing required field: {field}"

    if (
        not game.get("steamUrl")
        and not game.get("gogUrl")
        and not game.get("epicUrl")
        and not game.get("itchUrl")
    ):
        if not game.get("personalNote"):
            return False, "No store URL and no note"

    if game.get("coopScore") is None:
        return False, "coopScore must be pre-assigned"

    return True, "ok"


def create_game_entry(approved: dict, new_id: int) -> dict:
    """Create a full game entry from approved data."""
    entry = {
        "id": new_id,
        "igdbId": approved.get("igdbId", 0),
        "title": approved["title"],
        "categories": approved.get("categories", []),
        "genres": approved.get("genres", []),
        "coopMode": approved.get("coopMode", ["online"]),
        "maxPlayers": approved.get("maxPlayers", 4),
        "crossplay": False,
        "players": approved.get("players", "1-4"),
        "releaseYear": approved.get("releaseYear", 0),
        "image": "",
        "description": approved.get("description", ""),
        "description_en": approved.get("description_en", ""),
        "personalNote": approved.get("personalNote", ""),
        "played": False,
        "steamUrl": approved.get("steamUrl", ""),
        "gogUrl": approved.get("gogUrl", ""),
        "epicUrl": approved.get("epicUrl", ""),
        "itchUrl": approved.get("itchUrl", ""),
        "ccu": 0,
        "trending": False,
        "rating": 0,
        "igUrl": "",
        "igDiscount": 0,
        "gbUrl": "",
        "gbDiscount": 0,
        "gsUrl": "",
        "gsDiscount": 0,
        "kgUrl": "",
        "kgDiscount": 0,
        "k4gUrl": "",
        "k4gDiscount": 0,
        "gmvUrl": "",
        "gmvDiscount": 0,
        "gmgUrl": "",
        "gmgDiscount": 0,
        "coopScore": approved.get("coopScore"),
        "mini_review_it": "",
        "mini_review_en": "",
    }

    if (
        not entry["steamUrl"]
        and not entry["gogUrl"]
        and not entry["epicUrl"]
        and not entry["itchUrl"]
    ):
        entry["personalNote"] = (
            entry.get("personalNote", "") + " no active purchase URL"
        )

    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Add approved classics to catalog")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to catalog (default: dry-run)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input file (default: {DEFAULT_INPUT})",
    )
    args = parser.parse_args()

    input_path = args.input
    if not input_path.is_file():
        print(f"ERROR: Input file not found: {input_path}")
        return 1

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    approved = data.get("approved", [])
    if not approved:
        print("ERROR: No approved games in input file")
        return 1

    print(f"Loaded {len(approved)} approved games from {input_path}")

    if args.apply:
        print("APPLY MODE: Games will be added to catalog")
    else:
        print("DRY-RUN MODE: No changes will be made. Use --apply.")

    print("\nLoading catalog...")
    featured_id, games = catalog_data.load_legacy_catalog_bundle()
    max_id = max(g["id"] for g in games)
    print(f"  Current catalog: {len(games)} games, max ID: {max_id}")

    existing_titles = {g["title"].lower().strip() for g in games}
    existing_igdb_ids = {g.get("igdbId") for g in games if g.get("igdbId")}

    new_id = max_id + 1
    to_add = []
    errors = []
    skipped = []

    for approved_game in approved:
        title_lower = approved_game.get("title", "").lower().strip()
        if title_lower in existing_titles:
            skipped.append(
                {"game": approved_game.get("title", "?"), "reason": "duplicate title"}
            )
            continue

        igdb_id = approved_game.get("igdbId", 0)
        if igdb_id and igdb_id in existing_igdb_ids:
            skipped.append(
                {"game": approved_game.get("title", "?"), "reason": "duplicate igdbId"}
            )
            continue

        valid, reason = validate_game(approved_game)
        if not valid:
            errors.append({"game": approved_game.get("title", "?"), "error": reason})
            continue

        game_entry = create_game_entry(approved_game, new_id)
        to_add.append(game_entry)
        existing_titles.add(title_lower)
        new_id += 1

    if skipped:
        print(f"\n{len(skipped)} games skipped (duplicates):")
        for s in skipped:
            print(f"  - {s['game']}: {s['reason']}")

    if errors:
        print(f"\n{len(errors)} games with validation errors:")
        for e in errors:
            print(f"  - {e['game']}: {e['error']}")

    print(f"\nGames to add: {len(to_add)}")
    for g in to_add:
        print(f"  - ID {g['id']}: {g['title']} (coopScore={g['coopScore']})")

    if not args.apply:
        print("\n=== Dry-Run Complete ===")
        print("Use --apply to actually add games to catalog")
        return 0

    games.extend(to_add)

    output_path = catalog_data.write_legacy_games_js(games, featured_id)
    print(f"\nWritten to: {output_path}")

    print("\n=== Add Complete ===")
    print(f"  Added: {len(to_add)} games")
    print(f"  New catalog size: {len(games)} games")
    print(f"  ID range: {max_id + 1} to {new_id - 1}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
