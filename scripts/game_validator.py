#!/usr/bin/env python3
"""
Game Validator - Co-op Classifier using Ollama API
Optimized for speed with parallel requests
"""

import json
import re
import requests
from pathlib import Path
from tqdm import tqdm
import concurrent.futures

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "validated_db.json"
OLLAMA_HOST = "http://localhost:11434"

SYSTEM_PROMPT = """Classifica come VALID (co-op) o REJECTED (PvP).
- VALID: co-op PvE, survival collaborativo, hybrid (Rust, Dead by Daylight, Phasmophobia, Deep Rock, Helldivers 2, Terraria, It Takes Two)
- REJECTED: PvP (shooter, MOBA, Battle Royale, sports, esports) - CS2, Apex, R6, Valorant, Dota, LoL, Overwatch, FC25, PUBG
- The Outlast Trials = VALID (co-op PvE horror)

Rispondi SOLO JSON: {"status": "VALID"|"REJECTED", "category": "...", "reason": "..."""


def classify_game_api(model: str, game_data: dict) -> dict:
    """Classify using Ollama API (fast, no reload)."""
    title = game_data["title"]

    prompt = f"""Game: {title}

{SYSTEM_PROMPT}

Rispondi SOLO JSON."""

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 150},
            },
            timeout=60,
        )

        if resp.status_code != 200:
            return {
                "game": title,
                "status": "ERROR",
                "reason": f"API error: {resp.status_code}",
            }

        response = resp.json().get("response", "").strip()

        # Parse JSON
        try:
            parsed = json.loads(response)
        except:
            match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                return {"game": title, "status": "ERROR", "reason": "No JSON"}

        return {
            "game": title,
            "status": parsed.get("status", "REJECTED"),
            "category": parsed.get("category", "Unknown"),
            "reason": parsed.get("reason", ""),
            "sources": game_data.get("sources", []),
        }

    except Exception as e:
        return {"game": title, "status": "ERROR", "reason": str(e)}


def load_games():
    """Load games from all sources."""
    sources = {
        "steam": ROOT / "data" / "steam_coop_games.json",
        "igdb": ROOT / "data" / "igdb_coop_games.json",
        "rawg": ROOT / "data" / "rawg_coop_games.json",
        "gog": ROOT / "data" / "gog_coop_games.json",
    }

    all_games = {}
    for source, fp in sources.items():
        if fp.exists():
            with open(fp) as f:
                for game in json.load(f):
                    title = (game.get("title") or game.get("name") or "").strip()
                    if title and title not in all_games:
                        all_games[title] = {"title": title, "sources": [], "data": {}}
                    if title:
                        all_games[title]["sources"].append(source)
                        all_games[title]["data"][source] = game

    return list(all_games.values())


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--max", type=int, default=None)
    parser.add_argument("--continue", dest="cont", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    print(f"=== Game Validator === Model: {args.model}, Workers: {args.workers}")

    games = load_games()
    print(f"Total: {len(games)} games")

    # Continue option
    done = []
    if args.cont and OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            done = json.load(f)
        done_titles = {g["game"] for g in done}
        games = [g for g in games if g["title"] not in done_titles]
        print(f"Continuing: {len(done)} done, {len(games)} remaining")

    if args.max:
        games = games[: args.max]

    print(f"Processing {len(games)} games...")

    results = done.copy()

    # Parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(classify_game_api, args.model, g): g for g in games}

        for f in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(games),
            desc="Validating",
        ):
            result = f.result()
            results.append(result)

            if len(results) % 20 == 0:
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(results, f, indent=2)

    # Save final
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    valid = sum(1 for r in results if r["status"] == "VALID")
    rejected = sum(1 for r in results if r["status"] == "REJECTED")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print(f"\n=== Results ({len(results)} total) ===")
    print(f"VALID: {valid}, REJECTED: {rejected}, ERRORS: {errors}")


if __name__ == "__main__":
    main()
