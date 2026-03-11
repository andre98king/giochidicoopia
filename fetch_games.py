"""
Fetches popular co-op PC games from SteamSpy + Steam Store API
and generates an updated games.js file.
"""

import urllib.request
import json
import time
import re
import os
import html

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
PAGES_TO_FETCH   = 2          # SteamSpy pages (1000 games each, sorted by owners)
MAX_GAMES        = 200        # max entries in final games.js
STEAM_DELAY      = 1.2        # seconds between Steam API calls (rate limit)
STEAMSPY_DELAY   = 0.5
OUTPUT_FILE      = os.path.join(os.path.dirname(__file__), "games.js")

# Tag → category mapping (order matters: first match wins for primary)
TAG_CATEGORY_MAP = {
    "Horror":              "horror",
    "Psychological Horror":"horror",
    "Survival Horror":     "horror",
    "Zombies":             "horror",
    "Action":              "action",
    "Shooter":             "action",
    "FPS":                 "action",
    "Third-Person Shooter":"action",
    "Hack and Slash":      "action",
    "Beat 'em up":         "action",
    "Puzzle":              "puzzle",
    "Puzzle Platformer":   "puzzle",
    "Escape Room":         "puzzle",
    "Split Screen":        "splitscreen",
    "Local Co-Op":         "splitscreen",
    "Local Multiplayer":   "splitscreen",
    "RPG":                 "rpg",
    "Action RPG":          "rpg",
    "JRPG":                "rpg",
    "Dungeon Crawler":     "rpg",
    "Survival":            "survival",
    "Open World Survival Craft": "survival",
    "Factory Simulation":  "factory",
    "Base Building":       "factory",
    "Automation":          "factory",
    "Roguelike":           "roguelike",
    "Roguelite":           "roguelike",
    "Sports":              "sport",
    "Racing":              "sport",
    "Strategy":            "strategy",
    "Tower Defense":       "strategy",
    "RTS":                 "strategy",
    "Platformer":          "action",
    "Run and Gun":         "action",
}

# Tags that indicate NOT a real co-op game (competitive/solo)
EXCLUDE_TAGS = {
    "Battle Royale", "MOBA", "Card Game", "Turn-Based Strategy",
    "Visual Novel", "Simulation", "Early Access",  # keep EA but low priority
}

