"""
auto_update.py
==============
Aggiorna automaticamente games.js con:
  - CCU (giocatori concorrenti) e rating per tutti i giochi esistenti
  - Flag "trending" per i giochi con molti giocatori attivi
  - Descrizioni italiane da Steam API (nuovi giochi)
  - Descrizioni inglesi da Steam API (nuovi giochi + giochi esistenti senza)
  - Nuovi giochi co-op trending da SteamSpy
  - Tag "indie" e "free" per i giochi appropriati
  - Gioco indie della settimana (featuredIndieId)
  - [Opzionale] Giochi da itch.io (richiede ITCH_IO_KEY env var)
  - VERIFICA INTEGRITÀ: controlla free (prezzo reale), indie (publisher),
    co-op (categorie Steam), titoli (nome ufficiale Steam)

Uso locale : python3 auto_update.py
CI (GitHub): eseguito automaticamente da .github/workflows/update.yml
Per itch.io: export ITCH_IO_KEY=tuachiave  (da https://itch.io/user/settings/api-keys)
"""

import urllib.request, json, time, re, html as html_mod, os, datetime

import catalog_data

# ──────────────────────────────── CONFIG ────────────────────────────────
DELAY               = 1.5    # secondi tra richieste API
MAX_NEW_GAMES       = 15     # max nuovi giochi per run
MAX_EN_FETCH        = 30     # max giochi esistenti a cui aggiungere desc EN per run
MIN_CCU_TRENDING    = 800    # CCU minimo per badge 🔥 Trending
MAX_ITCH_GAMES      = 10     # max giochi itch.io per run
ITCH_IO_KEY         = os.environ.get('ITCH_IO_KEY', '')

# Tag Steam → categoria sito
TAG_MAP = {
    'Horror': 'horror', 'Psychological Horror': 'horror', 'Survival Horror': 'horror',
    'Action': 'action', 'Shooter': 'action', 'FPS': 'action',
    'Third-Person Shooter': 'action', "Beat 'em up": 'action', 'Fighting': 'action',
    'Puzzle': 'puzzle', 'Puzzle Platformer': 'puzzle', 'Logic': 'puzzle',
    'Local Co-Op': 'splitscreen', 'Split Screen': 'splitscreen',
    'Local Multiplayer': 'splitscreen', 'Couch Co-Op': 'splitscreen',
    'RPG': 'rpg', 'Action RPG': 'rpg', 'JRPG': 'rpg', 'Dungeon Crawler': 'rpg', 'Loot': 'rpg',
    'Survival': 'survival', 'Open World Survival Craft': 'survival',
    'Building': 'factory', 'Automation': 'factory', 'Colony Sim': 'factory',
    'Factory': 'factory', 'Resource Management': 'factory',
    'Roguelike': 'roguelike', 'Roguelite': 'roguelike', 'Rogue-lite': 'roguelike',
    'Sports': 'sport', 'Racing': 'sport', 'Soccer': 'sport', 'Football': 'sport',
    'Strategy': 'strategy', 'Turn-Based Strategy': 'strategy', 'RTS': 'strategy',
    'Tower Defense': 'strategy', 'Grand Strategy': 'strategy', 'Tactical': 'strategy',
    'Indie': 'indie',
}

