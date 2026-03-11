"""
fetch_ratings.py
================
Aggiunge/aggiorna il campo 'rating' (% recensioni positive Steam)
a tutti i giochi in games.js, usando SteamSpy API.

Esegui UNA VOLTA per popolare tutti i rating esistenti.
Dopo, auto_update.py mantiene i rating aggiornati ad ogni run.

Uso: python3 fetch_ratings.py
"""

import urllib.request, json, time, re, os

DELAY  = 1.2   # secondi tra richieste (SteamSpy è più permissivo)
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.js")


def fetch(url):
    time.sleep(DELAY)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  ⚠ {e}")
        return None


def calc_rating(positive, negative):
    """Calcola % recensioni positive. Ritorna 0 se meno di 10 recensioni."""
    total = (positive or 0) + (negative or 0)
    if total < 10:
        return 0
    return round((positive or 0) / total * 100)


def rating_label(r):
    if r >= 95: return "🏆 Acclamato"
    if r >= 85: return "😊 Molto Positivo"
    if r >= 70: return "👍 Positivo"
    if r >= 55: return "😐 Nella Norma"
    if r >= 40: return "😕 Misto"
    return "👎 Negativo"


def appid_from_url(url):
    m = re.search(r'/app/(\d+)', url or '')
    return m.group(1) if m else ''


def ef(block, field):
    m = re.search(
        rf'{field}:\s*("(?:[^"\\]|\\.)*"|\[.*?\]|true|false|-?\d+)',
        block, re.DOTALL
    )
    if not m: return None
    v = m.group(1)
    if v == 'true':  return True
    if v == 'false': return False
    if re.fullmatch(r'-?\d+', v): return int(v)
    if v.startswith('['): return re.findall(r'"([^"]+)"', v)
    return v.strip('"').replace('\\"', '"')


def js_esc(s):
    if s is None: return ''
    return str(s).replace('\\', '\\\\').replace('"', '\\"')


# ──────────────────── Leggi games.js ─────────────────────
print("📖 Lettura games.js...")
with open(OUTPUT, "r", encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
games  = []
max_id = 0

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
        'epicUrl':      ef(b, 'epicUrl') or '',
        'ccu':          ef(b, 'ccu') or 0,
        'trending':     ef(b, 'trending') or False,
        'rating':       ef(b, 'rating') or 0,
    }
    if g['id'] is not None:
        games.append(g)
        max_id = max(max_id, g['id'])

print(f"  Giochi trovati: {len(games)}")


# ──────────────────── Fetch rating per ogni gioco ────────────────────
print(f"\n⭐ Fetch rating ({len(games)} giochi) da SteamSpy...")
print("  (può richiedere ~5-7 minuti con rate limit)")

ok = 0
skipped = 0

for i, g in enumerate(games):
    aid = appid_from_url(g['steamUrl'])
    if not aid:
        skipped += 1
        continue

    # Se ha già un rating valido (già fetchato), salta per velocità
    # Rimuovi questo blocco se vuoi forzare il rinnovo di tutti i rating
    if g['rating'] > 0:
        print(f"  [{i+1:3}/{len(games)}] {g['title'][:40]:<40} — già {g['rating']}% ✓")
        ok += 1
        continue

    data = fetch(f"https://steamspy.com/api.php?request=appdetails&appid={aid}")
    if not data:
        print(f"  [{i+1:3}/{len(games)}] {g['title'][:40]:<40} — ✗ no data")
        continue

    pos = data.get('positive', 0) or 0
    neg = data.get('negative', 0) or 0
    rating = calc_rating(pos, neg)
    g['rating'] = rating

    label = rating_label(rating) if rating else "n/d"
    print(f"  [{i+1:3}/{len(games)}] {g['title'][:40]:<40} — {rating}% ({pos+neg} rec.) {label}")
    ok += 1


# ──────────────────── Scrivi games.js aggiornato ─────────────────────
print(f"\n💾 Scrittura games.js ({len(games)} giochi)...")
lines = ['const games = [\n']
for g in games:
    cats_js = json.dumps(g['categories'], ensure_ascii=False)
    block = (
        f"  {{\n"
        f"    id: {g['id']},\n"
        f"    title: \"{js_esc(g['title'])}\",\n"
        f"    categories: {cats_js},\n"
        f"    players: \"{js_esc(g['players'])}\",\n"
        f"    image: \"{js_esc(g['image'])}\",\n"
        f"    description: \"{js_esc(g['description'])}\",\n"
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

rated = sum(1 for g in games if g.get('rating', 0) > 0)
print(f"\n✅ Done! Rating aggiornati: {rated}/{len(games)}")
