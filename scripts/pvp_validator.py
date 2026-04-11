#!/usr/bin/env python3
"""
PvP Validator: Blocca l'inserimento di giochi PvP nel catalogo
Run: python3 scripts/pvp_validator.py [--check-only]

Usa il campo coopType direttamente dal catalogo (derivato da Steam categories).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(check_only=False):
    """Valida il catalogo."""
    print("=== PvP Validator (coopType-based) ===\n")

    # Carica il catalogo
    with open(ROOT / "data" / "catalog.games.v1.json") as f:
        catalog = json.load(f)

    games = catalog.get("games", [])
    print(f"Analizzando {len(games)} giochi nel catalogo...")

    # Categorizza basandosi su coopType
    pvp_games = []
    mixed_games = []
    coop_games = []
    unknown_games = []

    for game in games:
        coop_type = game.get("coopType", "UNKNOWN")
        title = game.get("title", "Unknown")

        if coop_type == "PVP":
            pvp_games.append({"id": game.get("id"), "title": title})
        elif coop_type == "MIXED":
            mixed_games.append({"id": game.get("id"), "title": title})
        elif coop_type == "COOP":
            coop_games.append(game.get("id"))
        else:
            unknown_games.append({"id": game.get("id"), "title": title})

    # Output
    print(f"\n=== RISULTATI ===")
    print(f"✅ COOP (solo co-op): {len(coop_games)}")
    print(f"⚠️  MIXED (co-op + PvP): {len(mixed_games)}")
    print(f"❌ PVP (solo PvP): {len(pvp_games)}")
    print(f"❓ UNKNOWN (non classificato): {len(unknown_games)}")

    if pvp_games:
        print(f"\n❌ GIOCHI PVP DA RIMUOVERE:")
        for g in pvp_games:
            print(f"  - ID {g['id']}: {g['title']}")

    if unknown_games:
        print(f"\n⚠️  GIOCHI NON CLASSIFICATI ({len(unknown_games)}):")
        for g in unknown_games[:10]:
            print(f"  - ID {g['id']}: {g['title']}")
        if len(unknown_games) > 10:
            print(f"  ... e altri {len(unknown_games) - 10}")

    # Se non in check_only, esci con errore se ci sono PvP
    if not check_only and pvp_games:
        print(f"\n🚫 ERRORE: {len(pvp_games)} giochi PvP nel catalogo!")
        print("Esegui con --check-only per vedere il report senza errore.")
        sys.exit(1)

    print("\n✅ Validazione superata!")
    sys.exit(0)


if __name__ == "__main__":
    check_only = "--check-only" in sys.argv
    main(check_only)
