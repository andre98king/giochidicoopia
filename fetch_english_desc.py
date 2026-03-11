#!/usr/bin/env python3
"""
Fetches English descriptions from Steam Store API for all games in games.js
and adds a description_en field to each game.
"""
import re, json, time, requests

DELAY = 1.5  # seconds between requests

# ===== PARSE games.js (regex-based, robust) =====
def get_str(block, key):
    """Extract a string field value from a JS object block."""
    m = re.search(r'\b' + key + r'\s*:\s*"((?:[^"\\]|\\.)*)"', block)
    return m.group(1) if m else ''

def get_int(block, key):
    m = re.search(r'\b' + key + r'\s*:\s*(-?\d+)', block)
    return int(m.group(1)) if m else 0

def get_bool(block, key):
    m = re.search(r'\b' + key + r'\s*:\s*(true|false)', block)
    return m.group(1) == 'true' if m else False

def get_list(block, key):
    m = re.search(r'\b' + key + r'\s*:\s*\[([^\]]*)\]', block)
    if not m: return []
    return re.findall(r'"([^"]*)"', m.group(1))

def unescape(s):
    return s.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')

def load_games(path='games.js'):
    js = open(path, encoding='utf-8').read()
    # Split into individual game blocks using id: N as separator
    blocks = re.split(r'\n  \{', js)
    games = []
    for block in blocks[1:]:  # skip header
        block = block.rstrip().rstrip(',').rstrip('}').rstrip()
        g = {
            'id':            get_int(block,  'id'),
            'title':         unescape(get_str(block, 'title')),
            'categories':    get_list(block, 'categories'),
            'players':       unescape(get_str(block, 'players')),
            'image':         unescape(get_str(block, 'image')),
            'description':   unescape(get_str(block, 'description')),
            'description_en':unescape(get_str(block, 'description_en')),
            'personalNote':  unescape(get_str(block, 'personalNote')),
            'played':        get_bool(block, 'played'),
            'steamUrl':      unescape(get_str(block, 'steamUrl')),
            'epicUrl':       unescape(get_str(block, 'epicUrl')),
            'ccu':           get_int(block,  'ccu'),
            'trending':      get_bool(block, 'trending'),
            'rating':        get_int(block,  'rating'),
        }
        if g['id'] > 0:
            games.append(g)
    return games

# ===== FETCH ENGLISH DESCRIPTION FROM STEAM =====
def fetch_en_desc(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english&cc=us"
        r = requests.get(url, timeout=12)
        data = r.json()
        info = data.get(str(appid), {})
        if not info.get('success'):
            return None
        return info['data'].get('short_description', '').strip() or None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def extract_appid(steam_url):
    if not steam_url:
        return None
    m = re.search(r'/app/(\d+)/', steam_url)
    return m.group(1) if m else None

# ===== WRITE games.js =====
def esc(s):
    return str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', '').strip()

def write_games(games, path='games.js'):
    lines = ['const games = [']
    for i, g in enumerate(games):
        comma = ',' if i < len(games) - 1 else ''
        cats = ', '.join(f'"{c}"' for c in g['categories'])
        lines += [
            '  {',
            f'    id: {g["id"]},',
            f'    title: "{esc(g["title"])}",',
            f'    categories: [{cats}],',
            f'    players: "{esc(g["players"])}",',
            f'    image: "{esc(g.get("image",""))}",',
            f'    description: "{esc(g["description"])}",',
            f'    description_en: "{esc(g.get("description_en",""))}",',
            f'    personalNote: "{esc(g.get("personalNote",""))}",',
            f'    played: {"true" if g.get("played") else "false"},',
            f'    steamUrl: "{esc(g.get("steamUrl",""))}",',
            f'    epicUrl: "{esc(g.get("epicUrl",""))}",',
            f'    ccu: {g.get("ccu", 0)},',
            f'    trending: {"true" if g.get("trending") else "false"},',
            f'    rating: {g.get("rating", 0)}',
            '  }' + comma,
        ]
    lines.append('];')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

# ===== MAIN =====
games = load_games()
print(f"Loaded {len(games)} games\n")

fetched = 0
skipped = 0
failed = 0

for i, g in enumerate(games):
    existing = g.get('description_en', '')
    if existing and len(existing) > 20:
        print(f"[{i+1}/{len(games)}] {g['title']}: già tradotto, skip")
        skipped += 1
        continue

    appid = extract_appid(g.get('steamUrl', ''))
    if not appid:
        print(f"[{i+1}/{len(games)}] {g['title']}: nessun appid, skip")
        g['description_en'] = ''
        skipped += 1
        continue

    print(f"[{i+1}/{len(games)}] {g['title']} ({appid})...", end=' ', flush=True)
    desc = fetch_en_desc(appid)
    if desc:
        g['description_en'] = desc
        print(f"OK ({len(desc)} chars)")
        fetched += 1
    else:
        g['description_en'] = ''
        print("FAILED")
        failed += 1
    time.sleep(DELAY)

write_games(games)
print(f"\nDone! Fetched: {fetched}, Skipped: {skipped}, Failed: {failed}")
print("games.js aggiornato con description_en per tutti i giochi.")
