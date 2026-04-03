#!/usr/bin/env python3
"""
Build static game pages and sitemap from games.js.

This keeps the project fully static while generating crawler-friendly
game pages for GitHub Pages.
"""

from __future__ import annotations

import datetime
import gzip
import html
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from html_fragments import (
    HTML_INLINE_STYLES,
    HTML_HEAD_IT,
    HTML_HEAD_EN,
    HTML_FOOTER_IT,
    HTML_FOOTER_EN,
    HTML_SCRIPTS_IT,
    HTML_SCRIPTS_EN,
    SCRIPT_GAME_TRANSLATIONS,
    HTML_RELATED_CARD,
    HTML_RELATED_CARD_IMG,
    HTML_RELATED_SECTION,
)

import catalog_data

from seo_content_generator import generate_game_description, generate_json_ld


def safe_template(template: str, **kwargs: str) -> str:
    """Substitute {name} placeholders only; literal CSS/JS braces are left untouched."""
    _pattern = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
    return _pattern.sub(lambda m: str(kwargs.get(m.group(1), m.group(0))), template)


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


def truncate_meta_desc(text: str, max_len: int = 155) -> str:
    """Tronca description meta tag con pulizia HTML e troncamento su word boundary."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>|&[a-z]+;", " ", text).strip()
    if len(clean) <= max_len:
        return clean.replace("'", "&#x27;")
    cut = clean[:max_len].rsplit(" ", 1)[0].rstrip(" .,;")
    return (cut + "…").replace("'", "&#x27;")


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
    # Preferisci catalog.public.v1.json (già filtrato dalla curation gate)
    # e mergia con games.js per mantenere tutti i campi originali
    public_catalog = ROOT / "data" / "catalog.public.v1.json"
    filtered_ids = set()

    if public_catalog.exists():
        try:
            with open(public_catalog, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "games" in data:
                filtered_ids = {g["id"] for g in data["games"]}
                filtered_games = {g["id"]: g for g in data["games"]}
            elif isinstance(data, list):
                filtered_ids = {g["id"] for g in data}
                filtered_games = {g["id"]: g for g in data}
        except Exception:
            pass

    # Carica games.js originale e filtra
    all_games = catalog_data.load_games()
    if filtered_ids:
        return [g for g in all_games if g["id"] in filtered_ids]
    return all_games


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


def build_related_card(game_dict: dict, lang: str = "it") -> str:
    """Build a single related-game card using .replace() (no .format() - CSS braces)."""
    if not game_dict:
        return ""

    img_html = ""
    img_src = game_dict.get("image") or ""
    if img_src:
        img_html = HTML_RELATED_CARD_IMG.replace(
            "PLACEHOLDER_IMG_SRC", esc(img_src)
        ).replace("PLACEHOLDER_GAME_TITLE", esc(game_dict.get("title", "")))

    gid = str(game_dict.get("id", ""))
    path = f"/games/en/{gid}.html" if lang == "en" else f"/games/{gid}.html"
    card = (
        HTML_RELATED_CARD.replace("PLACEHOLDER_GAME_PATH", path)
        .replace("PLACEHOLDER_IMG_HTML", img_html)
        .replace("PLACEHOLDER_GAME_TITLE", esc(game_dict.get("title", "")))
    )

    return card


def render_related_games(related: list) -> str:
    if not related:
        return ""
    cards = "".join(build_related_card(g) for g in related)
    return HTML_RELATED_SECTION.replace("{section_title}", "Giochi simili").replace(
        "{cards}", cards
    )


def render_related_games_en(related: list) -> str:
    if not related:
        return ""
    cards = "".join(build_related_card(g, lang="en") for g in related)
    return HTML_RELATED_SECTION.replace("{section_title}", "Similar Games").replace(
        "{cards}", cards
    )


def render_internal_links(game: dict, catalog: list, limit: int = 3) -> str:
    """Generate simple text links for internal SEO linking (max 3 links)."""
    if not catalog:
        return ""
    game_cats = set(c.lower() for c in (game.get("categories") or []))
    scored = []
    for g in catalog:
        if g.get("id") == game.get("id"):
            continue
        g_cats = set(c.lower() for c in (g.get("categories") or []))
        overlap = len(game_cats & g_cats)
        if overlap > 0:
            scored.append((overlap, g))
    scored.sort(key=lambda x: (-x[0], int(x[1].get("id", 0))))
    related = scored[:limit]

    items = []
    for _, g in related:
        title = g.get("title", "Game").replace('"', "&quot;")
        gid = g.get("id", "")
        items.append(
            f'<li><a href="/games/{gid}.html" title="{title}">{title}</a></li>'
        )

    if not items:
        return ""
    return f'<section class="related-games" aria-label="Giochi correlati"><h2>Giochi simili</h2><ul>{"".join(items)}</ul></section>'


def render_internal_links_en(game: dict, catalog: list, limit: int = 3) -> str:
    """Generate simple text links for internal SEO linking (EN version)."""
    if not catalog:
        return ""
    game_cats = set(c.lower() for c in (game.get("categories") or []))
    scored = []
    for g in catalog:
        if g.get("id") == game.get("id"):
            continue
        g_cats = set(c.lower() for c in (g.get("categories") or []))
        overlap = len(game_cats & g_cats)
        if overlap > 0:
            scored.append((overlap, g))
    scored.sort(key=lambda x: (-x[0], int(x[1].get("id", 0))))
    related = scored[:limit]

    items = []
    for _, g in related:
        title = g.get("title", "Game").replace('"', "&quot;")
        gid = g.get("id", "")
        items.append(
            f'<li><a href="/games/en/{gid}.html" title="{title}">{title}</a></li>'
        )

    if not items:
        return ""
    return f'<section class="related-games" aria-label="Related Games"><h2>Similar Games</h2><ul>{"".join(items)}</ul></section>'


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
    labels = {"online": "🌐 Online", "local": "🛋️ Local", "sofa": "🖥️ Split"}
    return "".join(
        '<span class="tag" data-mode="'
        f'{esc(mode)}" style="background:rgba(0,137,123,0.15);color:#80cbc4;'
        f'border:1px solid rgba(0,137,123,0.25)">{esc(labels.get(mode, mode))}</span>'
        for mode in game["coopMode"]
    )


def render_static_page(game: dict, all_games: list | None = None) -> str:
    coop_str = ", ".join(game.get("coopMode", ["Co-op"]))[:20]
    raw_title = (
        f"{game['title']} ({coop_str} · {game.get('players', '?')}P) | GiochiDiCoop"
    )
    seo_title = raw_title[:57] + "…" if len(raw_title) > 60 else raw_title
    image = game["image"] or f"{SITE_URL}/assets/og-image.jpg"

    raw_desc = game.get("description", "Gioco cooperativo per PC e console.")
    first_part = raw_desc.split(".")[0].strip()[:80]
    seo_desc_raw = f"{first_part}. Scopri modalità {coop_str} e alternative simili."
    seo_desc = truncate_meta_desc(seo_desc_raw)

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

    # ── JSON-LD VideoGame schema + thin-content expander ─────────────────
    jsonld_payload = generate_json_ld(game, page_url(game), lang="it")
    expanded_desc_html = generate_game_description(game, lang="it")

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

    internal_links_html = ""
    if all_games:
        internal_links_html = render_internal_links(game, all_games, limit=3)

    css_block = HTML_INLINE_STYLES
    head_block = safe_template(
        HTML_HEAD_IT,
        title=esc(seo_title),
        description=esc(seo_desc),
        it_url=esc(page_url(game)),
        en_url=esc(page_url_en(game)),
        image=esc(image),
        asset_version=ASSET_VERSION,
        jsonld=jsonld_payload,
    )
    footer_block = safe_template(HTML_FOOTER_IT, current_year=str(CURRENT_YEAR))
    scripts_block = safe_template(HTML_SCRIPTS_IT, asset_version=ASSET_VERSION)
    script_translations = SCRIPT_GAME_TRANSLATIONS.format(
        game_data_json=json_for_script(script_data)
    )

    return f"""{head_block}
{css_block}
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

    {expanded_desc_html}

    <div class="game-actions">
      {render_store_links(game)}
    </div>

    {render_external_links(game)}

    {related_html}

    {internal_links_html}
  </div>

