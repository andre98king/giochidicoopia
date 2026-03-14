#!/usr/bin/env python3
"""
Validate catalog data, generated static pages, and sitemap consistency.

This script is intentionally lightweight and uses only project-local modules
plus the Python standard library so it can run in CI without extra setup.
"""

from __future__ import annotations

import collections
import xml.etree.ElementTree as ET

import build_static_pages


INFO_PAGES = ("index.html", "about.html", "contact.html", "free.html", "privacy.html", "game.html")
ALLOWED_CATEGORIES = {
    "trending",
    "horror",
    "action",
    "puzzle",
    "splitscreen",
    "rpg",
    "survival",
    "factory",
    "roguelike",
    "sport",
    "strategy",
    "indie",
    "free",
}


def short_list(items, limit=10):
    items = list(items)
    if len(items) <= limit:
        return ", ".join(items)
    return ", ".join(items[:limit]) + f", ... (+{len(items) - limit})"


def main() -> int:
    errors = []
    warnings = []

    for page in INFO_PAGES:
        if not (build_static_pages.ROOT / page).is_file():
            errors.append(f"Missing required page: {page}")

    games = build_static_pages.load_games()
    if len(games) < 50:
        errors.append(f"Suspiciously low catalog size: {len(games)} games")

    ids = [game["id"] for game in games]
    duplicate_ids = sorted(
        str(game_id) for game_id, count in collections.Counter(ids).items() if count > 1
    )
    if duplicate_ids:
        errors.append(f"Duplicate game ids: {short_list(duplicate_ids)}")

    missing_required = []
    invalid_store_urls = []
    unknown_categories = []
    missing_english = []

    for game in games:
        game_id = game["id"]
        title = (game.get("title") or "").strip()
        description = (game.get("description") or "").strip()
        description_en = (game.get("description_en") or "").strip()
        steam_url = (game.get("steamUrl") or "").strip()
        categories = game.get("categories") or []

        if not title:
            missing_required.append(f"{game_id}: missing title")
        if not description:
            missing_required.append(f"{game_id}: missing description")
        if not categories:
            missing_required.append(f"{game_id}: missing categories")
        if not steam_url.startswith("https://store.steampowered.com/app/"):
            invalid_store_urls.append(f"{game_id}: {steam_url or 'empty steamUrl'}")
        unknown = sorted(set(categories) - ALLOWED_CATEGORIES)
        if unknown:
            unknown_categories.append(f"{game_id}: {', '.join(unknown)}")
        if not description_en:
            missing_english.append(f"{game_id} ({title})")

    if missing_required:
        errors.append(f"Catalog entries with missing required fields: {short_list(missing_required)}")
    if invalid_store_urls:
        errors.append(f"Invalid Steam URLs: {short_list(invalid_store_urls)}")
    if unknown_categories:
        errors.append(f"Unknown categories in games.js: {short_list(unknown_categories)}")
    if missing_english:
        warnings.append(
            f"Games missing English descriptions: {short_list(missing_english, limit=6)}"
        )

    generated_pages = list(build_static_pages.GAMES_DIR.glob("*.html"))
    if len(generated_pages) != len(games):
        errors.append(
            f"Generated page count mismatch: {len(generated_pages)} pages for {len(games)} games"
        )

    page_errors = []
    for game in games:
        page_path = build_static_pages.GAMES_DIR / f"{game['id']}.html"
        if not page_path.is_file():
            page_errors.append(f"{game['id']}.html missing")
            continue
        content = page_path.read_text(encoding="utf-8")
        expected_canonical = f'<link rel="canonical" href="{build_static_pages.page_url(game)}">'
        if expected_canonical not in content:
            page_errors.append(f"{game['id']}.html missing canonical")
        if "const GAME_DATA =" not in content:
            page_errors.append(f"{game['id']}.html missing embedded GAME_DATA")

    if page_errors:
        errors.append(f"Static page validation errors: {short_list(page_errors)}")

    try:
        tree = ET.parse(build_static_pages.SITEMAP)
    except ET.ParseError as exc:
        errors.append(f"sitemap.xml is not valid XML: {exc}")
        tree = None

    if tree is not None:
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = {
            node.text.strip()
            for node in tree.findall("sm:url/sm:loc", namespace)
            if node.text and node.text.strip()
        }
        expected_locs = {
            f"{build_static_pages.SITE_URL}/",
            f"{build_static_pages.SITE_URL}/about.html",
            f"{build_static_pages.SITE_URL}/contact.html",
            f"{build_static_pages.SITE_URL}/free.html",
        }
        expected_locs.update(build_static_pages.page_url(game) for game in games)
        missing_locs = sorted(expected_locs - locs)
        unexpected_locs = sorted(locs - expected_locs)
        if missing_locs:
            errors.append(f"Missing sitemap URLs: {short_list(missing_locs)}")
        if unexpected_locs:
            warnings.append(f"Unexpected sitemap URLs: {short_list(unexpected_locs)}")

    if all(not game.get("crossplay") for game in games):
        warnings.append(
            "No games are currently flagged as crossplay. Keep the UI filter disabled until the data source is reliable."
        )

    print(f"Validated catalog: {len(games)} games, {len(generated_pages)} static pages")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("Validation failed.")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
