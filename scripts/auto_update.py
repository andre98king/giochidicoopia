"""
auto_update.py
==============
Pipeline unificata di aggiornamento e discovery del catalogo co-op.

FASE 1 — Load catalog
FASE 2 — Update existing (CCU, rating, trending, desc EN, releaseYear, integrità)
FASE 3 — Discover candidates (4 fonti: Steam SteamSpy, Steam New, IGDB, GOG, RAWG)
FASE 4 — Deduplicate candidates
FASE 5 — quality_gate.validate() su ogni candidato con steam_appid
FASE 6 — Enrich approved (desc IT/EN, categories, spy_data)
FASE 7 — Build game dict + add to catalog
FASE 8 — Featured indie + write games.js

Uso locale : python3 auto_update.py
CI (GitHub): eseguito automaticamente da .github/workflows/update.yml
"""

from __future__ import annotations

import datetime
import html as _html
import json
import re
import time
import urllib.request
from pathlib import Path

import catalog_data
import quality_gate
from catalog_config import *  # noqa: F403 – tutte le costanti di progetto
from igdb_catalog_source import (
    IgdbCatalogSource,
    enrich_games_with_igdb,
    _parse_multiplayer_modes,
)
from gog_catalog_source import GogCatalogSource, fetch_gog_candidates
from itch_catalog_source import ItchCatalogSource
from rawg_catalog_source import RawgCatalogSource
from steam_new_releases_source import fetch_steam_new_coop_games
from steam_catalog_source import (
    SteamCatalogSource,
    appid_from_url,
    calc_rating,
    derive_coop_modes,
    derive_crossplay,
    derive_genres,
    derive_players_label,
    parse_max_players,
    parse_release_year,
)

steam_source = SteamCatalogSource(delay=DELAY)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def _categorize_from_labels(labels: list[str]) -> list[str]:
    """Mappa una lista di label (generi, categorie Steam, tag SteamSpy) in categorie sito."""
    categories: list[str] = []
    for label in labels:
        for tag, cat in TAG_MAP.items():
            if tag.lower() in label.lower() and cat not in categories:
                categories.append(cat)
                if len(categories) >= 3:
                    break
        if len(categories) >= 3:
            break
    return categories or ["action"]


def _build_steam_game_dict(
    next_id: int,
    appid: str,
    title: str,
    categories: list[str],
    coop_modes: list[str],
    max_players: int,
    crossplay: bool,
    players: str,
    release_year: int,
    desc_it: str,
    desc_en: str,
    ccu: int,
    rating: int,
    total_reviews: int = 0,
    igdb_id: int = 0,
    igdb_confirmed: bool | None = None,
    gog_confirmed: bool | None = None,
    rawg_confirmed: bool | None = None,
) -> dict:
    """Costruisce il dict canonico per un nuovo gioco con Steam URL."""
    return {
        "id": next_id,
        "igdbId": igdb_id,
        "title": title,
        "categories": categories[:4],
        "genres": derive_genres(categories[:4]),
        "coopMode": coop_modes,
        "maxPlayers": max_players,
        "crossplay": crossplay,
        "players": players,
        "releaseYear": release_year,
        "image": f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
        "description": desc_it,
        "description_en": desc_en,
        "personalNote": "",
        "played": False,
        "steamUrl": f"https://store.steampowered.com/app/{appid}/",
        "gogUrl": "",
        "epicUrl": "",
        "itchUrl": "",
        "ccu": ccu,
        "trending": ccu >= MIN_CCU_TRENDING,
        "rating": rating,
        "totalReviews": total_reviews,
        # Additional fields for new catalog format
        "_igdb_confirmed": igdb_confirmed or False,
        "_gog_confirmed": gog_confirmed or False,
        "_rawg_confirmed": rawg_confirmed or False,
    }


def _run_quality_gate(steam_appid: str) -> dict:
    """Chiama quality_gate.validate() con le credenziali disponibili dall'ambiente."""
    return quality_gate.validate(
        str(steam_appid),
        rawg_api_key=RAWG_API_KEY or None,
        igdb_client_id=IGDB_CLIENT_ID or None,
        igdb_client_secret=IGDB_CLIENT_SECRET or None,
        rate_limit_delay=0.5,
    )


def _fetch_steam_store_reviews(appid: str) -> tuple[int, int]:
    """Fallback: legge conteggio recensioni dalla store page Steam.
    Usato per giochi F2P dove SteamSpy non espone positive/negative.
    Restituisce (positive, negative) all-time, oppure (0, 0) se non trovato."""
    try:
        time.sleep(DELAY)
        req = urllib.request.Request(
            f"https://store.steampowered.com/app/{appid}/",
            headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
        )
        html_content = (
            urllib.request.urlopen(req, timeout=15)
            .read()
            .decode("utf-8", errors="ignore")
        )
        matches = re.findall(
            r"(\d+)%\s+of the\s+([\d,]+)\s+user reviews\s+for this game", html_content
        )
        if matches:
            pct, cnt = max(matches, key=lambda m: int(m[1].replace(",", "")))
            total = int(cnt.replace(",", ""))
            if total >= 10:
                pos = round(total * int(pct) / 100)
                return pos, total - pos
    except Exception:
        pass
    return 0, 0


