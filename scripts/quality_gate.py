#!/usr/bin/env python3
"""
Co-op Quality Gate — multi-source validation for new game candidates.

Validates whether a game is genuinely co-op before it enters the catalog.
Uses Steam categories (primary) + RAWG tags (secondary confirmation).

Returns a structured verdict: approve / reject / needs_review
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

# Steam category IDs that signal co-op
STEAM_COOP_CATS: dict[int, str] = {
    9:  "Co-op",
    38: "Online Co-op",
    39: "Shared/Split Screen Co-op",
    24: "Shared/Split Screen",
    48: "LAN Co-op",
    44: "Remote Play Together",
}

# Steam category IDs that signal PvP (competitive)
STEAM_PVP_CATS: dict[int, str] = {
    49: "PvP",
    36: "Online PvP",
    37: "Local PvP",
    47: "Shared/Split Screen PvP",
}

# RAWG tags that confirm co-op
RAWG_COOP_TAGS = {
    "co-op", "cooperative", "local co-op", "online co-op",
    "co-op campaign", "multiplayer co-op", "4-player co-op",
    "2-player co-op", "couch co-op",
}

# Minimum score to auto-approve without RAWG check
AUTO_APPROVE_COOP_CATS = {38, 39, 9, 48}  # Strong co-op signals


def _fetch_json(url: str, timeout: int = 10) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "coophubs-validator/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def fetch_steam_categories(app_id: str) -> tuple[list[dict], str, str]:
    """
    Returns (categories, name, header_image) from Steam API.
    Categories: list of {id: int, description: str}
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us"
    data = _fetch_json(url)
    if not data:
        return [], "", ""
    info = data.get(str(app_id), {})
    if not info.get("success"):
        return [], "", ""
    game = info.get("data", {})
    return (
        game.get("categories", []),
        game.get("name", ""),
        game.get("header_image", ""),
    )


def fetch_rawg_tags(game_name: str, api_key: str) -> set[str]:
    """Search RAWG for the game and return its tags (lowercased)."""
    import urllib.parse
    query = urllib.parse.quote(game_name)
    url = f"https://api.rawg.io/api/games?key={api_key}&search={query}&page_size=3"
    data = _fetch_json(url)
    if not data:
        return set()
    results = data.get("results", [])
    if not results:
        return set()
    # Use the best match (first result)
    tags = {t["name"].lower() for t in results[0].get("tags", [])}
    return tags


def derive_coop_modes(cat_ids: set[int]) -> list[str]:
    """Map Steam category IDs → canonical coopMode values."""
    modes = []
    online_ids = {38, 48, 44, 9}   # Online Co-op, LAN, Remote Play, generic Co-op
    local_ids  = {39, 24}           # Shared/Split Screen
    sofa_ids   = {24, 39}           # Couch/split = sofa

    if cat_ids & online_ids:
        modes.append("online")
    if cat_ids & local_ids:
        modes.append("local")
    # sofa is only added when split screen is the *only* local mode (no online)
    # In practice we keep "local" as the canonical value for split screen
    if not modes:
        modes.append("online")  # fallback
    return modes


def estimate_coop_score(cat_ids: set[int], pvp_ids: set[int]) -> int | None:
    """
    Hint for coopScore (1-3). Will be overridden by human review.
    - 3: co-op is clearly central (no PvP, strong co-op signal)
    - 2: solid co-op presence
    - 1: co-op exists but mixed with competitive
    """
    has_strong_coop = bool(cat_ids & AUTO_APPROVE_COOP_CATS)
    has_pvp = bool(pvp_ids)

    if has_strong_coop and not has_pvp:
        return 3 if 38 in cat_ids else 2
    if has_strong_coop and has_pvp:
        return 1
    return 2  # default when generic co-op present


