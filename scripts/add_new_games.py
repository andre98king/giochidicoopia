#!/usr/bin/env python3
"""
Add new co-op games from cross-reference data to catalog.

Reads data/coop_games_to_add.json and prepares entries for adding.
Requires manual review before applying.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES_JS = ROOT / "assets" / "games.js"
DATA_DIR = ROOT / "data"


def load_new_games():
    """Load games to add."""
    with open(DATA_DIR / "coop_games_to_add.json") as f:
        return json.load(f)


def get_max_id():
    """Get max game ID from catalog."""
    with open(GAMES_JS) as f:
        content = f.read()
    ids = re.findall(r"id:\s*(\d+)", content)
    return max(int(i) for i in ids)


def parse_coop_tags(tags_str_list):
    """Parse Steam tags to determine coopMode."""
    tags = " ".join(tags_str_list).lower()

    modes = []
    if "online co-op" in tags:
        modes.append("online")
    if "local co-op" in tags or "local multiplayer" in tags:
        modes.append("local")
    if "couch" in tags:
        modes.append("sofa")

    return modes if modes else ["online"]


def estimate_max_players(tags_str_list):
    """Estimate max players from tags."""
    tags = " ".join(tags_str_list).lower()

    if "4" in tags:
        return 4
    elif "co-op" in tags and "2" in tags:
        return 2
    elif "multiplayer" in tags:
        return 4

    return 2  # default


def create_game_entries(games, start_id):
    """Create game entries with proper structure."""
    entries = []

    for i, g in enumerate(games):
        # Parse coop tags
        tags = g.get("coop_tags", [])
        coop_modes = parse_coop_tags(tags)
        max_players = estimate_max_players(tags)

        entry = {
            "id": start_id + i + 1,
            "igdbId": 0,  # Will need to look up
            "title": g["title"],
            "categories": ["action"],  # Default
            "genres": [],
            "coopMode": coop_modes,
            "maxPlayers": max_players,
            "crossplay": False,
            "players": f"1-{max_players}",
            "releaseYear": 2024,  # Default - needs review
            "image": "",  # Will need to get from Steam
            "description": "",  # Needs manual input
            "description_en": "",
            "personalNote": f"Added from Steam (app_id: {g['app_id']}) - needs review",
            "played": False,
            "steamUrl": g.get("steam_url", ""),
            "gogUrl": "",
            "epicUrl": "",
            "itchUrl": "",
            "igdbUrl": "",
            "rating": 0,
            "ccu": 0,
            "trending": False,
            "coopScore": 2,  # Default - based on having co-op tags
            "mini_review_it": "",
            "mini_review_en": "",
            "igUrl": "",
            "igDiscount": 0,
            "gbUrl": "",
            "gbDiscount": 0,
        }

        entries.append(entry)

    return entries


def main():
    print("=== Preparing New Games for Catalog ===")
    print()

    # Load games to add
    games = load_new_games()
    print(f"Loaded {len(games)} games to add")

    # Get max ID
    max_id = get_max_id()
    print(f"Current max ID: {max_id}")

    # Create entries
    entries = create_game_entries(games, max_id)

    print(f"\n=== Created {len(entries)} entries ===")
    for e in entries:
        print(f"  ID {e['id']}: {e['title'][:35]}")
        print(f"    coopMode: {e['coopMode']}, maxPlayers: {e['maxPlayers']}")
        print(f"    steamUrl: {e['steamUrl'][:50]}...")

    # Save for review
    output = DATA_DIR / "new_games_entries.json"
    with open(output, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"\nSaved to {output}")
    print("\nReview and manually adjust before applying!")


if __name__ == "__main__":
    main()