{footer_block}

{scripts_block}
{script_translations}
</body>
</html>
"""


def render_static_page_en(game: dict, all_games: list | None = None) -> str:
    """English version of the static game page for SEO on EN searches."""
    coop_str = ", ".join(game.get("coopMode", ["Co-op"]))[:20]
    raw_title = (
        f"{game['title']} ({coop_str} · {game.get('players', '?')}P) | GiochiDiCoop"
    )
    seo_title = raw_title[:57] + "…" if len(raw_title) > 60 else raw_title
    image = game["image"] or f"{SITE_URL}/assets/og-image.jpg"

    raw_desc = game.get("description_en") or game.get(
        "description", "Co-op game for PC and console."
    )
    first_part = raw_desc.split(".")[0].strip()[:80]
    seo_desc_raw = f"{first_part}. Discover {coop_str} modes and similar alternatives."
    seo_desc = truncate_meta_desc(seo_desc_raw)

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

    # ── JSON-LD VideoGame schema + thin-content expander ─────────────────
    jsonld_payload = generate_json_ld(game, page_url_en(game), lang="en")
    expanded_desc_html = generate_game_description(game, lang="en")

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

    internal_links_html = ""
    if all_games:
        internal_links_html = render_internal_links_en(game, all_games, limit=3)

    css_block = HTML_INLINE_STYLES
    head_block = safe_template(
        HTML_HEAD_EN,
        title=esc(seo_title),
        description=esc(seo_desc),
        it_url=esc(page_url(game)),
        en_url=esc(page_url_en(game)),
        image=esc(image),
        asset_version=ASSET_VERSION,
        jsonld=jsonld_payload,
    )
    footer_block = safe_template(HTML_FOOTER_EN, current_year=str(CURRENT_YEAR))
    scripts_block = safe_template(HTML_SCRIPTS_EN, asset_version=ASSET_VERSION)
    script_translations = SCRIPT_GAME_TRANSLATIONS.format(
        game_data_json=json_for_script(script_data)
    )

    return f"""{head_block}
{css_block}
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

    {expanded_desc_html}

    <div class="game-actions">
      {render_store_links(game)}
    </div>

    {render_external_links(game, lang="en")}

    {related_html}

    {internal_links_html}
  </div>