# Tags that should be excluded entirely (competitive-only)
EXCLUDE_PRIMARY = {"Battle Royale", "MOBA"}

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def fetch_json(url, delay=0):
    time.sleep(delay)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def clean_text(text):
    """Strip HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300]  # truncate


def get_categories_from_tags(tags: dict) -> list:
    """Given a SteamSpy tags dict {tag: votes}, return our category list."""
    # Sort tags by votes (most relevant first)
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    tag_names = [t[0] for t in sorted_tags]

    # Check for hard excludes
    for t in tag_names[:5]:
        if t in EXCLUDE_PRIMARY:
            return []  # skip this game

    cats = []
    seen = set()
    for tag in tag_names:
        cat = TAG_CATEGORY_MAP.get(tag)
        if cat and cat not in seen:
            cats.append(cat)
            seen.add(cat)
        if len(cats) >= 3:
            break

    return cats if cats else ["action"]  # default fallback


def get_players_text(steam_data: dict) -> str:
    """Extract player count from Steam categories."""
    cats = steam_data.get("categories", [])
    ids = {c.get("id") for c in cats}
    # 1=multi, 9=co-op, 38=online co-op, 24=shared screen, 36=local multi
    if 38 in ids or 9 in ids:
        return "1-4"
    if 24 in ids or 36 in ids:
        return "1-4 (locale)"
    return "2+"


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Co-op Games Fetcher")
    print("=" * 60)

    # ── Step 1: collect app IDs from SteamSpy co-op tag pages ──
    print("\n[1/4] Fetching co-op game list from SteamSpy...")
    raw_games = {}  # appid → basic info

    for page in range(PAGES_TO_FETCH):
        url = f"https://steamspy.com/api.php?request=tag&tag=Co-op&page={page}"
        print(f"  Page {page}...", end=" ", flush=True)
        data = fetch_json(url, delay=STEAMSPY_DELAY)
        if not data:
            break
        raw_games.update(data)
        print(f"{len(data)} games")

    print(f"  Total collected: {len(raw_games)} games")

    # Sort by CCU (concurrent users) as quality signal, fallback owners
    def sort_key(item):
        d = item[1]
        return d.get("ccu", 0)

    sorted_games = sorted(raw_games.items(), key=sort_key, reverse=True)

    # ── Step 2: fetch SteamSpy details (tags) for top candidates ──
    print(f"\n[2/4] Fetching tags for top {min(400, len(sorted_games))} games...")
    candidates = []
    checked = 0

    for appid_str, basic in sorted_games[:600]:
        checked += 1
        if checked % 50 == 0:
            print(f"  Checked {checked}...")

        url = f"https://steamspy.com/api.php?request=appdetails&appid={appid_str}"
        detail = fetch_json(url, delay=STEAMSPY_DELAY)
        if not detail:
            continue

        tags = detail.get("tags", {})
        if not tags:
            continue

        cats = get_categories_from_tags(tags)
        if not cats:
            continue  # excluded

        candidates.append({
            "appid": appid_str,
            "name":  basic.get("name", "Unknown"),
            "tags":  tags,
            "cats":  cats,
            "ccu":   basic.get("ccu", 0),
        })

        if len(candidates) >= MAX_GAMES + 50:
            break

    print(f"  Valid co-op candidates: {len(candidates)}")

    # ── Step 3: fetch Steam Store details (description + players) ──
    print(f"\n[3/4] Fetching Steam Store details...")
    games_out = []
    game_id = 1

    for i, cand in enumerate(candidates[:MAX_GAMES]):
        appid = cand["appid"]
        print(f"  [{i+1}/{min(MAX_GAMES, len(candidates))}] {cand['name']} (app {appid})")

        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english&cc=us"
        steam = fetch_json(url, delay=STEAM_DELAY)

        description = ""
        players = "1-4"
        is_pc = True

        if steam and steam.get(appid, {}).get("success"):
            sd = steam[appid]["data"]
            # Check it's actually a game
            if sd.get("type") not in ("game", "dlc"):
                continue
            # Check PC platforms
            platforms = sd.get("platforms", {})
            if not platforms.get("windows"):
                continue
            description = clean_text(sd.get("short_description", ""))
            players = get_players_text(sd)

        if not description:
            description = f"Gioco co-op per PC. Categorie: {', '.join(cand['cats'])}."

        games_out.append({
            "id":           game_id,
            "title":        cand["name"],
            "categories":   cand["cats"],
            "players":      players,
            "image":        f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
            "description":  description,
            "personalNote": "",
            "played":       False,
            "steamUrl":     f"https://store.steampowered.com/app/{appid}/",
        })
        game_id += 1

    print(f"\n  Games ready: {len(games_out)}")

    # ── Step 4: generate games.js ──
    print(f"\n[4/4] Writing {OUTPUT_FILE}...")

    def js_str(s):
        return json.dumps(s, ensure_ascii=False)

    lines = ["const games = [\n"]
    for g in games_out:
        cats_js = json.dumps(g["categories"], ensure_ascii=False)
        block = f"""  {{
    id: {g['id']},
    title: {js_str(g['title'])},
    categories: {cats_js},
    players: {js_str(g['players'])},
    image: {js_str(g['image'])},
    description: {js_str(g['description'])},
    personalNote: "",
    played: false,
    steamUrl: {js_str(g['steamUrl'])}
  }},\n"""
        lines.append(block)

    lines.append("];\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"  Done! {len(games_out)} games written to games.js")
    print("=" * 60)


if __name__ == "__main__":
    main()
