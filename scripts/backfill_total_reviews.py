#!/usr/bin/env python3
"""
Backfill totalReviews for all games in catalog using SteamSpy API.
One-off script to fix missing totalReviews field.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import catalog_data
from steam_catalog_source import SteamCatalogSource, appid_from_url, calc_rating

steam = SteamCatalogSource(delay=0.3)

games = catalog_data.load_games()
print(f"Loaded {len(games)} games")

updated = 0
for g in games:
    aid = appid_from_url(g.get("steamUrl", ""))
    if not aid:
        continue
    spy = steam.fetch_json(f"https://steamspy.com/api.php?request=appdetails&appid={aid}")
    if not spy:
        continue
    pos = spy.get("positive", 0) or 0
    neg = spy.get("negative", 0) or 0
    total = pos + neg
    if total > 0:
        g["totalReviews"] = total
        # Also update rating if we have better data
        if pos + neg >= 10:
            g["rating"] = calc_rating(pos, neg)
        updated += 1
        if updated % 50 == 0:
            print(f"  ... {updated} updated")

print(f"Updated {updated} games with totalReviews")

# Write back
featured_id = catalog_data.parse_featured_indie_id(
    catalog_data.GAMES_JS.read_text(encoding="utf-8")
)
catalog_data.write_legacy_games_js(games, featured_id)
catalog_data.write_catalog_artifact(games)
catalog_data.write_public_catalog_export(games)
print("✅ Done")
