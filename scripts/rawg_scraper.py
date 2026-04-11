#!/usr/bin/env python3
"""
RAWG API Comprehensive Scraper - Gather more game data.
"""

import os
import requests
import json
import time
from difflib import SequenceMatcher


def load_env():
    """Load API key from .env"""
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("RAWG_API_KEY="):
                return line.split("=")[1].strip()
    return None


def search_games(api_key, query, page=1, page_size=20):
    """Search games on RAWG."""
    url = "https://api.rawg.io/api/games"
    params = {
        "key": api_key,
        "search": query,
        "page": page,
        "page_size": page_size,
    }

    resp = requests.get(url, params=params)
    return resp.json() if resp.status_code == 200 else {}


def get_game_details(api_key, game_id):
    """Get detailed info for a game."""
    url = f"https://api.rawg.io/api/games/{game_id}"
    params = {"key": api_key}

    resp = requests.get(url, params=params)
    return resp.json() if resp.status_code == 200 else {}


def gather_multi_search(api_key, searches, max_pages=2):
    """Gather games from multiple search terms."""
    all_games = {}

    print(f"Gathering from {len(searches)} search terms...")

    for term in searches:
        print(f'  Searching "{term}"...', end=" ")

        for page in range(1, max_pages + 1):
            result = search_games(api_key, term, page=page)
            games = result.get("results", [])

            for g in games:
                gid = g.get("id")
                if gid and gid not in all_games:
                    all_games[gid] = g

            time.sleep(0.3)  # Rate limit

        print(f"{len(all_games)} total so far")

    return list(all_games.values())


def main():
    print("=== RAWG Comprehensive Scraper ===")
    print()

    api_key = load_env()
    if not api_key:
        print("ERROR: RAWG_API_KEY not found")
        return

    # Multiple searches to find more co-op games
    searches = [
        "coop",
        "co-op",
        "local coop",
        " couch coop",
        "multiplayer",
        "local multiplayer",
        "split screen",
        "co-op action",
        "co-op rpg",
        "co-op shooter",
    ]

    games = gather_multi_search(api_key, searches, max_pages=2)

    print(f"\nTotal unique games found: {len(games)}")

    # Save raw data
    with open("data/rawg_coop_games.json", "w") as f:
        json.dump(games, f, indent=2)
    print(f"Saved to data/rawg_coop_games.json")

    # Show sample
    print("\nSample games:")
    for g in games[:15]:
        name = g.get("name", "N/A")
        released = g.get("released", "N/A")[:4] if g.get("released") else "N/A"
        platforms = [p["platform"]["name"] for p in g.get("parent_platforms", [])][:3]
        print(f"  {name[:40]} ({released}) - {', '.join(platforms[:2])}")


if __name__ == "__main__":
    main()