BLACKLIST_APPIDS = {
    '730',      # CS2 (PvP)
    '1172470',  # Apex Legends (PvP)
    '1938090',  # Call of Duty: Warzone (PvP)
    '431960',   # Wallpaper Engine
    '1091500',  # Cyberpunk 2077 (single player)
    '1245620',  # Elden Ring (NIGHTREIGN è già nel DB)
    '1817070',  # Marvel's Spider-Man
    '2358720',  # Black Myth: Wukong
    # Giochi senza co-op che SteamSpy tagga erroneamente come co-op
    '578080',   # PUBG (battle royale PvP)
    '289070',   # Civilization VI (multiplayer competitivo)
    '8930',     # Civilization V
    '629520',   # Soundpad (tool)
    '1325860',  # VTube Studio (tool)
    '761890',   # Albion Online (MMO PvP)
    '949230',   # Cities: Skylines II (single)
    '1407200',  # World of Tanks (PvP)
    '570940',   # Dark Souls Remastered
    '305620',   # The Long Dark (single)
    '703080',   # Planet Zoo (single)
    '363970',   # Clicker Heroes (idle)
    '1677740',  # Stumble Guys (PvP)
    '386360',   # SMITE (PvP/MOBA)
    '1013320',  # Firestone Idle RPG
    '3070070',  # TCG Card Shop Simulator
    '977950',   # A Dance of Fire and Ice (rhythm)
    '601510',   # Yu-Gi-Oh! Duel Links (card PvP)
    '582160',   # AC Origins (single)
    '1850570',  # Death Stranding (single)
    '805550',   # Assetto Corsa Competizione (racing sim)
    '1244460',  # Jurassic World Evolution 2 (single)
    '203770',   # Crusader Kings II (grand strategy)
    '2651280',  # Spider-Man 2 (single)
    '613100',   # House Flipper 1 (single)
    '1971870',  # Mortal Kombat 1 (fighting PvP)
    '1888160',  # Armored Core VI (single mostly)
    '1066780',  # Transport Fever 2 (single)
    '766570',   # Russian Fishing 4
    '367520',   # Hollow Knight (single player)
    '221380',   # Age of Empires II Retired
    '1128810',  # RISK: Global Domination
    '1645820',  # SurrounDead
    '3400930',  # Guilty as Sock
    '719890',   # Beasts of Bermuda
    '433850',   # Z1 Battle Royale
    '1046930',  # Dota Underlords
    '444090',   # Paladins
    '286690',   # Metro 2033 Redux
    '1237970',  # Titanfall 2
    '311690',   # Enter the Gungeon (no co-op on Steam)
    '883710',   # Resident Evil 2 (single)
    '1196590',  # Resident Evil Village (single mostly)
    '335240',   # Transformice
    '767560',   # War Robots
    '297000',   # Heroes of M&M III HD
    '2688950',  # Planet Coaster 2
    '1238860',  # Battlefield 4
}

# Filtro qualità minima per nuovi giochi
MIN_RATING_NEW   = 65    # rating minimo per aggiungere un nuovo gioco
MIN_CCU_NEW      = 500   # CCU minimo per candidati

SKIP_WORDS = [
    'demo', ' dlc', 'soundtrack', 'artbook', 'playtest',
    'beta', 'prologue', 'upgrade pack', 'season pass',
    'content pack', 'expansion', 'bundle', 'test server',
    'dedicated server', 'editor', 'modding', 'toolkit',
]

# Pattern per edizioni vecchie (FIFA 23 quando c'è FC 25, NBA 2K23 quando c'è 2K25, ecc.)
OLD_EDITION_PATTERNS = [
    (r'FIFA \d+', r'FC \d+'),           # vecchia FIFA → nuova FC
    (r'NBA 2K(\d+)', lambda m: int(m.group(1)) < 25),  # NBA 2K con anno < 25
    (r'F1 (\d+)', lambda m: int(m.group(1)) < 24),     # F1 con anno < 24
    (r'Football Manager (\d+)', lambda m: int(m.group(1)) < 25),
]

