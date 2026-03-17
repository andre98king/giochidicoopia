"""
auto_update.py
==============
Aggiorna automaticamente games.js con:
  - CCU (giocatori concorrenti) e rating per tutti i giochi esistenti
  - Flag "trending" per i giochi con molti giocatori attivi
  - Descrizioni italiane da Steam API (nuovi giochi)
  - Descrizioni inglesi da Steam API (nuovi giochi + giochi esistenti senza)
  - Nuovi giochi co-op trending da SteamSpy
  - Nuovi giochi co-op da IGDB discovery (cross-platform: Steam, GOG, ecc.)
  - Nuovi giochi co-op da GOG (giochi GOG-only non su Steam)
  - Tag "indie" e "free" per i giochi appropriati
  - Gioco indie della settimana (featuredIndieId)
  - [Opzionale] Giochi da itch.io (richiede ITCH_IO_KEY env var)
  - VERIFICA INTEGRITÀ: controlla free (prezzo reale), indie (publisher),
    co-op (categorie Steam), titoli (nome ufficiale Steam)
  - DEDUPLICAZIONE: igdbId + Steam App ID + titolo esatto

Uso locale : python3 auto_update.py
CI (GitHub): eseguito automaticamente da .github/workflows/update.yml
"""

import datetime, re

import catalog_data
from catalog_config import *          # noqa: F403 – tutte le costanti di progetto
from igdb_catalog_source import IgdbCatalogSource, enrich_games_with_igdb
from gog_catalog_source import fetch_gog_candidates
from itch_catalog_source import ItchCatalogSource
from steam_catalog_source import (
    SteamCatalogSource,
    appid_from_url,
    calc_rating,
    derive_coop_modes,
    derive_crossplay,
    derive_genres,
    derive_players_label,
    parse_max_players,
)

steam_source = SteamCatalogSource(delay=DELAY)


# ─────────────────────── Leggi games.js esistente ────────────────────────
print("📖 Lettura games.js...")
featured_id_existing, existing_games = catalog_data.load_legacy_catalog_bundle()
existing_appids = set()
existing_igdb_ids = set()
existing_gog_urls = set()
existing_titles = set()
max_id = 0

for g in existing_games:
    max_id = max(max_id, g['id'])
    aid = appid_from_url(g.get('steamUrl', ''))
    if aid:
        existing_appids.add(aid)
    if g.get('igdbId'):
        existing_igdb_ids.add(g['igdbId'])
    if g.get('gogUrl'):
        existing_gog_urls.add(g['gogUrl'])
    existing_titles.add(g.get('title', '').lower().strip())

print(f"  Giochi nel DB: {len(existing_games)}  |  ID max: {max_id}")


# ─────────────────────── Fetch trending da SteamSpy ──────────────────────
print("\n🔥 Fetch top giochi per giocatori recenti (SteamSpy)...")
top_recent = steam_source.fetch_json("https://steamspy.com/api.php?request=top100in2weeks") or {}
ccu_map = {aid: d.get('ccu', 0) for aid, d in top_recent.items()}
print(f"  Top recenti trovati: {len(ccu_map)}")


# ─────────────────────── Fetch giochi co-op ──────────────────────────────
print("\n🎮 Fetch giochi co-op da SteamSpy (tag multipli)...")
coop_games = {}
for tag in ['Co-op', 'Online+Co-Op', 'Local+Co-Op', 'Co-op+Campaign']:
    data = steam_source.fetch_json(f"https://steamspy.com/api.php?request=tag&tag={tag}") or {}
    for aid, gdata in data.items():
        if aid not in coop_games:
            coop_games[aid] = gdata
    print(f"  Tag '{tag}': {len(data)} giochi  (totale unici: {len(coop_games)})")


