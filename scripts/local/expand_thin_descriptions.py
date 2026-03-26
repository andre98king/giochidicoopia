#!/usr/bin/env python3
"""
Espande le descrizioni thin (< 150 char) dei giochi con steamUrl
fetchando short_description da Steam Store API (IT + EN).

Soglia: descrizioni sotto MIN_DESC_LEN vengono aggiornate solo se
la versione Steam è più lunga di quella esistente.

Utilizzo:
    python3 scripts/expand_thin_descriptions.py
"""
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog_data
from steam_catalog_source import SteamCatalogSource, clean_text

MIN_DESC_LEN = 150  # soglia thin content
TARGET_DESC_LEN = 300  # lunghezza target estratta da detailed_description


def extract_appid(steam_url: str) -> str | None:
    m = re.search(r"/app/(\d+)", steam_url or "")
    return m.group(1) if m else None


def extract_excerpt(html_text: str, max_len: int = TARGET_DESC_LEN) -> str:
    """Estrae excerpt leggibile da HTML Steam (detailed_description).
    Rimuove tag, prende i primi max_len caratteri, tronca a parola intera.
    """
    if not html_text:
        return ""
    # Rimuovi tag HTML
    text = re.sub(r"<[^>]+>", " ", html_text)
    # Normalizza spazi multipli e newline
    text = re.sub(r"\s+", " ", text).strip()
    # Decodifica entità HTML comuni
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    if len(text) <= max_len:
        return text
    # Tronca a parola intera aggiungendo ellissi
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated + "…"


def main() -> None:
    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()
    source = SteamCatalogSource()

    thin = [
        g for g in games
        if g.get("steamUrl") and len((g.get("description") or "").strip()) < MIN_DESC_LEN
    ]
    print(f"Giochi con description < {MIN_DESC_LEN} char e steamUrl: {len(thin)}")

    updated = 0
    for i, game in enumerate(thin, 1):
        appid = extract_appid(game["steamUrl"])
        if not appid:
            print(f"  [{i}/{len(thin)}] {game['title']}: appid non trovato — skip")
            continue

        print(f"  [{i}/{len(thin)}] {game['title']} (appid {appid})...", end=" ", flush=True)

        # Fetch IT — prova short_description, poi detailed_description
        steam_data_it, desc_it = source.fetch_steam_desc(appid, "italian")
        if steam_data_it and len(desc_it or "") < MIN_DESC_LEN:
            longer = extract_excerpt(steam_data_it.get("detailed_description", ""))
            if len(longer) > len(desc_it or ""):
                desc_it = longer
        time.sleep(0.8)

        # Fetch EN
        steam_data_en, desc_en = source.fetch_steam_desc(appid, "english")
        if steam_data_en and len(desc_en or "") < MIN_DESC_LEN:
            longer = extract_excerpt(steam_data_en.get("detailed_description", ""))
            if len(longer) > len(desc_en or ""):
                desc_en = longer
        time.sleep(0.8)

        changed = False
        if desc_it and len(desc_it) > len((game.get("description") or "")):
            game["description"] = desc_it
            changed = True
        if desc_en and len(desc_en) > len((game.get("description_en") or "")):
            game["description_en"] = desc_en
            changed = True

        if changed:
            updated += 1
            new_len = len(game.get("description") or "")
            print(f"✓ aggiornato ({new_len} char)")
        else:
            print("nessun miglioramento")

    print(f"\nAggiornati: {updated}/{len(thin)}")
    if updated > 0:
        catalog_data.write_legacy_games_js(games, featured_id)
        catalog_data.write_catalog_artifact(games)
        catalog_data.write_public_catalog_export(games)
        print("💾 games.js + catalog salvati")
    else:
        print("Nessuna modifica — games.js invariato")


if __name__ == "__main__":
    main()
