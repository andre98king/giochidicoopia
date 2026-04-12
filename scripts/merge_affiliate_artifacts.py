#!/usr/bin/env python3
"""
merge_affiliate_artifacts.py
=============================
Mergea i games.js prodotti dai job fetch paralleli nel workflow CI.

Ogni job fetch (affiliate, gameseal, gamivo, k4g, gmg) produce un games.js
con solo i propri campi aggiornati. Questo script li unisce partendo dal
games.js base (db-output di auto-update-db).

Campi gestiti da ogni sorgente:
  - affiliate: igUrl/igDiscount, gbUrl/gbDiscount, kgUrl/kgDiscount, gmvUrl/gmvDiscount
  - gameseal:  gsUrl/gsDiscount, kgUrl/kgDiscount (sovrascrive affiliate per Kinguin)
  - gamivo:    gmvUrl/gmvDiscount (sovrascrive affiliate per GAMIVO)
  - k4g:       k4gUrl/k4gDiscount
  - gmg:       gmgUrl/gmgDiscount

Utilizzo:
    python3 scripts/merge_affiliate_artifacts.py
    Legge i file da data/artifacts/ (popolato dal workflow CI)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES_JS = ROOT / "assets" / "bundles" / "games-data.js"
ARTIFACTS_DIR = ROOT / "data" / "artifacts"

# Mappa: nome artifact → lista di campi da mergeare
STORE_FIELDS = {
    "affiliate": ["igUrl", "igDiscount", "gbUrl", "gbDiscount"],
    "gameseal": ["gsUrl", "gsDiscount", "kgUrl", "kgDiscount"],
    "gamivo": ["gmvUrl", "gmvDiscount"],
    "k4g": ["k4gUrl", "k4gDiscount"],
    "gmg": ["gmgUrl", "gmgDiscount"],
}

# Ordine di merge: gameseal sovrascrive affiliate per Kinguin,
# gamivo sovrascrive affiliate per GAMIVO
MERGE_ORDER = ["affiliate", "gameseal", "gamivo", "k4g", "gmg"]


def load_games_js(path: Path) -> list[dict]:
    """Parse games.js con regex (stesso approccio di catalog_data.py)."""
    content = path.read_text(encoding="utf-8")
    blocks = re.findall(r"\{[^{}]*\}", content, re.DOTALL)
    games = []
    for block in blocks:
        game_id = _extract_int(block, "id")
        if game_id is None:
            continue
        game = {"id": game_id}
        for field in [
            "igdbId",
            "title",
            "categories",
            "genres",
            "coopMode",
            "maxPlayers",
            "crossplay",
            "players",
            "releaseYear",
            "image",
            "description",
            "description_en",
            "personalNote",
            "played",
            "steamUrl",
            "gogUrl",
            "epicUrl",
            "itchUrl",
            "ccu",
            "trending",
            "rating",
            "igUrl",
            "igDiscount",
            "gbUrl",
            "gbDiscount",
            "gsUrl",
            "gsDiscount",
            "kgUrl",
            "kgDiscount",
            "k4gUrl",
            "k4gDiscount",
            "gmvUrl",
            "gmvDiscount",
            "gmgUrl",
            "gmgDiscount",
            "coopScore",
            "mini_review_it",
            "mini_review_en",
        ]:
            game[field] = _extract_field(block, field)
        games.append(game)
    games.sort(key=lambda g: g["id"])
    return games


def _extract_int(block: str, field: str):
    match = re.search(rf"{field}:\s*(-?\d+)", block)
    return int(match.group(1)) if match else None


def _extract_field(block: str, field: str):
    match = re.search(
        rf'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|null|-?\d+)',
        block,
        re.DOTALL,
    )
    if not match:
        return None
    value = match.group(1)
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("["):
        return re.findall(r'"([^"]+)"', value)
    return re.sub(r"\\(.)", r"\1", value.strip('"'))


def js_esc(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def write_games_js(games: list[dict], path: Path) -> None:
    """Scrive games.js nello stesso formato dell'originale."""
    featured_id = 0
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    m = re.search(r"const\s+featuredIndieId\s*=\s*(\d+)\s*;", content)
    if m:
        featured_id = int(m.group(1))

    lines = [f"const featuredIndieId = {featured_id};\n\n", "const games = [\n"]

    for game in games:
        categories_json = json.dumps(game.get("categories") or [], ensure_ascii=False)
        genres_json = json.dumps(game.get("genres") or [], ensure_ascii=False)
        coop_json = json.dumps(game.get("coopMode") or ["online"], ensure_ascii=False)
        lines.append(
            "  {\n"
            f"    id: {game['id']},\n"
            f"    igdbId: {game.get('igdbId') or 0},\n"
            f'    title: "{js_esc(game.get("title", ""))}",\n'
            f"    categories: {categories_json},\n"
            f"    genres: {genres_json},\n"
            f"    coopMode: {coop_json},\n"
            f"    maxPlayers: {game.get('maxPlayers', 4)},\n"
            f"    crossplay: {'true' if game.get('crossplay') else 'false'},\n"
            f'    players: "{js_esc(game.get("players", "1-4"))}",\n'
            f"    releaseYear: {game.get('releaseYear') or 0},\n"
            f'    image: "{js_esc(game.get("image", ""))}",\n'
            f'    description: "{js_esc(game.get("description", ""))}",\n'
            f'    description_en: "{js_esc(game.get("description_en", ""))}",\n'
            f'    personalNote: "{js_esc(game.get("personalNote", ""))}",\n'
            f"    played: {'true' if game.get('played') else 'false'},\n"
            f'    steamUrl: "{js_esc(game.get("steamUrl", ""))}",\n'
            f'    gogUrl: "{js_esc(game.get("gogUrl", ""))}",\n'
            f'    epicUrl: "{js_esc(game.get("epicUrl", ""))}",\n'
            f'    itchUrl: "{js_esc(game.get("itchUrl", ""))}",\n'
            f"    ccu: {game.get('ccu') or 0},\n"
            f"    trending: {'true' if game.get('trending') else 'false'},\n"
            f"    rating: {game.get('rating') or 0},\n"
            f'    igUrl: "{js_esc(game.get("igUrl", ""))}",\n'
            f"    igDiscount: {game.get('igDiscount') or 0},\n"
            f'    gbUrl: "{js_esc(game.get("gbUrl", ""))}",\n'
            f"    gbDiscount: {game.get('gbDiscount') or 0},\n"
            f'    gsUrl: "{js_esc(game.get("gsUrl", ""))}",\n'
            f"    gsDiscount: {game.get('gsDiscount') or 0},\n"
            f'    kgUrl: "{js_esc(game.get("kgUrl", ""))}",\n'
            f"    kgDiscount: {game.get('kgDiscount') or 0},\n"
            f'    k4gUrl: "{js_esc(game.get("k4gUrl", ""))}",\n'
            f"    k4gDiscount: {game.get('k4gDiscount') or 0},\n"
            f'    gmvUrl: "{js_esc(game.get("gmvUrl", ""))}",\n'
            f"    gmvDiscount: {game.get('gmvDiscount') or 0},\n"
            f'    gmgUrl: "{js_esc(game.get("gmgUrl", ""))}",\n'
            f"    gmgDiscount: {game.get('gmgDiscount') or 0},\n"
            f"    coopScore: {json.dumps(game.get('coopScore'))},\n"
            f'    mini_review_it: "{js_esc(game.get("mini_review_it", ""))}",\n'
            f'    mini_review_en: "{js_esc(game.get("mini_review_en", ""))}"\n'
            "  },\n"
        )

    lines.append("];\n")
    full_js = "".join(lines)
    if full_js.count("{") != full_js.count("}"):
        raise ValueError("Brace count mismatch while serializing games.js")
    if len(games) < 50:
        raise ValueError(
            f"Refusing to write suspiciously small catalog: {len(games)} games"
        )

    path.write_text(full_js, encoding="utf-8")


