#!/usr/bin/env python3
"""
Validate free_games.js structure and offer sanity.

This script is intentionally standalone so it can run in CI without
network access or optional scraping dependencies.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parent
FREE_GAMES_JS = ROOT / "free_games.js"
ALLOWED_STORES = {"epic", "steam", "gog", "humble"}
EXPECTED_HOST_SNIPPETS = {
    "epic": ("epicgames.com",),
    "steam": ("steampowered.com",),
    "gog": ("gog.com",),
    "humble": ("humblebundle.com",),
}
NOW = dt.datetime.now(dt.timezone.utc)
EXPIRED_GRACE = dt.timedelta(minutes=15)


def parse_js_payload(path: pathlib.Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path.name}")

    content = path.read_text(encoding="utf-8")
    match = re.search(r"const\s+freeGames\s*=\s*(\[[\s\S]*\])\s*;?\s*$", content)
    if not match:
        raise ValueError("free_games.js does not expose a `const freeGames = [...]` payload")

    payload = json.loads(match.group(1))
    if not isinstance(payload, list):
        raise ValueError("freeGames payload is not an array")
    return payload


def parse_iso_datetime(value: str) -> dt.datetime | None:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def validate_https_url(value: str, field_name: str) -> str | None:
    if not value:
        return f"{field_name} is empty"

    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return f"{field_name} must be an https URL"
    return None


def host_matches_store(store: str, url: str) -> bool:
    host = urlparse(url).netloc.lower()
    expected = EXPECTED_HOST_SNIPPETS.get(store, ())
    return any(snippet in host for snippet in expected)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        offers = parse_js_payload(FREE_GAMES_JS)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    seen_keys = set()
    previous_expiry = None

    for index, offer in enumerate(offers, start=1):
        if not isinstance(offer, dict):
            errors.append(f"Entry #{index} is not an object")
            continue

        title = str(offer.get("title") or "").strip()
        store = str(offer.get("store") or "").strip().lower()
        image_url = str(offer.get("imageUrl") or "").strip()
        store_url = str(offer.get("storeUrl") or "").strip()
        free_until = str(offer.get("freeUntil") or "").strip()

        if not title:
            errors.append(f"Entry #{index}: missing title")
        if store not in ALLOWED_STORES:
            errors.append(f"Entry #{index}: invalid store `{store or 'empty'}`")
        if not free_until:
            errors.append(f"Entry #{index}: missing freeUntil")

        store_url_error = validate_https_url(store_url, f"Entry #{index} storeUrl")
        if store_url_error:
            errors.append(store_url_error)
        elif store in ALLOWED_STORES and not host_matches_store(store, store_url):
            warnings.append(f"Entry #{index}: storeUrl host does not obviously match store `{store}`")

        if image_url:
            image_url_error = validate_https_url(image_url, f"Entry #{index} imageUrl")
            if image_url_error:
                errors.append(image_url_error)
        else:
            warnings.append(f"Entry #{index}: imageUrl is empty")

        expires_at = parse_iso_datetime(free_until) if free_until else None
        if not expires_at:
            errors.append(f"Entry #{index}: invalid freeUntil `{free_until or 'empty'}`")
        else:
            if expires_at <= NOW - EXPIRED_GRACE:
                errors.append(
                    f"Entry #{index}: offer already expired at {free_until}"
                )
            if previous_expiry and expires_at < previous_expiry:
                warnings.append(
                    f"Entry #{index}: offers are not sorted by expiry ascending"
                )
            previous_expiry = expires_at

        dedupe_key = (store, title.lower())
        if title and store in ALLOWED_STORES:
            if dedupe_key in seen_keys:
                errors.append(f"Entry #{index}: duplicate offer for `{title}` on `{store}`")
            seen_keys.add(dedupe_key)

    print(f"Validated free games feed: {len(offers)} offers")

    if not offers:
        warnings.append("No active free offers in free_games.js. This is valid, but the homepage strip will stay hidden.")

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