# ─────────────────── Fetch set appid indie e free ────────────────────────
print("\n🏷️  Fetch tag Indie e Free to Play da SteamSpy...")
indie_appids = set((steam_source.fetch_json("https://steamspy.com/api.php?request=tag&tag=Indie") or {}).keys())
free_appids  = set((steam_source.fetch_json("https://steamspy.com/api.php?request=tag&tag=Free+to+Play") or {}).keys())
print(f"  Indie appids trovati: {len(indie_appids)}")
print(f"  Free  appids trovati: {len(free_appids)}")


# ─────────────────── Aggiorna CCU + rating giochi esistenti ──────────────
print("\n🔄 Aggiornamento CCU, rating e tag indie/free...")
updated_ccu = 0
updated_rating = 0
for g in existing_games:
    aid = appid_from_url(g['steamUrl'])
    if not aid:
        continue
    new_ccu = ccu_map.get(aid, coop_games.get(aid, {}).get('ccu', 0) or 0)
    g['ccu']      = new_ccu
    g['trending'] = new_ccu >= MIN_CCU_TRENDING
    if new_ccu > 0:
        updated_ccu += 1
    spy = coop_games.get(aid, {})
    pos = spy.get('positive', 0) or 0
    neg = spy.get('negative', 0) or 0
    if pos + neg >= 10:
        g['rating'] = calc_rating(pos, neg)
        updated_rating += 1
    # Aggiorna tag indie/free (la verifica approfondita avviene dopo nella fase VERIFICA)
    # Qui usiamo solo le blacklist note per rimuovere tag sicuramente sbagliati
    if aid in NOT_INDIE_APPIDS and 'indie' in g['categories']:
        g['categories'].remove('indie')
    if aid in NOT_FREE_APPIDS and 'free' in g['categories']:
        g['categories'].remove('free')

print(f"  CCU aggiornati   : {updated_ccu}")
print(f"  Rating aggiornati: {updated_rating}")
print(f"  Trending 🔥      : {sum(1 for g in existing_games if g['trending'])}")


# ─────────── Fetch descrizioni EN per giochi esistenti senza ──────────────
print(f"\n🌍 Fetch descrizioni inglesi mancanti (max {MAX_EN_FETCH})...")
en_fetched = 0
en_failed  = 0
for g in existing_games:
    if en_fetched >= MAX_EN_FETCH:
        break
    if g.get('description_en') and len(g['description_en']) > 20:
        continue  # già presente
    aid = appid_from_url(g['steamUrl'])
    if not aid:
        continue
    print(f"  EN: {g['title']} ({aid})...", end=' ', flush=True)
    _, en_desc = steam_source.fetch_steam_desc(aid, 'english')
    if en_desc:
        g['description_en'] = en_desc
        print(f"OK ({len(en_desc)} chars)")
        en_fetched += 1
    else:
        g['description_en'] = ''
        print("FAILED")
        en_failed += 1

print(f"  Descrizioni EN aggiunte: {en_fetched}  |  Fallite: {en_failed}")


# ─────────────────── Trova nuovi candidati ───────────────────────────────
print("\n🆕 Ricerca nuovi giochi co-op non nel database...")
new_candidates = []
for aid, gdata in coop_games.items():
    if aid in existing_appids or aid in BLACKLIST_APPIDS:
        continue
    name = gdata.get('name', '')
    if not name:
        continue
    if any(w in name.lower() for w in SKIP_WORDS):
        continue
    ccu = ccu_map.get(aid, gdata.get('ccu', 0) or 0)
    if ccu < MIN_CCU_NEW:
        continue
    # Salta edizioni vecchie (FIFA 23, NBA 2K23, ecc.)
    is_old = False
    if re.search(r'FIFA \d+', name):
        is_old = True
    for pat_name, check in OLD_EDITION_PATTERNS[1:]:
        m = re.search(pat_name, name)
        if m and callable(check) and check(m):
            is_old = True
            break
    if is_old:
        continue
    new_candidates.append({'appid': aid, 'name': name, 'ccu': ccu})

new_candidates.sort(key=lambda x: x['ccu'], reverse=True)
print(f"  Candidati trovati: {len(new_candidates)}")


