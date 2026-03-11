"""
Aggiorna games.js con:
- Descrizioni in italiano (Steam API con l=italian)
- epicUrl per i giochi disponibili su Epic Games
"""
import urllib.request, json, time, re, html as html_mod, os

DELAY = 1.2
OUTPUT = os.path.join(os.path.dirname(__file__), "games.js")

# appid → slug Epic Games
EPIC_MAP = {
    '252950':  'rocket-league',
    '271590':  'grand-theft-auto-v',
    '3240220': 'grand-theft-auto-v',
    '49520':   'borderlands-2',
    '397540':  'borderlands-3',
    '346110':  'ark',
    '440900':  'conan-exiles',
    '548430':  'deep-rock-galactic',
    '239140':  'dying-light',
    '534380':  'dying-light-2',
    '1282100': 'remnant-2',
    '552500':  'warhammer-vermintide-2',
    '1361210': 'warhammer-40000-darktide',
    '1172620': 'sea-of-thieves',
    '976730':  'halo-the-master-chief-collection',
    '1240440': 'halo-infinite',
    '2215430': 'ghost-of-tsushima-directors-cut',
    '2001120': 'split-fiction',
    '1426210': 'it-takes-two',
    '230410':  'warframe',
    '238960':  'path-of-exile',
    '304390':  'for-honor',
    '359550':  'rainbow-six-siege',
    '1085660': 'destiny-2',
    '460930':  'tom-clancys-ghost-recon-wildlands',
    '2231380': 'tom-clancys-ghost-recon-breakpoint',
    '1151340': 'fallout-76',
    '232090':  'killing-floor-2',
    '2183900': 'warhammer-40000-space-marine-2',
    '268500':  'xcom-2',
    '1217060': 'gunfire-reborn',
    '2344520': 'diablo-iv',
    '1086940': 'baldurs-gate-3',
    '435150':  'divinity-original-sin-2',
    '550':     'left-4-dead-2',
    '218620':  'payday-2',
    '1966720': 'lethal-company',
    '892970':  'valheim',
    '582010':  'monster-hunter-world',
    '1446780': 'monster-hunter-rise',
    '2246340': 'monster-hunter-wilds',
    '620':     'portal-2',
    '105600':  'terraria',
    '1426210': 'it-takes-two',
    '602960':  'barotrauma',
    '962130':  'grounded',
    '648800':  'raft',
    '526870':  'satisfactory',
    '427520':  'factorio',
}

def fetch(url):
    time.sleep(DELAY)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  ERR {e}")
        return None

def clean(text):
    if not text: return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:320]

def get_appid(url):
    m = re.search(r'/app/(\d+)', url or '')
    return m.group(1) if m else ''

# ── Leggi games.js
with open(OUTPUT, "r", encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(r'\{[^{}]*\}', content, re.DOTALL)

def ef(block, field):
    m = re.search(rf'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|\d+)', block, re.DOTALL)
    if not m: return None
    v = m.group(1)
    if v == 'true': return True
    if v == 'false': return False
    if v.isdigit(): return int(v)
    if v.startswith('['): return re.findall(r'"([^"]+)"', v)
    return v.strip('"').replace('\\"', '"')

games = []
for b in blocks:
    g = {
        'id':           ef(b, 'id'),
        'title':        ef(b, 'title') or '',
        'categories':   ef(b, 'categories') or [],
        'players':      ef(b, 'players') or '1-4',
        'image':        ef(b, 'image') or '',
        'description':  ef(b, 'description') or '',
        'personalNote': ef(b, 'personalNote') or '',
        'played':       ef(b, 'played') or False,
        'steamUrl':     ef(b, 'steamUrl') or '',
    }
    if g['id'] is not None:
        games.append(g)

print(f"Giochi letti: {len(games)}")

# ── Fetch descrizioni IT + epic
for i, g in enumerate(games):
    appid = get_appid(g['steamUrl'])
    print(f"  [{i+1}/{len(games)}] {g['title']} (app {appid})")

    # Descrizione italiana
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=italian&cc=it"
    data = fetch(url)
    if data and data.get(appid, {}).get('success'):
        sd = data[appid]['data']
        desc_it = clean(sd.get('short_description', ''))
        if desc_it and len(desc_it) > 30:
            g['description'] = desc_it
        else:
            # Fallback: prova con descrizione dettagliata
            desc_detail = clean(sd.get('detailed_description', ''))
            if desc_detail and len(desc_detail) > 30:
                g['description'] = desc_detail[:320]

    # Epic URL
    g['epicUrl'] = f"https://store.epicgames.com/en-US/p/{EPIC_MAP[appid]}" if appid in EPIC_MAP else ''

# ── Scrivi games.js
def js_esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

lines = ['const games = [\n']
for g in games:
    cats = json.dumps(g['categories'], ensure_ascii=False)
    block = f"""  {{
    id: {g['id']},
    title: "{js_esc(g['title'])}",
    categories: {cats},
    players: "{js_esc(g['players'])}",
    image: "{js_esc(g['image'])}",
    description: "{js_esc(g['description'])}",
    personalNote: "{js_esc(g['personalNote'])}",
    played: {'true' if g['played'] else 'false'},
    steamUrl: "{js_esc(g['steamUrl'])}",
    epicUrl: "{js_esc(g['epicUrl'])}"
  }},\n"""
    lines.append(block)
lines.append('];\n')

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\nDone! {len(games)} giochi aggiornati con descrizioni IT ed epicUrl.")
