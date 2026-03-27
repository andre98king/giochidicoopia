#!/usr/bin/env python3
"""
discover_backfill.py
====================
Trova giochi co-op di qualità usciti su Steam negli ultimi 2-3 anni
che non sono ancora nel catalogo.

Il problema che risolve:
  auto_update.py scopre nuovi giochi nella finestra 90 giorni.
  I giochi usciti PRIMA che la pipeline fosse attiva sono stati persi.
  Questo script fa uno scan storico e produce una lista di candidati
  da revisionare manualmente.

Output: data/backfill_candidates.json

Uso:
  python3 scripts/discover_backfill.py
  python3 scripts/discover_backfill.py --min-year 2021 --max-year 2024 --max-candidates 150
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ─── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
import catalog_data
from catalog_config import BLACKLIST_APPIDS, SKIP_WORDS

ROOT = catalog_data.ROOT
OUTPUT_FILE = ROOT / "data" / "backfill_candidates.json"

STEAMSPY_TAG_URL = "https://steamspy.com/api.php?request=tag&tag={tag}"
APPDETAILS_URL   = "https://store.steampowered.com/api/appdetails"

# Soglie qualità
MIN_RATING      = 72    # % positivo minimo
MIN_REVIEWS     = 80    # recensioni totali minime (pos+neg) per giochi noti
MAX_CANDIDATES  = 120   # max candidati da esaminare con appdetails (limita chiamate API)
TOP_OUTPUT      = 80    # max candidati nel file output

REQUEST_DELAY   = 1.3   # secondi tra chiamate


COOP_TAGS = ["Co-op", "Online+Co-Op", "Local+Co-Op", "Co-op+Campaign"]

# Categorie Steam che indicano co-op
COOP_CATEGORY_IDS = {9, 38, 39}


# ─── HTTP helper ───────────────────────────────────────────────────────────────

def fetch_json(url: str) -> dict | None:
    time.sleep(REQUEST_DELAY)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        print(f"    ⚠ {url[:80]}: {exc}")
        return None


def fetch_appdetails(appid: str) -> dict | None:
    params = urllib.parse.urlencode({"appids": appid, "l": "english", "cc": "us"})
    data = fetch_json(f"{APPDETAILS_URL}?{params}")
    if not data:
        return None
    info = data.get(str(appid), {})
    if not info.get("success"):
        return None
    return info.get("data")


# ─── Rating calculation ─────────────────────────────────────────────────────────

def calc_rating(positive: int, negative: int) -> int:
    total = positive + negative
    if total == 0:
        return 0
    return round(positive / total * 100)


def calc_score(rating: int, reviews: int, ccu: int) -> float:
    """Punteggio per ordinare i candidati: combina qualità, popolarità e attività."""
    if rating == 0 or reviews == 0:
        return 0.0
    base = rating * math.log1p(reviews)
    ccu_boost = 1.0 + math.log1p(ccu) / 10 if ccu > 0 else 1.0
    return base * ccu_boost


# ─── SteamSpy collection ───────────────────────────────────────────────────────

def collect_coop_candidates(existing_appids: set[str]) -> dict[str, dict]:
    """
    Raccoglie candidati da SteamSpy per i tag co-op.
    Restituisce dict appid → raw SteamSpy data.
    """
    candidates: dict[str, dict] = {}

    for tag in COOP_TAGS:
        url = STEAMSPY_TAG_URL.format(tag=urllib.parse.quote(tag))
        print(f"  Fetching SteamSpy tag: {tag}...")
        data = fetch_json(url)
        if not data:
            print(f"    ⚠ Nessun dato per tag {tag}")
            continue

        added = 0
        for appid, game in data.items():
            if appid in existing_appids:
                continue
            if appid in BLACKLIST_APPIDS:
                continue
            name = game.get("name", "") or ""
            if not name:
                continue
            name_lower = name.lower()
            if any(w in name_lower for w in SKIP_WORDS):
                continue

            positive = game.get("positive", 0) or 0
            negative = game.get("negative", 0) or 0
            total = positive + negative
            if total < MIN_REVIEWS:
                continue

            rating = calc_rating(positive, negative)
            if rating < MIN_RATING:
                continue

            if appid not in candidates:
                candidates[appid] = game
                added += 1

        print(f"    → {len(data)} giochi, {added} nuovi candidati validi")

    return candidates


# ─── Release year extraction ────────────────────────────────────────────────────

def parse_release_year(date_str: str) -> int | None:
    if not date_str:
        return None
    m = re.search(r'\b(20\d{2})\b', date_str)
    if m:
        return int(m.group(1))
    return None


def is_coop_verified(sd: dict) -> bool:
    cat_ids = {c.get("id") for c in sd.get("categories", [])}
    return bool(cat_ids & COOP_CATEGORY_IDS)


# ─── Main ───────────────────────────────────────────────────────────────────────

def main(min_year: int = 2022, max_year: int = 2024, max_output: int = TOP_OUTPUT, max_examine: int = MAX_CANDIDATES) -> None:
    print("📖 Lettura catalogo esistente...")
    games = catalog_data.load_games()
    existing_appids: set[str] = set()
    existing_titles: set[str] = set()
    for g in games:
        steam_url = g.get("steamUrl") or ""
        m = re.search(r'/app/(\d+)', steam_url)
        if m:
            existing_appids.add(m.group(1))
        existing_titles.add(g.get("title", "").lower().strip())
    print(f"  Giochi nel DB: {len(games)} | AppID noti: {len(existing_appids)}")

    print("\n🔍 Raccolta candidati da SteamSpy...")
    raw_candidates = collect_coop_candidates(existing_appids)
    print(f"\n  Candidati pre-filtro (buon rating+reviews, non nel DB): {len(raw_candidates)}")

    # Ordina per score per esaminare i migliori prima (limita chiamate API)
    scored = []
    for appid, g in raw_candidates.items():
        positive = g.get("positive", 0) or 0
        negative = g.get("negative", 0) or 0
        ccu = g.get("ccu", 0) or 0
        rating = calc_rating(positive, negative)
        reviews = positive + negative
        score = calc_score(rating, reviews, ccu)
        scored.append((score, appid, g))
    scored.sort(reverse=True)

    # Prendi top max_examine per esaminare con appdetails
    to_examine = scored[:max_examine]
    print(f"  Esaminando top {len(to_examine)} con appdetails per anno uscita e co-op verifica...")

    results = []
    examined = 0
    skipped_year = 0
    skipped_not_coop = 0
    skipped_type = 0
    skipped_existing_title = 0

    for _score, appid, spy_data in to_examine:
        examined += 1
        name = spy_data.get("name", "?")
        sys.stdout.write(f"\r  [{examined}/{len(to_examine)}] {name[:50]:<50}")
        sys.stdout.flush()

        sd = fetch_appdetails(appid)
        if not sd:
            continue

        if sd.get("type") != "game":
            skipped_type += 1
            continue

        # Verifica co-op dalle categorie Steam ufficiali
        if not is_coop_verified(sd):
            skipped_not_coop += 1
            continue

        # Titolo ufficiale Steam (potrebbe differire da SteamSpy)
        official_name = sd.get("name", name)
        if official_name.lower().strip() in existing_titles:
            skipped_existing_title += 1
            continue

        # Anno uscita
        release = sd.get("release_date") or {}
        if release.get("coming_soon"):
            continue
        date_str = release.get("date", "")
        year = parse_release_year(date_str)
        if year is None or not (min_year <= year <= max_year):
            skipped_year += 1
            continue

        # Dati qualità
        positive = spy_data.get("positive", 0) or 0
        negative = spy_data.get("negative", 0) or 0
        ccu = spy_data.get("ccu", 0) or 0
        price_raw = spy_data.get("price", "0") or "0"
        try:
            price_usd = int(price_raw) / 100
        except (ValueError, TypeError):
            price_usd = 0.0

        rating = calc_rating(positive, negative)
        reviews = positive + negative

        # Co-op modes
        cat_ids = {c.get("id") for c in sd.get("categories", [])}
        coop_modes = []
        if 38 in cat_ids or 9 in cat_ids:
            coop_modes.append("online")
        if 39 in cat_ids:
            coop_modes.append("local")
        if not coop_modes:
            coop_modes = ["online"]

        # Descrizione EN
        desc_en = sd.get("short_description", "") or ""
        desc_en = re.sub(r"<[^>]+>", " ", desc_en)
        desc_en = re.sub(r"\s+", " ", desc_en).strip()[:400]

        results.append({
            "appid":       appid,
            "title":       official_name,
            "releaseYear": year,
            "releaseDate": date_str,
            "rating":      rating,
            "reviews":     reviews,
            "ccu":         ccu,
            "price_usd":   price_usd,
            "coopModes":   coop_modes,
            "description_en": desc_en,
            "steamUrl":    f"https://store.steampowered.com/app/{appid}/",
            "headerImage": sd.get("header_image", ""),
            "score":       round(_score, 1),
        })

        if len(results) >= max_output:
            break

    print(f"\n\n  Esaminati: {examined}")
    print(f"  Scartati: tipo non-game={skipped_type}, no co-op={skipped_not_coop}, "
          f"anno fuori range={skipped_year}, titolo già presente={skipped_existing_title}")
    print(f"  Candidati nel range {min_year}-{max_year}: {len(results)}")

    # Ordina output per score
    results.sort(key=lambda x: x["score"], reverse=True)

    # Salva output
    output = {
        "generated": __import__("datetime").date.today().isoformat(),
        "min_year": min_year,
        "max_year": max_year,
        "filters": {
            "min_rating": MIN_RATING,
            "min_reviews": MIN_REVIEWS,
            "coop_verified_via_steam_categories": True,
        },
        "count": len(results),
        "candidates": results,
    }
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Salvato: {OUTPUT_FILE}")
    print(f"   {len(results)} candidati — revisiona e aggiungi i migliori al catalogo")

    # Preview top 10
    if results:
        print("\n🎮 Top 10 candidati:")
        for i, c in enumerate(results[:10], 1):
            modes = "+".join(c["coopModes"])
            price = f"${c['price_usd']:.0f}" if c["price_usd"] > 0 else "F2P"
            print(f"  {i:2}. [{c['releaseYear']}] {c['title']:<45} {c['rating']}% | {c['reviews']:,} rec | {c['ccu']:,} ccu | {modes} | {price}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scopri giochi co-op mancanti nel catalogo")
    parser.add_argument("--min-year", type=int, default=2022, help="Anno minimo uscita (default 2022)")
    parser.add_argument("--max-year", type=int, default=2024, help="Anno massimo uscita (default 2024)")
    parser.add_argument("--max-candidates", type=int, default=TOP_OUTPUT, help=f"Max candidati nel file output (default {TOP_OUTPUT})")
    parser.add_argument("--examine", type=int, default=MAX_CANDIDATES, help=f"Max candidati da esaminare con Steam appdetails (default {MAX_CANDIDATES})")
    args = parser.parse_args()
    main(min_year=args.min_year, max_year=args.max_year, max_output=args.max_candidates, max_examine=args.examine)
