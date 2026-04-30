#!/usr/bin/env python3
"""
remove_game.py — Rimuove un gioco dal catalogo in modo permanente e corretto.

Uso:
    python3 scripts/remove_game.py <id_gioco> [--reason "motivo"]
    python3 scripts/remove_game.py 619
    python3 scripts/remove_game.py 619 --reason "VR niche, <50 reviews"

Cosa fa:
    1. Carica il catalogo tramite catalog_data.load_games()
    2. Trova il gioco per ID
    3. Estrae il suo Steam appid (se presente)
    4. Rimuove il gioco dalla lista e riscrive games.js/games-data.js
    5. Aggiunge l'appid a data/excluded_games.json (previene re-ingestion)
    6. Rigenera data/catalog.public.v1.json

NOTA: questo script è compatibile con il bundle split introdotto in v1.2
(games.js = loader, games-data.js = dati).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Import catalog_data using the same pattern as other scripts
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import catalog_data

EXCLUDED_PATH = ROOT / "data" / "excluded_games.json"


def load_excluded() -> list:
    if EXCLUDED_PATH.exists():
        try:
            return json.loads(EXCLUDED_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_excluded(appids: list) -> None:
    EXCLUDED_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXCLUDED_PATH.write_text(
        json.dumps(sorted(set(appids)), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def extract_appid(steam_url: str) -> str | None:
    m = re.search(r"/app/(\d+)", steam_url or "")
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(description="Rimuove un gioco dal catalogo")
    parser.add_argument("game_id", type=int, help="ID numerico del gioco")
    parser.add_argument("--reason", default="", help="Motivo della rimozione (opzionale)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra cosa farebbe senza modificare")
    args = parser.parse_args()

    # Load the catalog via the canonical API (handles both loader and data bundle)
    games = catalog_data.load_games()

    # Find the game
    game_index = None
    game = None
    for i, g in enumerate(games):
        if g["id"] == args.game_id:
            game_index = i
            game = g
            break

    if game is None:
        print(f"❌ Gioco con ID {args.game_id} non trovato nel catalogo")
        sys.exit(1)

    title = game.get("title", f"ID={args.game_id}")
    appid = extract_appid(game.get("steamUrl", ""))

    print(f"🎮 Trovato: [{args.game_id}] {title}")
    if appid:
        print(f"   Steam appid: {appid}")
    if args.reason:
        print(f"   Motivo: {args.reason}")
    print(f"   Catalogo attuale: {len(games)} giochi")

    if args.dry_run:
        print("\n[dry-run] Nessuna modifica applicata.")
        print(f"  - Rimuoverebbe gioco {args.game_id} dal catalogo")
        print(f"  - Catalogo risultante: {len(games) - 1} giochi")
        if appid:
            print(f"  - Aggiungerebbe appid {appid} a {EXCLUDED_PATH}")
        print(f"  - Rigenererebbe catalog.public.v1.json")
        return

    # 1. Remove from the list
    removed = games.pop(game_index)
    print(f"✅ Rimosso [{removed['id']}] {removed.get('title', '?')} dal catalogo in memoria")

    # 2. Write back via the canonical API (handles both files and normalisation)
    featured_indie_id = catalog_data.parse_featured_indie_id(
        catalog_data.GAMES_JS.read_text(encoding="utf-8")
    )
    catalog_data.write_legacy_games_js(games, featured_indie_id)
    print(f"✅ Catalogo aggiornato: {len(games)} giochi scritti su games.js + games-data.js")

    # 3. Regenerate JSON artifacts
    catalog_data.write_catalog_artifact(games)
    catalog_data.write_public_catalog_export(games)
    print("✅ JSON artifacts aggiornati: catalog.games.v1.json + catalog.public.v1.json")

    # 4. Add appid to excluded_games.json
    if appid:
        excluded = load_excluded()
        if appid not in excluded:
            excluded.append(appid)
            save_excluded(excluded)
            print(f"✅ Aggiunto appid {appid} a {EXCLUDED_PATH}")
        else:
            print(f"ℹ️  Appid {appid} già in {EXCLUDED_PATH}")

    print(f"\n✅ Fatto. [{args.game_id}] {title} rimosso definitivamente.")
    if appid:
        print(f"   L'appid {appid} è ora in excluded_games.json — non rientrerà mai più.")


if __name__ == "__main__":
    main()