# ─────────────────── Processa nuovi giochi ───────────────────────────────
print(f"\n➕ Aggiungo fino a {MAX_NEW_GAMES} nuovi giochi...")
next_id = max_id + 1
added   = 0
tried   = 0

for candidate in new_candidates:
    if added >= MAX_NEW_GAMES:
        break
    tried += 1
    if tried > MAX_NEW_GAMES * 4:
        break

    aid  = candidate['appid']
    name = candidate['name']
    ccu  = candidate['ccu']
    print(f"\n  [{added+1}/{MAX_NEW_GAMES}] {name} (app {aid}, CCU: {ccu})")

    # Descrizione italiana
    sd, desc_it = steam_source.fetch_steam_desc(aid, 'italian')
    if sd is None:
        print("    ✗ Nessun dato Steam")
        continue
    if sd.get('type', '') != 'game':
        print(f"    ✗ Tipo: {sd.get('type')} — skip")
        continue
    if not desc_it:
        print("    ✗ Nessuna descrizione italiana utile")
        continue

    # Verifica co-op nelle categorie Steam
    steam_cats = [c.get('description', '') for c in sd.get('categories', [])]
    has_coop = any('co-op' in c.lower() or 'multiplayer' in c.lower() for c in steam_cats)
    if not has_coop:
        print("    ✗ Nessuna categoria co-op")
        continue

    # Descrizione inglese
    _, desc_en = steam_source.fetch_steam_desc(aid, 'english')
    desc_en = desc_en or ''

    # Categorizzazione da tag SteamSpy
    spy_data = steam_source.fetch_json(f"https://steamspy.com/api.php?request=appdetails&appid={aid}") or {}
    spy_tags = list((spy_data.get('tags') or {}).keys())
    genres   = [g.get('description', '') for g in sd.get('genres', [])]
    all_labels = genres + steam_cats + spy_tags

    categories = []
    for label in all_labels:
        for tag, cat in TAG_MAP.items():
            if tag.lower() in label.lower() and cat not in categories:
                categories.append(cat)
                if len(categories) >= 3:
                    break
        if len(categories) >= 3:
            break
    if not categories:
        categories = ['action']
    # Verifica indie: controlla publisher/developer (non fidarsi dei tag)
    new_pub = sd.get('publishers', []) or []
    new_dev = sd.get('developers', []) or []
    new_publishers = [p.lower() for p in new_pub + new_dev if isinstance(p, str)]
    new_is_big = any(known in pub for pub in new_publishers for known in NOT_INDIE_PUBLISHERS)
    if aid in indie_appids and aid not in NOT_INDIE_APPIDS and not new_is_big and 'indie' not in categories:
        categories.append('indie')
    # Verifica free: usa is_free + genere F2P (non fidarsi dei tag)
    new_genres = [gr2.get('description', '').lower() for gr2 in sd.get('genres', [])]
    new_is_free = sd.get('is_free', False) and 'free to play' in new_genres
    if new_is_free and aid not in NOT_FREE_APPIDS and 'free' not in categories:
        categories.append('free')

    # Numero giocatori
    players = derive_players_label(steam_cats)

    # Rating
    pos    = spy_data.get('positive', 0) or 0
    neg    = spy_data.get('negative', 0) or 0
    rating = calc_rating(pos, neg)

    # Filtro qualità: scarta giochi con rating troppo basso
    if rating > 0 and rating < MIN_RATING_NEW:
        print(f"    ✗ Rating troppo basso: {rating}%")
        continue

    # Nuovi campi strutturali
    steam_cats_lower = [c.lower() for c in steam_cats]
    new_coop_modes = derive_coop_modes(steam_cats_lower)
    new_crossplay = derive_crossplay(steam_cats_lower)
    new_max_players = parse_max_players(players)

    new_game = {
        'id':             next_id,
        'title':          name,
        'categories':     categories[:4],
        'genres':         derive_genres(categories[:4]),
        'coopMode':       new_coop_modes,
        'maxPlayers':     new_max_players,
        'crossplay':      new_crossplay,
        'players':        players,
        'image':          f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{aid}/header.jpg",
        'description':    desc_it,
        'description_en': desc_en,
        'personalNote':   '',
        'played':         False,
        'steamUrl':       f"https://store.steampowered.com/app/{aid}/",
        'epicUrl':        '',
        'itchUrl':        '',
        'ccu':            ccu,
        'trending':       ccu >= MIN_CCU_TRENDING,
        'rating':         rating,
    }
    existing_games.append(new_game)
    existing_appids.add(aid)
    next_id += 1
    added   += 1
    print(f"    ✓ {name} | cats: {categories[:3]} | {rating}% | CCU: {ccu}")

