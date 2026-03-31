#!/usr/bin/env python3
"""
fetch_gmg_prices.py
===================
Aggiorna gmgUrl/gmgDiscount via Green Man Gaming (Impact.com).

Link affiliato: https://greenmangaming.sjv.io/qWzoQy
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog_data

GMG_AFFILIATE_BASE = "https://greenmangaming.sjv.io/qWzoQy"
GMG_SEARCH_URL = "https://www.greenmangaming.com/search/?q="


def _build_gmg_url(title: str) -> tuple[str, int]:
    """
    Genera URL GMG con tracking Impact.
    Format: https://greenmangaming.sjv.io/qWzoQy?url=<product_url>
    """
    # Clean title per search
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)

    # Build product URL
    product_url = f"https://www.greenmangaming.com/en/games/{slug}/"

    # Add affiliate tracking
    # Impact usa il parametro 'url' per deep linking
    url = f"{GMG_AFFILIATE_BASE}?url={quote(product_url)}"

    # GMG non espone sconti - use default 5%
    return url, 5


def run():
    games = catalog_data.load_games()
    targets = [g for g in games if g.get("steamUrl")]
    print(f"🔍 Genero link GMG per {len(targets)} giochi...")

    found = 0

    for i, game in enumerate(targets, 1):
        gmg_url, gmg_disc = _build_gmg_url(game["title"])

        for g in games:
            if g["id"] == game["id"]:
                g["gmgUrl"] = gmg_url
                g["gmgDiscount"] = gmg_disc
                if gmg_url:
                    found += 1
                print(
                    f"  ✓ [{i}/{len(targets)}] {game['title'][:30]}: {'OK' if gmg_url else '—'}"
                )
                break

        if i % 100 == 0:
            print(f"  Progresso: {i}/{len(targets)}")

    print(f"\n✅ GMG: {found}/{len(targets)}")
    catalog_data.write_legacy_games_js(games, None)
    print("💾 games.js aggiornato")


if __name__ == "__main__":
    run()
