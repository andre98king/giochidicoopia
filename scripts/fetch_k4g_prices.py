#!/usr/bin/env python3
"""
fetch_k4g_prices.py
===================
Aggiorna k4gUrl/k4gDiscount via K4G direct affiliate program.

Link affiliato: https://k4g.com?r=coophubs

K4G supporta DirectLinks - il tracking funziona tramite HTTP_REFERER.
Per ora usa parametro ?r=coophubs nei link.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog_data

K4G_AFFILIATE_REF = "coophubs"
K4G_BASE_URL = "https://k4g.com"
K4G_PRODUCT_URL = "https://k4g.com/product/"


def _build_k4g_url(title: str) -> tuple[str, int]:
    """
    Genera URL K4G basandosi sul nome del gioco.
    K4G usa URL: k4g.com/product/{game-name}

    Link format: https://k4g.com/product/{slug}?r=coophubs
    """
    # Clean title per URL slug
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = slug[:50]  # limit slug length

    # Prova diverse varianti
    variants = [
        f"{slug}-pc-steam-key",
        f"{slug}-pc-steam",
        f"{slug}-pc",
        slug,
    ]

    for variant in variants:
        url = f"{K4G_PRODUCT_URL}{variant}?r={K4G_AFFILIATE_REF}"
        # Sconto default 10% (K4G non espone sconti)
        return url, 10

    return "", 0


def run():
    games = catalog_data.load_games()
    targets = [g for g in games if g.get("steamUrl")]
    print(f"🔍 Genero link K4G per {len(targets)} giochi...")

    found = 0

    for i, game in enumerate(targets, 1):
        k4g_url, k4g_disc = _build_k4g_url(game["title"])

        for g in games:
            if g["id"] == game["id"]:
                g["k4gUrl"] = k4g_url
                g["k4gDiscount"] = k4g_disc
                if k4g_url:
                    found += 1
                print(
                    f"  ✓ [{i}/{len(targets)}] {game['title'][:30]}: {'OK' if k4g_url else '—'}"
                )
                break

        if i % 100 == 0:
            print(f"  Progresso: {i}/{len(targets)}")

    print(f"\n✅ K4G: {found}/{len(targets)}")
    catalog_data.write_legacy_games_js(games, None)
    print("💾 games.js aggiornato")


if __name__ == "__main__":
    run()