def merge_artifacts(base_games: list[dict], artifact_dir: Path) -> list[dict]:
    """Mergea i campi da ogni artifact nel games.js base."""
    games_by_id = {g["id"]: g for g in base_games}

    for store_name in MERGE_ORDER:
        fields = STORE_FIELDS[store_name]
        artifact_path = artifact_dir / store_name / "games.js"
        if not artifact_path.exists():
            print(f"  ⏭️  {store_name}: artifact non trovato, salto")
            continue

        store_games = load_games_js(artifact_path)
        store_by_id = {g["id"]: g for g in store_games}

        merged = 0
        for game_id, base_game in games_by_id.items():
            store_game = store_by_id.get(game_id)
            if not store_game:
                continue
            for field in fields:
                value = store_game.get(field)
                if value:
                    base_game[field] = value
                    merged += 1

        print(
            f"  ✅ {store_name}: {merged} campi mergeati da {len(store_games)} giochi"
        )

    return list(games_by_id.values())


def run() -> None:
    base_games_js = GAMES_JS
    if not base_games_js.exists():
        print("❌ games.js base non trovato")
        sys.exit(1)

    print(f"📖 Leggo games.js base...")
    base_games = load_games_js(base_games_js)
    print(f"  {len(base_games)} giochi caricati")

    artifact_dir = ARTIFACTS_DIR
    if not artifact_dir.exists():
        print(f"⚠️  Directory artifact non trovata: {artifact_dir}")
        print("  Nessun merge necessario, uso games.js base")
        sys.exit(0)

    print(f"\n🔀 Mergeo artifact da {artifact_dir}...")
    merged_games = merge_artifacts(base_games, artifact_dir)

    print(f"\n💾 Scrivo games.js finale...")
    write_games_js(sorted(merged_games, key=lambda g: g["id"]), base_games_js)
    print(f"  ✅ games.js scritto con {len(merged_games)} giochi")


if __name__ == "__main__":
    run()