print(f"\n  Nuovi giochi aggiunti: {added}")


# ─────────────────────── itch.io (opzionale) ─────────────────────────────
if ITCH_IO_KEY:
    print(f"\n🎲 Fetch giochi co-op da itch.io (query multiple)...")
    itch_source = ItchCatalogSource(ITCH_IO_KEY, steam_source.fetch_json, MAX_ITCH_GAMES)
    existing_itch_urls = {g.get('itchUrl', '') for g in existing_games if g.get('itchUrl')}
    itch_new = itch_source.fetch_games(existing_itch_urls, next_id, existing_titles)
    for ng in itch_new:
        existing_games.append(ng)
        existing_titles.add(ng.get('title', '').lower().strip())
        print(f"  + {ng['title']} ({ng['itchUrl']})")
    next_id += len(itch_new)
    print(f"  Aggiunti da itch.io: {len(itch_new)}")
else:
    print("\n🎲 itch.io: saltato (nessun ITCH_IO_KEY — vedi README)")


# ─────────────── IGDB Discovery (nuovi giochi cross-platform) ─────────────
igdb_discovery_added = 0
if IGDB_CLIENT_ID and IGDB_CLIENT_SECRET:
    print(f"\n🌐 IGDB Discovery: ricerca nuovi giochi co-op PC...")
    igdb_source = IgdbCatalogSource(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
    candidates = igdb_source.discover_coop_games(
        existing_igdb_ids=existing_igdb_ids,
        existing_steam_appids=existing_appids,
        existing_titles=existing_titles,
        max_games=MAX_IGDB_DISCOVERY,
    )
    print(f"  Candidati IGDB trovati: {len(candidates)}")

    for cand in candidates:
        steam_appid = cand.get('steamAppId')
        gog_id = cand.get('gogId')
        title = cand.get('title', '')

        if steam_appid:
            # Ha Steam → usa pipeline Steam per dati completi
            if steam_appid in BLACKLIST_APPIDS:
                print(f"  [IGDB→Steam] {title} → blacklisted")
                continue
            if steam_appid in existing_appids:
                print(f"  [IGDB→Steam] {title} → già nel catalogo")
                continue
            print(f"\n  [IGDB→Steam] {title} ({steam_appid})")
            sd, desc_it = steam_source.fetch_steam_desc(steam_appid, 'italian')
            if sd is None or sd.get('type', '') != 'game' or not desc_it:
                print(f"    ✗ Dati Steam insufficienti")
                continue
            steam_cats = [c.get('description', '') for c in sd.get('categories', [])]
            has_coop = any('co-op' in c.lower() or 'multiplayer' in c.lower() for c in steam_cats)
            if not has_coop:
                print(f"    ✗ Nessuna categoria co-op su Steam")
                continue
            _, desc_en = steam_source.fetch_steam_desc(steam_appid, 'english')
            spy_data = steam_source.fetch_json(f"https://steamspy.com/api.php?request=appdetails&appid={steam_appid}") or {}
            spy_tags = list((spy_data.get('tags') or {}).keys())
            genres = [g2.get('description', '') for g2 in sd.get('genres', [])]
            all_labels = genres + steam_cats + spy_tags
            categories = []
            for label in all_labels:
                for tag, cat in TAG_MAP.items():
                    if tag.lower() in label.lower() and cat not in categories:
                        categories.append(cat)
                        if len(categories) >= 3:
                            break
                if len(categories) >= 3:
                    break
            if not categories:
                categories = ['action']
            pos = spy_data.get('positive', 0) or 0
            neg = spy_data.get('negative', 0) or 0
            total_reviews = pos + neg
            rating = calc_rating(pos, neg)
            igdb_rating = cand.get('rating_igdb', 0) or 0

            # Qualità: non usiamo CCU (penalizza co-op locale e indie di nicchia).
            # Accettiamo se: recensioni sufficienti + rating ok, OPPURE IGDB rating alto.
            quality_by_steam = total_reviews >= MIN_REVIEWS_QUALITY and rating >= MIN_RATING_QUALITY
            quality_by_igdb = igdb_rating >= MIN_IGDB_RATING and total_reviews >= 10
            if not quality_by_steam and not quality_by_igdb:
                print(f"    ✗ Qualità insufficiente: {rating}% su {total_reviews} rec, IGDB={igdb_rating}")
                continue
            players = derive_players_label([c.lower() for c in steam_cats])
            new_game = {
                'id':             next_id,
                'igdbId':         cand['igdbId'],
                'title':          title,
                'categories':     categories[:4],
                'genres':         derive_genres(categories[:4]),
                'coopMode':       derive_coop_modes([c.lower() for c in steam_cats]),
                'maxPlayers':     parse_max_players(players),
                'crossplay':      derive_crossplay([c.lower() for c in steam_cats]),
                'players':        players,
                'image':          f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{steam_appid}/header.jpg",
                'description':    desc_it,
                'description_en': desc_en or '',
                'personalNote':   '',
                'played':         False,
                'steamUrl':       f"https://store.steampowered.com/app/{steam_appid}/",
                'gogUrl':         '',
                'epicUrl':        '',
                'itchUrl':        '',
                'ccu':            ccu_map.get(steam_appid, 0),
                'trending':       ccu_map.get(steam_appid, 0) >= MIN_CCU_TRENDING,
                'rating':         rating,
            }
            existing_games.append(new_game)
            existing_appids.add(steam_appid)
            existing_igdb_ids.add(cand['igdbId'])
            existing_titles.add(title.lower().strip())
            next_id += 1
            igdb_discovery_added += 1
            print(f"    ✓ {title} | {categories[:3]} | {rating}%")

        elif gog_id:
            # GOG-only: aggiungiamo con dati base (nessuna CCU disponibile)
            # Descrizioni verranno aggiunte manualmente o da RAWG in futuro
            print(f"\n  [IGDB→GOG-only] {title} — da implementare con GOG adapter")
            # TODO: fetch GOG product details per descrizione e immagine

    print(f"  Aggiunti da IGDB discovery: {igdb_discovery_added}")
else:
    print("\n🌐 IGDB Discovery: saltato (nessun IGDB_CLIENT_ID)")


# ─────────────────────── GOG (giochi GOG-only) ───────────────────────────
gog_added = 0
if IGDB_CLIENT_ID and IGDB_CLIENT_SECRET:
    print(f"\n🎮 GOG: ricerca giochi co-op GOG-only...")
    gog_candidates = fetch_gog_candidates(
        existing_titles=existing_titles,
        existing_gog_urls=existing_gog_urls,
        existing_igdb_ids=existing_igdb_ids,
        max_games=MAX_GOG_GAMES,
    )
    print(f"  Candidati GOG trovati: {len(gog_candidates)}")

    igdb_source_gog = IgdbCatalogSource(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)

    for cand in gog_candidates:
        title = cand['title']
        gog_url = cand['gogUrl']
        print(f"\n  [GOG] {title}")

        # Cerca su IGDB per dati multiplayer, rating e verifica non è su Steam
        query = (
            f"fields id, name, rating, rating_count, "
            f"external_games.uid, external_games.category, "
            f"multiplayer_modes.onlinecoop, multiplayer_modes.onlinecoopmax, "
            f"multiplayer_modes.offlinecoop, multiplayer_modes.offlinecoopmax, "
            f"multiplayer_modes.splitscreen, multiplayer_modes.lancoop; "
            f"search \"{title}\"; "
            f"where platforms = (6) & game_modes = (3); "
            f"limit 3;"
        )
        igdb_results = igdb_source_gog._post("games", query) or []

        # Trova il match esatto per titolo
        igdb_match = None
        for r in igdb_results:
            if r.get('name', '').lower().strip() == title.lower().strip():
                igdb_match = r
                break
        if not igdb_match and igdb_results:
            igdb_match = igdb_results[0]  # primo risultato come fallback

        if not igdb_match:
            print(f"    ✗ Nessun match IGDB per '{title}'")
            continue

        igdb_id = igdb_match.get('id', 0)
        if igdb_id in existing_igdb_ids:
            print(f"    ✗ igdbId {igdb_id} già nel catalogo")
            continue

        # Controlla se ha Steam → se sì, sarà aggiunto dalla pipeline Steam, skip
        has_steam = any(
            ext.get('category') == 1
            for ext in (igdb_match.get('external_games') or [])
        )
        if has_steam:
            print(f"    ✗ Ha anche Steam — gestito da pipeline Steam")
            continue

        # Qualità: preferisce IGDB rating, accetta anche solo GOG rating
        igdb_rating = igdb_match.get('rating') or 0
        igdb_rating_count = igdb_match.get('rating_count') or 0
        gog_rating = cand.get('rating_gog', 0) or 0  # 0-100 su GOG

        quality_igdb = igdb_rating >= MIN_IGDB_RATING and igdb_rating_count >= 5
        quality_gog = gog_rating >= 70  # GOG rating su 100
        if not quality_igdb and not quality_gog:
            print(f"    ✗ Qualità insufficiente: IGDB={igdb_rating:.0f}({igdb_rating_count}), GOG={gog_rating}")
            continue

        # Dati multiplayer da IGDB
        modes_list = igdb_match.get('multiplayer_modes') or []
        from igdb_catalog_source import _parse_multiplayer_modes
        mp = _parse_multiplayer_modes(modes_list) or {'coopMode': ['online'], 'maxPlayers': 4}

        # Categorie dai tag GOG
        gog_tags = cand.get('tags', [])
        categories = []
        for tag in gog_tags:
            for key, cat in TAG_MAP.items():
                if key.lower() in tag.lower() and cat not in categories:
                    categories.append(cat)
                    break
        if not categories:
            categories = ['action']

        new_game = {
            'id':             next_id,
            'igdbId':         igdb_id,
            'title':          title,
            'categories':     categories[:4],
            'genres':         derive_genres(categories[:4]),
            'coopMode':       mp['coopMode'],
            'maxPlayers':     mp['maxPlayers'] or 4,
            'crossplay':      False,
            'players':        f"1-{mp['maxPlayers'] or 4}",
            'image':          cand.get('image', ''),
            'description':    '',
            'description_en': '',
            'personalNote':   '',
            'played':         False,
            'steamUrl':       '',
            'gogUrl':         gog_url,
            'epicUrl':        '',
            'itchUrl':        '',
            'ccu':            0,
            'trending':       False,
            'rating':         round(igdb_rating) if igdb_rating else 0,
        }
        existing_games.append(new_game)
        existing_igdb_ids.add(igdb_id)
        existing_gog_urls.add(gog_url)
        existing_titles.add(title.lower().strip())
        next_id += 1
        gog_added += 1
        print(f"    ✓ {title} (GOG-only, igdbId={igdb_id})")

    print(f"  Aggiunti da GOG: {gog_added}")
else:
    print("\n🎮 GOG: saltato (richiede IGDB_CLIENT_ID per verifica dedup)")


# ─────────────────── VERIFICA INTEGRITÀ DATABASE ──────────────────────────
print("\n🔍 Verifica integrità database...")

v_fixed_free   = 0
v_fixed_indie  = 0
v_fixed_title  = 0
v_removed_nocoop = 0
v_checked      = 0

# Rotazione: ad ogni run verifica un blocco diverso di giochi
# Così in ~4 run copriamo tutto il DB
iso_week = datetime.datetime.now().isocalendar()
verify_offset = ((iso_week[0] * 52 + iso_week[1]) * 7 + iso_week[2]) % max(len(existing_games), 1)
rotated_games = existing_games[verify_offset:] + existing_games[:verify_offset]

for g in rotated_games:
    if v_checked >= MAX_VERIFY:
        break

    aid = appid_from_url(g['steamUrl'])
    if not aid:
        continue

    v_checked += 1
    cc_url = f"https://store.steampowered.com/api/appdetails?appids={aid}&l=english&cc=us"
    data = steam_source.fetch_json(cc_url)
    if not data:
        continue
    info = data.get(str(aid), {})
    if not info.get('success'):
        continue
    sd = info.get('data', {})

    # ── 0. Sanity check: verifica che l'API abbia restituito il gioco giusto ──
    # Steam API sotto rate limit può restituire dati di un altro gioco!
    api_name = sd.get('name', '')
    db_name = g['title']
    if api_name:
        # Confronto: almeno 30% delle parole significative in comune
        api_words = set(re.findall(r'[a-zA-Z]{3,}', api_name.lower()))
        db_words = set(re.findall(r'[a-zA-Z]{3,}', db_name.lower()))
        common = api_words & db_words
        total = max(len(api_words | db_words), 1)
        similarity = len(common) / total
        if similarity < 0.25 and len(api_words) > 0 and len(db_words) > 0:
            print(f"  ⛔ {db_name}: API ha restituito '{api_name}' (sim={similarity:.0%}) — scartato")
            continue

    # ── 1. Verifica FREE: usa is_free + price_overview + genere F2P ──
    steam_is_free = sd.get('is_free', False)
    price = sd.get('price_overview', {})
    price_cents = price.get('final', 0) if price else 0
    genres_list = [gr.get('description', '').lower() for gr in sd.get('genres', [])]
    has_f2p_genre = 'free to play' in genres_list
    # Veramente free = Steam dice is_free E (nessun prezzo O prezzo = 0) E genere F2P
    actually_free = steam_is_free and price_cents == 0 and has_f2p_genre

    if 'free' in g['categories'] and not actually_free:
        g['categories'].remove('free')
        v_fixed_free += 1
        fmt = price.get('final_formatted', 'N/A')
        print(f"  💰 {g['title']}: rimosso tag 'free' (is_free={steam_is_free}, prezzo={fmt}, genere_f2p={has_f2p_genre})")

    if actually_free and 'free' not in g['categories'] and aid not in NOT_FREE_APPIDS:
        g['categories'].append('free')
        v_fixed_free += 1
        print(f"  🆓 {g['title']}: aggiunto tag 'free' (verificato: is_free + genere F2P)")

    # ── 2. Verifica INDIE: controlla publisher/developer ──
    pub_names = sd.get('publishers', []) or []
    dev_names = sd.get('developers', []) or []
    publishers = [p.lower() for p in pub_names + dev_names if isinstance(p, str)]

    is_big_studio = any(
        known in pub for pub in publishers for known in NOT_INDIE_PUBLISHERS
    )

    if 'indie' in g['categories'] and (is_big_studio or aid in NOT_INDIE_APPIDS):
        g['categories'].remove('indie')
        v_fixed_indie += 1
        print(f"  🏢 {g['title']}: rimosso tag 'indie' (publisher: {publishers})")

    # ── 3. Verifica CO-OP + aggiorna coopMode/crossplay ──
    steam_cats = [c.get('description', '').lower() for c in sd.get('categories', [])]
    has_coop = any('co-op' in c or 'multiplayer' in c or 'multi-player' in c for c in steam_cats)
    if not has_coop:
        v_removed_nocoop += 1
        print(f"  ⚠️  {g['title']}: NESSUNA categoria co-op su Steam!")
        # Non rimuoviamo, ma logghiamo per revisione manuale

    # Aggiorna coopMode e crossplay dai dati Steam reali
    g['coopMode'] = derive_coop_modes(steam_cats)
    g['crossplay'] = derive_crossplay(steam_cats)
    g['genres'] = derive_genres(g['categories'])
    g['maxPlayers'] = parse_max_players(g['players'])

    # ── 4. Verifica TITOLO: solo log, non modifica automaticamente ──
    # Il rinominamento automatico è troppo rischioso con i rate limit di Steam
    steam_name = sd.get('name', '')
    if steam_name and steam_name != g['title'] and len(steam_name) > 2:
        clean_api = steam_name.lower().replace('™', '').replace('®', '').replace(':', '').strip()
        clean_db = g['title'].lower().replace('™', '').replace('®', '').replace(':', '').strip()
        if clean_api != clean_db:
            v_fixed_title += 1
            print(f"  📝 Titolo diverso (solo log): '{g['title']}' vs Steam '{steam_name}'")

print(f"\n  Verificati: {v_checked} giochi")
print(f"  Fix free  : {v_fixed_free}")
print(f"  Fix indie : {v_fixed_indie}")
print(f"  Fix titoli: {v_fixed_title}")
print(f"  Senza co-op (warning): {v_removed_nocoop}")


# ─────────────────────── Arricchimento IGDB ──────────────────────────────
igdb_enriched = 0
if IGDB_CLIENT_ID and IGDB_CLIENT_SECRET:
    print("\n🎯 Arricchimento multiplayer con IGDB...")
    igdb_enriched = enrich_games_with_igdb(existing_games, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
    print(f"  ✅ IGDB: {igdb_enriched} giochi arricchiti (coopMode, maxPlayers)")
else:
    print("\n🎯 IGDB: saltato (nessun IGDB_CLIENT_ID/IGDB_CLIENT_SECRET)")


# ─────────────────────── Gioco Indie della Settimana ─────────────────────
print("\n🌟 Selezione gioco indie della settimana...")
indie_rated = [g for g in existing_games if 'indie' in g.get('categories', []) and g.get('rating', 0) >= 75]
if indie_rated:
    indie_sorted  = sorted(indie_rated, key=lambda x: x.get('rating', 0), reverse=True)
    top_indie     = indie_sorted[:12]   # top 12 giochi indie per rating
    iso           = datetime.datetime.now().isocalendar()
    week_idx      = (iso[0] * 52 + iso[1]) % len(top_indie)
    featured_id   = top_indie[week_idx]['id']
    print(f"  Featured: {top_indie[week_idx]['title']} (id {featured_id}, rating {top_indie[week_idx]['rating']}%)")
else:
    featured_id = 0
    print("  Nessun gioco indie con rating >= 75%")


# ─────────────────────── Scrivi games.js ─────────────────────────────────
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

trending_count = sum(1 for g in existing_games if g.get('trending'))
rated_count    = sum(1 for g in existing_games if g.get('rating', 0) > 0)
en_count       = sum(1 for g in existing_games if g.get('description_en'))
indie_count    = sum(1 for g in existing_games if 'indie' in g.get('categories', []))
free_count     = sum(1 for g in existing_games if 'free'  in g.get('categories', []))
print(f"\n✅ Done!")
print(f"   Giochi totali    : {len(existing_games)}")
print(f"   Trending 🔥      : {trending_count}")
print(f"   Con rating ⭐    : {rated_count}")
print(f"   Con desc EN 🌍   : {en_count}")
print(f"   Indie 🎮         : {indie_count}")
print(f"   Free 🆓          : {free_count}")
print(f"   Featured ID 🌟   : {featured_id}")
print(f"   Nuovi aggiunti   : {added} (SteamSpy) + {igdb_discovery_added} (IGDB) + {gog_added} (GOG)")
print(f"   IGDB arricchiti  : {igdb_enriched}")
print(f"   Verifiche        : {v_checked} controllati, {v_fixed_free + v_fixed_indie + v_fixed_title} corretti, {v_removed_nocoop} warning co-op")