{footer_block}

{scripts_block}
{script_translations}
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


def compress_assets(build_dir: str = "dist/") -> None:
    """Genera .br e .gz per HTML/CSS/JS/JSON accanto agli originali (idempotente)."""
    try:
        import brotli as _brotli
        has_brotli = True
    except ImportError:
        try:
            import brotlicffi as _brotli
            has_brotli = True
        except ImportError:
            has_brotli = False
            print("WARNING: brotli/brotlicffi non disponibile — .br saltato (pip install brotli)")

    build_path = Path(build_dir)
    if not build_path.exists():
        print(f"compress_assets: {build_dir} non esiste, skip.")
        return

    files = [
        f for ext in ("*.html", "*.css", "*.js", "*.json")
        for f in build_path.rglob(ext)
        if not f.suffix.endswith((".br", ".gz"))
    ]

    br_count = gz_count = unchanged = 0
    for src in files:
        data = src.read_bytes()
        if has_brotli:
            br_path = src.with_suffix(src.suffix + ".br")
            new_br = _brotli.compress(data)
            if not br_path.exists() or br_path.read_bytes() != new_br:
                br_path.write_bytes(new_br)
                br_count += 1
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9) as gz_f:
            gz_f.write(data)
        new_gz = buf.getvalue()
        gz_path = src.with_suffix(src.suffix + ".gz")
        if not gz_path.exists() or gz_path.read_bytes() != new_gz:
            gz_path.write_bytes(new_gz)
            gz_count += 1
        else:
            unchanged += 1

    print(f"compress_assets: {gz_count} .gz, {br_count} .br scritti ({unchanged} invariati) — dir={build_dir}")


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
    compress_assets(str(ROOT))