def validate(
    steam_app_id: str,
    rawg_api_key: str | None = None,
    rate_limit_delay: float = 1.0,
) -> dict[str, Any]:
    """
    Validate a game candidate for co-op quality.

    Returns a verdict dict:
      status:    "approved" | "rejected" | "needs_review"
      reason:    human-readable explanation
      confidence: "high" | "medium" | "low"
      coop_modes: list[str]
      coop_score_hint: int | None
      steam_name: str
      pvp_signals: list[str]
      coop_signals: list[str]
      rawg_confirmed: bool
    """
    time.sleep(rate_limit_delay)
    cats, steam_name, _ = fetch_steam_categories(steam_app_id)

    if not cats and not steam_name:
        return {
            "status": "needs_review",
            "reason": "Steam API returned no data — check app ID",
            "confidence": "low",
            "coop_modes": ["online"],
            "coop_score_hint": None,
            "steam_name": "",
            "pvp_signals": [],
            "coop_signals": [],
            "rawg_confirmed": False,
        }

    cat_ids = {int(c["id"]) for c in cats}
    found_coop_ids = cat_ids & set(STEAM_COOP_CATS)
    found_pvp_ids  = cat_ids & set(STEAM_PVP_CATS)

    coop_signals = [STEAM_COOP_CATS[i] for i in found_coop_ids]
    pvp_signals  = [STEAM_PVP_CATS[i] for i in found_pvp_ids]

    # Hard reject: PvP categories present with NO co-op categories
    if found_pvp_ids and not found_coop_ids:
        return {
            "status": "rejected",
            "reason": f"PvP-only game: {', '.join(pvp_signals)}",
            "confidence": "high",
            "coop_modes": [],
            "coop_score_hint": None,
            "steam_name": steam_name,
            "pvp_signals": pvp_signals,
            "coop_signals": [],
            "rawg_confirmed": False,
        }

    # Hard reject: no co-op signals at all
    if not found_coop_ids:
        return {
            "status": "rejected",
            "reason": "No co-op categories found on Steam",
            "confidence": "high",
            "coop_modes": [],
            "coop_score_hint": None,
            "steam_name": steam_name,
            "pvp_signals": pvp_signals,
            "coop_signals": [],
            "rawg_confirmed": False,
        }

    # Has co-op categories — check RAWG for confirmation if key available
    rawg_confirmed = False
    if rawg_api_key and steam_name:
        time.sleep(rate_limit_delay)
        rawg_tags = fetch_rawg_tags(steam_name, rawg_api_key)
        rawg_confirmed = bool(rawg_tags & RAWG_COOP_TAGS)

    # Determine confidence
    has_strong_steam = bool(found_coop_ids & AUTO_APPROVE_COOP_CATS)
    has_pvp_mixed    = bool(found_pvp_ids)

    if has_pvp_mixed:
        # Always needs_review when PvP is present alongside co-op
        confidence = "medium"
        status = "needs_review"
    elif has_strong_steam and (rawg_confirmed or not rawg_api_key):
        confidence = "high"
        status = "approved"
    elif found_coop_ids:
        confidence = "medium"
        status = "approved"
    else:
        confidence = "low"
        status = "needs_review"

    coop_modes = derive_coop_modes(found_coop_ids)
    score_hint = estimate_coop_score(found_coop_ids, found_pvp_ids)

    reason_parts = [f"Steam co-op: {', '.join(coop_signals)}"]
    if rawg_confirmed:
        reason_parts.append("RAWG confirms co-op tags")
    if has_pvp_mixed:
        reason_parts.append(f"⚠ also has PvP: {', '.join(pvp_signals)}")

    return {
        "status": status,
        "reason": " | ".join(reason_parts),
        "confidence": confidence,
        "coop_modes": coop_modes,
        "coop_score_hint": score_hint,
        "steam_name": steam_name,
        "pvp_signals": pvp_signals,
        "coop_signals": coop_signals,
        "rawg_confirmed": rawg_confirmed,
    }


if __name__ == "__main__":
    import sys
    app_id = sys.argv[1] if len(sys.argv) > 1 else "230230"  # Divinity Original Sin
    print(f"Testing quality gate on app_id={app_id}")
    result = validate(app_id)
    print(json.dumps(result, indent=2))
