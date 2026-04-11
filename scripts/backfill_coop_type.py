#!/usr/bin/env python3
"""
Backfill coopType per i giochi esistenti nel catalogo.

Questo script:
1. Legge il catalogo games.js
2. Per ogni gioco con Steam URL, chiama quality_gate.validate() per ottenere coopType
3. Aggiorna il campo coopType nel game dict
4. Salva il catalogo aggiornato

Run: python3 scripts/backfill_coop_type.py [--dry-run]
"""

import json
import os
import sys
import time
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


def get_coop_type_for_game(game: dict) -> tuple[int, str, str]:
    """
    Processa un singolo gioco e ritorna (id, title, coop_type).
    Usa validation con tutte le fonti disponibili (Steam + IGDB + GOG).
    """
    game_id = game.get("id")
    title = game.get("title", "Unknown")
    steam_url = game.get("steamUrl", "")

    appid = extract_appid(steam_url)
    if not appid:
        # Prova a usare IGDB per giochi non-Steam
        igdb_id = game.get("igdbId")
        if igdb_id:
            # TODO: implementare validazione IGDB
            pass
        return game_id, title, "UNKNOWN"

    try:
        # Usa tutte le fonti disponibili
        verdict = quality_gate.validate(
            appid,
            sources=frozenset({"steam", "igdb", "gog"}),  # Multi-source
            rate_limit_delay=0.5,
        )

        coop_type = verdict.get("coop_type")

        # Fallback: se coop_type è None, deriva dal status
        if coop_type is None:
            status = verdict.get("status")
            if status == "rejected":
                # Check se è PvP o solo nessuna category
                if verdict.get("pvp_signals"):
                    coop_type = "PVP"
                else:
                    coop_type = "UNKNOWN"
            elif status == "approved":
                coop_type = "COOP"
            elif status == "needs_review":
                coop_type = "MIXED"

        return game_id, title, coop_type if coop_type else "UNKNOWN"
    except Exception as e:
        return game_id, title, f"ERROR: {str(e)[:50]}"


def main(dry_run=True, force=False):
    print("=== Backfill coopType per catalogo esistente ===\n")

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

    # Process in batches to avoid overwhelming the API
    batch_size = 20
    for i in range(0, len(games_to_process), batch_size):
        batch = games_to_process[i : i + batch_size]
        print(
            f"Elaborazione batch {i // batch_size + 1}/{(len(games_to_process) - 1) // batch_size + 1}..."
        )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(get_coop_type_for_game, g): g for g in batch}
            for future in as_completed(futures):
                game_id, title, coop_type = future.result()
                results[game_id] = coop_type
                status_icon = (
                    "✅"
                    if coop_type in ("COOP", "MIXED")
                    else "❌"
                    if coop_type == "PVP"
                    else "⚠️"
                )
                print(f"  {status_icon} ID {game_id}: {title[:35]:35} → {coop_type}")

        time.sleep(1)  # Rate limit

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

    if not dry_run:
        # Update catalog
        updated = 0
        for game in games:
            game_id = game.get("id")
            if game_id in results:
                game["coopType"] = results[game_id]
                updated += 1

        # Save
        with open(ROOT / "data" / "catalog.games.v1.json", "w") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        # Also update catalog.public.v1.json
        with open(ROOT / "data" / "catalog.public.v1.json") as f:
            public_catalog = json.load(f)

        for game in public_catalog.get("games", []):
            game_id = game.get("id")
            if game_id in results:
                game["coopType"] = results[game_id]

        with open(ROOT / "data" / "catalog.public.v1.json", "w") as f:
            json.dump(public_catalog, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Catalogo aggiornato ({updated} giochi)")

        if pvp_count > 0:
            print(f"\n⚠️  ATTENZIONE: {pvp_count} giochi PvP rilevati nel catalogo!")
            print("Raccomandazione: eseguire pulizia manuale")
    else:
        print("\n🔍 Eseguire senza --dry-run per applicare le modifiche")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    main(dry_run, force)
