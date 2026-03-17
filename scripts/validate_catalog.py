#!/usr/bin/env python3
"""
Validate catalog data, generated static pages, and sitemap consistency.

This script is intentionally lightweight and uses only project-local modules
plus the Python standard library so it can run in CI without extra setup.
"""

from __future__ import annotations

import collections
import json
import xml.etree.ElementTree as ET

import build_static_pages
import catalog_data


INFO_PAGES = ("index.html", "about.html", "contact.html", "free.html", "privacy.html", "game.html")
CROSSPLAY_UI_ENABLED = False
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

    games = catalog_data.load_games()
    if len(games) < 50:
        errors.append(f"Suspiciously low catalog size: {len(games)} games")

    ids = [game["id"] for game in games]
    duplicate_ids = sorted(
        str(game_id) for game_id, count in collections.Counter(ids).items() if count > 1
    )
    if duplicate_ids:
        errors.append(f"Duplicate game ids: {short_list(duplicate_ids)}")

    duplicate_slugs = sorted(
        slug for slug, count in collections.Counter(game["slug"] for game in games).items() if count > 1
    )
    if duplicate_slugs:
        errors.append(f"Duplicate canonical slugs: {short_list(duplicate_slugs)}")

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
        gog_url = (game.get("gogUrl") or "").strip()
        epic_url = (game.get("epicUrl") or "").strip()
        itch_url = (game.get("itchUrl") or "").strip()
        has_any_store = (
            steam_url.startswith("https://store.steampowered.com/app/")
            or gog_url.startswith("https://www.gog.com/")
            or epic_url.startswith("https://")
            or itch_url.startswith("https://")
        )
        if not has_any_store:
            invalid_store_urls.append(f"{game_id}: no valid store URL")
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

    if not catalog_data.CATALOG_JSON.is_file():
        errors.append(f"Missing canonical catalog artifact: {catalog_data.CATALOG_JSON.name}")
    else:
        try:
            artifact = json.loads(catalog_data.CATALOG_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Canonical catalog artifact is not valid JSON: {exc}")
            artifact = None

        if isinstance(artifact, dict):
            if artifact.get("schemaVersion") != catalog_data.SCHEMA_VERSION:
                errors.append(
                    "Canonical catalog artifact schemaVersion mismatch: "
                    f"{artifact.get('schemaVersion')} != {catalog_data.SCHEMA_VERSION}"
                )

            artifact_games = artifact.get("games")
            if not isinstance(artifact_games, list):
                errors.append("Canonical catalog artifact is missing the games array")
            else:
                if len(artifact_games) != len(games):
                    errors.append(
                        "Canonical catalog artifact game count mismatch: "
                        f"{len(artifact_games)} != {len(games)}"
                    )

            stats = artifact.get("stats")
            if not isinstance(stats, dict) or stats.get("games") != len(games):
                errors.append("Canonical catalog artifact stats.games does not match the catalog size")

            featured_indie_id = artifact.get("featuredIndieId")
            if featured_indie_id is not None and featured_indie_id not in set(ids):
                errors.append(
                    f"Canonical catalog artifact references missing featuredIndieId: {featured_indie_id}"
                )

    if not catalog_data.PUBLIC_CATALOG_JSON.is_file():
        errors.append(f"Missing public catalog export: {catalog_data.PUBLIC_CATALOG_JSON.name}")
    else:
        try:
            public_export = json.loads(catalog_data.PUBLIC_CATALOG_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Public catalog export is not valid JSON: {exc}")
            public_export = None

        if isinstance(public_export, dict):
            if public_export.get("schemaVersion") != catalog_data.SCHEMA_VERSION:
                errors.append(
                    "Public catalog export schemaVersion mismatch: "
                    f"{public_export.get('schemaVersion')} != {catalog_data.SCHEMA_VERSION}"
                )

            public_games = public_export.get("games")
            if not isinstance(public_games, list):
                errors.append("Public catalog export is missing the games array")
            else:
                if len(public_games) != len(games):
                    errors.append(
                        "Public catalog export game count mismatch: "
                        f"{len(public_games)} != {len(games)}"
                    )

            featured_indie_id = public_export.get("featuredIndieId")
            if featured_indie_id is not None and featured_indie_id not in set(ids):
                errors.append(
                    f"Public catalog export references missing featuredIndieId: {featured_indie_id}"
                )

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

    crossplay_count = sum(1 for game in games if game.get("crossplay"))
    if crossplay_count == 0:
        warnings.append(
            "Crossplay data is currently empty. The UI stays intentionally hidden until the source is reliable."
        )
    elif not CROSSPLAY_UI_ENABLED:
        warnings.append(
            f"{crossplay_count} games are flagged as crossplay internally, but the UI remains intentionally hidden pending manual validation of the source."
        )

    print(
        f"Validated catalog: {len(games)} games, {len(generated_pages)} static pages, "
        f"artifact {catalog_data.CATALOG_JSON.name}"
    )

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
