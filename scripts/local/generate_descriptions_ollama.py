#!/usr/bin/env python3
"""
Genera descrizioni IT + EN per giochi thin (< 150 char) senza steamUrl
usando Ollama locale (qwen2.5-coder:14b).

Utilizzo:
    python3 scripts/generate_descriptions_ollama.py
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog_data

MIN_DESC_LEN = 300  # Rigenera tutto con modello migliore
OLLAMA_URL = "http://localhost:8080/v1/chat/completions"  # llama-server OpenAI-compatible
OLLAMA_MODEL = "mistral-small-3.1-24b"


def coop_mode_label(coop_modes: list) -> str:
    labels = []
    if "local" in coop_modes or "split" in coop_modes:
        labels.append("locale")
    if "online" in coop_modes:
        labels.append("online")
    if "sofa" in coop_modes:
        labels.append("divano")
    return " e ".join(labels) if labels else "cooperativa"


def coop_mode_label_en(coop_modes: list) -> str:
    labels = []
    if "local" in coop_modes or "split" in coop_modes:
        labels.append("local")
    if "online" in coop_modes:
        labels.append("online")
    if "sofa" in coop_modes:
        labels.append("couch")
    return " and ".join(labels) if labels else "co-op"


def build_prompt_it(game: dict) -> str:
    title = game["title"]
    coop = coop_mode_label(game.get("coopMode") or [])
    players = game.get("players") or f"2-{game.get('maxPlayers', 4)}"
    cats = game.get("categories") or []
    genres = game.get("genres") or []
    tags = [c for c in cats if c not in ("indie", "splitscreen", "free")] + genres
    tag_str = ", ".join(tags[:3]) if tags else "indie"
    existing = (game.get("description") or "").strip()

    if existing:
        expand = f'Partendo da questa breve descrizione: "{existing}", scrivine una versione espansa e coinvolgente.'
    else:
        expand = f"Scrivi una descrizione coinvolgente."

    return (
        f'{expand} '
        f'Il gioco si chiama "{title}", è co-op {coop} per {players} giocatori, tag: {tag_str}. '
        f'Scrivi 2-3 frasi in italiano fluente. Non inventare trama specifica. '
        f'Rispondi SOLO con la descrizione.'
    )


def build_prompt_en(game: dict) -> str:
    title = game["title"]
    coop = coop_mode_label_en(game.get("coopMode") or [])
    players = game.get("players") or f"2-{game.get('maxPlayers', 4)}"
    cats = game.get("categories") or []
    genres = game.get("genres") or []
    tags = [c for c in cats if c not in ("indie", "splitscreen", "free")] + genres
    tag_str = ", ".join(tags[:3]) if tags else "indie"
    existing_en = (game.get("description_en") or "").strip()

    if existing_en:
        expand = f'Starting from this short description: "{existing_en}", write an expanded and engaging version.'
    else:
        expand = f"Write an engaging description."

    return (
        f'{expand} '
        f'The game is called "{title}", it is a {coop} co-op game for {players} players, tags: {tag_str}. '
        f'Write 2-3 sentences in fluent English. Do not invent specific plot details. '
        f'Reply ONLY with the description.'
    )


def ollama_generate(prompt: str, retries: int = 2) -> str | None:
    # llama-server OpenAI-compatible API
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.7,
        "stream": False,
    }
    for attempt in range(retries + 1):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            choices = r.json().get("choices", [])
            text = choices[0]["message"]["content"].strip() if choices else ""
            return text if text else None
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                print(f"    [ERRORE llama-server] {e}")
                return None


def clean_generated(text: str, max_len: int = 250) -> str:
    """Pulisce output Ollama: rimuove prefissi comuni, tronca a frase intera."""
    if not text:
        return ""
    # Rimuovi prefissi tipo "Descrizione:", "Here is:", ecc.
    text = re.sub(r"^(Descrizione|Description|Ecco|Here is|Sure|Certamente)[:\s]+", "", text, flags=re.IGNORECASE).strip()
    # Rimuovi virgolette iniziali/finali e parentesi tipo (150-190 caratteri)
    text = text.strip('"').strip("'").strip()
    text = re.sub(r"\s*\(\d+[-–]\d+ caratteri\)", "", text).strip()
    # Tronca a frase intera a max_len
    if len(text) > max_len:
        cut = text[:max_len]
        last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        if last_dot > 120:
            text = text[:last_dot + 1]
        else:
            text = cut.rsplit(" ", 1)[0] + "…"
    return text


def main() -> None:
    import concurrent.futures

    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()

    thin = [
        g for g in games
        if not g.get("steamUrl")
        and len((g.get("description") or "").strip()) < MIN_DESC_LEN
    ]
    print(f"Giochi thin non-Steam (< {MIN_DESC_LEN} char): {len(thin)}")
    print(f"Modello: {OLLAMA_MODEL}")
    print(f"Modalità: parallela (IT+EN simultanee per ogni gioco)\n")

    def generate_both(game: dict) -> tuple[dict, bool]:
        """Genera IT e EN in parallelo per un gioco."""
        title = game["title"]
        old_len_it = len((game.get("description") or "").strip())
        old_len_en = len((game.get("description_en") or "").strip())

        # Genera in parallelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            it_future = executor.submit(ollama_generate, build_prompt_it(game))
            en_future = executor.submit(ollama_generate, build_prompt_en(game))
            desc_it = clean_generated(it_future.result() or "")
            desc_en = clean_generated(en_future.result() or "")

        changed = False
        if desc_it and len(desc_it) > old_len_it:
            game["description"] = desc_it
            changed = True
        if desc_en and len(desc_en) > old_len_en:
            game["description_en"] = desc_en
            changed = True

        return game, changed

    updated = 0
    for i, game in enumerate(thin, 1):
        title = game["title"]
        print(f"[{i:3}/{len(thin)}] {title}", end=" ... ", flush=True)

        game, changed = generate_both(game)

        if changed:
            updated += 1
            new_it = len(game.get("description") or "")
            new_en = len(game.get("description_en") or "")
            print(f"✓ IT={new_it}c EN={new_en}c")
        else:
            print(f"× (non migliorava)")

        # Salva ogni 5 giochi (più frequente con parallelo)
        if updated > 0 and i % 5 == 0:
            catalog_data.write_legacy_games_js(games, featured_id)
            catalog_data.write_catalog_artifact(games)
            print(f"  [checkpoint] salvati {updated} aggiornamenti finora")

    print(f"\n✅ Aggiornati: {updated}/{len(thin)}")
    if updated > 0:
        catalog_data.write_legacy_games_js(games, featured_id)
        catalog_data.write_catalog_artifact(games)
        catalog_data.write_public_catalog_export(games)
        print("💾 games.js + catalog salvati")
    else:
        print("Nessuna modifica.")


if __name__ == "__main__":
    main()
