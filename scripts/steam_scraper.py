#!/usr/bin/env python3
"""
Steam Store Co-op Scraper — ricerca per categoria, non per keyword.

Cerca giochi con categorie co-op reali su Steam:
  9  = Online Co-op
  39 = Local Co-op
  24 = Shared/Split Screen
  48 = LAN Co-op
  44 = Remote Play Together

Output: data/steam_coop_games.json  [{title, app_id, steam_url, categories}]
"""

import json
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import quality_gate  # usa il singleton cloudscraper

COOP_CATEGORIES = {
    9:  "Online Co-op",
    39: "Local Co-op",
    24: "Shared/Split Screen",
    48: "LAN Co-op",
    44: "Remote Play Together",
}

MAX_PER_CATEGORY = 500   # Steam mostra max ~500 risultati per ricerca
PAGE_DELAY       = 1.5   # secondi tra pagine


def search_by_category(cat_id: int, cat_name: str, max_results: int = MAX_PER_CATEGORY) -> dict[str, dict]:
    """Cerca su Steam store per categoria co-op. Ritorna {app_id: {title, app_id, steam_url}}."""
    scraper = quality_gate._get_scraper()
    games: dict[str, dict] = {}
    page = 1

    print(f"  [{cat_id}] {cat_name}...")

    while len(games) < max_results:
        try:
            r = scraper.get(
                "https://store.steampowered.com/search/",
                params={"category3": cat_id, "page": page},
                timeout=30,
            )
        except Exception as e:
            print(f"    Pagina {page}: errore {e}")
            break

        if r.status_code != 200:
            print(f"    Pagina {page}: HTTP {r.status_code}")
            break

        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select(".search_result_row")
        if not rows:
            break

        for row in rows:
            app_id = row.get("data-ds-appid", "").strip()
            if not app_id:
                continue
            title_el = row.select_one(".title")
            title = title_el.get_text(strip=True) if title_el else ""
            if app_id not in games:
                games[app_id] = {
                    "title":     title,
                    "app_id":    app_id,
                    "steam_url": f"https://store.steampowered.com/app/{app_id}/",
                    "categories": [],
                }
            if cat_name not in games[app_id]["categories"]:
                games[app_id]["categories"].append(cat_name)

        # Paginazione: Steam non ha "next" button fisso, usa il count per capire se finito
        if len(rows) < 25:
            break  # ultima pagina

        page += 1
        time.sleep(PAGE_DELAY)

    print(f"    → {len(games)} giochi unici")
    return games


def main() -> None:
    print("=" * 55)
    print("STEAM CO-OP SCRAPER — per categoria")
    print("=" * 55)

    all_games: dict[str, dict] = {}

    for cat_id, cat_name in COOP_CATEGORIES.items():
        found = search_by_category(cat_id, cat_name)
        for app_id, game in found.items():
            if app_id in all_games:
                for c in game["categories"]:
                    if c not in all_games[app_id]["categories"]:
                        all_games[app_id]["categories"].append(c)
            else:
                all_games[app_id] = game
        time.sleep(2)

    result = list(all_games.values())
    out = ROOT / "data" / "steam_coop_games.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nTotale giochi unici: {len(result)}")
    print(f"Salvato in {out.name}")

    # Sample
    for g in result[:5]:
        print(f"  [{g['app_id']}] {g['title'][:45]:<45}  {g['categories']}")


if __name__ == "__main__":
    main()
