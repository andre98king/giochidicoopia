#!/usr/bin/env python3
"""
Shared catalog loader and canonical artifact exporter.

This keeps `games.js` as the legacy runtime source for the current frontend,
while introducing a normalized, versioned JSON artifact that future pipelines
can consume without re-parsing the site bundle format.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import re
import unicodedata
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
GAMES_JS = ROOT / "games.js"
DATA_DIR = ROOT / "data"
CATALOG_JSON = DATA_DIR / "catalog.games.v1.json"
PUBLIC_CATALOG_JSON = DATA_DIR / "catalog.public.v1.json"
SCHEMA_VERSION = 1


def source_generated_at() -> str:
    return dt.datetime.fromtimestamp(
        GAMES_JS.stat().st_mtime,
        tz=dt.timezone.utc,
    ).replace(microsecond=0).isoformat()


def ef(block: str, field: str):
    match = re.search(
        rf'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|-?\d+)',
        block,
        re.DOTALL,
    )
    if not match:
        return None
    value = match.group(1)
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("["):
        return re.findall(r'"([^"]+)"', value)
    return value.strip('"').replace('\\"', '"')


def unique_preserving(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        text = (value or "").strip().lower()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def slugify(value: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().replace("&", " and ")
    normalized = re.sub(r"[’']", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or fallback


def parse_featured_indie_id(content: str) -> int | None:
    match = re.search(r"const\s+featuredIndieId\s*=\s*(\d+)\s*;", content)
    if not match:
        return None
    return int(match.group(1))


def appid_from_steam_url(url: str) -> str | None:
    match = re.search(r"/app/(\d+)", url or "")
    return match.group(1) if match else None


def epic_slug_from_url(url: str) -> str | None:
    match = re.search(r"/p/([^/?#]+)", url or "")
    return match.group(1) if match else None


def itch_slug_from_url(url: str) -> str | None:
    match = re.search(r"https?://([^/]+/[^/?#]+)", url or "")
    return match.group(1) if match else None


def normalize_game(raw_game: dict[str, Any], featured_indie_id: int | None) -> dict[str, Any]:
    game_id = raw_game["id"]
    title = raw_game["title"]
    categories = unique_preserving(raw_game.get("categories") or [])
    genres = unique_preserving(raw_game.get("genres") or [])
    coop_modes = unique_preserving(raw_game.get("coopMode") or ["online"])
    steam_url = (raw_game.get("steamUrl") or "").strip()
    epic_url = (raw_game.get("epicUrl") or "").strip()
    itch_url = (raw_game.get("itchUrl") or "").strip()

    external_ids = {}
    steam_app_id = appid_from_steam_url(steam_url)
    if steam_app_id:
        external_ids["steamAppId"] = steam_app_id

    epic_slug = epic_slug_from_url(epic_url)
    if epic_slug:
        external_ids["epicSlug"] = epic_slug

    itch_slug = itch_slug_from_url(itch_url)
    if itch_slug:
        external_ids["itchSlug"] = itch_slug

    storefronts = []
    if steam_url:
        storefronts.append({"store": "steam", "url": steam_url, "externalId": steam_app_id})
    if epic_url:
        storefronts.append({"store": "epic", "url": epic_url, "externalId": epic_slug})
    if itch_url:
        storefronts.append({"store": "itch", "url": itch_url, "externalId": itch_slug})

    description_it = (raw_game.get("description") or "").strip()
    description_en = (raw_game.get("description_en") or "").strip()

    return {
        # Legacy-compatible keys still consumed by the current site build.
        **raw_game,
        "categories": categories,
        "genres": genres,
        "coopMode": coop_modes,
        # New canonical fields for future ingest/merge pipelines.
        "slug": slugify(title, f"game-{game_id}"),
        "isFeaturedIndie": featured_indie_id == game_id,
        "descriptions": {
            "it": description_it,
            "en": description_en,
        },
        "taxonomy": {
            "categories": categories,
            "genres": genres,
        },
        "capabilities": {
            "onlineCoop": "online" in coop_modes,
            "localCoop": "local" in coop_modes,
            "splitScreen": "split" in coop_modes,
            "sharedScreen": "split" in coop_modes,
            "crossplay": bool(raw_game.get("crossplay")),
            "playersLabel": raw_game.get("players") or "",
            "maxPlayers": raw_game.get("maxPlayers") or 0,
        },
        "storefronts": storefronts,
        "externalIds": external_ids,
        "signals": {
            "ccu": raw_game.get("ccu") or 0,
            "trending": bool(raw_game.get("trending")),
            "rating": raw_game.get("rating") or 0,
        },
        "editorial": {
            "played": bool(raw_game.get("played")),
            "personalNote": raw_game.get("personalNote") or "",
        },
        "sourceMeta": {
            "ingestSource": "games.js",
            "schemaVersion": SCHEMA_VERSION,
        },
    }


def load_games() -> list[dict[str, Any]]:
    content = GAMES_JS.read_text(encoding="utf-8")
    featured_indie_id = parse_featured_indie_id(content)
    blocks = re.findall(r"\{[^{}]*\}", content, re.DOTALL)

    games = []
    for block in blocks:
        game = {
            "id": ef(block, "id"),
            "title": ef(block, "title") or "",
            "categories": ef(block, "categories") or [],
            "genres": ef(block, "genres") or [],
            "coopMode": ef(block, "coopMode") or ["online"],
            "maxPlayers": ef(block, "maxPlayers") or 4,
            "crossplay": ef(block, "crossplay") or False,
            "players": ef(block, "players") or "1-4",
            "image": ef(block, "image") or "",
            "description": ef(block, "description") or "",
            "description_en": ef(block, "description_en") or "",
            "personalNote": ef(block, "personalNote") or "",
            "played": ef(block, "played") or False,
            "steamUrl": ef(block, "steamUrl") or "",
            "epicUrl": ef(block, "epicUrl") or "",
            "itchUrl": ef(block, "itchUrl") or "",
            "ccu": ef(block, "ccu") or 0,
            "trending": ef(block, "trending") or False,
            "rating": ef(block, "rating") or 0,
        }
        if game["id"] is not None:
            games.append(normalize_game(game, featured_indie_id))

    games.sort(key=lambda item: item["id"])
    return games


def build_catalog_artifact(games: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = collections.Counter()
    store_counts = collections.Counter()

    for game in games:
        category_counts.update(game["categories"])
        for storefront in game["storefronts"]:
            store_counts.update([storefront["store"]])

    featured_indie_id = next((game["id"] for game in games if game["isFeaturedIndie"]), None)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": source_generated_at(),
        "source": {
            "type": "legacy-runtime-import",
            "path": GAMES_JS.name,
        },
        "featuredIndieId": featured_indie_id,
        "stats": {
            "games": len(games),
            "played": sum(1 for game in games if game["editorial"]["played"]),
            "trending": sum(1 for game in games if game["signals"]["trending"]),
            "withEnglishDescription": sum(1 for game in games if game["descriptions"]["en"]),
            "categoryCounts": dict(sorted(category_counts.items())),
            "storeCounts": dict(sorted(store_counts.items())),
        },
        "games": games,
    }


def build_public_catalog_export(games: list[dict[str, Any]]) -> dict[str, Any]:
    featured_indie_id = next((game["id"] for game in games if game["isFeaturedIndie"]), None)
    public_games = []

    for game in games:
        public_games.append(
            {
                "id": game["id"],
                "slug": game["slug"],
                "title": game["title"],
                "categories": list(game["categories"]),
                "genres": list(game["genres"]),
                "coopMode": list(game["coopMode"]),
                "maxPlayers": game["maxPlayers"],
                "crossplay": bool(game["crossplay"]),
                "players": game["players"],
                "image": game["image"],
                "description": game["description"],
                "description_en": game["description_en"],
                "personalNote": game["personalNote"],
                "played": bool(game["played"]),
                "steamUrl": game["steamUrl"],
                "epicUrl": game["epicUrl"],
                "itchUrl": game["itchUrl"],
                "ccu": game["ccu"],
                "trending": bool(game["trending"]),
                "rating": game["rating"],
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": source_generated_at(),
        "featuredIndieId": featured_indie_id,
        "games": public_games,
    }


def write_catalog_artifact(games: list[dict[str, Any]] | None = None) -> pathlib.Path:
    if games is None:
        games = load_games()
    DATA_DIR.mkdir(exist_ok=True)
    payload = build_catalog_artifact(games)
    CATALOG_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return CATALOG_JSON


def write_public_catalog_export(games: list[dict[str, Any]] | None = None) -> pathlib.Path:
    if games is None:
        games = load_games()
    DATA_DIR.mkdir(exist_ok=True)
    payload = build_public_catalog_export(games)
    PUBLIC_CATALOG_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return PUBLIC_CATALOG_JSON
