#!/usr/bin/env python3
"""
Co-op Game Classifier using Ollama via subprocess - Batch version
Processes games one by one and saves progress incrementally
"""

import subprocess
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "data" / "coop_classification_results.json"


def classify_game_subprocess(model, title, coop_mode):
    """Classify using subprocess."""

    prompt = f"""Is this video game primarily CO-OP or PvP?

Game: "{title}"
Database co-op modes: {", ".join(coop_mode) if coop_mode else "none"}

Classification rules:
- CO-OP = players work TOGETHER to complete objectives (campaign, missions, raids) against AI/bosses
- PvP = players compete AGAINST each other (deathmatch, MOBA, tactical shooter, battle royale)
- MIXED = has both co-op campaign AND significant PvP modes (Rust, GTA Online, Sea of Thieves)

STRICT rules:
- PvP tactical shooters (CS2, Rainbow Six, Valorant, COD) = NO
- PvP battle royale (Apex, Fortnite, PUBG) = NO
- PvP MOBAs (LoL, Dota) = NO
- Co-op shooters (Deep Rock, Helldivers, Borderlands) = YES
- Co-op campaigns (It Takes Two, A Way Out) = YES
- Co-op survival without PvP (Don't Starve, Valheim) = YES
- Survival with PvP (Rust, DayZ) = MIXED
- Open world with PvP option (GTA Online) = MIXED

Answer with ONE word: YES | NO | MIXED"""

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=120,
            input="",
        )

        response = result.stdout.strip()

        # Clean ANSI
        response = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", response)
        response = response.strip()

        # Take last part after "done thinking"
        if "done thinking" in response.lower():
            response = response.split("done thinking")[-1].strip()

        check_text = response[:80].upper()

        if "YES" in check_text and "NO" not in check_text:
            return "YES", response[:150]
        elif "NO" in check_text:
            return "NO", response[:150]
        elif "MIXED" in check_text:
            return "MIXED", response[:150]
        else:
            return "UNKNOWN", response[:150]

    except Exception as e:
        return "ERROR", str(e)


def load_catalog():
    """Load catalog from JSON."""
    with open(ROOT / "data" / "catalog.games.v1.json") as f:
        data = json.load(f)

    games = []
    for game in data.get("games", []):
        games.append(
            {
                "id": game.get("id"),
                "title": game.get("title", ""),
                "coopMode": game.get("coopMode", []),
            }
        )

    return games


def load_existing_results():
    """Load existing results if any."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []


def save_results(results):
    """Save results to file."""
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)


def validate_catalog(model="qwen3:14b", max_games=100, start_from=0):
    print(f"=== Co-op Classifier via subprocess ===\n")

    games = load_catalog()
    print(f"Loaded {len(games)} games")

    # Load existing results
    results = load_existing_results()
    processed_ids = {r["id"] for r in results}
    print(f"Already processed: {len(processed_ids)} games")

    # Filter to unprocessed games - process ALL remaining, don't skip by index
    if start_from > 0:
        games = [
            g for g in games if g["id"] >= start_from and g["id"] not in processed_ids
        ]
    else:
        games = [g for g in games if g["id"] not in processed_ids]

    if max_games:
        games = games[:max_games]

    print(f"Processing {len(games)} games...\n")

    for i, g in enumerate(games):
        print(
            f"[{i + 1}/{len(games)}] ID {g['id']}: {g['title'][:35]}...",
            end=" ",
            flush=True,
        )

        label, reasoning = classify_game_subprocess(model, g["title"], g["coopMode"])

        results.append(
            {
                "id": g["id"],
                "title": g["title"],
                "current_coopMode": g["coopMode"],
                "classification": label,
                "reasoning": reasoning[:100],
            }
        )

        print(f"→ {label}")

        # Save incrementally every 5 games
        if (i + 1) % 5 == 0:
            save_results(results)
            print(f"  [Saved {i + 1} results]")

    # Final save
    save_results(results)

    # Summary
    yes = sum(1 for r in results if r["classification"] == "YES")
    no = sum(1 for r in results if r["classification"] == "NO")
    mixed = sum(1 for r in results if r["classification"] == "MIXED")
    unknown = sum(1 for r in results if r["classification"] in ("UNKNOWN", "ERROR"))

    print(f"\n=== Total Results ({len(results)} games) ===")
    print(f"YES (Co-op): {yes}")
    print(f"NO (PvP): {no}")
    print(f"MIXED: {mixed}")
    print(f"UNKNOWN/ERROR: {unknown}")


if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3:14b"
    max_games = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    start_from = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    validate_catalog(model, max_games, start_from)
