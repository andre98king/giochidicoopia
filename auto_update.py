"""
auto_update.py
==============
Aggiorna automaticamente games.js con:
  - CCU (giocatori concorrenti) e rating per tutti i giochi esistenti
  - Flag "trending" per i giochi con molti giocatori attivi
  - Descrizioni italiane da Steam API (nuovi giochi)
  - Descrizioni inglesi da Steam API (nuovi giochi + giochi esistenti senza)
  - Nuovi giochi co-op trending da SteamSpy

Uso locale : python3 auto_update.py
CI (GitHub): eseguito automaticamente da .github/workflows/update.yml
"""

import urllib.request, json, time, re, html as html_mod, os

# ──────────────────────────────── CONFIG ────────────────────────────────
DELAY               = 1.5    # secondi tra richieste API
MAX_NEW_GAMES       = 15     # max nuovi giochi per run
MAX_EN_FETCH        = 30     # max giochi esistenti a cui aggiungere desc EN per run
MIN_CCU_TRENDING    = 800    # CCU minimo per badge 🔥 Trending
OUTPUT              = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.js")

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


# ─────────────────── Aggiorna CCU + rating giochi esistenti ──────────────
print("\n🔄 Aggiornamento CCU e rating giochi esistenti...")
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
        'categories':     categories[:3],
        'players':        players,
        'image':          f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{aid}/header.jpg",
        'description':    desc_it,
        'description_en': desc_en,
        'personalNote':   '',
        'played':         False,
        'steamUrl':       f"https://store.steampowered.com/app/{aid}/",
        'epicUrl':        '',
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


# ─────────────────────── Scrivi games.js ─────────────────────────────────
print(f"\n💾 Scrittura games.js ({len(existing_games)} giochi)...")
lines = ['const games = [\n']
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
print(f"\n✅ Done!")
print(f"   Giochi totali    : {len(existing_games)}")
print(f"   Trending 🔥      : {trending_count}")
print(f"   Con rating ⭐    : {rated_count}")
print(f"   Con desc EN 🌍   : {en_count}")
print(f"   Nuovi aggiunti   : {added}")