# Giochi che Steam/SteamSpy tagga come "Indie" ma NON sono indie
# (studi AA/AAA, publisher grossi, IP di grandi aziende)
NOT_INDIE_APPIDS = {
    '251570',   # 7 Days to Die
    '436150',   # A Way Out
    '346110',   # ARK: Survival Evolved
    '945360',   # Among Us
    '361420',   # Astroneer
    '960090',   # Bloons TD 6
    '291550',   # Brawlhalla
    '221100',   # DayZ
    '435150',   # Divinity: Original Sin 2
    '373420',   # Divinity: Original Sin Enhanced Edition
    '1203620',  # Enshrouded
    '505460',   # Foxhole
    '467710',   # Gang Beasts
    '4000',     # Garry's Mod
    '815370',   # Green Hell
    '219990',   # Grim Dawn
    '581320',   # Insurgency: Sandstorm
    '232090',   # Killing Floor 2
    '899770',   # Last Epoch
    '1129580',  # Medieval Dynasty
    '275850',   # No Man's Sky
    '1623730',  # Palworld
    '1260320',  # Party Animals
    '238960',   # Path of Exile
    '1042710',  # Predecessor
    '252950',   # Rocket League
    '252490',   # Rust
    '526870',   # Satisfactory
    '244850',   # Space Engineers
    '393380',   # Squad
    '985890',   # Streets of Rage 4
    '286160',   # Tabletop Simulator
    '1361510',  # TMNT: Shredder's Revenge
    '690640',   # Trine 4
    '1225560',  # Unravel Two
    '235540',   # Warhammer: End Times - Vermintide
    '552500',   # Warhammer: Vermintide 2
}

# Publisher/developer noti come NON indie (match parziale, lowercase)
NOT_INDIE_PUBLISHERS = {
    'electronic arts', 'ea ', 'ubisoft', 'activision', 'blizzard',
    'bethesda', 'square enix', 'capcom', 'bandai namco', 'sega',
    'warner bros', 'take-two', '2k games', '2k ', 'rockstar',
    'epic games', 'riot games', 'valve', 'microsoft', 'xbox game studios',
    'sony', 'playstation', 'tencent', 'netease', 'nexon',
    'level infinite', 'amazon games', 'focus entertainment',
    'deep silver', 'thq nordic', 'embracer', 'gearbox',
    'curve games', 'curve digital', 'paradox interactive',
    'hi-rez', 'hi rez', 'grinding gear', 'digital extremes',
    'psyonix', 'respawn', 'innersloth', 'facepunch',
    'funcom', 'techland', 'keen software', 'new world interactive',
    'offworld industries', 'stunlock', 'fatshark',
    'iron gate', 'hopoo', 'behaviour interactive',
    'daybreak', 'jagex', 'ncsoft', 'smilegate', 'pearl abyss',
    'krafton', 'pubg', 'supercell', 'mihoyo', 'hoyoverse',
    'gaijin', 'wargaming', 'coffee stain',
}

# Giochi che SteamSpy tagga come "Free to Play" ma NON sono gratis
NOT_FREE_APPIDS = {
    '346110',   # ARK: Survival Evolved
    '906850',   # Age of Empires III: Definitive Edition
    '945360',   # Among Us
    '361420',   # Astroneer
    '960090',   # Bloons TD 6
    '1240440',  # EA SPORTS FC 25
    '39210',    # FINAL FANTASY XIV Online
    '654310',   # Fishing Planet
    '1293830',  # Forza Horizon 4 — NOTA: è nella lista free perché diventato F2P
    '505460',   # Foxhole
    '467710',   # Gang Beasts
    '815370',   # Green Hell
    '962130',   # Grounded
    '394360',   # Hearts of Iron IV
    '477160',   # Human: Fall Flat
    '594650',   # Hunt: Showdown 1896
    '232090',   # Killing Floor 2
    '238210',   # Magicka 2
    '274190',   # Move or Die
    '1290000',  # PowerWash Simulator
    '648800',   # Raft
    '1174180',  # Red Dead Online
    '393380',   # Squad
    '674940',   # Stick Fight: The Game
    '573090',   # Stormworks: Build and Rescue
    '376210',   # The Isle
    '386940',   # Ultimate Chicken Horse
    '865360',   # We Were Here Together
    '253710',   # theHunter: Call of the Wild
}
# ─────────────────────────────────────────────────────────────────────────


