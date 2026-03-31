#!/usr/bin/env python3
"""
Build static game pages and sitemap from games.js.

This keeps the project fully static while generating crawler-friendly
game pages for GitHub Pages.
"""

from __future__ import annotations

import datetime
import html
import json

import catalog_data

ROOT = catalog_data.ROOT
GAMES_DIR = ROOT / "games"
GAMES_EN_DIR = ROOT / "games" / "en"
SITEMAP = ROOT / "sitemap.xml"
SITEMAP_INDEX = ROOT / "sitemap.xml"
SITEMAP_MAIN = ROOT / "sitemap-main.xml"
SITEMAP_HUBS = ROOT / "sitemap-hubs.xml"
SITE_URL = "https://coophubs.net"
TODAY = datetime.date.today().isoformat()
CURRENT_YEAR = datetime.date.today().year
ASSET_VERSION = "20260327"
CROSSPLAY_UI_ENABLED = True

# Caricamento override SEO
SEO_OVERRIDES = {}
try:
    with open(ROOT / "data" / "seo_overrides.json", "r") as f:
        SEO_OVERRIDES = json.load(f)
except FileNotFoundError:
    pass


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def format_ccu(value: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return str(value)


def rating_tier(rating: int) -> str:
    if rating >= 95:
        return "acclaimed"
    if rating >= 85:
        return "verypos"
    if rating >= 70:
        return "positive"
    if rating >= 55:
        return "mixed"
    return "negative"


def rating_icon(rating: int) -> str:
    if rating >= 95:
        return "🏆"
    if rating >= 85:
        return "😊"
    if rating >= 70:
        return "👍"
    if rating >= 55:
        return "😐"
    return "👎"


def rating_label_it(rating: int) -> str:
    if rating >= 95:
        return "Acclamato"
    if rating >= 85:
        return "Molto Positivo"
    if rating >= 70:
        return "Positivo"
    if rating >= 55:
        return "Nella Norma"
    if rating >= 40:
        return "Misto"
    return "Negativo"


def rating_label_en(rating: int) -> str:
    if rating >= 95:
        return "Overwhelmingly Positive"
    if rating >= 85:
        return "Very Positive"
    if rating >= 70:
        return "Mostly Positive"
    if rating >= 55:
        return "Mixed"
    if rating >= 40:
        return "Mostly Negative"
    return "Overwhelmingly Negative"


def load_games():
    return catalog_data.load_games()


def page_url(game: dict) -> str:
    return f"{SITE_URL}/games/{game['id']}.html"


def page_url_en(game: dict) -> str:
    return f"{SITE_URL}/games/en/{game['id']}.html"


def json_for_script(value) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


# Affiliate config — inserisci i tuoi ID dopo la registrazione
# GOG:  gog.com/partner → AFFILIATE_GOG = '12345'
AFFILIATE_GOG = ""
# Attivi: link di ricerca per gioco (Instant Gaming + GameBillet + Green Man Gaming)
AFFILIATE_IG = "gamer-ddc4a8"
AFFILIATE_GB = "fb308ca0-647e-4ce7-9e80-74c2c591eac1"
AFFILIATE_GMG = "https://greenmangaming.sjv.io/qWzoQy"  # Impact deep link base
AFFILIATE_GAMESEAL = (
    "https://www.tkqlhce.com/click-101708519-17170422"  # CJ Affiliate deep link
)
AFFILIATE_KINGUIN = (
    "https://www.tkqlhce.com/click-101708519-15734285"  # CJ Affiliate deep link
)
AFFILIATE_GAMIVO = "https://www.tkqlhce.com/click-101708519-15839605?url=https%3A%2F%2Fwww.gamivo.com%2F"  # CJ Affiliate deep link


def add_utm(url: str, campaign: str = "gamepage") -> str:
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    result = (
        url + sep + f"utm_source=coophubs&utm_medium=referral&utm_campaign={campaign}"
    )
    if AFFILIATE_GOG and "gog.com" in url:
        result += f"&pp={AFFILIATE_GOG}"
    return result


def find_related_games(game: dict, all_games: list, count: int = 6) -> list:
    """Find related games by shared categories, excluding the current game."""
    game_cats = set(game.get("categories") or [])
    scored = []
    for other in all_games:
        if other["id"] == game["id"]:
            continue
        other_cats = set(other.get("categories") or [])
        shared = len(game_cats & other_cats)
        if shared == 0:
            continue
        # Score: shared categories first, then rating as tiebreaker
        scored.append((shared, other.get("rating") or 0, other))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [item[2] for item in scored[:count]]


def render_related_games(related: list) -> str:
    if not related:
        return ""
    cards = []
    for g in related:
        img = g.get("image") or ""
        img_html = (
            f'<img src="{esc(img)}" alt="{esc(g["title"])}" loading="lazy" style="width:100%;height:120px;object-fit:cover;border-radius:8px 8px 0 0">'
            if img
            else ""
        )
        cards.append(
            f'<a href="{g["id"]}.html" class="related-card" style="text-decoration:none;color:inherit">'
            f"{img_html}"
            f'<div style="padding:10px;font-size:0.85rem;font-weight:600;line-height:1.3">{esc(g["title"])}</div>'
            f"</a>"
        )
    return (
        '<div class="game-section" style="margin-top:36px">'
        '<div class="game-section-title" id="relatedTitle">Giochi simili</div>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px">'
        + "".join(cards)
        + "</div></div>"
    )


def render_related_games_en(related: list) -> str:
    """Like render_related_games but links to EN pages (same directory)."""
    if not related:
        return ""
    cards = []
    for g in related:
        img = g.get("image") or ""
        img_html = (
            f'<img src="{esc(img)}" alt="{esc(g["title"])}" loading="lazy" style="width:100%;height:120px;object-fit:cover;border-radius:8px 8px 0 0">'
            if img
            else ""
        )
        cards.append(
            f'<a href="{g["id"]}.html" class="related-card" style="text-decoration:none;color:inherit">'
            f"{img_html}"
            f'<div style="padding:10px;font-size:0.85rem;font-weight:600;line-height:1.3">{esc(g["title"])}</div>'
            f"</a>"
        )
    return (
        '<div class="game-section" style="margin-top:36px">'
        '<div class="game-section-title" id="relatedTitle">Similar Games</div>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px">'
        + "".join(cards)
        + "</div></div>"
    )


def extract_steam_appid(steam_url: str) -> str | None:
    """Extract Steam App ID from a Steam store URL."""
    if not steam_url:
        return None
    import re

    m = re.search(r"/app/(\d+)", steam_url)
    return m.group(1) if m else None


def render_external_links(game: dict, lang: str = "it") -> str:
    """Render links to SteamDB, HowLongToBeat, ProtonDB."""
    appid = extract_steam_appid(game.get("steamUrl") or "")
    if not appid:
        return ""
    from urllib.parse import quote

    title_q = quote(game["title"])
    links = [
        f'<a href="https://steamdb.info/app/{appid}/" target="_blank" rel="noopener noreferrer"'
        f' class="ext-link">📊 SteamDB</a>',
        f'<a href="https://howlongtobeat.com/?q={title_q}" target="_blank" rel="noopener noreferrer"'
        f' class="ext-link">⏱️ HowLongToBeat</a>',
        f'<a href="https://www.protondb.com/app/{appid}" target="_blank" rel="noopener noreferrer"'
        f' class="ext-link">🐧 ProtonDB</a>',
        f'<a href="https://www.pcgamingwiki.com/api/appid.php?appid={appid}" target="_blank" rel="noopener noreferrer"'
        f' class="ext-link">🔧 PCGamingWiki</a>',
    ]
    section_title = "External Resources" if lang == "en" else "Risorse esterne"
    return (
        '<div class="game-section" style="margin-top:20px">'
        f'<div class="game-section-title" id="extLinksTitle">{section_title}</div>'
        '<div class="ext-links">' + "".join(links) + "</div></div>"
    )


def render_store_links(game: dict) -> str:
    from urllib.parse import quote

    btns = []
    # Store ufficiali
    if game["steamUrl"]:
        btns.append(
            f'<a class="btn-affiliate btn-steam" href="{esc(add_utm(game["steamUrl"]))}" target="_blank" '
            'rel="noopener noreferrer"><span class="affiliate-store">Steam</span></a>'
        )
    if game["epicUrl"]:
        btns.append(
            f'<a class="btn-affiliate btn-epic" href="{esc(add_utm(game["epicUrl"]))}" target="_blank" '
            'rel="noopener noreferrer"><span class="affiliate-store">Epic Games</span></a>'
        )
    if game["itchUrl"]:
        btns.append(
            f'<a class="btn-affiliate btn-itch" href="{esc(add_utm(game["itchUrl"]))}" target="_blank" '
            'rel="noopener noreferrer"><span class="affiliate-store">itch.io</span></a>'
        )
    # Prezzi alternativi — solo per giochi a pagamento (non free-to-play)
    is_free = "free" in (game.get("categories") or [])
    partner_badge = '<span class="partner-badge" title="Partner Ufficiale">✓</span>'

    if (
        not is_free
        and game["steamUrl"]
        and (
            AFFILIATE_IG
            or AFFILIATE_GB
            or AFFILIATE_GMG
            or AFFILIATE_GAMESEAL
            or AFFILIATE_KINGUIN
            or AFFILIATE_GAMIVO
        )
    ):
        q = quote(game["title"])
        if AFFILIATE_IG:
            ig_url = (
                game.get("igUrl")
                or f"https://www.instant-gaming.com/en/search/?query={q}&igr={AFFILIATE_IG}"
            )
            ig_discount = game.get("igDiscount") or 0
            disc_badge = (
                f'<span class="affiliate-discount">-{ig_discount}%</span>'
                if ig_discount > 0
                else ""
            )
            btns.append(
                f'<a class="btn-affiliate btn-ig" href="{esc(ig_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">Instant Gaming {partner_badge}</span>{disc_badge}</a>'
            )
        if AFFILIATE_GB:
            gb_url = (
                game.get("gbUrl")
                or f"https://www.gamebillet.com/search?q={q}&affiliate={AFFILIATE_GB}"
            )
            gb_discount = game.get("gbDiscount") or 0
            gb_badge = (
                f'<span class="affiliate-discount">-{gb_discount}%</span>'
                if gb_discount > 0
                else ""
            )
            btns.append(
                f'<a class="btn-affiliate btn-gb" href="{esc(gb_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">GameBillet {partner_badge}</span>{gb_badge}</a>'
            )
        if AFFILIATE_GMG:
            gmg_search = f"https://www.greenmangaming.com/search/?query={q}"
            from urllib.parse import quote as _q

            gmg_url = f"{AFFILIATE_GMG}?u={_q(gmg_search)}"
            btns.append(
                f'<a class="btn-affiliate btn-gmg" href="{esc(gmg_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">Green Man Gaming {partner_badge}</span></a>'
            )
        if AFFILIATE_GAMESEAL:
            from urllib.parse import quote as _q

            if game.get("gsUrl"):
                gs_url = game["gsUrl"]
            else:
                gs_search = f"https://gameseal.com/search?search={q}"
                gs_url = f"{AFFILIATE_GAMESEAL}?url={_q(gs_search)}"
            gs_badge = (
                f'<span class="affiliate-discount">-{game["gsDiscount"]}%</span>'
                if game.get("gsDiscount")
                else ""
            )
            btns.append(
                f'<a class="btn-affiliate btn-gameseal" href="{esc(gs_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">Gameseal {partner_badge}</span>{gs_badge}</a>'
            )
        if AFFILIATE_KINGUIN:
            kg_url = game.get("kgUrl") or AFFILIATE_KINGUIN
            kg_discount = game.get("kgDiscount") or 0
            kg_badge = (
                f'<span class="affiliate-discount">-{kg_discount}%</span>'
                if kg_discount > 0
                else ""
            )
            btns.append(
                f'<a class="btn-affiliate btn-kinguin" href="{esc(kg_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">Kinguin {partner_badge}</span>{kg_badge}</a>'
            )
        if AFFILIATE_GAMIVO:
            gmv_url = game.get("gmvUrl") or AFFILIATE_GAMIVO
            gmv_discount = game.get("gmvDiscount") or 0
            gmv_badge = (
                f'<span class="affiliate-discount">-{gmv_discount}%</span>'
                if gmv_discount > 0
                else ""
            )
            btns.append(
                f'<a class="btn-affiliate btn-gamivo" href="{esc(gmv_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">GAMIVO {partner_badge}</span>{gmv_badge}</a>'
            )
    if not btns:
        return ""

    trust_note = (
        '<div class="trust-note">'
        "🛡️ <strong>Partner Ufficiale:</strong> Coophubs collabora solo con rivenditori autorizzati. "
        "Supporta il sito acquistando in sicurezza."
        "</div>"
    )

    return (
        '<div class="store-section"><div class="game-section-title" id="storeTitle">Migliori Prezzi Partner</div>'
        '<div class="affiliate-btns">' + "".join(btns) + "</div>"
        f"{trust_note}</div>"
    )


def render_tags(game: dict) -> str:
    return "".join(
        f'<span class="tag tag-{esc(category)}" data-cat="{esc(category)}">{esc(category)}</span>'
        for category in game["categories"]
    )


def render_modes(game: dict) -> str:
    labels = {"online": "🌐 Online", "local": "🛋️ Local", "split": "🖥️ Split"}
    return "".join(
        '<span class="tag" data-mode="'
        f'{esc(mode)}" style="background:rgba(0,137,123,0.15);color:#80cbc4;'
        f'border:1px solid rgba(0,137,123,0.25)">{esc(labels.get(mode, mode))}</span>'
        for mode in game["coopMode"]
    )


def render_static_page(game: dict, all_games: list | None = None) -> str:
    title = f"{game['title']}: gioco coop PC ({game['players']} giocatori) — Coophubs"
    image = game["image"] or f"{SITE_URL}/assets/og-image.jpg"

    # Meta description (con supporto override manuale)
    game_id = str(game.get("id"))
    if game_id in SEO_OVERRIDES and "description" in SEO_OVERRIDES[game_id]:
        description_it = SEO_OVERRIDES[game_id]["description"]
    else:
        modes_str = ", ".join(game.get("coopMode", []))
        description_it = (
            f"Scopri {game['title']}, gioco cooperativo per PC ({game['players']} giocatori). Modalità {modes_str}. Recensione Steam: {game['rating']}%. "
            + game["description"]
        )
        description_it = description_it[:160]

    rating_html = ""
    if game["rating"] > 0:
        rating_html = (
            '<div class="game-info-card">'
            f'<div class="game-info-value"><span class="rating-badge rating-{rating_tier(game["rating"])}" '
            f'style="font-size:1rem;padding:4px 12px">{rating_icon(game["rating"])} {game["rating"]}%</span></div>'
            f'<div class="game-info-label" id="ratingLabel" data-label-it="{esc(rating_label_it(game["rating"]))}" '
            f'data-label-en="{esc(rating_label_en(game["rating"]))}">{esc(rating_label_it(game["rating"]))}</div>'
            "</div>"
        )

    ccu_html = ""
    if game["ccu"] > 0:
        ccu_html = (
            '<div class="game-info-card">'
            f'<div class="game-info-value" style="color:var(--accent3)">{esc(format_ccu(game["ccu"]))}</div>'
            '<div class="game-info-label" id="onlineLabel">online ora</div>'
            "</div>"
        )

    note_html = ""
    if game["played"] and game["personalNote"]:
        note_html = (
            '<div class="game-section game-note">'
            '<div class="game-section-title" id="noteTitle">La mia esperienza</div>'
            f"<p>{esc(game['personalNote'])}</p>"
            "</div>"
        )

    played_badge = ""
    if game["played"]:
        played_badge = '<span class="played-badge" id="playedBadge">✓ Giocato</span>'

    trending_badge = ""
    if game["trending"]:
        trending_badge = (
            '<span class="trending-badge" id="trendingBadge" '
            'style="position:static;display:inline-block;vertical-align:middle;margin-left:8px">'
            "🔥 Trending</span>"
        )

    crossplay_badge = ""
    if CROSSPLAY_UI_ENABLED and game["crossplay"]:
        crossplay_badge = (
            '<span class="tag" data-i18n="mode_crossplay" style="background:rgba(92,107,192,0.15);color:#9fa8da;'
            'border:1px solid rgba(92,107,192,0.25)">🔄 Crossplay</span>'
        )

    # ── JSON-LD VideoGame schema ──────────────────────────────────────────
    coop_modes = game.get("coopMode") or []
    play_modes = ["SinglePlayer"]
    if "online" in coop_modes:
        play_modes += ["CoOp", "MultiPlayer"]
    if "local" in coop_modes or "split" in coop_modes:
        if "CoOp" not in play_modes:
            play_modes.append("CoOp")

    # numberOfPlayers: parse "1-4" → QuantitativeValue
    players_str = game.get("players") or "1-4"
    players_parts = players_str.replace(" ", "").split("-")
    try:
        players_min = int(players_parts[0])
        players_max = int(players_parts[-1])
    except (ValueError, IndexError):
        players_min, players_max = 1, 4

    video_game_json = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": game["title"],
        "url": page_url(game),
        "description": game.get("description_en") or game["description"],
        "image": image,
        "genre": game["categories"],
        "gamePlatform": "PC",
        "operatingSystem": "Windows",
        "applicationCategory": "Game",
        "numberOfPlayers": {
            "@type": "QuantitativeValue",
            "minValue": players_min,
            "maxValue": players_max,
        },
        "playMode": play_modes,
    }

    if game.get("releaseYear") and game["releaseYear"] > 0:
        video_game_json["datePublished"] = str(game["releaseYear"])

    if game.get("rating") and game["rating"] > 0:
        agg = {
            "@type": "AggregateRating",
            "ratingValue": game["rating"],
            "bestRating": 100,
            "worstRating": 0,
        }
        if game.get("totalReviews") and game["totalReviews"] > 0:
            agg["ratingCount"] = game["totalReviews"]
        video_game_json["aggregateRating"] = agg

    if game.get("steamUrl"):
        video_game_json["offers"] = {
            "@type": "Offer",
            "url": game["steamUrl"],
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
        }

    script_data = {
        "description": game["description"],
        "description_en": game["description_en"],
    }

    hero_image_html = ""
    if game["image"]:
        hero_image_html = (
            f'<img class="game-hero-img" src="{esc(image)}" alt="{esc(game["title"])}" '
            "onerror=\"this.style.display='none'\">"
        )

    related_html = ""
    if all_games:
        related = find_related_games(game, all_games)
        related_html = render_related_games(related)

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description_it)}">
  <meta name="theme-color" content="#7c6aff">
  <meta name="color-scheme" content="dark">
  <link rel="canonical" href="{esc(page_url(game))}">
  <link rel="alternate" hreflang="it" href="{esc(page_url(game))}">
  <link rel="alternate" hreflang="en" href="{esc(page_url_en(game))}">
  <link rel="alternate" hreflang="x-default" href="{esc(page_url(game))}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Coophubs">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description_it)}">
  <meta property="og:url" content="{esc(page_url(game))}">
  <meta property="og:image" content="{esc(image)}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description_it)}">
  <meta name="twitter:image" content="{esc(image)}">

  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/icon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../assets/icon-180.png">
  <link rel="stylesheet" href="../assets/style.css?v={ASSET_VERSION}">
  <script type="application/ld+json">
  {json.dumps(video_game_json, ensure_ascii=False)}
  </script>
  <style>
    .game-page {{ max-width: 800px; margin: 0 auto; padding: 30px 20px 60px; position: relative; z-index: 1; }}
    .game-back {{ display: inline-flex; align-items: center; gap: 6px; color: var(--accent); text-decoration: none; font-weight: 600; margin-bottom: 24px; transition: color 0.25s; }}
    .game-back:hover {{ color: #a78bfa; }}
    .page-head .game-back {{ margin-bottom: 0; }}
    .game-hero-img {{ width: 100%; max-height: 360px; object-fit: cover; border-radius: var(--radius); margin-bottom: 24px; display: block; }}
    .game-title {{ font-size: clamp(1.6rem, 4vw, 2.4rem); font-weight: 800; letter-spacing: -1px; margin-bottom: 12px; }}
    .game-meta {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 20px; }}
    .game-section {{ margin-bottom: 24px; }}
    .game-section-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text2); margin-bottom: 8px; font-weight: 600; }}
    .game-desc {{ color: var(--text2); font-size: 1rem; line-height: 1.7; }}
    .game-note {{ background: rgba(124,106,255,0.08); border: 1px solid rgba(124,106,255,0.2); border-radius: var(--radius); padding: 16px; }}
    .game-note p {{ color: #b0b8e8; font-style: italic; line-height: 1.65; }}
    .game-actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 24px; }}
    .game-info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
    .game-info-card {{ background: var(--bg3); border: 1px solid var(--border); border-radius: 12px; padding: 14px; text-align: center; }}
    .game-info-value {{ font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: var(--accent); }}
    .game-info-label {{ font-size: 0.72rem; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
    .related-card {{ background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; transition: border-color 0.25s, transform 0.2s; overflow: hidden; }}
    .related-card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
    .ext-links {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .ext-link {{ display: inline-flex; align-items: center; gap: 4px; padding: 8px 14px; background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; color: var(--text2); text-decoration: none; font-size: 0.82rem; font-weight: 500; transition: border-color 0.25s, color 0.25s; }}
    .ext-link:hover {{ border-color: var(--accent); color: var(--accent); }}
  </style>
</head>
<body>
  <canvas id="bgCanvas" class="bg-canvas" aria-hidden="true"></canvas>

  <div class="game-page">
    <div class="page-head">
      <a href="../" class="game-back" id="backLink">← Torna al catalogo</a>
      <div class="page-head-actions">
        <button class="btn-lang" id="langBtn" onclick="setLang(currentLang === 'it' ? 'en' : 'it')" aria-label="Cambia lingua" data-i18n-aria-label="btn_lang_aria">🇬🇧 EN</button>
      </div>
    </div>

    {hero_image_html}

    <h1 class="game-title">
      {esc(game["title"])}
      {played_badge}
      {trending_badge}
    </h1>

    <div class="game-meta">
      {render_tags(game)} {render_modes(game)} {crossplay_badge}
    </div>

    <div class="game-info-grid">
      <div class="game-info-card">
        <div class="game-info-value">{esc(game["players"])}</div>
        <div class="game-info-label" id="playersLabel">Giocatori</div>
      </div>
      {rating_html}
      {ccu_html}
      <div class="game-info-card">
        <div class="game-info-value">{game["maxPlayers"] or "?"}</div>
        <div class="game-info-label" id="maxPlayersLabel">Max giocatori</div>
      </div>
    </div>

    <div class="game-section" style="margin-top:24px">
      <div class="game-section-title" id="descTitle">Descrizione</div>
      <div class="game-desc" id="gameDesc">{esc(game["description"])}</div>
    </div>

    {note_html}

    <div class="game-actions">
      {render_store_links(game)}
    </div>

    {render_external_links(game)}

    {related_html}
  </div>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">Co-op Games Hub</div>
      <div class="footer-sub" id="footerSub" data-i18n="footer_sub">Coophubs è un progetto indipendente dedicato alla scoperta di giochi cooperativi per PC.</div>
      <div class="footer-links">
        <a href="../about.html" id="footerAbout" data-i18n="footer_about">Sul progetto</a>
        <a href="../contact.html" id="footerContact" data-i18n="footer_contact">Contatti</a>
        <a href="../free.html" id="footerFree" data-i18n="footer_free">Giochi gratis</a>
        <a href="../privacy.html" id="footerPrivacy" data-i18n="footer_privacy">Privacy Policy</a>
      </div>
      <div class="footer-support">
        <a href="https://ko-fi.com/coophubs" class="btn-kofi" target="_blank" rel="noopener noreferrer" data-i18n="footer_kofi">☕ Supporta il progetto</a>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-copy" data-i18n="footer_copy">&copy; {CURRENT_YEAR} — Dati da Steam &amp; SteamSpy</div>
    </div>
  </footer>

  <script src="../assets/i18n.js?v={ASSET_VERSION}" defer></script>
  <script src="../assets/particles.js?v={ASSET_VERSION}" defer></script>
  <script>
    const GAME_DATA = {json_for_script(script_data)};

    function applyGameTranslations() {{
      const isEn = currentLang === 'en';
      const desc = isEn && GAME_DATA.description_en ? GAME_DATA.description_en : GAME_DATA.description;
      const metaDesc = desc.slice(0, 320);

      document.getElementById('backLink').textContent = t('page_back_catalog');
      document.getElementById('descTitle').textContent = t('modal_desc');
      document.getElementById('playersLabel').textContent = t('modal_players');
      document.getElementById('maxPlayersLabel').textContent = t('max_players');
      document.getElementById('gameDesc').textContent = desc;

      document.querySelectorAll('[data-cat]').forEach((el) => {{
        el.textContent = t('cat_' + el.dataset.cat);
      }});

      document.querySelectorAll('[data-mode]').forEach((el) => {{
        el.textContent = t('mode_' + el.dataset.mode);
      }});

      const onlineLabel = document.getElementById('onlineLabel');
      if (onlineLabel) onlineLabel.textContent = t('modal_online');

      const noteTitle = document.getElementById('noteTitle');
      if (noteTitle) noteTitle.textContent = t('modal_experience');

      const playedBadge = document.getElementById('playedBadge');
      if (playedBadge) playedBadge.textContent = t('played_badge');

      const trendingBadge = document.getElementById('trendingBadge');
      if (trendingBadge) trendingBadge.textContent = t('trending_badge');

      const ratingLabel = document.getElementById('ratingLabel');
      if (ratingLabel) {{
        ratingLabel.textContent = isEn ? ratingLabel.dataset.labelEn : ratingLabel.dataset.labelIt;
      }}

      const relatedTitle = document.getElementById('relatedTitle');
      if (relatedTitle) relatedTitle.textContent = isEn ? 'Similar Games' : 'Giochi simili';

      const extLinksTitle = document.getElementById('extLinksTitle');
      if (extLinksTitle) extLinksTitle.textContent = isEn ? 'External Resources' : 'Risorse esterne';

      const storeTitle = document.getElementById('storeTitle');
      if (storeTitle) storeTitle.textContent = isEn ? 'Buy' : 'Acquista';

      document.querySelector('meta[name="description"]').content = metaDesc;
      document.querySelector('meta[property="og:description"]').content = metaDesc;
      document.querySelector('meta[name="twitter:description"]').content = metaDesc;
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      document.documentElement.lang = currentLang;
      if (typeof applyStaticTranslations === 'function') applyStaticTranslations();
      applyGameTranslations();
    }});

    window.addEventListener('langchange', applyGameTranslations);
  </script>
</body>
</html>
"""


def render_static_page_en(game: dict, all_games: list | None = None) -> str:
    """English version of the static game page for SEO on EN searches."""
    title = f"{game['title']}: {game['players']} players PC co-op game — Coophubs"
    image = game["image"] or f"{SITE_URL}/assets/og-image.jpg"

    # Richer English meta description
    modes_str = ", ".join(game.get("coopMode", []))
    desc_en = (
        f"Discover {game['title']}, a {game['players']} players PC co-op game. Modes: {modes_str}. Steam rating: {game['rating']}%. "
        + (game.get("description_en") or game["description"])
    )
    desc_en = desc_en[:160]

    rating_html = ""
    if game["rating"] > 0:
        rating_html = (
            '<div class="game-info-card">'
            f'<div class="game-info-value"><span class="rating-badge rating-{rating_tier(game["rating"])}" '
            f'style="font-size:1rem;padding:4px 12px">{rating_icon(game["rating"])} {game["rating"]}%</span></div>'
            f'<div class="game-info-label" id="ratingLabel" data-label-it="{esc(rating_label_it(game["rating"]))}" '
            f'data-label-en="{esc(rating_label_en(game["rating"]))}">{esc(rating_label_en(game["rating"]))}</div>'
            "</div>"
        )

    ccu_html = ""
    if game["ccu"] > 0:
        ccu_html = (
            '<div class="game-info-card">'
            f'<div class="game-info-value" style="color:var(--accent3)">{esc(format_ccu(game["ccu"]))}</div>'
            '<div class="game-info-label" id="onlineLabel">playing now</div>'
            "</div>"
        )

    note_html = ""
    if game["played"] and game["personalNote"]:
        note_html = (
            '<div class="game-section game-note">'
            '<div class="game-section-title" id="noteTitle">My Experience</div>'
            f"<p>{esc(game['personalNote'])}</p>"
            "</div>"
        )

    played_badge = ""
    if game["played"]:
        played_badge = '<span class="played-badge" id="playedBadge">✓ Played</span>'

    trending_badge = ""
    if game["trending"]:
        trending_badge = (
            '<span class="trending-badge" id="trendingBadge" '
            'style="position:static;display:inline-block;vertical-align:middle;margin-left:8px">'
            "🔥 Trending</span>"
        )

    crossplay_badge = ""
    if CROSSPLAY_UI_ENABLED and game["crossplay"]:
        crossplay_badge = (
            '<span class="tag" data-i18n="mode_crossplay" style="background:rgba(92,107,192,0.15);color:#9fa8da;'
            'border:1px solid rgba(92,107,192,0.25)">🔄 Crossplay</span>'
        )

    # ── JSON-LD VideoGame schema ──────────────────────────────────────────
    coop_modes = game.get("coopMode") or []
    play_modes = ["SinglePlayer"]
    if "online" in coop_modes:
        play_modes += ["CoOp", "MultiPlayer"]
    if "local" in coop_modes or "split" in coop_modes:
        if "CoOp" not in play_modes:
            play_modes.append("CoOp")

    players_str = game.get("players") or "1-4"
    players_parts = players_str.replace(" ", "").split("-")
    try:
        players_min = int(players_parts[0])
        players_max = int(players_parts[-1])
    except (ValueError, IndexError):
        players_min, players_max = 1, 4

    video_game_json = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": game["title"],
        "url": page_url_en(game),
        "description": desc_en,
        "image": image,
        "genre": game["categories"],
        "gamePlatform": "PC",
        "operatingSystem": "Windows",
        "applicationCategory": "Game",
        "numberOfPlayers": {
            "@type": "QuantitativeValue",
            "minValue": players_min,
            "maxValue": players_max,
        },
        "playMode": play_modes,
    }

    if game.get("releaseYear") and game["releaseYear"] > 0:
        video_game_json["datePublished"] = str(game["releaseYear"])

    if game.get("rating") and game["rating"] > 0:
        agg = {
            "@type": "AggregateRating",
            "ratingValue": game["rating"],
            "bestRating": 100,
            "worstRating": 0,
        }
        if game.get("totalReviews") and game["totalReviews"] > 0:
            agg["ratingCount"] = game["totalReviews"]
        video_game_json["aggregateRating"] = agg

    if game.get("steamUrl"):
        video_game_json["offers"] = {
            "@type": "Offer",
            "url": game["steamUrl"],
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
        }

    script_data = {
        "description": game["description"],
        "description_en": game.get("description_en") or game["description"],
    }

    hero_image_html = ""
    if game["image"]:
        hero_image_html = (
            f'<img class="game-hero-img" src="{esc(image)}" alt="{esc(game["title"])}" '
            "onerror=\"this.style.display='none'\">"
        )

    related_html = ""
    if all_games:
        related = find_related_games(game, all_games)
        related_html = render_related_games_en(related)

    return f"""<!DOCTYPE html>
<html lang="en" data-default-lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc_en)}">
  <meta name="theme-color" content="#7c6aff">
  <meta name="color-scheme" content="dark">
  <link rel="canonical" href="{esc(page_url_en(game))}">
  <link rel="alternate" hreflang="it" href="{esc(page_url(game))}">
  <link rel="alternate" hreflang="en" href="{esc(page_url_en(game))}">
  <link rel="alternate" hreflang="x-default" href="{esc(page_url(game))}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Coophubs">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc_en)}">
  <meta property="og:url" content="{esc(page_url_en(game))}">
  <meta property="og:image" content="{esc(image)}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(desc_en)}">
  <meta name="twitter:image" content="{esc(image)}">

  <link rel="icon" type="image/svg+xml" href="../../assets/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/icon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../../assets/icon-180.png">
  <link rel="stylesheet" href="../../assets/style.css?v={ASSET_VERSION}">
  <script type="application/ld+json">
  {json.dumps(video_game_json, ensure_ascii=False)}
  </script>
  <style>
    .game-page {{ max-width: 800px; margin: 0 auto; padding: 30px 20px 60px; position: relative; z-index: 1; }}
    .game-back {{ display: inline-flex; align-items: center; gap: 6px; color: var(--accent); text-decoration: none; font-weight: 600; margin-bottom: 24px; transition: color 0.25s; }}
    .game-back:hover {{ color: #a78bfa; }}
    .page-head .game-back {{ margin-bottom: 0; }}
    .game-hero-img {{ width: 100%; max-height: 360px; object-fit: cover; border-radius: var(--radius); margin-bottom: 24px; display: block; }}
    .game-title {{ font-size: clamp(1.6rem, 4vw, 2.4rem); font-weight: 800; letter-spacing: -1px; margin-bottom: 12px; }}
    .game-meta {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 20px; }}
    .game-section {{ margin-bottom: 24px; }}
    .game-section-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text2); margin-bottom: 8px; font-weight: 600; }}
    .game-desc {{ color: var(--text2); font-size: 1rem; line-height: 1.7; }}
    .game-note {{ background: rgba(124,106,255,0.08); border: 1px solid rgba(124,106,255,0.2); border-radius: var(--radius); padding: 16px; }}
    .game-note p {{ color: #b0b8e8; font-style: italic; line-height: 1.65; }}
    .game-actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 24px; }}
    .game-info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
    .game-info-card {{ background: var(--bg3); border: 1px solid var(--border); border-radius: 12px; padding: 14px; text-align: center; }}
    .game-info-value {{ font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: var(--accent); }}
    .game-info-label {{ font-size: 0.72rem; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
    .related-card {{ background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; transition: border-color 0.25s, transform 0.2s; overflow: hidden; }}
    .related-card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
    .ext-links {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .ext-link {{ display: inline-flex; align-items: center; gap: 4px; padding: 8px 14px; background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; color: var(--text2); text-decoration: none; font-size: 0.82rem; font-weight: 500; transition: border-color 0.25s, color 0.25s; }}
    .ext-link:hover {{ border-color: var(--accent); color: var(--accent); }}
  </style>
</head>
<body>
  <canvas id="bgCanvas" class="bg-canvas" aria-hidden="true"></canvas>

  <div class="game-page">
    <div class="page-head">
      <a href="../../" class="game-back" id="backLink">← Back to catalog</a>
      <div class="page-head-actions">
        <button class="btn-lang" id="langBtn" onclick="setLang(currentLang === 'it' ? 'en' : 'it')" aria-label="Change language" data-i18n-aria-label="btn_lang_aria">🇮🇹 IT</button>
      </div>
    </div>

    {hero_image_html}

    <h1 class="game-title">
      {esc(game["title"])}
      {played_badge}
      {trending_badge}
    </h1>

    <div class="game-meta">
      {render_tags(game)} {render_modes(game)} {crossplay_badge}
    </div>

    <div class="game-info-grid">
      <div class="game-info-card">
        <div class="game-info-value">{esc(game["players"])}</div>
        <div class="game-info-label" id="playersLabel">Players</div>
      </div>
      {rating_html}
      {ccu_html}
      <div class="game-info-card">
        <div class="game-info-value">{game["maxPlayers"] or "?"}</div>
        <div class="game-info-label" id="maxPlayersLabel">Max Players</div>
      </div>
    </div>

    <div class="game-section" style="margin-top:24px">
      <div class="game-section-title" id="descTitle">Description</div>
      <div class="game-desc" id="gameDesc">{esc(game.get("description_en") or game["description"])}</div>
    </div>

    {note_html}

    <div class="game-actions">
      {render_store_links(game)}
    </div>

    {render_external_links(game, lang="en")}

    {related_html}
  </div>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">Co-op Games Hub</div>
      <div class="footer-sub" id="footerSub" data-i18n="footer_sub">Coophubs is an independent project dedicated to discovering co-op games for PC.</div>
      <div class="footer-links">
        <a href="../../about.html" id="footerAbout" data-i18n="footer_about">About</a>
        <a href="../../contact.html" id="footerContact" data-i18n="footer_contact">Contact</a>
        <a href="../../free.html" id="footerFree" data-i18n="footer_free">Free Games</a>
        <a href="../../privacy.html" id="footerPrivacy" data-i18n="footer_privacy">Privacy Policy</a>
      </div>
      <div class="footer-support">
        <a href="https://ko-fi.com/coophubs" class="btn-kofi" target="_blank" rel="noopener noreferrer" data-i18n="footer_kofi">☕ Support the project</a>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-copy" data-i18n="footer_copy">&copy; {CURRENT_YEAR} — Data from Steam &amp; SteamSpy</div>
    </div>
  </footer>

  <script src="../../assets/i18n.js?v={ASSET_VERSION}" defer></script>
  <script src="../../assets/particles.js?v={ASSET_VERSION}" defer></script>
  <script>
    const GAME_DATA = {json_for_script(script_data)};

    function applyGameTranslations() {{
      const isEn = currentLang === 'en';
      const desc = isEn && GAME_DATA.description_en ? GAME_DATA.description_en : GAME_DATA.description;
      const metaDesc = desc.slice(0, 320);

      document.getElementById('backLink').textContent = t('page_back_catalog');
      document.getElementById('descTitle').textContent = t('modal_desc');
      document.getElementById('playersLabel').textContent = t('modal_players');
      document.getElementById('maxPlayersLabel').textContent = t('max_players');
      document.getElementById('gameDesc').textContent = desc;

      document.querySelectorAll('[data-cat]').forEach((el) => {{
        el.textContent = t('cat_' + el.dataset.cat);
      }});

      document.querySelectorAll('[data-mode]').forEach((el) => {{
        el.textContent = t('mode_' + el.dataset.mode);
      }});

      const onlineLabel = document.getElementById('onlineLabel');
      if (onlineLabel) onlineLabel.textContent = t('modal_online');

      const noteTitle = document.getElementById('noteTitle');
      if (noteTitle) noteTitle.textContent = t('modal_experience');

      const playedBadge = document.getElementById('playedBadge');
      if (playedBadge) playedBadge.textContent = t('played_badge');

      const trendingBadge = document.getElementById('trendingBadge');
      if (trendingBadge) trendingBadge.textContent = t('trending_badge');

      const ratingLabel = document.getElementById('ratingLabel');
      if (ratingLabel) {{
        ratingLabel.textContent = isEn ? ratingLabel.dataset.labelEn : ratingLabel.dataset.labelIt;
      }}

      const relatedTitle = document.getElementById('relatedTitle');
      if (relatedTitle) relatedTitle.textContent = isEn ? 'Similar Games' : 'Giochi simili';

      const extLinksTitle = document.getElementById('extLinksTitle');
      if (extLinksTitle) extLinksTitle.textContent = isEn ? 'External Resources' : 'Risorse esterne';

      const storeTitle = document.getElementById('storeTitle');
      if (storeTitle) storeTitle.textContent = isEn ? 'Buy' : 'Acquista';

      document.querySelector('meta[name="description"]').content = metaDesc;
      document.querySelector('meta[property="og:description"]').content = metaDesc;
      document.querySelector('meta[name="twitter:description"]').content = metaDesc;
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      document.documentElement.lang = currentLang;
      if (typeof applyStaticTranslations === 'function') applyStaticTranslations();
      applyGameTranslations();
    }});

    window.addEventListener('langchange', applyGameTranslations);
  </script>
</body>
</html>
"""


def write_pages(games):
    GAMES_DIR.mkdir(exist_ok=True)
    current_ids = {str(g["id"]) for g in games}
    written = skipped = removed = 0

    for game in games:
        out = GAMES_DIR / f"{game['id']}.html"
        new_content = render_static_page(game, all_games=games)
        if out.exists() and out.read_text(encoding="utf-8") == new_content:
            skipped += 1
        else:
            out.write_text(new_content, encoding="utf-8")
            written += 1

    # Rimuove pagine orfane (giochi eliminati dal catalogo)
    for existing in GAMES_DIR.glob("*.html"):
        if existing.stem not in current_ids:
            existing.unlink()
            removed += 1

    print(f"  📄 Pagine IT: {written} scritte, {skipped} invariate, {removed} rimosse")


def write_pages_en(games):
    GAMES_EN_DIR.mkdir(parents=True, exist_ok=True)
    current_ids = {str(g["id"]) for g in games}
    written = skipped = removed = 0

    for game in games:
        out = GAMES_EN_DIR / f"{game['id']}.html"
        new_content = render_static_page_en(game, all_games=games)
        if out.exists() and out.read_text(encoding="utf-8") == new_content:
            skipped += 1
        else:
            out.write_text(new_content, encoding="utf-8")
            written += 1

    # Rimuove pagine orfane EN
    for existing in GAMES_EN_DIR.glob("*.html"):
        if existing.stem not in current_ids:
            existing.unlink()
            removed += 1

    print(f"  📄 Pagine EN: {written} scritte, {skipped} invariate, {removed} rimosse")


def write_sitemap(games):
    """Write sitemap index + separate sitemap files for better Google indexing."""

    def url_entry(loc, priority, lastmod=TODAY, hreflangs=None):
        lines = [
            "  <url>\n",
            f"    <loc>{loc}</loc>\n",
            f"    <lastmod>{lastmod}</lastmod>\n",
            "    <changefreq>weekly</changefreq>\n",
            f"    <priority>{priority}</priority>\n",
            "  </url>\n",
        ]
        if hreflangs:
            for lang, href in hreflangs:
                lines.insert(
                    2,
                    f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{href}"/>\n',
                )
        return lines

    pages_main = [
        ("/", "1.0"),
        ("/about.html", "0.5"),
        ("/contact.html", "0.5"),
        ("/free.html", "0.6"),
    ]
    hubs = [
        ("/migliori-giochi-coop-2026.html", "/en/best-coop-games-2026.html"),
        ("/giochi-coop-local.html", "/en/local-coop-games.html"),
        ("/giochi-coop-2-giocatori.html", "/en/2-player-coop-games.html"),
        ("/giochi-coop-free.html", "/en/free-coop-games.html"),
        ("/giochi-coop-indie.html", "/en/indie-coop-games.html"),
    ]

    # sitemap-main.xml: static pages + hub pages (max ~20 URLs)
    main_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n',
    ]
    for path, priority in pages_main:
        main_lines.extend(url_entry(f"{SITE_URL}{path}", priority))
    for it_slug, en_slug in hubs:
        main_lines.extend(
            url_entry(
                f"{SITE_URL}{it_slug}",
                "0.8",
                hreflangs=[
                    ("it", f"{SITE_URL}{it_slug}"),
                    ("en", f"{SITE_URL}{en_slug}"),
                    ("x-default", f"{SITE_URL}{it_slug}"),
                ],
            )
        )
    main_lines.append("</urlset>\n")
    SITEMAP_MAIN.write_text("".join(main_lines), encoding="utf-8")

    # sitemap-hubs.xml: hub EN pages (separate for SEO clarity)
    hubs_en_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n',
    ]
    for it_slug, en_slug in hubs:
        hubs_en_lines.extend(
            url_entry(
                f"{SITE_URL}{en_slug}",
                "0.8",
                hreflangs=[
                    ("it", f"{SITE_URL}{it_slug}"),
                    ("en", f"{SITE_URL}{en_slug}"),
                    ("x-default", f"{SITE_URL}{it_slug}"),
                ],
            )
        )
    hubs_en_lines.append("</urlset>\n")
    SITEMAP_HUBS.write_text("".join(hubs_en_lines), encoding="utf-8")

    # Sitemap index
    index_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
        f"  <sitemap>\n    <loc>{SITE_URL}/sitemap-main.xml</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n",
        f"  <sitemap>\n    <loc>{SITE_URL}/sitemap-hubs.xml</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n",
    ]

    # Generate game sitemaps (max 500 URLs each)
    GAMES_PER_SITEMAP = 450
    for i in range(0, len(games), GAMES_PER_SITEMAP):
        batch = games[i : i + GAMES_PER_SITEMAP]
        sitemap_file = ROOT / f"sitemap-games-{i // GAMES_PER_SITEMAP + 1}.xml"
        game_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n',
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n',
        ]
        for game in batch:
            url = page_url(game)
            url_en = page_url_en(game)
            ccu = game.get("ccu") or 0
            priority = (
                "0.9"
                if game.get("trending") or ccu >= 10000
                else ("0.7" if ccu > 0 else "0.6")
            )
            game_lines.extend(
                url_entry(
                    url,
                    priority,
                    hreflangs=[("it", url), ("en", url_en), ("x-default", url)],
                )
            )
            game_lines.extend(
                url_entry(
                    url_en,
                    priority,
                    hreflangs=[("it", url), ("en", url_en), ("x-default", url)],
                )
            )
        game_lines.append("</urlset>\n")
        sitemap_file.write_text("".join(game_lines), encoding="utf-8")
        index_lines.append(
            f"  <sitemap>\n    <loc>{SITE_URL}/sitemap-games-{i // GAMES_PER_SITEMAP + 1}.xml</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n"
        )

    index_lines.append("</sitemapindex>\n")
    SITEMAP_INDEX.write_text("".join(index_lines), encoding="utf-8")

    # Update robots.txt
    robots = ROOT / "robots.txt"
    if robots.exists():
        content = robots.read_text(encoding="utf-8")
        if "Sitemap:" in content:
            content = content.replace(
                "Sitemap: https://coophubs.net/sitemap.xml",
                f"Sitemap: {SITE_URL}/sitemap.xml",
            )
        robots.write_text(content, encoding="utf-8")


def update_game_counters(count: int) -> None:
    """Keep the hardcoded game counters in index.html and i18n.js in sync with the real count."""
    import re as _re

    # Round down to nearest 100 for stable copy ("500+", not "534+")
    floored = (count // 100) * 100
    label = f"{floored}+"

    targets = [
        (
            ROOT / "index.html",
            [
                (r"Scopri oltre \d+ giochi", f"Scopri oltre {floored} giochi"),
                (
                    r"Oltre \d+ giochi cooperativi",
                    f"Oltre {floored} giochi cooperativi",
                ),
            ],
        ),
        (
            ROOT / "assets" / "i18n.js",
            [
                (r"Scopri oltre \d+ giochi", f"Scopri oltre {floored} giochi"),
                (r"Discover \d+\+ co-op games", f"Discover {label} co-op games"),
            ],
        ),
    ]

    for path, replacements in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for pattern, replacement in replacements:
            text = _re.sub(pattern, replacement, text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"Updated game counter to {floored} in {path.name}")


def main():
    games = load_games()
    artifact_path = catalog_data.write_catalog_artifact(games)
    public_export_path = catalog_data.write_public_catalog_export(games)
    write_pages(games)
    write_pages_en(games)
    write_sitemap(games)
    update_game_counters(len(games))
    print(f"Built {len(games)} static game pages in {GAMES_DIR}")
    print(f"Updated sitemap: {SITEMAP}")
    print(f"Wrote canonical catalog artifact: {artifact_path}")
    print(f"Wrote public catalog export: {public_export_path}")


if __name__ == "__main__":
    main()