def _enrich_steam_candidate(
    appid: str,
    title: str,
    ccu: int,
    igdb_id: int,
    igdb_rating: int,
    next_id: int,
    qg_verdict: dict,
) -> dict | None:
    """
    Fetcha tutti i dati Steam necessari per un candidato approvato dal quality gate.
    Ritorna il dict del gioco pronto per l'aggiunta, o None se i dati sono insufficienti.
    """
    # Descrizione italiana
    sd, desc_it = steam_source.fetch_steam_desc(appid, "italian")
    if sd is None:
        print(f"    ✗ Nessun dato Steam")
        return None
    if sd.get("type", "") != "game":
        print(f"    ✗ Tipo Steam: {sd.get('type')} — skip")
        return None
    if not desc_it:
        print(f"    ✗ Nessuna descrizione italiana utile")
        return None

    _, desc_en = steam_source.fetch_steam_desc(appid, "english")
    desc_en = desc_en or ""

    steam_cats = [c.get("description", "") for c in sd.get("categories", [])]
    spy_data = (
        steam_source.fetch_json(
            f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
        )
        or {}
    )
    spy_tags = list((spy_data.get("tags") or {}).keys())
    genres_raw = [g.get("description", "") for g in sd.get("genres", [])]

    categories = _categorize_from_labels(genres_raw + steam_cats + spy_tags)

    # Verifica indie e free
    new_pub = sd.get("publishers", []) or []
    new_dev = sd.get("developers", []) or []
    new_publishers = [p.lower() for p in new_pub + new_dev if isinstance(p, str)]
    is_big = any(
        known in pub for pub in new_publishers for known in NOT_INDIE_PUBLISHERS
    )
    if (
        appid in indie_appids
        and appid not in NOT_INDIE_APPIDS
        and not is_big
        and "indie" not in categories
    ):
        categories.append("indie")
    new_genres_lower = [
        gr.get("description", "").lower() for gr in sd.get("genres", [])
    ]
    is_free = sd.get("is_free", False) and "free to play" in new_genres_lower
    if is_free and appid not in NOT_FREE_APPIDS and "free" not in categories:
        categories.append("free")

    pos = spy_data.get("positive", 0) or 0
    neg = spy_data.get("negative", 0) or 0
    rating = calc_rating(pos, neg)

    if rating > 0 and rating < MIN_RATING_NEW:
        # Controllo qualità: usa anche IGDB rating come fallback
        if igdb_rating < MIN_IGDB_RATING:
            print(f"    ✗ Rating troppo basso: Steam={rating}% IGDB={igdb_rating}")
            return None

    players = derive_players_label([c.lower() for c in steam_cats])
    steam_cats_lower = [c.lower() for c in steam_cats]
    coop_modes = qg_verdict["coop_modes"] or derive_coop_modes(steam_cats_lower)
    release_year = parse_release_year(sd.get("release_date"))

    return _build_steam_game_dict(
        next_id=next_id,
        appid=appid,
        title=title,
        categories=categories,
        coop_modes=coop_modes,
        max_players=parse_max_players(players),
        crossplay=derive_crossplay(steam_cats_lower),
        players=players,
        release_year=release_year,
        desc_it=desc_it,
        desc_en=desc_en,
        ccu=ccu,
        rating=rating,
        total_reviews=pos + neg,
        igdb_id=igdb_id,
        igdb_confirmed=qg_verdict.get("igdb_confirmed"),
        gog_confirmed=qg_verdict.get("gog_confirmed"),
        rawg_confirmed=qg_verdict.get("rawg_confirmed"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# FASE 1 — Load catalog
# ═══════════════════════════════════════════════════════════════════════════
print("📖 FASE 1 — Lettura games.js...")
featured_id_existing, existing_games = catalog_data.load_legacy_catalog_bundle()
existing_appids: set[str] = set()
existing_igdb_ids: set[int] = set()
existing_gog_urls: set[str] = set()
existing_titles: set[str] = set()
max_id = 0

# Carica excluded_games.json — appids bocciati dal gate, non rientrano mai
_excluded_path = Path("data/excluded_games.json")
excluded_appids: set[str] = set()
if _excluded_path.exists():
    try:
        excluded_appids = set(json.loads(_excluded_path.read_text(encoding="utf-8")))
        print(f"  🚫 Excluded list: {len(excluded_appids)} appids")
    except Exception:
        pass

for g in existing_games:
    max_id = max(max_id, g["id"])
    aid = appid_from_url(g.get("steamUrl", ""))
    if aid:
        existing_appids.add(aid)
    if g.get("igdbId"):
        existing_igdb_ids.add(g["igdbId"])
    if g.get("gogUrl"):
        existing_gog_urls.add(g["gogUrl"])
    existing_titles.add(g.get("title", "").lower().strip())

print(f"  Giochi nel DB: {len(existing_games)}  |  ID max: {max_id}")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 2 — Update existing (CCU, rating, trending, desc EN, releaseYear, integrità)
# ═══════════════════════════════════════════════════════════════════════════
print("\n🔄 FASE 2 — Aggiornamento giochi esistenti...")

# 2a: Fetch CCU e tag co-op da SteamSpy
print("  🔥 Fetch top giochi per giocatori recenti (SteamSpy)...")
top_recent = (
    steam_source.fetch_json("https://steamspy.com/api.php?request=top100in2weeks") or {}
)
ccu_map = {aid: d.get("ccu", 0) for aid, d in top_recent.items()}
print(f"  Top recenti trovati: {len(ccu_map)}")

print("  🎮 Fetch giochi co-op da SteamSpy (tag multipli)...")
coop_games: dict = {}
for tag in ["Co-op", "Online+Co-Op", "Local+Co-Op", "Co-op+Campaign"]:
    data = (
        steam_source.fetch_json(f"https://steamspy.com/api.php?request=tag&tag={tag}")
        or {}
    )
    for aid, gdata in data.items():
        if aid not in coop_games:
            coop_games[aid] = gdata
print(f"  Giochi co-op SteamSpy: {len(coop_games)} unici")

print("  🏷️  Fetch tag Indie e Free to Play da SteamSpy...")
indie_appids = set(
    (
        steam_source.fetch_json("https://steamspy.com/api.php?request=tag&tag=Indie")
        or {}
    ).keys()
)
free_appids = set(
    (
        steam_source.fetch_json(
            "https://steamspy.com/api.php?request=tag&tag=Free+to+Play"
        )
        or {}
    ).keys()
)
print(f"  Indie: {len(indie_appids)} | Free: {len(free_appids)}")

# 2b: Aggiorna CCU + rating + totalReviews + tag indie/free
updated_ccu = 0
updated_rating = 0
updated_reviews = 0
for g in existing_games:
    aid = appid_from_url(g["steamUrl"])
    if not aid:
        continue
    new_ccu = ccu_map.get(aid, coop_games.get(aid, {}).get("ccu", 0) or 0)
    g["ccu"] = new_ccu
    g["trending"] = new_ccu >= MIN_CCU_TRENDING
    if new_ccu > 0:
        updated_ccu += 1
    spy = coop_games.get(aid, {})
    pos = spy.get("positive", 0) or 0
    neg = spy.get("negative", 0) or 0
    if pos + neg >= 10:
        g["rating"] = calc_rating(pos, neg)
        updated_rating += 1
    # Update totalReviews for existing games
    g["totalReviews"] = pos + neg
    if pos + neg > 0:
        updated_reviews += 1
    if aid in NOT_INDIE_APPIDS and "indie" in g["categories"]:
        g["categories"].remove("indie")
    if aid in NOT_FREE_APPIDS and "free" in g["categories"]:
        g["categories"].remove("free")

print(
    f"  CCU aggiornati: {updated_ccu} | Rating: {updated_rating} | Reviews: {updated_reviews} | Trending 🔥: {sum(1 for g in existing_games if g['trending'])}"
)

# 2c: Fallback CCU individuale per giochi con CCU 0
zero_ccu = [
    g
    for g in existing_games
    if g.get("ccu", 0) == 0 and appid_from_url(g.get("steamUrl", ""))
]
print(f"  🔍 Fallback CCU: {len(zero_ccu)} giochi con CCU 0...")
fallback_ok = 0
for g in zero_ccu:
    aid = appid_from_url(g["steamUrl"])
    spy = steam_source.fetch_json(
        f"https://steamspy.com/api.php?request=appdetails&appid={aid}"
    )
    if not spy:
        continue
    ccu = spy.get("ccu", 0) or 0
    if ccu > 0:
        g["ccu"] = ccu
        g["trending"] = ccu >= MIN_CCU_TRENDING
        fallback_ok += 1
    pos = spy.get("positive", 0) or 0
    neg = spy.get("negative", 0) or 0
    if pos + neg >= 10:
        g["rating"] = calc_rating(pos, neg)
        g["totalReviews"] = pos + neg
    elif pos + neg == 0 and g.get("rating", 0) == 0:
        steam_pos, steam_neg = _fetch_steam_store_reviews(aid)
        if steam_pos + steam_neg >= 10:
            g["rating"] = calc_rating(steam_pos, steam_neg)
            g["totalReviews"] = steam_pos + steam_neg
            print(
                f"    ↳ Steam store fallback [{g['id']}] {g['title']}: rating={g['rating']}, reviews={steam_pos + steam_neg}"
            )
    elif pos + neg > 0:
        g["totalReviews"] = pos + neg
print(
    f"  Fallback CCU trovati: {fallback_ok}  |  Ancora 0: {len(zero_ccu) - fallback_ok}"
)

# 2d: Descrizioni EN mancanti
print(f"  🌍 Fetch descrizioni inglesi mancanti (max {MAX_EN_FETCH})...")
en_fetched = 0
for g in existing_games:
    if en_fetched >= MAX_EN_FETCH:
        break
    if g.get("description_en") and len(g["description_en"]) > 20:
        continue
    aid = appid_from_url(g["steamUrl"])
    if not aid:
        continue
    _, en_desc = steam_source.fetch_steam_desc(aid, "english")
    if en_desc:
        g["description_en"] = en_desc
        en_fetched += 1
    else:
        g["description_en"] = ""
print(f"  Descrizioni EN aggiunte: {en_fetched}")

# 2e: releaseYear mancante
missing_year = [
    g
    for g in existing_games
    if not g.get("releaseYear") and appid_from_url(g.get("steamUrl", ""))
]
print(f"  📅 Fetch releaseYear mancante: {len(missing_year)} giochi...")
year_fetched = 0
for g in missing_year:
    aid = appid_from_url(g["steamUrl"])
    sd_year, _ = steam_source.fetch_steam_desc(aid, "english")
    if sd_year:
        yr = parse_release_year(sd_year.get("release_date"))
        if yr:
            g["releaseYear"] = yr
            year_fetched += 1
print(f"  releaseYear aggiunti: {year_fetched}")

# 2f: Verifica integrità database (campionamento rotante)
print("  🔍 Verifica integrità database...")
v_fixed_free = v_fixed_indie = v_fixed_title = v_removed_nocoop = v_checked = 0
nocoop_flagged_ids: list[int] = []
iso_week = datetime.datetime.now().isocalendar()
verify_offset = ((iso_week[0] * 52 + iso_week[1]) * 7 + iso_week[2]) % max(
    len(existing_games), 1
)
rotated_games = existing_games[verify_offset:] + existing_games[:verify_offset]

for g in rotated_games:
    if v_checked >= MAX_VERIFY:
        break
    aid = appid_from_url(g["steamUrl"])
    if not aid:
        continue
    v_checked += 1
    cc_url = (
        f"https://store.steampowered.com/api/appdetails?appids={aid}&l=english&cc=us"
    )
    data = steam_source.fetch_json(cc_url)
    if not data:
        continue
    info = data.get(str(aid), {})
    if not info.get("success"):
        continue
    sd = info.get("data", {})

    # Sanity check: verifica che l'API abbia restituito il gioco giusto
    api_name = sd.get("name", "")
    db_name = g["title"]
    if api_name:
        api_words = set(re.findall(r"[a-zA-Z]{3,}", api_name.lower()))
        db_words = set(re.findall(r"[a-zA-Z]{3,}", db_name.lower()))
        common = api_words & db_words
        total = max(len(api_words | db_words), 1)
        if len(common) / total < 0.25 and len(api_words) > 0 and len(db_words) > 0:
            print(f"  ⛔ {db_name}: API ha restituito '{api_name}' — scartato")
            continue

    # Verifica FREE
    steam_is_free = sd.get("is_free", False)
    price = sd.get("price_overview", {})
    price_cents = price.get("final", 0) if price else 0
    genres_list = [gr.get("description", "").lower() for gr in sd.get("genres", [])]
    actually_free = steam_is_free and price_cents == 0 and "free to play" in genres_list
    if "free" in g["categories"] and not actually_free:
        g["categories"].remove("free")
        v_fixed_free += 1
        print(f"  💰 {g['title']}: rimosso tag 'free'")
    if actually_free and "free" not in g["categories"] and aid not in NOT_FREE_APPIDS:
        g["categories"].append("free")
        v_fixed_free += 1
        print(f"  🆓 {g['title']}: aggiunto tag 'free'")

    # Verifica INDIE
    pub_names = sd.get("publishers", []) or []
    dev_names = sd.get("developers", []) or []
    publishers = [p.lower() for p in pub_names + dev_names if isinstance(p, str)]
    is_big_studio = any(
        known in pub for pub in publishers for known in NOT_INDIE_PUBLISHERS
    )
    if "indie" in g["categories"] and (is_big_studio or aid in NOT_INDIE_APPIDS):
        g["categories"].remove("indie")
        v_fixed_indie += 1
        print(f"  🏢 {g['title']}: rimosso tag 'indie'")

    # Verifica CO-OP + aggiorna coopMode/crossplay
    steam_cats = [c.get("description", "").lower() for c in sd.get("categories", [])]
    has_coop = any(
        "co-op" in c or "multiplayer" in c or "multi-player" in c for c in steam_cats
    )
    if not has_coop:
        v_removed_nocoop += 1
        nocoop_flagged_ids.append(g["id"])
        print(f"  ⚠️  {g['title']}: NESSUNA categoria co-op su Steam!")
    g["coopMode"] = derive_coop_modes(steam_cats)
    g["crossplay"] = derive_crossplay(steam_cats)
    g["genres"] = derive_genres(g["categories"])
    g["maxPlayers"] = parse_max_players(g["players"])

    # Log differenze titolo
    steam_name = sd.get("name", "")
    if steam_name and steam_name != g["title"] and len(steam_name) > 2:
        clean_api = (
            steam_name.lower()
            .replace("™", "")
            .replace("®", "")
            .replace(":", "")
            .strip()
        )
        clean_db = (
            g["title"]
            .lower()
            .replace("™", "")
            .replace("®", "")
            .replace(":", "")
            .strip()
        )
        if clean_api != clean_db:
            v_fixed_title += 1
            print(
                f"  📝 Titolo diverso (solo log): '{g['title']}' vs Steam '{steam_name}'"
            )

print(
    f"  Verificati: {v_checked} | Fix free: {v_fixed_free} | Fix indie: {v_fixed_indie} | Fix titoli: {v_fixed_title} | Senza co-op: {v_removed_nocoop}"
)

catalog_data.DATA_DIR.mkdir(exist_ok=True)
(catalog_data.DATA_DIR / "_nocoop_flagged.json").write_text(
    json.dumps({"game_ids": nocoop_flagged_ids}, indent=2) + "\n", encoding="utf-8"
)


# ═══════════════════════════════════════════════════════════════════════════
# FASE 3 — Discover candidates (4 fonti)
# ═══════════════════════════════════════════════════════════════════════════
print("\n🔍 FASE 3 — Discovery candidati da 4 fonti...")

# Schema candidato normalizzato:
# {title, steam_appid, igdb_id, gog_url, ccu, source, rating_rawg?, rating_igdb?}

all_candidates: list[dict] = []

# 3a: Steam SteamSpy co-op tags
print("  🎮 3a) SteamSpy co-op tags...")
steamspy_candidates: list[dict] = []
for aid, gdata in coop_games.items():
    if aid in existing_appids or aid in BLACKLIST_APPIDS:
        continue
    name = gdata.get("name", "")
    if not name or any(w in name.lower() for w in SKIP_WORDS):
        continue
    ccu = ccu_map.get(aid, gdata.get("ccu", 0) or 0)
    if ccu < MIN_CCU_NEW:
        continue
    is_old = bool(re.search(r"FIFA \d+", name))
    if not is_old:
        for pat_name, check in OLD_EDITION_PATTERNS[1:]:
            m = re.search(pat_name, name)
            if m and callable(check) and check(m):
                is_old = True
                break
    if is_old:
        continue
    steamspy_candidates.append(
        {
            "title": name,
            "steam_appid": aid,
            "igdb_id": None,
            "gog_url": None,
            "ccu": ccu,
            "source": "steamspy",
        }
    )

steamspy_candidates.sort(key=lambda x: x["ccu"], reverse=True)
all_candidates.extend(steamspy_candidates[: MAX_NEW_GAMES * 4])
print(
    f"  Trovati: {len(steamspy_candidates)} candidati SteamSpy (tenuti top {min(len(steamspy_candidates), MAX_NEW_GAMES * 4)})"
)

# 3b: Steam New Releases
if STEAM_API_KEY:
    print("  🆕 3b) Steam New Releases (ultimi 90 giorni)...")
    steam_new_raw = fetch_steam_new_coop_games(
        api_key=STEAM_API_KEY,
        existing_appids=existing_appids,
        existing_titles=existing_titles,
        blacklist_appids=BLACKLIST_APPIDS,
        skip_words=SKIP_WORDS,
        max_games=MAX_STEAM_NEW,
    )
    for cand in steam_new_raw:
        all_candidates.append(
            {
                "title": cand["name"],
                "steam_appid": cand["appid"],
                "igdb_id": None,
                "gog_url": None,
                "ccu": 0,
                "source": "steam_new",
                "_steam_new_data": cand,  # dati preenricchiti da fetch
            }
        )
    print(f"  Trovati: {len(steam_new_raw)} candidati Steam New")
else:
    print("  🆕 3b) Steam New Releases: saltato (nessun STEAM_API_KEY)")

# 3c: IGDB Discovery
if IGDB_CLIENT_ID and IGDB_CLIENT_SECRET:
    print("  🌐 3c) IGDB Discovery...")
    try:
        igdb_source = IgdbCatalogSource(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
        igdb_raw = igdb_source.discover_coop_games(
            existing_igdb_ids=existing_igdb_ids,
            existing_steam_appids=existing_appids,
            existing_titles=existing_titles,
            max_games=MAX_IGDB_DISCOVERY,
        )
        for cand in igdb_raw:
            steam_appid = cand.get("steamAppId")
            if steam_appid and steam_appid not in BLACKLIST_APPIDS:
                all_candidates.append(
                    {
                        "title": cand.get("title", ""),
                        "steam_appid": steam_appid,
                        "igdb_id": cand.get("igdbId"),
                        "gog_url": None,
                        "ccu": ccu_map.get(steam_appid, 0),
                        "source": "igdb",
                        "rating_igdb": cand.get("rating_igdb", 0) or 0,
                    }
                )
        print(f"  Trovati: {len(igdb_raw)} candidati IGDB (con steam_appid)")
    except Exception as e:
        print(f"  ⚠️ IGDB Discovery fallita: {e}")
else:
    print("  🌐 3c) IGDB Discovery: saltato (nessun IGDB_CLIENT_ID)")

# 3d: GOG Discovery (giochi GOG-only, senza Steam)
gog_direct_candidates: list[
    dict
] = []  # candidati GOG già enrichiti (no quality_gate steam)
if IGDB_CLIENT_ID and IGDB_CLIENT_SECRET:
    print("  🎮 3d) GOG Discovery (giochi GOG-only)...")
    gog_raw = fetch_gog_candidates(
        existing_titles=existing_titles,
        existing_gog_urls=existing_gog_urls,
        existing_igdb_ids=existing_igdb_ids,
        max_games=MAX_GOG_GAMES,
    )
    igdb_source_gog = IgdbCatalogSource(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
    gog_source = GogCatalogSource()
    for cand in gog_raw:
        # GOG-only: non ha steam_appid → quality_gate non applicabile
        # Validazione tramite IGDB game_modes query diretta
        all_candidates.append(
            {
                "title": cand["title"],
                "steam_appid": None,
                "igdb_id": None,
                "gog_url": cand["gogUrl"],
                "ccu": 0,
                "source": "gog",
                "_gog_data": cand,
                "_igdb_source_gog": igdb_source_gog,
                "_gog_source": gog_source,
            }
        )
    print(f"  Trovati: {len(gog_raw)} candidati GOG")
else:
    print("  🎮 3d) GOG: saltato (richiede IGDB_CLIENT_ID per verifica dedup)")

# 3e: RAWG Discovery
if RAWG_API_KEY:
    print("  🔷 3e) RAWG Discovery (co-op PC su Steam)...")
    try:
        rawg_source = RawgCatalogSource(api_key=RAWG_API_KEY, delay=1.0)
        rawg_raw = rawg_source.discover_coop_games(
            existing_steam_appids=existing_appids,
            existing_titles=existing_titles,
            max_games=MAX_RAWG_DISCOVERY,
        )
        for cand in rawg_raw:
            if cand["steam_appid"] not in BLACKLIST_APPIDS:
                all_candidates.append(cand)
        print(f"  Trovati: {len(rawg_raw)} candidati RAWG")
    except Exception as e:
        print(f"  ⚠️ RAWG Discovery fallita: {e}")
else:
    print("  🔷 3e) RAWG Discovery: saltato (nessun RAWG_API_KEY)")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 4 — Deduplicate candidates
# ═══════════════════════════════════════════════════════════════════════════
print("\n🔎 FASE 4 — Deduplicazione candidati...")
seen_appids: set[str] = set()
seen_titles: set[str] = set()
unique_candidates: list[dict] = []

for cand in all_candidates:
    appid = cand.get("steam_appid")
    title_key = cand.get("title", "").lower().strip()

    # Skip se già in catalogo (doppio controllo sicurezza)
    if appid and appid in existing_appids:
        continue
    if title_key in existing_titles:
        continue

    # Skip duplicati tra candidati
    if appid and appid in seen_appids:
        continue
    if title_key in seen_titles:
        continue

    if appid:
        seen_appids.add(appid)
    seen_titles.add(title_key)
    unique_candidates.append(cand)

print(f"  Candidati totali: {len(all_candidates)} → unici: {len(unique_candidates)}")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 5 — Quality gate su candidati con steam_appid
# FASE 6 — Enrich approved
# FASE 7 — Build game dict + add to catalog
# (Fasi 5-7 eseguite insieme per candidato per limitare le richieste API)
# ═══════════════════════════════════════════════════════════════════════════
print(
    f"\n✅ FASE 5-7 — Quality gate + Enrich + Add (max {MAX_NEW_GAMES} giochi Steam)..."
)

next_id = max_id + 1
added_steam = 0  # SteamSpy + Steam New + IGDB + RAWG (tutti hanno steam_appid)
added_gog = 0
steam_budget = MAX_NEW_GAMES  # budget totale giochi Steam da aggiungere

for cand in unique_candidates:
    appid = cand.get("steam_appid")
    title = cand.get("title", "")
    source = cand.get("source", "")

    # ── PATH GOG (senza steam_appid) ──
    if source == "gog" and not appid:
        if added_gog >= MAX_GOG_GAMES:
            continue
        gog_url = cand["gog_url"]
        igdb_src = cand["_igdb_source_gog"]
        gog_src = cand["_gog_source"]
        gog_cand_data = cand["_gog_data"]
        print(f"\n  [GOG] {title}")

        query = (
            f"fields id, name, rating, rating_count, "
            f"external_games.uid, external_games.category, "
            f"multiplayer_modes.onlinecoop, multiplayer_modes.onlinecoopmax, "
            f"multiplayer_modes.offlinecoop, multiplayer_modes.offlinecoopmax, "
            f"multiplayer_modes.splitscreen, multiplayer_modes.lancoop; "
            f'search "{title}"; '
            f"where platforms = (6) & game_modes = (3); "
            f"limit 3;"
        )
        igdb_results = igdb_src._post("games", query) or []
        igdb_match = next(
            (
                r
                for r in igdb_results
                if r.get("name", "").lower().strip() == title.lower().strip()
            ),
            None,
        )
        if not igdb_match and igdb_results:
            igdb_match = igdb_results[0]
        if not igdb_match:
            print(f"    ✗ Nessun match IGDB per '{title}'")
            continue

        igdb_id = igdb_match.get("id", 0)
        if igdb_id in existing_igdb_ids:
            print(f"    ✗ igdbId {igdb_id} già nel catalogo")
            continue

        has_steam = any(
            ext.get("category") == 1 for ext in (igdb_match.get("external_games") or [])
        )
        if has_steam:
            print(f"    ✗ Ha anche Steam — gestito da pipeline Steam")
            continue

        igdb_rating = igdb_match.get("rating") or 0
        igdb_rating_count = igdb_match.get("rating_count") or 0
        if (
            igdb_rating > 0
            and igdb_rating < MIN_IGDB_RATING
            and igdb_rating_count >= 20
        ):
            print(
                f"    ✗ Rating IGDB basso: {igdb_rating:.0f} ({igdb_rating_count} voti)"
            )
            continue

        modes_list = igdb_match.get("multiplayer_modes") or []
        mp = _parse_multiplayer_modes(modes_list) or {
            "coopMode": ["online"],
            "maxPlayers": 4,
        }
        _, desc_en = gog_src.fetch_product_description(
            gog_cand_data.get("gogProductId", "")
        )
        gog_tags = gog_cand_data.get("tags", [])
        categories = _categorize_from_labels(gog_tags)

        new_game = {
            "id": next_id,
            "igdbId": igdb_id,
            "title": title,
            "categories": categories[:4],
            "genres": derive_genres(categories[:4]),
            "coopMode": mp["coopMode"],
            "maxPlayers": mp["maxPlayers"] or 4,
            "crossplay": False,
            "players": f"1-{mp['maxPlayers'] or 4}",
            "image": gog_cand_data.get("image", ""),
            "description": desc_en,
            "description_en": desc_en,
            "personalNote": "",
            "played": False,
            "steamUrl": "",
            "gogUrl": gog_url,
            "epicUrl": "",
            "itchUrl": "",
            "ccu": 0,
            "trending": False,
            "rating": round(igdb_rating) if igdb_rating else 0,
        }
        existing_games.append(new_game)
        existing_igdb_ids.add(igdb_id)
        existing_gog_urls.add(gog_url)
        existing_titles.add(title.lower().strip())
        next_id += 1
        added_gog += 1
        print(f"    ✓ {title} (GOG-only, igdbId={igdb_id})")
        continue

    # ── PATH STEAM (tutti gli altri: steamspy, steam_new, igdb, rawg) ──
    if not appid:
        continue
    if added_steam >= steam_budget:
        continue
    if appid in excluded_appids:
        print(f"  ⏭️  [Excluded] {appid} ({title}) → già bocciato/escluso, salto.")
        continue

    print(
        f"\n  [{added_steam + 1}/{steam_budget}] {title} (app {appid}, CCU: {cand.get('ccu', 0)}, src: {source})"
    )

    # Steam New Releases: dati preenricchiti, solo verifica quality gate
    if source == "steam_new":
        snd = cand.get("_steam_new_data", {})
        verdict = _run_quality_gate(appid)
        if verdict["status"] == "rejected":
            print(f"    ✗ Quality gate: {verdict['reason']}")
            continue
        if verdict["status"] == "needs_review":
            print(f"    ⚠ Quality gate needs_review: {verdict['reason']} — skipped")
            continue
        desc_it_raw = (
            snd.get("description_it", "") or snd.get("description_en", "") or ""
        )
        desc_it_raw = re.sub(r"<[^>]+>", " ", desc_it_raw)
        desc_it_raw = _html.unescape(desc_it_raw)
        desc_it_raw = re.sub(r"\s+", " ", desc_it_raw).strip()[:400]
        new_game = _build_steam_game_dict(
            next_id=next_id,
            appid=appid,
            title=title,
            categories=_categorize_from_labels(list((snd.get("tags") or {}).keys())),
            coop_modes=verdict["coop_modes"] or snd.get("coopMode", ["online"]),
            max_players=4,
            crossplay=False,
            players="2-4",
            release_year=0,
            desc_it=desc_it_raw,
            desc_en=snd.get("description_en", ""),
            ccu=0,
            rating=0,
            igdb_confirmed=verdict.get("igdb_confirmed"),
            gog_confirmed=verdict.get("gog_confirmed"),
            rawg_confirmed=verdict.get("rawg_confirmed"),
        )
        new_game["image"] = snd.get("image", new_game["image"])
        new_game["steamUrl"] = snd.get("steamUrl", new_game["steamUrl"])
        new_game["totalReviews"] = snd.get("recommendations", 0)
        existing_games.append(new_game)
        existing_appids.add(appid)
        existing_titles.add(title.lower().strip())
        next_id += 1
        added_steam += 1
        print(f"    ✓ {title} (new release)")
        continue

    # Tutti gli altri path Steam: quality gate → enrich completo
    verdict = _run_quality_gate(appid)
    if verdict["status"] == "rejected":
        print(f"    ✗ Quality gate: {verdict['reason']}")
        continue
    if verdict["status"] == "needs_review":
        print(f"    ⚠ Quality gate needs_review: {verdict['reason']} — skipped")
        continue

    igdb_id = cand.get("igdb_id") or 0
    igdb_rating = cand.get("rating_igdb", 0) or 0
    new_game = _enrich_steam_candidate(
        appid=appid,
        title=title,
        ccu=cand.get("ccu", 0),
        igdb_id=igdb_id,
        igdb_rating=igdb_rating,
        next_id=next_id,
        qg_verdict=verdict,
    )
    if new_game is None:
        continue

    existing_games.append(new_game)
    existing_appids.add(appid)
    if igdb_id:
        existing_igdb_ids.add(igdb_id)
    existing_titles.add(title.lower().strip())
    next_id += 1
    added_steam += 1
    print(
        f"    ✓ {title} | {new_game['categories'][:3]} | {new_game['rating']}% | src: {source}"
    )

print(f"\n  Nuovi giochi aggiunti: {added_steam} (Steam) + {added_gog} (GOG)")


# ── itch.io disabilitato: troppi giochi senza segnali di qualità (rating=0, ccu=0)
# Per riabilitare: implementare quality gate per itch prima di aggiungere al catalog
print("\n🎲 itch.io: disabilitato (qualità insufficiente senza segnali verificabili)")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 8 — Arricchimento IGDB + Featured indie + Write games.js
# ═══════════════════════════════════════════════════════════════════════════
print("\n🎯 FASE 8 — Finalizzazione...")

# Arricchimento IGDB (coopMode, maxPlayers per giochi esistenti)
igdb_enriched = 0
if IGDB_CLIENT_ID and IGDB_CLIENT_SECRET:
    print("  🎯 Arricchimento multiplayer con IGDB...")
    igdb_enriched = enrich_games_with_igdb(
        existing_games, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET
    )
    print(f"  ✅ IGDB: {igdb_enriched} giochi arricchiti")
else:
    print("  🎯 IGDB arricchimento: saltato")

# Selezione gioco indie della settimana
print("  🌟 Selezione gioco indie della settimana...")
if FEATURED_OVERRIDE_ID > 0:
    featured_id = FEATURED_OVERRIDE_ID
    featured_game = next((g for g in existing_games if g["id"] == featured_id), None)
    title = featured_game["title"] if featured_game else "ID Sconosciuto"
    print(f"  Featured (MANUAL OVERRIDE): {title} (id {featured_id})")
else:
    indie_rated = [
        g
        for g in existing_games
        if "indie" in g.get("categories", []) and g.get("rating", 0) >= 75
    ]
    if indie_rated:
        indie_sorted = sorted(
            indie_rated, key=lambda x: x.get("rating", 0), reverse=True
        )
        top_indie = indie_sorted[:12]
        iso = datetime.datetime.now().isocalendar()
        week_idx = (iso[0] * 52 + iso[1]) % len(top_indie)
        featured_id = top_indie[week_idx]["id"]
        print(f"  Featured (AUTO): {top_indie[week_idx]['title']} (id {featured_id})")
    else:
        featured_id = 0
        print("  Nessun gioco indie con rating >= 75%")

# Scrittura games.js
print(f"\n💾 Scrittura games.js ({len(existing_games)} giochi)...")
try:
    catalog_data.write_legacy_games_js(
        existing_games,
        featured_indie_id=featured_id or featured_id_existing,
    )
except ValueError as exc:
    print(f"  ⛔ ERRORE: {exc} — file NON scritto!")
else:
    print(f"  ✅ games.js scritto con successo ({len(existing_games)} giochi)")

# Statistiche finali
trending_count = sum(1 for g in existing_games if g.get("trending"))
rated_count = sum(1 for g in existing_games if g.get("rating", 0) > 0)
en_count = sum(1 for g in existing_games if g.get("description_en"))
indie_count = sum(1 for g in existing_games if "indie" in g.get("categories", []))
free_count = sum(1 for g in existing_games if "free" in g.get("categories", []))
print(f"\n✅ Done!")
print(f"   Giochi totali    : {len(existing_games)}")
print(f"   Trending 🔥      : {trending_count}")
print(f"   Con rating ⭐    : {rated_count}")
print(f"   Con desc EN 🌍   : {en_count}")
print(f"   Indie 🎮         : {indie_count}")
print(f"   Free 🆓          : {free_count}")
print(f"   Featured ID 🌟   : {featured_id}")
print(
    f"   Nuovi aggiunti   : {added_steam} (Steam: steamspy/new/igdb/rawg) + {added_gog} (GOG)"
)
print(f"   IGDB arricchiti  : {igdb_enriched}")
print(
    f"   Verifiche integrità: {v_checked} controllati, {v_fixed_free + v_fixed_indie + v_fixed_title} corretti, {v_removed_nocoop} warning co-op"
)
