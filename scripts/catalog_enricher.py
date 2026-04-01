#!/usr/bin/env python3
"""
Catalog Enricher — fetches full game data from Steam + SteamSpy + RAWG.

Given a Steam app ID, returns a complete, catalog-ready game entry:
- Steam: name, description_en, header_image, releaseYear, categories
- SteamSpy: rating (positive/negative reviews), ccu
- RAWG: Italian description (if available), additional metadata

Usage:
    from catalog_enricher import enrich
    entry = enrich("230230", rawg_api_key="...", game_id=42)
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any


def _fetch_json(url: str, timeout: int = 12) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "coophubs-enricher/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _clean_text(text: str, max_len: int = 320) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    import html
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def fetch_steam_details(app_id: str) -> dict[str, Any]:
    """Fetch full Steam app details (EN)."""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=english&cc=us"
    data = _fetch_json(url)
    if not data:
        return {}
    info = data.get(str(app_id), {})
    if not info.get("success"):
        return {}
    return info.get("data", {})


def fetch_steamspy_stats(app_id: str) -> dict[str, Any]:
    """Fetch review counts and CCU from SteamSpy."""
    url = f"https://steamspy.com/api.php?request=appdetails&appid={app_id}"
    return _fetch_json(url) or {}


def fetch_rawg_description(game_name: str, api_key: str) -> str:
    """Try to find an Italian description from RAWG (falls back to EN description_raw)."""
    query = urllib.parse.quote(game_name)
    url = f"https://api.rawg.io/api/games?key={api_key}&search={query}&page_size=3"
    data = _fetch_json(url)
    if not data:
        return ""
    results = data.get("results", [])
    if not results:
        return ""
    # Get details for the first (best) match
    game_id = results[0].get("id")
    if not game_id:
        return ""
    detail_url = f"https://api.rawg.io/api/games/{game_id}?key={api_key}"
    details = _fetch_json(detail_url) or {}
    desc = _clean_text(details.get("description_raw", ""), max_len=300)
    return desc


def calc_rating(positive: int, negative: int) -> int:
    total = (positive or 0) + (negative or 0)
    if total < 10:
        return 0
    return round((positive or 0) / total * 100)


def parse_release_year(release_date: dict | None) -> int:
    if not release_date or release_date.get("coming_soon"):
        return 0
    date_str = release_date.get("date", "")
    match = re.search(r"\b((?:19|20)\d{2})\b", date_str)
    return int(match.group(1)) if match else 0


def enrich(
    app_id: str,
    game_id: int,
    rawg_api_key: str | None = None,
    coop_modes: list[str] | None = None,
    coop_score_hint: int | None = None,
    rate_limit_delay: float = 1.5,
) -> dict[str, Any] | None:
    """
    Build a complete games.js entry for a Steam game.

    Returns None if Steam data is unavailable.
    """
    steam = fetch_steam_details(app_id)
    if not steam:
        return None

    time.sleep(rate_limit_delay)
    spy = fetch_steamspy_stats(app_id)

    positive = spy.get("positive", 0) or 0
    negative = spy.get("negative", 0) or 0
    rating = calc_rating(positive, negative)
    ccu = spy.get("ccu", 0) or 0

    name = steam.get("name", "")
    desc_en = _clean_text(steam.get("short_description", ""))
    if not desc_en or len(desc_en) < 25:
        desc_en = _clean_text(steam.get("detailed_description", ""))

    image = steam.get("header_image", "")
    release_year = parse_release_year(steam.get("release_date"))

    # Italian description: try RAWG if key provided, otherwise same as EN
    desc_it = ""
    if rawg_api_key and name:
        time.sleep(rate_limit_delay)
        desc_it = fetch_rawg_description(name, rawg_api_key)

    # Categories → genres
    cats = steam.get("categories", [])
    genres_raw = steam.get("genres", [])
    genre_names_map = {
        "Action": "action", "Adventure": "adventure", "RPG": "rpg",
        "Strategy": "strategy", "Simulation": "simulation", "Puzzle": "puzzle",
        "Sports": "sports", "Racing": "racing", "Horror": "horror",
        "Shooter": "shooter", "Platformer": "platformer", "Fighting": "fighting",
    }
    genres = []
    for g in genres_raw:
        desc_g = g.get("description", "")
        mapped = genre_names_map.get(desc_g)
        if mapped and mapped not in genres:
            genres.append(mapped)

    # Free-to-play
    is_free = steam.get("is_free", False)
    categories = ["free"] if is_free else ["action"]
    if not genres:
        genres = list(categories)

    # maxPlayers from categories
    cat_descs = [c.get("description", "").lower() for c in cats]
    max_players = 4
    if any("2" in d for d in cat_descs):
        max_players = 2

    effective_coop = coop_modes or ["online"]

    return {
        "id": game_id,
        "igdbId": 0,
        "title": name,
        "categories": categories,
        "genres": genres,
        "coopMode": effective_coop,
        "maxPlayers": max_players,
        "crossplay": False,
        "players": f"1-{max_players}",
        "releaseYear": release_year,
        "image": image,
        "description": desc_it,
        "description_en": desc_en,
        "personalNote": "",
        "played": False,
        "steamUrl": f"https://store.steampowered.com/app/{app_id}/",
        "gogUrl": "",
        "epicUrl": "",
        "itchUrl": "",
        "ccu": ccu,
        "trending": ccu >= 500,
        "rating": rating,
        "igUrl": "",
        "igDiscount": 0,
        "gbUrl": "",
        "gbDiscount": 0,
        "gsUrl": "",
        "gsDiscount": 0,
        "kgUrl": "",
        "kgDiscount": 0,
        "k4gUrl": "",
        "k4gDiscount": 0,
        "gmvUrl": "",
        "gmvDiscount": 0,
        "gmgUrl": "",
        "gmgDiscount": 0,
        "coopScore": coop_score_hint,
        "mini_review_it": "",
        "mini_review_en": "",
    }


if __name__ == "__main__":
    import sys
    app_id = sys.argv[1] if len(sys.argv) > 1 else "230230"
    game_id = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    print(f"Enriching app_id={app_id}, game_id={game_id}")
    result = enrich(app_id, game_id)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("ERROR: could not fetch Steam data")