def fetch(url):
    time.sleep(DELAY)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"    ⚠ ERR {url[:70]}: {e}")
        return None


def clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:320]


def appid_from_url(url):
    m = re.search(r'/app/(\d+)', url or '')
    return m.group(1) if m else ''


def calc_rating(positive, negative):
    total = (positive or 0) + (negative or 0)
    if total < 10:
        return 0
    return round((positive or 0) / total * 100)


GENRE_CATS = {'horror', 'action', 'puzzle', 'rpg', 'survival', 'factory', 'roguelike', 'sport', 'strategy'}


def derive_genres(categories):
    """Estrae solo i generi reali dalle categorie."""
    return [c for c in categories if c in GENRE_CATS]


def derive_coop_modes(steam_cats_list):
    """Deriva coopMode dalle categorie Steam (lista di stringhe lowercase)."""
    modes = []
    has_online = any('online' in c and ('co-op' in c or 'multi' in c) for c in steam_cats_list)
    has_local = any(('local' in c and ('co-op' in c or 'multi' in c)) or 'couch' in c for c in steam_cats_list)
    has_split = any('split' in c for c in steam_cats_list)
    if has_online or (not has_local and not has_split):
        modes.append('online')
    if has_local or has_split:
        modes.append('local')
    if has_split:
        modes.append('split')
    return modes if modes else ['online']


def derive_crossplay(steam_cats_list):
    """Controlla se il gioco supporta crossplay dalle categorie Steam."""
    return any('cross-platform' in c for c in steam_cats_list)


def parse_max_players(players_str):
    """Estrae il numero massimo di giocatori dalla stringa players."""
    if not players_str:
        return 4
    numbers = re.findall(r'\d+', players_str)
    return max(int(n) for n in numbers) if numbers else 4


def fetch_steam_desc(appid, lang):
    """Fetches short_description from Steam in the given language ('italian' or 'english')."""
    cc = 'it' if lang == 'italian' else 'us'
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={lang}&cc={cc}"
    data = fetch(url)
    if not data:
        return None, None
    info = data.get(str(appid), {})
    if not info.get('success'):
        return None, None
    sd = info.get('data', {})
    desc = clean(sd.get('short_description', ''))
    if not desc or len(desc) < 25:
        desc = clean(sd.get('detailed_description', ''))[:320]
    return sd, desc if len(desc) >= 25 else None


# ─────────────────────── Leggi games.js esistente ────────────────────────
print("📖 Lettura games.js...")
featured_id_existing, existing_games = catalog_data.load_legacy_catalog_bundle()
existing_appids = set()
max_id = 0

for g in existing_games:
    max_id = max(max_id, g['id'])
    aid = appid_from_url(g['steamUrl'])
    if aid:
        existing_appids.add(aid)

print(f"  Giochi nel DB: {len(existing_games)}  |  ID max: {max_id}")


# ─────────────────────── Fetch trending da SteamSpy ──────────────────────
print("\n🔥 Fetch top giochi per giocatori recenti (SteamSpy)...")
top_recent = fetch("https://steamspy.com/api.php?request=top100in2weeks") or {}
ccu_map = {aid: d.get('ccu', 0) for aid, d in top_recent.items()}
print(f"  Top recenti trovati: {len(ccu_map)}")


# ─────────────────────── Fetch giochi co-op ──────────────────────────────
print("\n🎮 Fetch giochi co-op da SteamSpy (tag multipli)...")
coop_games = {}
for tag in ['Co-op', 'Online+Co-Op', 'Local+Co-Op', 'Co-op+Campaign']:
    data = fetch(f"https://steamspy.com/api.php?request=tag&tag={tag}") or {}
    for aid, gdata in data.items():
        if aid not in coop_games:
            coop_games[aid] = gdata
    print(f"  Tag '{tag}': {len(data)} giochi  (totale unici: {len(coop_games)})")


