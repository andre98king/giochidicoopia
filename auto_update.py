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

Uso locale : python3 auto_update.py
CI (GitHub): eseguito automaticamente da .github/workflows/update.yml
Per itch.io: export ITCH_IO_KEY=tuachiave  (da https://itch.io/user/settings/api-keys)
"""

import urllib.request, json, time, re, html as html_mod, os, datetime

# ──────────────────────────────── CONFIG ────────────────────────────────
DELAY               = 1.5    # secondi tra richieste API
MAX_NEW_GAMES       = 15     # max nuovi giochi per run
MAX_EN_FETCH        = 30     # max giochi esistenti a cui aggiungere desc EN per run
MIN_CCU_TRENDING    = 800    # CCU minimo per badge 🔥 Trending
MAX_ITCH_GAMES      = 10     # max giochi itch.io per run
OUTPUT              = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.js")
ITCH_IO_KEY         = os.environ.get('ITCH_IO_KEY', '')

# Tag Steam → categoria sito
TAG_MAP = {
    'Horror': 'horror', 'Psychological Horror': 'horror', 'Survival Horror': 'horror',
    'Gore': 'horror', 'Dark': 'horror',
    'Action': 'action', 'Shooter': 'action', 'FPS': 'action',
    'Third-Person Shooter': 'action', "Beat 'em up": 'action', 'Fighting': 'action',
    'Puzzle': 'puzzle', 'Puzzle Platformer': 'puzzle', 'Logic': 'puzzle',
    'Local Co-Op': 'splitscreen', 'Split Screen': 'splitscreen',
    'Local Multiplayer': 'splitscreen', 'Couch Co-Op': 'splitscreen',
    'RPG': 'rpg', 'Action RPG': 'rpg', 'JRPG': 'rpg', 'Dungeon Crawler': 'rpg', 'Loot': 'rpg',
    'Survival': 'survival', 'Open World Survival Craft': 'survival',
    'Crafting': 'survival', 'Base Building': 'survival',
    'Building': 'factory', 'Automation': 'factory', 'Colony Sim': 'factory',
    'Factory': 'factory', 'Resource Management': 'factory',
    'Roguelike': 'roguelike', 'Roguelite': 'roguelike', 'Rogue-lite': 'roguelike',
    'Permadeath': 'roguelike', 'Run and Gun': 'roguelike',
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
}

SKIP_WORDS = [
    'demo', ' dlc', 'soundtrack', 'artbook', 'playtest',
    'beta', 'prologue', 'upgrade pack', 'season pass',
    'content pack', 'expansion', 'bundle',
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

# Giochi che SteamSpy tagga come "Free to Play" ma NON sono gratis
# (hanno avuto weekend gratuiti o versioni trial temporanee)
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


def ef(block, field):
    m = re.search(
        rf'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|-?\d+)',
        block, re.DOTALL
    )
    if not m:
        return None
    v = m.group(1)
    if v == 'true':  return True
    if v == 'false': return False
    if re.fullmatch(r'-?\d+', v): return int(v)
    if v.startswith('['): return re.findall(r'"([^"]+)"', v)
    return v.strip('"').replace('\\"', '"')


def js_esc(s):
    if s is None: return ''
    return str(s).replace('\\', '\\\\').replace('"', '\\"')


def calc_rating(positive, negative):
    total = (positive or 0) + (negative or 0)
    if total < 10:
        return 0
    return round((positive or 0) / total * 100)


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
with open(OUTPUT, "r", encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
existing_games = []
existing_appids = set()
max_id = 0

for b in blocks:
    g = {
        'id':             ef(b, 'id'),
        'title':          ef(b, 'title') or '',
        'categories':     ef(b, 'categories') or [],
        'players':        ef(b, 'players') or '1-4',
        'image':          ef(b, 'image') or '',
        'description':    ef(b, 'description') or '',
        'description_en': ef(b, 'description_en') or '',
        'personalNote':   ef(b, 'personalNote') or '',
        'played':         ef(b, 'played') or False,
        'steamUrl':       ef(b, 'steamUrl') or '',
        'epicUrl':        ef(b, 'epicUrl') or '',
        'itchUrl':        ef(b, 'itchUrl') or '',
        'ccu':            ef(b, 'ccu') or 0,
        'trending':       ef(b, 'trending') or False,
        'rating':         ef(b, 'rating') or 0,
    }
    if g['id'] is not None:
        existing_games.append(g)
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
    # Aggiorna tag indie/free (escludi NOT_INDIE_APPIDS)
    if aid in indie_appids and aid not in NOT_INDIE_APPIDS and 'indie' not in g['categories']:
        g['categories'].append('indie')
    if aid in NOT_INDIE_APPIDS and 'indie' in g['categories']:
        g['categories'].remove('indie')
    if aid in free_appids and aid not in NOT_FREE_APPIDS and 'free' not in g['categories']:
        g['categories'].append('free')
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
    # Aggiungi indie/free in base ai set SteamSpy
    if aid in indie_appids and aid not in NOT_INDIE_APPIDS and 'indie' not in categories:
        categories.append('indie')
    if aid in free_appids and 'free' not in categories:
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

    new_game = {
        'id':             next_id,
        'title':          name,
        'categories':     categories[:4],
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
lines = [f'const featuredIndieId = {featured_id};\n\n', 'const games = [\n']
for g in existing_games:
    cats_js = json.dumps(g['categories'], ensure_ascii=False)
    block = (
        f"  {{\n"
        f"    id: {g['id']},\n"
        f"    title: \"{js_esc(g['title'])}\",\n"
        f"    categories: {cats_js},\n"
        f"    players: \"{js_esc(g['players'])}\",\n"
        f"    image: \"{js_esc(g['image'])}\",\n"
        f"    description: \"{js_esc(g['description'])}\",\n"
        f"    description_en: \"{js_esc(g.get('description_en', ''))}\",\n"
        f"    personalNote: \"{js_esc(g['personalNote'])}\",\n"
        f"    played: {'true' if g['played'] else 'false'},\n"
        f"    steamUrl: \"{js_esc(g['steamUrl'])}\",\n"
        f"    epicUrl: \"{js_esc(g['epicUrl'])}\",\n"
        f"    itchUrl: \"{js_esc(g.get('itchUrl', ''))}\",\n"
        f"    ccu: {g.get('ccu') or 0},\n"
        f"    trending: {'true' if g.get('trending') else 'false'},\n"
        f"    rating: {g.get('rating') or 0}\n"
        f"  }},\n"
    )
    lines.append(block)
lines.append('];\n')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.writelines(lines)

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
