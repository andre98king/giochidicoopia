#!/usr/bin/env python3
"""
Cross-validate co-op tags using Steam + IGDB data.

Per ogni gioco, confronta i segnali co-op da due fonti indipendenti:
  - Steam: categories dall'API appdetails
  - IGDB: multiplayer_modes strutturati (onlinecoop, offlinecoop, splitscreen, lancoop)

Produce un report JSON con verdetti: CONFIRMED, LIKELY, DISPUTED, REJECTED.

Modalita:
  --full       Valida TUTTI i giochi (usa per audit iniziale, ~15 min)
  --flagged    Valida solo i giochi flaggati da auto_update.py (default in CI)
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# Add scripts dir to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from catalog_config import (
    IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, MAX_CROSSVAL,
    VERIFIED_COOP_APPIDS, BLACKLIST_APPIDS,
)
from catalog_data import ROOT, load_games, appid_from_steam_url

DATA_DIR = ROOT / "data"
REPORT_PATH = DATA_DIR / "coop_validation_report.json"
FLAGGED_PATH = DATA_DIR / "_nocoop_flagged.json"

STEAM_DELAY = 1.5  # seconds between Steam API calls


# ─────────────── Steam co-op signal ───────────────

def fetch_steam_coop_signal(appid: str) -> dict[str, Any]:
    """Fetch Steam appdetails and extract co-op signals."""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CoopHub/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        return {"error": str(exc), "has_data": False}

    app_data = data.get(appid, {})
    if not app_data.get("success"):
        return {"error": "not found on Steam", "has_data": False}

    details = app_data.get("data", {})
    cats = [c.get("description", "").lower() for c in details.get("categories", [])]

    has_coop = any("co-op" in c for c in cats)
    has_online_coop = any("online co-op" in c for c in cats)
    has_local_coop = any("local co-op" in c for c in cats)
    has_split = any("split" in c for c in cats)
    has_multiplayer = any("multi" in c for c in cats)

    return {
        "has_data": True,
        "has_coop": has_coop,
        "has_multiplayer": has_multiplayer,
        "online_coop": has_online_coop,
        "local_coop": has_local_coop,
        "splitscreen": has_split,
        # Solo "Co-op" conta, non "Multiplayer" generico (include PvP)
        "is_coop": has_coop,
    }


# ─────────────── IGDB co-op signal ───────────────

def fetch_igdb_coop_signals_batch(
    igdb_source,
    appid_list: list[str],
) -> dict[str, dict[str, Any]]:
    """Fetch IGDB multiplayer_modes + game_modes for a batch of Steam appids.

    Uses two IGDB signals:
      1. multiplayer_modes (structured: onlinecoop, offlinecoop, splitscreen)
      2. game_modes (mode 3 = Co-operative) — broader, more commonly populated
    """
    from igdb_catalog_source import _parse_multiplayer_modes

    results: dict[str, dict[str, Any]] = {}

    # Resolve appids to IGDB IDs
    appid_to_igdb = igdb_source.fetch_appid_to_igdb_id(appid_list)
    if not appid_to_igdb:
        for aid in appid_list:
            results[aid] = {"has_data": False}
        return results

    igdb_ids = list(set(appid_to_igdb.values()))

    # Fetch multiplayer_modes
    igdb_to_modes = igdb_source.fetch_multiplayer_modes(igdb_ids)

    # Fetch game_modes (mode 3 = Co-operative)
    ids_str = ", ".join(str(i) for i in igdb_ids)
    game_modes_query = (
        f"fields id, game_modes; "
        f"where id = ({ids_str}); "
        f"limit {len(igdb_ids)};"
    )
    game_modes_raw = igdb_source._post("games", game_modes_query) or []
    igdb_to_game_modes = {
        item["id"]: item.get("game_modes") or []
        for item in game_modes_raw
        if "id" in item
    }

    for aid in appid_list:
        igdb_id = appid_to_igdb.get(aid)
        if igdb_id is None:
            results[aid] = {"has_data": False}
            continue

        # Signal 1: multiplayer_modes (structured)
        modes_list = igdb_to_modes.get(igdb_id, [])
        parsed = _parse_multiplayer_modes(modes_list)

        # Signal 2: game_modes (3 = Co-operative)
        gm = igdb_to_game_modes.get(igdb_id, [])
        has_coop_game_mode = 3 in gm

        if parsed is not None:
            # multiplayer_modes confirms co-op with details
            coop_modes = parsed.get("coopMode", [])
            results[aid] = {
                "has_data": True,
                "igdb_id": igdb_id,
                "has_coop": True,
                "game_modes_coop": has_coop_game_mode,
                "online_coop": "online" in coop_modes,
                "local_coop": "local" in coop_modes,
                "splitscreen": "split" in coop_modes,
            }
        elif has_coop_game_mode:
            # multiplayer_modes empty but game_modes says co-op
            results[aid] = {
                "has_data": True,
                "igdb_id": igdb_id,
                "has_coop": True,
                "game_modes_coop": True,
                "online_coop": None,  # unknown specifics
                "local_coop": None,
                "splitscreen": None,
            }
        else:
            # Neither signal confirms co-op
            has_any_data = bool(gm)  # IGDB has the game but no co-op signal
            results[aid] = {
                "has_data": has_any_data,
                "igdb_id": igdb_id,
                "has_coop": False if has_any_data else None,
                "game_modes_coop": False,
                "online_coop": None,
                "local_coop": None,
                "splitscreen": None,
            }

    return results


# ─────────────── Verdict logic ───────────────

def compute_verdict(steam: dict, igdb: dict) -> dict[str, Any]:
    """
    Cross-validate Steam vs IGDB signals.

    Verdicts:
      CONFIRMED — both sources agree it's co-op
      LIKELY    — one source says co-op, other has no data
      DISPUTED  — sources disagree
      REJECTED  — neither source confirms co-op
    """
    steam_says_coop = steam.get("is_coop", False) if steam.get("has_data") else None
    igdb_says_coop = igdb.get("has_coop", False) if igdb.get("has_data") else None

    if steam_says_coop and igdb_says_coop:
        verdict = "confirmed"
    elif steam_says_coop and igdb_says_coop is None:
        verdict = "likely"
    elif steam_says_coop is None and igdb_says_coop:
        verdict = "likely"
    elif steam_says_coop and igdb_says_coop is False:
        verdict = "disputed"
    elif steam_says_coop is False and igdb_says_coop:
        verdict = "disputed"
    elif steam_says_coop is False and (igdb_says_coop is False or igdb_says_coop is None):
        verdict = "rejected"
    elif steam_says_coop is None and igdb_says_coop is False:
        verdict = "rejected"
    elif steam_says_coop is None and igdb_says_coop is None:
        verdict = "likely"  # no data from either — keep, but review
    else:
        verdict = "likely"

    # Per-mode verdicts
    modes = {}
    for mode in ("online_coop", "local_coop", "splitscreen"):
        s = steam.get(mode) if steam.get("has_data") else None
        i = igdb.get(mode) if igdb.get("has_data") else None
        if s and i:
            modes[mode] = "confirmed"
        elif s and i is None:
            modes[mode] = "likely"
        elif s and i is False:
            modes[mode] = "disputed"
        elif i and (s is False or s is None):
            modes[mode] = "igdb_only"
        else:
            modes[mode] = "not_present"

    return {"verdict": verdict, "modes": modes}


# ─────────────── Main validation ───────────────

def validate_games(
    games: list[dict[str, Any]],
    full: bool = False,
    flagged_ids: set[int] | None = None,
) -> dict[str, Any]:
    """Run cross-validation on catalog games."""
    from igdb_catalog_source import IgdbCatalogSource

    has_igdb = bool(IGDB_CLIENT_ID and IGDB_CLIENT_SECRET)
    igdb_source = None
    if has_igdb:
        igdb_source = IgdbCatalogSource(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
        print("  IGDB credentials found, cross-validation attiva")
    else:
        print("  IGDB credentials non disponibili, solo verifica Steam")

    # Determine which games to validate
    steam_games = [g for g in games if appid_from_steam_url(g.get("steamUrl", ""))]

    if flagged_ids:
        to_validate = [g for g in steam_games if g["id"] in flagged_ids]
        print(f"  Modalita flagged: {len(to_validate)} giochi da validare")
    elif full:
        to_validate = steam_games
        print(f"  Modalita full: {len(to_validate)} giochi da validare")
    else:
        # Rotation: validate a subset per run
        to_validate = steam_games[:MAX_CROSSVAL]
        print(f"  Modalita rotation: {len(to_validate)}/{len(steam_games)} giochi")

    # Load existing report for merging (rotation mode)
    existing_results = {}
    if REPORT_PATH.is_file() and not full:
        try:
            existing = json.loads(REPORT_PATH.read_text())
            for entry in existing.get("results", []):
                existing_results[entry["id"]] = entry
        except Exception:
            pass

    results = []
    confirmed = likely = disputed = rejected = 0

    # Batch IGDB lookups
    appid_map = {}  # appid -> game
    for g in to_validate:
        aid = appid_from_steam_url(g["steamUrl"])
        if aid:
            appid_map[aid] = g

    # Fetch all IGDB signals in batches
    igdb_signals = {}
    if igdb_source and appid_map:
        appid_list = list(appid_map.keys())
        print(f"\n  Fetching IGDB data per {len(appid_list)} giochi...")
        for i in range(0, len(appid_list), 20):
            batch = appid_list[i:i + 20]
            batch_num = i // 20 + 1
            total_batches = (len(appid_list) + 19) // 20
            print(f"    IGDB batch {batch_num}/{total_batches}...", end=" ", flush=True)
            batch_results = fetch_igdb_coop_signals_batch(igdb_source, batch)
            igdb_signals.update(batch_results)
            found = sum(1 for v in batch_results.values() if v.get("has_data"))
            print(f"{found}/{len(batch)} trovati")

    # Fetch Steam signals and compute verdicts
    print(f"\n  Fetching Steam data e computing verdicts...")
    for idx, (aid, game) in enumerate(appid_map.items()):
        # Skip whitelisted games — already verified manually
        if aid in VERIFIED_COOP_APPIDS:
            entry = {
                "id": game["id"], "title": game["title"], "steamAppId": aid,
                "igdbId": game.get("igdbId", 0),
                "steam_coop": None, "steam_has_data": False,
                "igdb_coop": None, "igdb_has_data": False,
                "verdict": "verified", "modes": {},
                "currentCoopMode": game.get("coopMode", []),
                "currentCategories": game.get("categories", []),
            }
            results.append(entry)
            confirmed += 1
            continue

        steam_signal = fetch_steam_coop_signal(aid)
        time.sleep(STEAM_DELAY)

        igdb_signal = igdb_signals.get(aid, {"has_data": False})
        verdict_data = compute_verdict(steam_signal, igdb_signal)

        entry = {
            "id": game["id"],
            "title": game["title"],
            "steamAppId": aid,
            "igdbId": igdb_signal.get("igdb_id", game.get("igdbId", 0)),
            "steam_coop": steam_signal.get("is_coop", False),
            "steam_has_data": steam_signal.get("has_data", False),
            "igdb_coop": igdb_signal.get("has_coop", False),
            "igdb_has_data": igdb_signal.get("has_data", False),
            "igdb_game_modes_coop": igdb_signal.get("game_modes_coop", False),
            "verdict": verdict_data["verdict"],
            "modes": verdict_data["modes"],
            "currentCoopMode": game.get("coopMode", []),
            "currentCategories": game.get("categories", []),
        }
        results.append(entry)

        v = verdict_data["verdict"]
        if v == "confirmed":
            confirmed += 1
        elif v == "likely":
            likely += 1
        elif v == "disputed":
            disputed += 1
        elif v == "rejected":
            rejected += 1

        if v in ("disputed", "rejected"):
            print(f"    {'!!!' if v == 'rejected' else '???'} {game['title']} — {v.upper()}"
                  f" (Steam:{steam_signal.get('is_coop')}, IGDB:{igdb_signal.get('has_coop')}"
                  f", game_modes_coop:{igdb_signal.get('game_modes_coop')})")

        if (idx + 1) % 20 == 0:
            print(f"    ... {idx + 1}/{len(appid_map)} completati")

    # Merge with existing results (rotation mode)
    if existing_results and not full:
        for entry in results:
            existing_results[entry["id"]] = entry
        all_results = sorted(existing_results.values(), key=lambda x: x["id"])
    else:
        all_results = sorted(results, key=lambda x: x["id"])

    # Recount from merged results
    total_verified = sum(1 for r in all_results if r["verdict"] == "verified")
    total_confirmed = sum(1 for r in all_results if r["verdict"] == "confirmed")
    total_likely = sum(1 for r in all_results if r["verdict"] == "likely")
    total_disputed = sum(1 for r in all_results if r["verdict"] == "disputed")
    total_rejected = sum(1 for r in all_results if r["verdict"] == "rejected")

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "full" if full else ("flagged" if flagged_ids else "rotation"),
        "gamesValidated": len(results),
        "summary": {
            "total": len(all_results),
            "verified": total_verified,
            "confirmed": total_confirmed,
            "likely": total_likely,
            "disputed": total_disputed,
            "rejected": total_rejected,
        },
        "disputed": [r for r in all_results if r["verdict"] == "disputed"],
        "rejected": [r for r in all_results if r["verdict"] == "rejected"],
        "results": all_results,
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Cross-validate co-op tags")
    parser.add_argument("--full", action="store_true", help="Validate ALL games (slow)")
    args = parser.parse_args()

    print("\n=== Cross-Validation Co-op Tags ===\n")

    games = load_games()
    print(f"  Catalogo: {len(games)} giochi")

    # Check for flagged games from auto_update.py
    flagged_ids = None
    if not args.full and FLAGGED_PATH.is_file():
        try:
            flagged = json.loads(FLAGGED_PATH.read_text())
            flagged_ids = set(flagged.get("game_ids", []))
            if flagged_ids:
                print(f"  Trovati {len(flagged_ids)} giochi flaggati da auto_update")
        except Exception:
            pass

    report = validate_games(games, full=args.full, flagged_ids=flagged_ids)

    # Write report
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Summary
    s = report["summary"]
    print(f"\n=== Risultati Cross-Validation ===")
    print(f"  Validati in questo run: {report['gamesValidated']}")
    print(f"  Totale nel report: {s['total']}")
    print(f"  Confirmed: {s['confirmed']}")
    print(f"  Likely:    {s['likely']}")
    print(f"  Disputed:  {s['disputed']}")
    print(f"  Rejected:  {s['rejected']}")

    if report["rejected"]:
        print(f"\n  REJECTED (candidati a rimozione):")
        for r in report["rejected"]:
            print(f"    - {r['id']}: {r['title']}")

    if report["disputed"]:
        print(f"\n  DISPUTED (da verificare manualmente):")
        for r in report["disputed"]:
            print(f"    - {r['id']}: {r['title']} (Steam:{r['steam_coop']}, IGDB:{r['igdb_coop']})")

    print(f"\n  Report salvato in: {REPORT_PATH}")


if __name__ == "__main__":
    main()
