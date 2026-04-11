#!/usr/bin/env python3
"""
Discover classic co-op games not in the current catalog.

Queries IGDB for classic co-op games (pre-2020, with multiplayer_modes),
deduplicates against existing catalog, outputs candidates for manual review.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

import catalog_data
import catalog_config
import igdb_catalog_source


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CANDIDATES_PATH = DATA_DIR / "classic_candidates.json"

IGDB_PC_PLATFORM = 6
CLASSIC_CUTOFF_EPOCH = 1609459200  # 2021-01-01


def extract_steam_appid(url: str) -> str | None:
    """Extract appid from Steam URL."""
    import re

    match = re.search(r"/app/(\d+)", url or "")
    return match.group(1) if match else None


def main() -> int:
    print("Loading catalog for deduplication...")
    games = catalog_data.load_games()

    existing_titles = {g["title"].lower().strip() for g in games}
    existing_igdb_ids = {g.get("igdbId") for g in games if g.get("igdbId")}
    existing_steam_appids = {
        extract_steam_appid(g.get("steamUrl", "")) for g in games if g.get("steamUrl")
    }
    existing_steam_appids.discard(None)
    existing_steam_appids.discard("")

    print(f"  Existing titles: {len(existing_titles)}")
    print(f"  Existing igdbIds: {len(existing_igdb_ids)}")
    print(f"  Existing steamAppIds: {len(existing_steam_appids)}")

    print("\nInitializing IGDB source...")
    client_id = os.environ.get("IGDB_CLIENT_ID")
    client_secret = os.environ.get("IGDB_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: IGDB credentials not found in environment")
        return 1

    igdb = igdb_catalog_source.IgdbCatalogSource(client_id, client_secret)
    try:
        _ = igdb.token
        print("  IGDB authenticated")
    except Exception as e:
        print(f"ERROR: IGDB auth failed: {e}")
        return 1

    print("\nQuerying IGDB for classic co-op games...")
    query = (
        "fields id, name, first_release_date, rating, rating_count, "
        "game_modes, multiplayer_modes, genres, platforms, "
        "external_games.uid, external_games.category; "
        f"where first_release_date < {CLASSIC_CUTOFF_EPOCH} "
        "& multiplayer_modes != null "
        "& rating > 55 "
        "& rating_count > 10 "
        f"& platforms = ({IGDB_PC_PLATFORM}); "
        "sort rating desc; "
        "limit 100;"
    )

    results = igdb._post("games", query)
    if not results:
        print("ERROR: No results from IGDB")
        return 1

    print(f"  Found {len(results)} games from IGDB")

    candidates = []
    for item in results:
        title = item.get("name", "").strip()
        if not title:
            continue

        igdb_id = item.get("id")

        if igdb_id in existing_igdb_ids:
            continue

        title_lower = title.lower()
        if title_lower in existing_titles:
            continue

        steam_appid = None
        for ext in item.get("external_games", []):
            if ext.get("category") == 1:  # Steam
                uid = str(ext.get("uid", ""))
                if uid.isdigit():
                    steam_appid = uid
                    if steam_appid in existing_steam_appids:
                        break

        if steam_appid and steam_appid in existing_steam_appids:
            continue

        first_release = item.get("first_release_date", 0)
        release_year = None
        if first_release:
            import datetime as dt

            release_year = dt.datetime.fromtimestamp(
                first_release, tz=dt.timezone.utc
            ).year

        rating = item.get("rating", 0)

        genres = []
        for genre_id in item.get("genres", []) or []:
            genres.append(str(genre_id))

        multiplayer_modes = item.get("multiplayer_modes") or []
        coop_modes = []
        has_online = False
        has_offline = False
        has_split = False
        max_players = 0

        for mode in multiplayer_modes:
            if not isinstance(mode, dict):
                continue
            if mode.get("onlinecoop"):
                has_online = True
                max_players = max(max_players, mode.get("onlinecoopmax", 0))
            if mode.get("offlinecoop"):
                has_offline = True
                max_players = max(max_players, mode.get("offlinecoopmax", 0))
            if mode.get("splitscreen"):
                has_split = True

        if has_online or has_offline or has_split:
            if has_online:
                coop_modes.append("online")
            if has_offline or has_split:
                coop_modes.append("local")
            if has_split:
                coop_modes.append("sofa")

        if not coop_modes:
            coop_modes = ["online"]

        if max_players < 2:
            max_players = 4

        year_str = f"{release_year}" if release_year else "unknown"
        rating_str = f"{rating}%" if rating else "N/A"

        reason = f"Classic co-op, rating {rating_str}, released {year_str}"

        candidate = {
            "title": title,
            "igdbId": igdb_id,
            "first_release_date": first_release,
            "release_year": release_year,
            "rating": rating,
            "genres": genres,
            "coopMode": coop_modes,
            "maxPlayers": max_players,
            "steamAppId": steam_appid,
            "steamUrl": f"https://store.steampowered.com/app/{steam_appid}/"
            if steam_appid
            else "",
            "reason": reason,
        }

        candidates.append(candidate)

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stats": {
            "igdb_results": len(results),
            "candidates": len(candidates),
        },
        "candidates": candidates,
    }

    DATA_DIR.mkdir(exist_ok=True)
    CANDIDATES_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"\nDiscovery complete!")
    print(f"  IGDB results: {report['stats']['igdb_results']}")
    print(f"  Candidates: {report['stats']['candidates']}")
    print(f"\nCandidates written to: {CANDIDATES_PATH}")

    if candidates:
        print("\n=== Sample Candidates (first 10) ===")
        for c in candidates[:10]:
            print(f"  - {c['title']} ({c.get('release_year', '?')}): {c['reason']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
