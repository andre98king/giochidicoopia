#!/usr/bin/env python3
"""
Co-op Quality Gate — multi-source validation for new game candidates.

Validates whether a game is genuinely co-op before it enters the catalog.

Sources (in priority order):
  1. Steam categories (primary — always checked)
  2. IGDB game_modes (secondary — checks via Steam app ID → IGDB ID lookup)
  3. GOG catalog features (tertiary — checks by game title search)
  4. RAWG tags (quaternary — additional confirmation)

Returns a structured verdict: approve / reject / needs_review

Source sets (pass as `sources=` to validate()):
  SOURCES_FAST  — Steam only. No API keys needed. ~1s/game.
  SOURCES_FULL  — All four sources. ~4s/game.
  None (default)— Auto: Steam always; IGDB/RAWG if credentials present; GOG always.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

# Steam category IDs that signal co-op
STEAM_COOP_CATS: dict[int, str] = {
    9: "Co-op",
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
    "co-op",
    "cooperative",
    "local co-op",
    "online co-op",
    "co-op campaign",
    "multiplayer co-op",
    "4-player co-op",
    "2-player co-op",
    "couch co-op",
}

# Strong co-op signals — enough for auto-approve without secondary sources
AUTO_APPROVE_COOP_CATS = {38, 39, 9, 48}

# Source set constants
SOURCES_FAST = frozenset({"steam"})
SOURCES_FULL = frozenset({"steam", "igdb", "gog", "rawg"})


_scraper = None


def _get_scraper():
    global _scraper
    if _scraper is None:
        import cloudscraper

        _scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
    return _scraper


def _fetch_json(url: str, timeout: int = 15) -> dict | None:
    try:
        r = _get_scraper().get(url, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


# ─────────────── IGDB helpers ───────────────


def _get_igdb_token(client_id: str, client_secret: str) -> str | None:
    """Get Twitch OAuth2 token for IGDB access."""
    url = (
        f"https://id.twitch.tv/oauth2/token"
        f"?client_id={client_id}"
        f"&client_secret={client_secret}"
        f"&grant_type=client_credentials"
    )
    try:
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get("access_token")
    except Exception:
        return None


def _igdb_post(endpoint: str, query: str, token: str, client_id: str) -> list | None:
    """POST an IGDB APIv4 query, returns list of results or None on error."""
    url = f"https://api.igdb.com/v4/{endpoint}"
    try:
        req = urllib.request.Request(
            url,
            data=query.encode("utf-8"),
            headers={
                "Client-ID": client_id,
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/plain",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fetch_igdb_coop(
    steam_app_id: str, client_id: str, client_secret: str
) -> bool | None:
    """
    Check co-op via IGDB using the Steam app ID.
    Returns True  → IGDB confirms co-op (game_modes contains 3)
    Returns False → IGDB found the game but no co-op game_mode
    Returns None  → lookup failed (network error, game not found)
    """
    token = _get_igdb_token(client_id, client_secret)
    if not token:
        return None

    ext_results = _igdb_post(
        "external_games",
        f"fields uid, game; where uid = ({steam_app_id}); limit 5;",
        token,
        client_id,
    )
    if not ext_results:
        return None

    igdb_ids = [r["game"] for r in ext_results if "game" in r]
    if not igdb_ids:
        return None

    ids_str = ", ".join(str(i) for i in igdb_ids[:3])
    game_results = _igdb_post(
        "games",
        f"fields game_modes; where id = ({ids_str}); limit 3;",
        token,
        client_id,
    )
    if not game_results:
        return None

    for g in game_results:
        if 3 in (g.get("game_modes") or []):  # 3 = Co-operative
            return True

    return False  # Found on IGDB, no co-op game_mode


# ─────────────── GOG catalog helper ───────────────


def fetch_igdb_coop_by_title(
    game_name: str, client_id: str, client_secret: str
) -> bool | None:
    """
    Check co-op via IGDB using a title search (for games without Steam app ID).
    Returns True  → IGDB confirms co-op (game_modes contains 3)
    Returns False → IGDB found the game but no co-op game_mode
    Returns None  → not found or lookup failed
    """
    token = _get_igdb_token(client_id, client_secret)
    if not token:
        return None

    # Search by title, take top 2 results
    safe_name = game_name.replace('"', "")
    results = _igdb_post(
        "games",
        f'fields game_modes, name; search "{safe_name}"; limit 2;',
        token,
        client_id,
    )
    if not results:
        return None

    for g in results:
        if 3 in (g.get("game_modes") or []):
            return True

    return False  # Found but no co-op mode


def fetch_gog_coop(game_name: str) -> bool | None:
    """
    Check co-op via GOG catalog API (title search).
    Returns True  → GOG catalog shows a "Co-op" feature for the best match
    Returns False → GOG found the game but no co-op feature listed
    Returns None  → No results or request failed
    """
    import urllib.parse

    query = urllib.parse.quote(game_name)
    url = f"https://catalog.gog.com/v1/catalog?productType=in%3Agame&search={query}&limit=3"
    data = _fetch_json(url)
    if not data:
        return None
    products = data.get("products") or []
    if not products:
        return None

    features = products[0].get("features") or []
    coop_slugs = {"co-op", "coop", "co_op", "cooperative"}
    for f in features:
        if isinstance(f, dict):
            if f.get("slug", "").lower() in coop_slugs:
                return True
            if "co-op" in f.get("name", "").lower():
                return True
        elif isinstance(f, str) and f.lower() in coop_slugs:
            return True

    return False  # Found on GOG, no co-op feature


def fetch_steam_categories(app_id: str) -> tuple[list[dict], str, str, str]:
    """
    Returns (categories, name, header_image, app_type) from Steam API.
    Categories: list of {id: int, description: str}
    app_type: "game" | "dlc" | "demo" | "music" | ...
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us"
    data = _fetch_json(url)
    if not data:
        return [], "", "", ""
    info = data.get(str(app_id), {})
    if not info.get("success"):
        return [], "", "", ""
    game = info.get("data", {})
    return (
        game.get("categories", []),
        game.get("name", ""),
        game.get("header_image", ""),
        game.get("type", "game"),
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
    return {t["name"].lower() for t in results[0].get("tags", [])}


def derive_coop_modes(cat_ids: set[int]) -> list[str]:
    """Map Steam category IDs → canonical coopMode values."""
    modes = []
    if cat_ids & {38, 48, 44, 9}:  # Online Co-op, LAN, Remote Play, generic Co-op
        modes.append("online")
    if cat_ids & {39, 24}:  # Shared/Split Screen
        modes.append("local")
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
    return 2


def validate(
    steam_app_id: str,
    rawg_api_key: str | None = None,
    igdb_client_id: str | None = None,
    igdb_client_secret: str | None = None,
    sources: frozenset[str] | None = None,
    rate_limit_delay: float = 1.0,
) -> dict[str, Any]:
    """
    Validate a game candidate for co-op quality.

    sources controls which APIs are queried:
      SOURCES_FAST  — Steam only (~1s/game, no keys needed)
      SOURCES_FULL  — Steam + IGDB + GOG + RAWG (~4s/game)
      None (default)— auto: Steam always; IGDB/RAWG if keys present; GOG always

    Returns a verdict dict with keys:
      status, reason, confidence, coop_modes, coop_score_hint,
      steam_name, pvp_signals, coop_signals,
      rawg_confirmed, igdb_confirmed, gog_confirmed
    """
    # Resolve active sources
    if sources is None:
        active: frozenset[str] = frozenset(
            {
                "steam",
                "gog",
                *(["igdb"] if igdb_client_id and igdb_client_secret else []),
                *(["rawg"] if rawg_api_key else []),
            }
        )
    else:
        active = sources

    def _empty_verdict(status: str, reason: str, confidence: str) -> dict[str, Any]:
        return {
            "status": status,
            "reason": reason,
            "confidence": confidence,
            "coop_modes": [],
            "coop_score_hint": None,
            "steam_name": "",
            "pvp_signals": [],
            "coop_signals": [],
            "rawg_confirmed": False,
            "igdb_confirmed": None,
            "gog_confirmed": None,
        }

    # ── Steam (always) ──
    time.sleep(rate_limit_delay)
    cats, steam_name, _, app_type = fetch_steam_categories(steam_app_id)

    # Reject DLC, demos, soundtracks, tools — not games
    if app_type and app_type not in ("game", ""):
        return {
            **_empty_verdict(
                "rejected", f"Not a game on Steam (type={app_type})", "high"
            ),
            "coop_modes": [],
            "steam_name": steam_name,
        }

    if not cats and not steam_name:
        # Steam unavailable — fall back to secondary sources if available
        if "igdb" not in active and "gog" not in active and "rawg" not in active:
            return {
                **_empty_verdict(
                    "needs_review", "Steam API unavailable — no fallback sources", "low"
                ),
                "coop_modes": ["online"],
            }

        igdb_confirmed: bool | None = None
        if "igdb" in active and igdb_client_id and igdb_client_secret:
            time.sleep(rate_limit_delay)
            igdb_confirmed = fetch_igdb_coop(
                steam_app_id, igdb_client_id, igdb_client_secret
            )

        gog_confirmed: bool | None = None
        # Can't search GOG without a title — skip when Steam name is missing

        rawg_confirmed = False
        # Can't search RAWG without a title — skip when Steam name is missing

        confirmed_count = sum([igdb_confirmed is True])
        if igdb_confirmed is True:
            status, confidence = "approved", "medium"
            reason = "Steam unavailable | IGDB confirms co-op"
        elif igdb_confirmed is False:
            status, confidence = "rejected", "medium"
            reason = "Steam unavailable | IGDB found game but no co-op mode"
        else:
            status, confidence = "needs_review", "low"
            reason = "Steam unavailable | IGDB could not find game"

        return {
            "status": status,
            "reason": reason,
            "confidence": confidence,
            "coop_modes": ["online"],
            "coop_score_hint": None,
            "steam_name": "",
            "pvp_signals": [],
            "coop_signals": [],
            "rawg_confirmed": False,
            "igdb_confirmed": igdb_confirmed,
            "gog_confirmed": None,
        }

    cat_ids = {int(c["id"]) for c in cats}
    found_coop_ids = cat_ids & set(STEAM_COOP_CATS)
    found_pvp_ids = cat_ids & set(STEAM_PVP_CATS)
    coop_signals = [STEAM_COOP_CATS[i] for i in found_coop_ids]
    pvp_signals = [STEAM_PVP_CATS[i] for i in found_pvp_ids]

    # Hard rejects — no secondary checks needed
    if found_pvp_ids and not found_coop_ids:
        return {
            **_empty_verdict(
                "rejected", f"PvP-only game: {', '.join(pvp_signals)}", "high"
            ),
            "steam_name": steam_name,
            "pvp_signals": pvp_signals,
        }

    if not found_coop_ids:
        return {
            **_empty_verdict("rejected", "No co-op categories found on Steam", "high"),
            "steam_name": steam_name,
            "pvp_signals": pvp_signals,
        }

    # ── Secondary sources (only reached when Steam confirms co-op) ──

    igdb_confirmed: bool | None = None
    if "igdb" in active and igdb_client_id and igdb_client_secret:
        time.sleep(rate_limit_delay)
        igdb_confirmed = fetch_igdb_coop(
            steam_app_id, igdb_client_id, igdb_client_secret
        )

    gog_confirmed: bool | None = None
    if "gog" in active and steam_name:
        time.sleep(rate_limit_delay)
        gog_confirmed = fetch_gog_coop(steam_name)

    rawg_confirmed = False
    if "rawg" in active and rawg_api_key and steam_name:
        time.sleep(rate_limit_delay)
        rawg_tags = fetch_rawg_tags(steam_name, rawg_api_key)
        rawg_confirmed = bool(rawg_tags & RAWG_COOP_TAGS)

    # ── Confidence logic ──
    has_strong_steam = bool(found_coop_ids & AUTO_APPROVE_COOP_CATS)
    has_pvp_mixed = bool(found_pvp_ids)
    confirmed_count = sum(
        [bool(rawg_confirmed), igdb_confirmed is True, gog_confirmed is True]
    )

    if has_pvp_mixed:
        status, confidence = "needs_review", "medium"
    elif igdb_confirmed is False:
        status, confidence = "needs_review", "medium"
    elif has_strong_steam and confirmed_count >= 1:
        status, confidence = "approved", "high"
    elif has_strong_steam:
        status, confidence = "approved", "medium"
    elif found_coop_ids and confirmed_count >= 1:
        status, confidence = "approved", "medium"
    else:
        status, confidence = "approved", "low"

    reason_parts = [f"Steam co-op: {', '.join(coop_signals)}"]
    if igdb_confirmed is True:
        reason_parts.append("IGDB confirms co-op")
    elif igdb_confirmed is False:
        reason_parts.append("⚠ IGDB found game but no co-op mode")
    if gog_confirmed is True:
        reason_parts.append("GOG confirms co-op")
    if rawg_confirmed:
        reason_parts.append("RAWG confirms co-op tags")
    if has_pvp_mixed:
        reason_parts.append(f"⚠ also has PvP: {', '.join(pvp_signals)}")

    return {
        "status": status,
        "reason": " | ".join(reason_parts),
        "confidence": confidence,
        "coop_modes": derive_coop_modes(found_coop_ids),
        "coop_score_hint": estimate_coop_score(found_coop_ids, found_pvp_ids),
        "steam_name": steam_name,
        "pvp_signals": pvp_signals,
        "coop_signals": coop_signals,
        "rawg_confirmed": rawg_confirmed,
        "igdb_confirmed": igdb_confirmed,
        "gog_confirmed": gog_confirmed,
    }


if __name__ == "__main__":
    import os
    import sys

    app_id = sys.argv[1] if len(sys.argv) > 1 else "230230"  # Divinity Original Sin

    igdb_id = os.environ.get("IGDB_CLIENT_ID")
    igdb_secret = os.environ.get("IGDB_CLIENT_SECRET")
    rawg_key = os.environ.get("RAWG_API_KEY")
    if not igdb_id:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            for line in open(env_file).read().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k == "IGDB_CLIENT_ID":
                        igdb_id = v.strip()
                    elif k == "IGDB_CLIENT_SECRET":
                        igdb_secret = v.strip()
                    elif k == "RAWG_API_KEY":
                        rawg_key = v.strip()

    print(f"Testing quality gate on app_id={app_id}")
    print(
        f"IGDB: {'enabled' if igdb_id else 'disabled'} | RAWG: {'enabled' if rawg_key else 'disabled'}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# CURATION GATE — Filtra giochi a bassa qualità dal catalogo pubblicato
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_CURATION_RULES = {
    "min_reviews": 20,
    "min_rating_percent": 70,
    "blocked_keywords": ["shovelware", "ripoff", "demo", "test", "prototype", "beta", "prologue", "early access", " alpha", "(alpha)"],
    "required_fields": ["title", "categories", "coopMode"],
}


def run_curation_gate(
    catalog: list,
    rules: dict | None = None,
    strict: bool = False,
    apply: bool = False,
) -> tuple[list, list, dict]:
    """
    Filtra giochi a bassa qualità dal catalogo.

    Args:
        catalog: Lista di giochi dal catalogo
        rules: Dizionario con soglie di qualità
        strict: Se True, esce con exit(1) se ci sono critical_fails
        apply: Se True, riscrive il catalogo filtrato

    Returns:
        (valid_games, hidden_games, stats)
    """
    rules = rules or DEFAULT_CURATION_RULES

    valid = []
    hidden = []
    stats = {
        "total": len(catalog),
        "valid": 0,
        "hidden": 0,
        "critical_fails": 0,
    }

    for g in catalog:
        g_id = g.get("id", "?")
        title = (g.get("title") or "").lower()

        reviews = 0
        if g.get("totalReviews"):
            reviews = g["totalReviews"]

        rating = g.get("rating") or g.get("signals", {}).get("rating") or 0

        missing = [f for f in rules["required_fields"] if not g.get(f)]

        blocked = any(kw in title for kw in rules["blocked_keywords"])

        if missing:
            reason = f"missing_fields:{','.join(missing)}"
            stats["critical_fails"] += 1
            hidden.append(
                {
                    "id": g_id,
                    "title": g.get("title"),
                    "reason": reason,
                    "severity": "critical",
                }
            )
            continue

        if blocked:
            reason = f"blocked_keyword:{[k for k in rules['blocked_keywords'] if k in title][0]}"
            stats["critical_fails"] += 1
            hidden.append(
                {
                    "id": g_id,
                    "title": g.get("title"),
                    "reason": reason,
                    "severity": "critical",
                }
            )
            continue

        # Blocca giochi Steam con poche recensioni (soglia minima assoluta)
        if reviews > 0 and reviews < rules["min_reviews"]:
            reason = f"low_reviews:{reviews}"
            stats["hidden"] += 1
            hidden.append(
                {
                    "id": g_id,
                    "title": g.get("title"),
                    "reason": reason,
                    "severity": "warning",
                }
            )
            continue

        # Blocca giochi itch.io-only senza segnali di qualità (rating=0, ccu=0)
        is_itch_only = bool(g.get("itchUrl")) and not g.get("steamUrl")
        if is_itch_only and rating == 0 and (g.get("ccu") or 0) == 0:
            reason = "itch_no_signals"
            stats["hidden"] += 1
            hidden.append(
                {
                    "id": g_id,
                    "title": g.get("title"),
                    "reason": reason,
                    "severity": "warning",
                }
            )
            continue

        valid.append(g)
        stats["valid"] += 1

    report = {
        "date": datetime.utcnow().isoformat() + "Z",
        "rules": rules,
        "stats": stats,
        "hidden_games": hidden,
    }

    Path("reports").mkdir(exist_ok=True)
    report_file = Path(
        f"reports/curation_gate_{datetime.utcnow().strftime('%Y%m%d')}.json"
    )
    report_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  📊 Curation report: {report_file}")

    # Esporta audit giornaliero con delta
    export_daily_audit(stats, hidden, "reports/")

    if strict and stats["critical_fails"] > 0:
        print(
            f"🚫 CI BLOCKED: {stats['critical_fails']} critical fails ({stats['hidden']} warnings)"
        )
        print(f"   Report: {report_file}")
        sys.exit(1)

    if apply and (stats["hidden"] > 0 or stats["critical_fails"] > 0):
        data_dir = Path("data")
        catalog_file = data_dir / "catalog.public.v1.json"

        if catalog_file.exists():
            backup_file = data_dir / "catalog.public.v1.json.bak"
            shutil.copy2(catalog_file, backup_file)
            print(f"  💾 Backup: {backup_file}")

        catalog_file.write_text(
            json.dumps(valid, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"  ✅ Applied: {stats['valid']} kept, {stats['hidden'] + stats['critical_fails']} filtered"
        )

    return valid, hidden, stats


def export_daily_audit(stats: dict, hidden: list, report_dir: str = "reports/") -> None:
    """Esporta un audit JSON giornaliero con tracciabilità e delta rispetto al giorno precedente."""
    from datetime import date
    from collections import Counter

    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()

    # Calcola raggruppamento motivi
    reason_counts = Counter()
    for h in hidden:
        reason = h.get("reason", "unknown").split(":")[0]
        reason_counts[reason] += 1

    audit_data = {
        "date": today,
        "valid": stats.get("valid", 0),
        "hidden": stats.get("hidden", 0),
        "critical": stats.get("critical_fails", 0),
        "reasons": dict(reason_counts),
    }

    # Leggi il file del giorno precedente e calcola delta
    prev_file = (
        report_path
        / f"daily_audit_{date.fromordinal(date.today().toordinal() - 1).isoformat()}.json"
    )
    if prev_file.exists():
        try:
            prev_data = json.loads(prev_file.read_text(encoding="utf-8"))
            audit_data["delta_valid"] = audit_data["valid"] - prev_data.get("valid", 0)
            audit_data["delta_hidden"] = audit_data["hidden"] - prev_data.get(
                "hidden", 0
            )
            audit_data["delta_critical"] = audit_data["critical"] - prev_data.get(
                "critical", 0
            )
        except Exception:
            pass

    # Scrivi il file giornaliero
    output_file = report_path / f"daily_audit_{today}.json"
    output_file.write_text(
        json.dumps(audit_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  📊 Daily audit: {output_file}")
