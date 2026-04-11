#!/usr/bin/env python3
"""
Audit co-op tags against Steam and IGDB APIs.

This script is READ-ONLY — it never modifies games.js or any catalog files.
It produces data/coop_audit_report.json with three discrepancy categories:
- tag_mismatch: catalog coopMode doesn't match API data
- missing_fields: maxPlayers/coopMode absent or suspicious defaults
- suspect_coop: game probably not co-op per APIs

Games without steamUrl are listed separately as manual_review_only.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import catalog_data
import catalog_config
import steam_catalog_source
import igdb_catalog_source


STEAM_COOP_CATS = {
    9: "Co-op",
    38: "Online Co-op",
    39: "Shared/Split Screen Co-op",
    24: "Shared/Split Screen",
    48: "LAN Co-op",
    44: "Remote Play Together",
}

STEAM_PVP_CATS = {
    49: "PvP",
    36: "Online PvP",
    37: "Local PvP",
    47: "Shared/Split Screen PvP",
}

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REPORT_PATH = DATA_DIR / "coop_audit_report.json"
PROGRESS_CACHE = DATA_DIR / ".audit_steam_cache.json"


def load_progress_cache() -> dict[str, dict]:
    if PROGRESS_CACHE.is_file():
        try:
            return json.loads(PROGRESS_CACHE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_progress_cache(cache: dict[str, dict]) -> None:
    PROGRESS_CACHE.write_text(json.dumps(cache, indent=2))


def get_verified_coop_appids() -> set[int]:
    """Load VERIFIED_COOP_APPIDS from catalog_config."""
    return getattr(catalog_config, "VERIFIED_COOP_APPIDS", set())


def extract_steam_appid(url: str) -> str | None:
    """Extract appid from Steam URL."""
    import re

    match = re.search(r"/app/(\d+)", url or "")
    return match.group(1) if match else None


def audit_game(
    game: dict[str, Any],
    steam_source: steam_catalog_source.SteamCatalogSource,
    igdb_source: igdb_catalog_source.IgdbCatalogSource | None,
    progress_cache: dict[str, dict],
    verified_appids: set[int],
) -> dict[str, Any]:
    """Audit a single game and return its audit result."""
    game_id = game["id"]
    title = game.get("title", "")
    steam_url = game.get("steamUrl", "")
    igdb_id = game.get("igdbId", 0)

    result = {
        "game_id": game_id,
        "title": title,
        "current_coopMode": game.get("coopMode", []),
        "current_maxPlayers": game.get("maxPlayers", 0),
    }

    has_steam = bool(steam_url)
    has_igdb = bool(igdb_id and igdb_id > 0)

    steam_data = None
    steam_cat_ids = set()
    igdb_modes = None

    if has_steam:
        appid = extract_steam_appid(steam_url)
        if appid:
            if appid in progress_cache:
                steam_data = progress_cache[appid].get("steam_data")
                steam_cat_ids = set(
                    steam_data.get("categories", []) if steam_data else []
                )
            else:
                try:
                    data, _ = steam_source.fetch_steam_desc(appid, "english")
                    steam_data = data
                    if data:
                        steam_cat_ids = {c["id"] for c in data.get("categories", [])}
                        progress_cache[appid] = {"steam_data": data}
                except Exception as e:
                    print(f"    ⚠ Error fetching Steam {appid}: {e}")

    if has_igdb and steam_url:
        appid = extract_steam_appid(steam_url)
        if appid and igdb_source:
            try:
                appid_to_igdb = igdb_source.fetch_appid_to_igdb_id([appid])
                if appid_to_igdb:
                    igdb_id_resolved = appid_to_igdb.get(appid)
                    if igdb_id_resolved:
                        modes_dict = igdb_source.fetch_multiplayer_modes(
                            [igdb_id_resolved]
                        )
                        modes_list = modes_dict.get(igdb_id_resolved, [])
                        igdb_modes = igdb_catalog_source._parse_multiplayer_modes(
                            modes_list
                        )
            except Exception as e:
                print(f"    ⚠ Error fetching IGDB for {appid}: {e}")

    result["steam_categories"] = list(steam_cat_ids) if steam_cat_ids else []
    result["igdb_modes"] = igdb_modes

    has_coop = bool(steam_cat_ids & STEAM_COOP_CATS.keys())
    has_pvp_only = bool(steam_cat_ids & STEAM_PVP_CATS.keys()) and not has_coop

    issues = []

    if has_steam:
        if has_pvp_only and game_id not in verified_appids:
            issues.append("suspect_coop")

        current_modes = set(game.get("coopMode", []))
        steam_has_local = bool(steam_cat_ids & {24, 39, 48})
        steam_has_online = bool(steam_cat_ids & {9, 38, 44})

        if (
            steam_has_local
            and "local" not in current_modes
            and "sofa" not in current_modes
        ):
            issues.append("tag_mismatch")
        if steam_has_online and "online" not in current_modes:
            issues.append("tag_mismatch")

    max_players = game.get("maxPlayers", 0)
    if max_players == 0 or max_players == 4:
        issues.append("missing_fields")

    if not game.get("coopMode"):
        issues.append("missing_fields")

    result["issues"] = list(set(issues))
    result["has_coop"] = has_coop
    result["has_pvp_only"] = has_pvp_only

    return result


def main() -> int:
    print("Loading catalog...")
    games = catalog_data.load_games()

    print("Initializing Steam source...")
    steam_source = steam_catalog_source.SteamCatalogSource(delay=1.5)

    print("Initializing IGDB source...")
    igdb_source = None
    client_id = os.environ.get("IGDB_CLIENT_ID")
    client_secret = os.environ.get("IGDB_CLIENT_SECRET")
    if client_id and client_secret:
        try:
            igdb_source = igdb_catalog_source.IgdbCatalogSource(
                client_id, client_secret
            )
            _ = igdb_source.token
            print("  IGDB authenticated")
        except Exception as e:
            print(f"  ⚠ IGDB auth failed: {e}")
            igdb_source = None
    else:
        print("  ⚠ IGDB credentials not found in environment")

    verified_appids = get_verified_coop_appids()
    print(f"  Verified co-op appids: {len(verified_appids)}")

    progress_cache = load_progress_cache()
    print(f"  Progress cache: {len(progress_cache)} games")

    tag_mismatch = []
    missing_fields = []
    suspect_coop = []
    manual_review_only = []
    passed = []

    steam_games = [g for g in games if g.get("steamUrl")]
    print(f"Auditing {len(steam_games)} games with Steam URL...")

    for i, game in enumerate(steam_games):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(steam_games)}")
            save_progress_cache(progress_cache)

        result = audit_game(
            game, steam_source, igdb_source, progress_cache, verified_appids
        )

        issues = result.get("issues", [])

        entry = {
            "game_id": result["game_id"],
            "title": result["title"],
            "current_coopMode": result["current_coopMode"],
            "current_maxPlayers": result["current_maxPlayers"],
            "steam_categories": result.get("steam_categories", []),
            "igdb_modes": result.get("igdb_modes"),
        }

        if "suspect_coop" in issues:
            entry["reason"] = "Has PvP categories but no co-op categories"
            suspect_coop.append(entry)
        elif "tag_mismatch" in issues:
            entry["reason"] = "coopMode in catalog doesn't match Steam API data"
            tag_mismatch.append(entry)
        elif "missing_fields" in issues:
            entry["reason"] = "maxPlayers or coopMode missing/default"
            missing_fields.append(entry)
        else:
            passed.append(entry)

    for game in games:
        igdb_id = game.get("igdbId") or 0
        if not game.get("steamUrl") and not igdb_id:
            manual_review_only.append(
                {
                    "game_id": game["id"],
                    "title": game.get("title", ""),
                    "reason": "no steamUrl, no igdbId",
                }
            )

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stats": {
            "total_games": len(games),
            "audited_steam": len(steam_games),
            "audited_igdb": len([g for g in games if (g.get("igdbId") or 0) > 0]),
            "manual_review_only": len(manual_review_only),
            "tag_mismatch": len(tag_mismatch),
            "missing_fields": len(missing_fields),
            "suspect_coop": len(suspect_coop),
            "passed": len(passed),
        },
        "tag_mismatch": tag_mismatch,
        "missing_fields": missing_fields,
        "suspect_coop": suspect_coop,
        "manual_review_only": manual_review_only,
        "passed": passed,
    }

    DATA_DIR.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"\nAudit complete!")
    print(f"  Total games: {report['stats']['total_games']}")
    print(f"  Audited (Steam): {report['stats']['audited_steam']}")
    print(f"  Manual review only: {report['stats']['manual_review_only']}")
    print(f"  Tag mismatch: {report['stats']['tag_mismatch']}")
    print(f"  Missing fields: {report['stats']['missing_fields']}")
    print(f"  Suspect co-op: {report['stats']['suspect_coop']}")
    print(f"  Passed: {report['stats']['passed']}")
    print(f"\nReport written to: {REPORT_PATH}")

    save_progress_cache(progress_cache)

    return 0


if __name__ == "__main__":
    sys.exit(main())
