#!/usr/bin/env python3
"""
Co-op Game Classifier using Ollama

Uses local LLM to validate whether games in the catalog are truly co-op.
Uses few-shot learning to teach the model what makes a game co-op.
"""

import json
import requests
import time
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = "http://localhost:11434/api/generate"

# Few-shot examples for training
FEW_SHOT_EXAMPLES = """
## Examples of CO-OP games (answer YES):
- "Borderlands 3" - Multiplayer co-op campaign, 4 players online
- "It Takes Two" - Local and online co-op, 2 players
- "Stardew Valley" - Online co-op up to 4 players
- "Deep Rock Galactic" - Online co-op, 4 players
- "Don't Starve Together" - Online co-op, multiple players
- "Warframe" - Online co-op, multiplayer
- "Divinity: Original Sin 2" - Online/local co-op, 4 players
- "Helldivers 2" - Online co-op, 4 players

## Examples of NON-CO-OP games (answer NO):
- "Counter-Strike 2" - Primarily PvP multiplayer, not co-op campaign
- "League of Legends" - PvP MOBA, no co-op
- "Rocket League" - PvP sports, no co-op
- "Fortnite" - Battle royale with some co-op but mostly PvP
- "Apex Legends" - Battle royale PvP
- "Minecraft" - Can be co-op but primarily single-player/survival
- "Call of Duty: Warzone" - Battle royale PvP
- "Valorant" - PvP tactical shooter

## Examples with MIXED modes (answer MIXED):
- "GTA Online" - Has both co-op missions and PvP
- "Red Dead Online" - Mixed co-op and PvP activities
- "Sea of Thieves" - Co-op sailing but can be PvP
"""


def load_catalog():
    """Load the games catalog."""
    with open(ROOT / "assets" / "games.js") as f:
        content = f.read()

    games = []
    # Simpler pattern - just get id, title, coopMode
    pattern = r'id: (\d+),.*?title: "([^"]+)",.*?coopMode: \[([^\]]*)\]'

    for m in re.finditer(pattern, content, re.DOTALL):
        coop_mode_raw = m.group(3)
        # Parse coop modes
        modes = [
            x.strip().replace('"', "") for x in coop_mode_raw.split(",") if x.strip()
        ]

        games.append(
            {
                "id": int(m.group(1)),
                "title": m.group(2),
                "coopMode": modes,
                "categories": [],  # Will skip for now
            }
        )

    return games


def build_prompt(title, coop_mode, categories):
    """Build classification prompt for a game."""
    coop_modes = ", ".join([m.strip() for m in coop_mode if m.strip()])
    cats = ", ".join([c.strip() for c in categories if c.strip()])

    prompt = f"""You are an expert at identifying co-op video games.

{FEW_SHOT_EXAMPLES}

Now classify this game:

Game: {title}
Current co-op modes in database: {coop_modes}
Categories: {cats}

Is this game a CO-OP game?
Answer format: YES | NO | MIXED

Think step by step, then give your answer."""

    return prompt


def classify_game(model, title, coop_mode, categories):
    """Classify a single game using Ollama."""
    prompt = build_prompt(title, coop_mode, categories)

    # Simpler prompt
    full_prompt = f"""A game classifier. Be brief.

Examples:
- "Borderlands 3" -> YES (co-op game)
- "Counter-Strike 2" -> NO (PvP, not co-op)
- "It Takes Two" -> YES (co-op game)

Game: {title}
Co-op modes: {", ".join(coop_mode) if coop_mode else "none"}

Is this co-op? Answer: YES | NO | MIXED"""

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 30,
        },
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        if resp.status_code == 200:
            result = resp.json()
            response = result.get("response", "").strip()

            import re

            response = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", response)
            response = response.strip()

            if "YES" in response.upper()[:30]:
                return "YES", response
            elif "NO" in response.upper()[:30]:
                return "NO", response
            elif "MIXED" in response.upper()[:30]:
                return "MIXED", response
            else:
                return "UNKNOWN", response
        else:
            return "ERROR", f"Status {resp.status_code}"
    except Exception as e:
        return "ERROR", str(e)


def validate_catalog(model="qwen3:14b", max_games=None):
    """Validate the entire catalog."""
    print(f"=== Co-op Classifier using {model} ===\n")

    games = load_catalog()
    print(f"Loaded {len(games)} games from catalog")

    if max_games:
        games = games[:max_games]
        print(f"Testing on {max_games} games\n")

    results = []

    for i, g in enumerate(games):
        print(f"[{i + 1}/{len(games)}] Validating: {g['title'][:35]}...", end=" ")

        label, reasoning = classify_game(
            model, g["title"], g["coopMode"], g["categories"]
        )

        results.append(
            {
                "id": g["id"],
                "title": g["title"],
                "current_coopMode": g["coopMode"],
                "classification": label,
                "reasoning": reasoning[:200],  # First 200 chars
            }
        )

        print(f"→ {label}")

        time.sleep(0.5)  # Rate limit

    # Save results
    output = ROOT / "data" / "coop_classification_results.json"
    with open(output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== RESULTS ===")
    yes = sum(1 for r in results if r["classification"] == "YES")
    no = sum(1 for r in results if r["classification"] == "NO")
    mixed = sum(1 for r in results if r["classification"] == "MIXED")
    errors = sum(1 for r in results if r["classification"] in ["ERROR", "UNKNOWN"])

    print(f"YES (co-op): {yes}")
    print(f"NO (not co-op): {no}")
    print(f"MIXED: {mixed}")
    print(f"ERROR/UNKNOWN: {errors}")

    # Find discrepancies
    print(f"\n=== DISCREPANCIES ===")
    discrepancies = []
    for r in results:
        current = r["current_coopMode"]
        classified = r["classification"]

        # If classified as NO but has co-op modes -> flag
        if classified == "NO" and any(m.strip() for m in current):
            discrepancies.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "current": current,
                    "issue": "Has co-op mode but classified as NOT co-op",
                }
            )

        # If classified as YES but no co-op modes -> flag
        if classified == "YES" and not any(m.strip() for m in current):
            discrepancies.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "current": current,
                    "issue": "No co-op mode but classified as co-op",
                }
            )

    print(f"Found {len(discrepancies)} discrepancies")

    for d in discrepancies[:10]:
        print(f"  ID {d['id']}: {d['title'][:30]}")
        print(f"    Issue: {d['issue']}")

    # Save discrepancies
    with open(ROOT / "data" / "coop_discrepancies.json", "w") as f:
        json.dump(discrepancies, f, indent=2)

    print(f"\nResults saved to data/coop_classification_results.json")
    print(f"Discrepancies saved to data/coop_discrepancies.json")


if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3:14b"
    max_games = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"Using model: {model}")
    validate_catalog(model, max_games)
