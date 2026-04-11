#!/usr/bin/env python3
"""
Backfill coopType per i giochi esistenti nel catalogo.

Questo script:
1. Legge il catalogo
2. Per ogni gioco con Steam URL, chiama quality_gate.validate() con retry
3. Monitora cambiamenti di stato (COOP→UNKNOWN, etc.)
4. Logga gli unknown per review manuale
5. Aggiorna il campo coopType nel catalogo

Run: python3 scripts/backfill_coop_type.py [--dry-run] [--force]
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import quality_gate

ROOT = Path(__file__).resolve().parent.parent

# Load .env credentials for API access
_env_file = ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# File per logging unknown games
UNKNOWN_LOG_FILE = ROOT / "data" / "unknown_games.json"


def extract_appid(steam_url: str) -> str | None:
    """Estrae l'appid Steam da un URL."""
    if not steam_url:
        return None
    parts = steam_url.rstrip("/").split("/")
    if len(parts) >= 2 and parts[-2].isdigit():
        return parts[-2]
    if len(parts) >= 1 and parts[-1].isdigit():
        return parts[-1]
    return None


def get_coop_type_with_retry(
    game: dict, max_retries: int = 3
) -> tuple[int, str, str, dict]:
    """
    Processa un singolo gioco con retry logic e multi-source validation.

    Returns: (game_id, title, coop_type, verdict)
    """
    game_id = game.get("id")
    title = game.get("title", "Unknown")
    steam_url = game.get("steamUrl", "")
    previous_type = game.get("coopType", "")

    appid = extract_appid(steam_url)
    if not appid:
        return game_id, title, "UNKNOWN", {"error": "No Steam URL"}

    last_error = None

    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            # Multi-source validation: Steam + IGDB + GOG + RAWG
            verdict = quality_gate.validate(
                appid,
                sources=frozenset({"steam", "igdb", "gog", "rawg"}),
                rate_limit_delay=0.5,
            )

            coop_type = verdict.get("coop_type")

            # Se ha un tipo valido, ritorna
            if coop_type and coop_type != "UNKNOWN":
                # Check per cambiamento di stato
                if previous_type and previous_type != coop_type:
                    verdict["_state_changed"] = True
                    verdict["_previous_type"] = previous_type
                return game_id, title, coop_type, verdict

            # Se è UNKNOWN, retry
            last_error = verdict.get("reason", "Unknown error")
            if attempt < max_retries - 1:
                delay = 2**attempt  # 1s, 2s, 4s
                time.sleep(delay)
                continue

        except Exception as e:
            last_error = str(e)[:100]
            if attempt < max_retries - 1:
                delay = 2**attempt
                time.sleep(delay)
                continue

    # Tutti i tentativi falliti → logga per review
    return (
        game_id,
        title,
        "UNKNOWN",
        {
            "error": last_error,
            "attempts": max_retries,
            "appid": appid,
        },
    )


def log_unknown_game(game_id: int, title: str, verdict: dict):
    """Logga un gioco unknown per review manuale."""
    unknown_data = {"lastUpdated": None, "count": 0, "games": []}

    if UNKNOWN_LOG_FILE.exists():
        try:
            unknown_data = json.loads(UNKNOWN_LOG_FILE.read_text(encoding="utf-8"))
        except:
            pass

    # Check se già presente
    existing = [g for g in unknown_data.get("games", []) if g["id"] == game_id]
    if existing:
        # Aggiorna
        existing[0].update(
            {
                "lastRetry": datetime.now().isoformat(),
                "lastError": verdict.get("error", ""),
            }
        )
    else:
        # Aggiungi nuovo
        unknown_data["games"].append(
            {
                "id": game_id,
                "title": title,
                "steamUrl": verdict.get("appid", ""),
                "firstSeen": datetime.now().isoformat(),
                "lastRetry": datetime.now().isoformat(),
                "lastError": verdict.get("error", ""),
                "attempts": verdict.get("attempts", 0),
            }
        )

    unknown_data["lastUpdated"] = datetime.now().isoformat()
    unknown_data["count"] = len(unknown_data["games"])

    UNKNOWN_LOG_FILE.write_text(json.dumps(unknown_data, indent=2, ensure_ascii=False))


