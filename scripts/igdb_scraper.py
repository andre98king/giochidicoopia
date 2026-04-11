#!/usr/bin/env python3
"""
IGDB API Scraper - Use IGDB to validate and enrich the catalog.

Requires IGDB credentials (already in .env):
- IGDB_CLIENT_ID
- IGDB_CLIENT_SECRET
"""

import os
import requests
import json
from time import sleep


def get_igdb_token(client_id, client_secret):
    """Get IGDB access token."""
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    resp = requests.post(url, data=data)
    return resp.json()["access_token"]


def search_games(token, client_id, query, limit=20):
    """Search games on IGDB."""
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}

    url = "https://api.igdb.com/v4/games"
    # Request: name, genres, game_modes, platforms, first_release_date, mode (coop)
    data = f'fields name,genres,game_modes,platforms,first_release_date,category; search "{query}"; limit {limit};'

    resp = requests.post(url, headers=headers, data=data)
    return resp.json() if resp.status_code == 200 else []


def get_game_details(token, client_id, game_id):
    """Get detailed info for a specific game."""
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}

    url = "https://api.igdb.com/v4/games"
    data = f"fields name,summary,genres,game_modes,platforms,first_release_date,mode,player_perspective; where id={game_id};"

    resp = requests.post(url, headers=headers, data=data)
    return resp.json()[0] if resp.status_code == 200 and resp.json() else {}


def search_by_steam_id(token, client_id, steam_app_id):
    """Search game by Steam app ID."""
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}

    url = "https://api.igdb.com/v4/games"
    # Search by external identifier (Steam)
    data = f"fields name,genres,game_modes,platforms; where external_ids={steam_app_id}; limit 1;"

    resp = requests.post(url, headers=headers, data=data)
    return resp.json()[0] if resp.status_code == 200 and resp.json() else {}


def main():
    print("=== IGDB API Scraper ===")
    print()

    # Get credentials from .env
    client_id = "crisa3ggg32zf700ycw6um1rdp7fc3"
    client_secret = "rrszo3z0gntuf6vu63v7pm0cy94e21"

    # Get token
    print("Getting IGDB access token...")
    token = get_igdb_token(client_id, client_secret)
    print(f"Token: {token[:20]}...")
    print()

    # Test search
    print("Testing search for 'coop'...")
    games = search_games(token, client_id, "coop", limit=30)
    print(f"Found {len(games)} games")

    for g in games[:10]:
        name = g.get("name", "N/A")
        modes = g.get("game_modes", [])
        print(f"  - {name[:40]} (modes: {modes})")

    # Save results
    with open("data/igdb_coop_games.json", "w") as f:
        json.dump(games, f, indent=2)
    print(f"\nSaved to data/igdb_coop_games.json")


if __name__ == "__main__":
    main()
