#!/usr/bin/env python3
"""
remove_game.py — Rimuove un gioco dal catalogo in modo permanente e corretto.

Uso:
    python3 scripts/remove_game.py <id_gioco> [--reason "motivo"]
    python3 scripts/remove_game.py 619
    python3 scripts/remove_game.py 619 --reason "VR niche, <50 reviews"

Cosa fa:
    1. Cerca il gioco per ID in assets/games.js
    2. Estrae il suo Steam appid (se presente)
    3. Rimuove il blocco dal games.js
    4. Aggiunge l'appid a data/excluded_games.json (previene re-ingestion)
    5. Rigenera data/catalog.public.v1.json via run_curation_gate
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

GAMES_JS = Path("assets/games.js")
EXCLUDED_PATH = Path("data/excluded_games.json")


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


def find_game_block(content: str, game_id: int) -> tuple[int, int] | None:
    """Trova start/end del blocco { id: <game_id>, ... } in games.js."""
    # Trova la riga con id: <game_id>
    pattern = re.compile(r"\bid\s*:\s*" + str(game_id) + r"\b")
    match = pattern.search(content)
    if not match:
        return None

    # Risali al { di apertura del blocco
    start = content.rfind("{", 0, match.start())
    if start == -1:
        return None

    # Trova il } di chiusura (depth tracking)
    depth = 0
    i = start
    while i < len(content):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                # Includi la virgola/newline dopo il blocco se presente
                while end < len(content) and content[end] in " \t":
                    end += 1
                if end < len(content) and content[end] == ",":
                    end += 1
                while end < len(content) and content[end] in " \t\n":
                    end += 1
                return start, end
        i += 1
    return None


def extract_appid(block: str) -> str | None:
    m = re.search(r"steamUrl\s*:\s*[\"']https?://store\.steampowered\.com/app/(\d+)", block)
    if m:
        return m.group(1)
    return None


def extract_title(block: str, game_id: int) -> str:
    m = re.search(r'title\s*:\s*["\']([^"\']+)["\']', block)
    return m.group(1) if m else f"ID={game_id}"


def main():
    parser = argparse.ArgumentParser(description="Rimuove un gioco dal catalogo")
    parser.add_argument("game_id", type=int, help="ID numerico del gioco")
    parser.add_argument("--reason", default="", help="Motivo della rimozione (opzionale)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra cosa farebbe senza modificare")
    args = parser.parse_args()

    if not GAMES_JS.exists():
        print(f"❌ {GAMES_JS} non trovato. Esegui dalla root del progetto.")
        sys.exit(1)

    content = GAMES_JS.read_text(encoding="utf-8")
    result = find_game_block(content, args.game_id)

    if not result:
        print(f"❌ Gioco con ID {args.game_id} non trovato in {GAMES_JS}")
        sys.exit(1)

    start, end = result
    block = content[start:end]
    title = extract_title(block, args.game_id)
    appid = extract_appid(block)

    print(f"🎮 Trovato: [{args.game_id}] {title}")
    if appid:
        print(f"   Steam appid: {appid}")
    if args.reason:
        print(f"   Motivo: {args.reason}")

    if args.dry_run:
        print("\n[dry-run] Nessuna modifica applicata.")
        print(f"  - Rimuoverebbe blocco da games.js (righe ~{content[:start].count(chr(10))+1})")
        if appid:
            print(f"  - Aggiungerebbe appid {appid} a excluded_games.json")
        print(f"  - Rigenererebbe catalog.public.v1.json")
        return

    # 1. Rimuovi da games.js
    new_content = content[:start] + content[end:]
    # Assicura non rimangano doppi newline eccessivi
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)
    GAMES_JS.write_text(new_content, encoding="utf-8")
    print(f"✅ Rimosso da {GAMES_JS}")

    # 2. Aggiungi appid a excluded_games.json
    if appid:
        excluded = load_excluded()
        if appid not in excluded:
            excluded.append(appid)
            save_excluded(excluded)
            print(f"✅ Aggiunto appid {appid} a {EXCLUDED_PATH}")
        else:
            print(f"ℹ️  Appid {appid} già in {EXCLUDED_PATH}")

    # 3. Rigenera catalog.public.v1.json
    print("🔄 Rigenero catalog.public.v1.json...")
    result = subprocess.run(
        [sys.executable, "scripts/run_curation_gate.py"],
        capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        print(f"⚠️  run_curation_gate.py ha restituito errore:\n{result.stderr}")
    else:
        print("✅ Catalogo pubblico aggiornato")

    print(f"\n✅ Fatto. [{args.game_id}] {title} rimosso definitivamente.")
    if appid:
        print(f"   L'appid {appid} è ora in excluded_games.json — non rientrerà mai più.")


if __name__ == "__main__":
    main()