def main(dry_run=True, force=False):
    print("=== Backfill coopType - Enhanced ===\n")
    print("Features: Retry (3x), Multi-source, State monitoring, Unknown logging\n")

    # Load catalog
    with open(ROOT / "data" / "catalog.games.v1.json") as f:
        catalog = json.load(f)

    games = catalog.get("games", [])
    print(f"Caricati {len(games)} giochi")

    # Filter games with Steam URL
    games_with_steam = [g for g in games if g.get("steamUrl")]
    print(f"Giochi con Steam URL: {len(games_with_steam)}")

    # Check which already have coopType
    games_with_coop_type = [g for g in games if g.get("coopType")]
    print(f"Giochi con coopType già presente: {len(games_with_coop_type)}")

    if force:
        games_to_process = games_with_steam
        print(f"FORCE: ricalcolo per tutti i {len(games_to_process)} giochi")
    else:
        games_to_process = [g for g in games_with_steam if not g.get("coopType")]
        print(f"Giochi da elaborare: {len(games_to_process)}")

    if not games_to_process:
        print("\n✅ Nessun gioco da elaborare!")
        return

    if dry_run:
        print("\n🔍 Modalità DRY-RUN - nessuna modifica scritta\n")

    results = {}
    state_changes = {"upgrades": [], "downgrades": [], "warnings": []}
    unknown_games = []

    # Process in batches
    batch_size = 20
    for i in range(0, len(games_to_process), batch_size):
        batch = games_to_process[i : i + batch_size]
        print(
            f"Elaborazione batch {i // batch_size + 1}/{(len(games_to_process) - 1) // batch_size + 1}..."
        )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(get_coop_type_with_retry, g): g for g in batch}
            for future in as_completed(futures):
                game_id, title, coop_type, verdict = future.result()
                results[game_id] = coop_type

                # Check state changes
                if verdict.get("_state_changed"):
                    previous = verdict.get("_previous_type")
                    if coop_type == "PVP":
                        state_changes["downgrades"].append(
                            {
                                "id": game_id,
                                "title": title,
                                "from": previous,
                                "to": coop_type,
                            }
                        )
                    elif previous == "MIXED" and coop_type == "COOP":
                        state_changes["upgrades"].append(
                            {
                                "id": game_id,
                                "title": title,
                                "from": previous,
                                "to": coop_type,
                            }
                        )
                    else:
                        state_changes["warnings"].append(
                            {
                                "id": game_id,
                                "title": title,
                                "from": previous,
                                "to": coop_type,
                            }
                        )

                # Log unknown games
                if coop_type == "UNKNOWN":
                    unknown_games.append({"id": game_id, "title": title})
                    log_unknown_game(game_id, title, verdict)

                # Output
                status_icon = (
                    "✅"
                    if coop_type in ("COOP", "MIXED")
                    else "❌"
                    if coop_type == "PVP"
                    else "⚠️"
                )
                change_indicator = "→" if verdict.get("_state_changed") else ""
                print(
                    f"  {status_icon} ID {game_id}: {title[:30]:30} {change_indicator} → {coop_type}"
                )

        time.sleep(1)

    # Summary
    coop_count = sum(1 for v in results.values() if v == "COOP")
    mixed_count = sum(1 for v in results.values() if v == "MIXED")
    pvp_count = sum(1 for v in results.values() if v == "PVP")
    unknown_count = sum(
        1 for v in results.values() if v not in ("COOP", "MIXED", "PVP")
    )

    print(f"\n=== RISULTATI ===")
    print(f"COOP (solo co-op): {coop_count}")
    print(f"MIXED (co-op + PvP): {mixed_count}")
    print(f"PVP (solo PvP): {pvp_count}")
    print(f"UNKNOWN/ERROR: {unknown_count}")

    # State changes summary
    if state_changes["upgrades"]:
        print(f"\n✅ UPGRADES (MIXED → COOP): {len(state_changes['upgrades'])}")
        for u in state_changes["upgrades"]:
            print(f"  - {u['title']}")

    if state_changes["warnings"]:
        print(f"\n⚠️  STATE CHANGES: {len(state_changes['warnings'])}")
        for w in state_changes["warnings"]:
            print(f"  - {w['title']}: {w['from']} → {w['to']}")

    if unknown_count > 0:
        print(f"\n⚠️  Unknown games loggati in: {UNKNOWN_LOG_FILE}")

    if not dry_run:
        # Update catalog
        updated = 0
        games_to_remove = []

        for game in games:
            game_id = game.get("id")
            if game_id in results:
                previous_type = game.get("coopType", "")
                new_type = results[game_id]

                # Check se deve essere rimosso
                if new_type == "PVP":
                    games_to_remove.append(game_id)
                    print(
                        f"❌ REMOVED: {game.get('title')} ({game_id}) - changed to PvP"
                    )
                    continue

                # Aggiorna
                game["coopType"] = new_type
                game["lastValidated"] = datetime.now().isoformat()
                updated += 1

        # Rimuovi PvP
        for gid in games_to_remove:
            catalog["games"] = [g for g in catalog["games"] if g.get("id") != gid]

        # Save
        catalog["stats"]["games"] = len(catalog["games"])
        with open(ROOT / "data" / "catalog.games.v1.json", "w") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        # Also update catalog.public.v1.json
        with open(ROOT / "data" / "catalog.public.v1.json") as f:
            public_catalog = json.load(f)

        for game in public_catalog.get("games", []):
            game_id = game.get("id")
            if game_id in results:
                game["coopType"] = results[game_id]
                game["lastValidated"] = datetime.now().isoformat()

        with open(ROOT / "data" / "catalog.public.v1.json", "w") as f:
            json.dump(public_catalog, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Catalogo aggiornato ({updated} giochi)")

        if pvp_count > 0:
            print(f"\n⚠️  ATTENZIONE: {pvp_count} giochi PvP rimossi!")
    else:
        print("\n🔍 Eseguire senza --dry-run per applicare le modifiche")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    main(dry_run, force)
