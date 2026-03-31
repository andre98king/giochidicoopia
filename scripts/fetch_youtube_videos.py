#!/usr/bin/env python3
"""
fetch_youtube_videos.py
=======================
Aggiorna il campo youtubeVideos per ogni gioco nel catalogo.
Cerca video YouTube con query "game title coop" o simili.

Utilizzo:
    python3 scripts/fetch_youtube_videos.py
    # Richiede YOUTUBE_API_KEY in .env o variabile d'ambiente

Output:
    Aggiorna youtubeVideos in games.js per ogni gioco trovato
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog_data

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

CONCURRENCY = 10
TIMEOUT = 15.0
DELAY = 0.2


def _youtube_search(client: httpx.Client, query: str, max_results: int = 5) -> int:
    """Restituisce il numero di video trovati per la query."""
    if not YOUTUBE_API_KEY:
        return 0

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "order": "relevance",
    }

    try:
        resp = client.get(YOUTUBE_SEARCH_URL, params=params, timeout=TIMEOUT)
        if resp.status_code == 403:
            print("  ⚠️  YouTube API quota esaurita")
            return 0
        if resp.status_code != 200:
            return 0
        data = resp.json()
        return len(data.get("items", []))
    except Exception:
        return 0


def _build_search_queries(title: str) -> list[str]:
    """Costruisce query di ricerca per il gioco."""
    queries = [
        f"{title} coop multiplayer",
        f"{title} co-op gameplay",
        f"{title} coop review",
    ]
    return queries


async def main():
    if not YOUTUBE_API_KEY:
        print("❌ YOUTUBE_API_KEY mancante. Aggiungila a .env")
        print("   Crea una key su: https://console.cloud.google.com/")
        return

    games = catalog_data.load_games()
    print(f"🔍 YouTube video search per {len(games)} giochi...")

    updated = 0
    start = time.time()

    async with httpx.AsyncClient() as client:
        for i, game in enumerate(games, 1):
            title = game.get("title", "")
            if not title:
                continue

            queries = _build_search_queries(title)
            max_videos = 0

            for query in queries:
                count = _youtube_search(client, query)
                max_videos = max(max_videos, count)
                time.sleep(DELAY)

            if max_videos > 0:
                game["youtubeVideos"] = max_videos
                updated += 1
                print(f"  ✓ [{i}/{len(games)}] {title[:30]}: {max_videos} video")

            if i % 50 == 0:
                elapsed = time.time() - start
                print(f"  Progresso: {i}/{len(games)} — {elapsed:.0f}s")

    elapsed = time.time() - start
    print(f"\n✅ Aggiornati: {updated}/{len(games)} giochi")
    print(f"⏱  Tempo totale: {elapsed:.0f}s")

    if updated > 0:
        catalog_data.write_legacy_games_js(games, None)
        print("💾 games.js aggiornato")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