# ─────────────────── Fetch set appid indie e free ────────────────────────
print("\n🏷️  Fetch tag Indie e Free to Play da SteamSpy...")
indie_appids = set((fetch("https://steamspy.com/api.php?request=tag&tag=Indie") or {}).keys())
free_appids  = set((fetch("https://steamspy.com/api.php?request=tag&tag=Free+to+Play") or {}).keys())
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
    _, en_desc = fetch_steam_desc(aid, 'english')
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
    sd, desc_it = fetch_steam_desc(aid, 'italian')
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
    _, desc_en = fetch_steam_desc(aid, 'english')
    desc_en = desc_en or ''

    # Categorizzazione da tag SteamSpy
    spy_data = fetch(f"https://steamspy.com/api.php?request=appdetails&appid={aid}") or {}
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
    players = '1-4'
    for c in steam_cats:
        m = re.search(r'(\d+)', c)
        if m and 'player' in c.lower():
            n = int(m.group(1))
            players = f'1-{n}' if n > 1 else '1-2'
            break

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
    itch_queries = ['co-op', 'cooperative multiplayer', 'local co-op', 'online co-op', 'multiplayer indie']
    itch_games_all = {}
    for q in itch_queries:
        url = f"https://itch.io/api/1/{ITCH_IO_KEY}/search/games?query={q.replace(' ', '+')}"
        data = fetch(url) or {}
        for g in data.get('games', []):
            gid = g.get('id')
            if gid and gid not in itch_games_all:
                itch_games_all[gid] = g
    itch_games = list(itch_games_all.values())
    # Ordina per priorità: giochi con più info disponibili
    itch_games.sort(key=lambda g: (len(g.get('short_text') or ''), g.get('id', 0)), reverse=True)
    print(f"  Trovati: {len(itch_games)} giochi")
    existing_itch_urls = {g.get('itchUrl', '') for g in existing_games if g.get('itchUrl')}
    itch_added = 0
    for ig in itch_games:
        if itch_added >= MAX_ITCH_GAMES:
            break
        game_url = ig.get('url', '')
        if not game_url or game_url in existing_itch_urls:
            continue
        short_text = ig.get('short_text', '') or ''
        if len(short_text) < 20:
            continue
        cover = ig.get('cover_url') or ig.get('cover') or ''
        title = ig.get('title', '')
        if not title:
            continue
        is_free = (ig.get('min_price', 1) == 0)
        cats = ['indie']
        if is_free:
            cats.append('free')
        new_game = {
            'id':             next_id,
            'title':          title,
            'categories':     cats,
            'genres':         derive_genres(cats),
            'coopMode':       ['online'],
            'maxPlayers':     4,
            'crossplay':      False,
            'players':        '2-4',
            'image':          cover,
            'description':    short_text,
            'description_en': short_text,
            'personalNote':   '',
            'played':         False,
            'steamUrl':       '',
            'epicUrl':        '',
            'itchUrl':        game_url,
            'ccu':            0,
            'trending':       False,
            'rating':         0,
        }
        existing_games.append(new_game)
        existing_itch_urls.add(game_url)
        next_id  += 1
        itch_added += 1
        print(f"  + {title} ({game_url})")
    print(f"  Aggiunti da itch.io: {itch_added}")
else:
    print("\n🎲 itch.io: saltato (nessun ITCH_IO_KEY — vedi README)")


# ─────────────────── VERIFICA INTEGRITÀ DATABASE ──────────────────────────
print("\n🔍 Verifica integrità database...")

v_fixed_free   = 0
v_fixed_indie  = 0
v_fixed_title  = 0
v_removed_nocoop = 0
v_checked      = 0
MAX_VERIFY     = 80   # max giochi da verificare via API per run (rate limit)

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
    data = fetch(cc_url)
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
print(f"   Nuovi aggiunti   : {added}")
print(f"   Verifiche        : {v_checked} controllati, {v_fixed_free + v_fixed_indie + v_fixed_title} corretti, {v_removed_nocoop} warning co-op")
