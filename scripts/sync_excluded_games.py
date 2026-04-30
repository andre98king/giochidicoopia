#!/usr/bin/env python3
"""
sync_excluded_games.py
======================
Rimuove dal catalogo tutti i giochi il cui Steam appid è in data/excluded_games.json.
Questo script viene eseguito automaticamente dal workflow CI dopo il curation gate.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog_data import load_games, write_legacy_games_js

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_PATH = ROOT / "data" / "excluded_games.json"


def main():
    games = load_games()
    original_count = len(games)

    if not EXCLUDED_PATH.exists():
        print("No excluded_games.json found, nothing to remove")
        return

    excluded_appids = set(json.loads(EXCLUDED_PATH.read_text(encoding="utf-8")))
    print(f"Excluded appids in blocklist: {len(excluded_appids)}")

    # Build lookup: appid -> game
    def appid_from_url(url: str) -> str | None:
        import re
        m = re.search(r"/app/(\d+)", url or "")
        return m.group(1) if m else None

    to_remove = []
    for g in games:
        appid = appid_from_url(g.get("steamUrl", ""))
        if appid and appid in excluded_appids:
            to_remove.append((g["id"], g["title"], appid))

    if not to_remove:
        print("No blocked games found in current catalog")
        return

    print(f"\nRemoving {len(to_remove)} blocked games from catalog:")
    removed_ids = set()
    for gid, title, appid in to_remove:
        print(f"  - [{gid}] {title} (appid={appid})")
        removed_ids.add(gid)

    # Filter out removed games
    games = [g for g in games if g["id"] not in removed_ids]

    write_legacy_games_js(games)
    print(f"\nCatalog updated: {original_count} → {len(games)} games")
    print(f"  Saved to assets/bundles/games-data.js + assets/games.js")


if __name__ == "__main__":
    main()
