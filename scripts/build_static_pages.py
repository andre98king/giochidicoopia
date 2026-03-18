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
SITEMAP = ROOT / "sitemap.xml"
SITE_URL = "https://coophubs.net"
TODAY = datetime.date.today().isoformat()
CURRENT_YEAR = datetime.date.today().year
ASSET_VERSION = "20260318-gogfix"
CROSSPLAY_UI_ENABLED = True


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


def json_for_script(value) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


# Affiliate config — inserisci i tuoi ID dopo la registrazione
# Epic: epicgames.com/affiliate  → AFFILIATE_EPIC = 'TUOCODICE'
# GOG:  gog.com/partner          → AFFILIATE_GOG  = '12345'
AFFILIATE_EPIC = ""
AFFILIATE_GOG  = ""
# Attivi: link di ricerca per gioco (Instant Gaming + GameBillet)
AFFILIATE_IG = "gamer-ddc4a8"
AFFILIATE_GB = "fb308ca0-647e-4ce7-9e80-74c2c591eac1"


def add_utm(url: str, campaign: str = "gamepage") -> str:
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    result = url + sep + f"utm_source=coophubs&utm_medium=referral&utm_campaign={campaign}"
    if AFFILIATE_EPIC and "epicgames.com" in url:
        result += f"&creator={AFFILIATE_EPIC}"
    if AFFILIATE_GOG and "gog.com" in url:
        result += f"&pp={AFFILIATE_GOG}"
    return result


def render_store_links(game: dict) -> str:
    from urllib.parse import quote
    links = []
    if game["steamUrl"]:
        links.append(
            f'<a class="btn-primary" href="{esc(add_utm(game["steamUrl"]))}" target="_blank" '
            'rel="noopener noreferrer">Steam ↗</a>'
        )
    if game["epicUrl"]:
        links.append(
            f'<a class="btn-primary btn-epic-lg" href="{esc(add_utm(game["epicUrl"]))}" target="_blank" '
            'rel="noopener noreferrer">Epic Games ↗</a>'
        )
    if game["itchUrl"]:
        links.append(
            f'<a class="btn-store btn-itch" href="{esc(add_utm(game["itchUrl"]))}" target="_blank" '
            'rel="noopener noreferrer" style="padding:10px 20px;font-size:0.9rem">itch.io ↗</a>'
        )
    # Prezzi alternativi — bottoni grandi con sconto IG se disponibile
    if game["steamUrl"] and (AFFILIATE_IG or AFFILIATE_GB):
        q = quote(game["title"])
        btns = []
        if AFFILIATE_IG:
            ig_url = game.get("igUrl") or f"https://www.instant-gaming.com/en/search/?query={q}&igr={AFFILIATE_IG}"
            ig_discount = game.get("igDiscount") or 0
            disc_badge = f'<span class="affiliate-discount">-{ig_discount}%</span>' if ig_discount > 0 else ""
            btns.append(
                f'<a class="btn-affiliate btn-ig" href="{esc(ig_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">Instant Gaming</span>{disc_badge}</a>'
            )
        if AFFILIATE_GB:
            gb_url = game.get("gbUrl") or f"https://www.gamebillet.com/search?q={q}&affiliate={AFFILIATE_GB}"
            gb_discount = game.get("gbDiscount") or 0
            gb_badge = f'<span class="affiliate-discount">-{gb_discount}%</span>' if gb_discount > 0 else ""
            btns.append(
                f'<a class="btn-affiliate btn-gb" href="{esc(gb_url)}" '
                f'target="_blank" rel="noopener noreferrer sponsored">'
                f'<span class="affiliate-store">GameBillet</span>{gb_badge}</a>'
            )
        links.append(
            '<div class="affiliate-section"><div class="affiliate-title">💸 Prezzi alternativi</div>'
            '<div class="affiliate-btns">' + "".join(btns) + "</div></div>"
        )
    return "".join(links)


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


def render_static_page(game: dict) -> str:
    title = f"{game['title']} — Coophubs"
    image = game["image"] or f"{SITE_URL}/assets/og-image.jpg"
    description_it = game["description"][:320]

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

    video_game_json = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": game["title"],
        "url": page_url(game),
        "description": game["description"],
        "image": image,
        "genre": game["categories"],
        "gamePlatform": "PC",
        "numberOfPlayers": game["players"],
    }

    script_data = {
        "description": game["description"],
        "description_en": game["description_en"],
    }

    hero_image_html = ""
    if game["image"]:
        hero_image_html = (
            f'<img class="game-hero-img" src="{esc(image)}" alt="{esc(game["title"])}" '
            'onerror="this.style.display=\'none\'">'
        )

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
  <link rel="alternate" hreflang="en" href="{esc(page_url(game))}">
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

  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎮</text></svg>">
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
  </div>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">Co-op Games Hub</div>
      <div class="footer-sub" id="footerSub">Coophubs è un progetto indipendente dedicato alla scoperta di giochi cooperativi per PC.</div>
      <div class="footer-links">
        <a href="../about.html" id="footerAbout">Sul progetto</a>
        <a href="../contact.html" id="footerContact">Contatti</a>
        <a href="../free.html" id="footerFree">Giochi gratis</a>
        <a href="../privacy.html" id="footerPrivacy">Privacy Policy</a>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-copy">&copy; {CURRENT_YEAR} — Dati da Steam &amp; SteamSpy</div>
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
    for existing in GAMES_DIR.glob("*.html"):
        existing.unlink()
    for game in games:
        out = GAMES_DIR / f"{game['id']}.html"
        out.write_text(render_static_page(game), encoding="utf-8")


def write_sitemap(games):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
        "  <url>\n",
        f"    <loc>{SITE_URL}/</loc>\n",
        f"    <lastmod>{TODAY}</lastmod>\n",
        "    <changefreq>weekly</changefreq>\n",
        "    <priority>1.0</priority>\n",
        "  </url>\n",
        "  <url>\n",
        f"    <loc>{SITE_URL}/about.html</loc>\n",
        f"    <lastmod>{TODAY}</lastmod>\n",
        "    <changefreq>monthly</changefreq>\n",
        "    <priority>0.5</priority>\n",
        "  </url>\n",
        "  <url>\n",
        f"    <loc>{SITE_URL}/contact.html</loc>\n",
        f"    <lastmod>{TODAY}</lastmod>\n",
        "    <changefreq>monthly</changefreq>\n",
        "    <priority>0.5</priority>\n",
        "  </url>\n",
        "  <url>\n",
        f"    <loc>{SITE_URL}/free.html</loc>\n",
        f"    <lastmod>{TODAY}</lastmod>\n",
        "    <changefreq>daily</changefreq>\n",
        "    <priority>0.6</priority>\n",
        "  </url>\n",
    ]
    for game in games:
        lines.extend(
            [
                "  <url>\n",
                f"    <loc>{page_url(game)}</loc>\n",
                f"    <lastmod>{TODAY}</lastmod>\n",
                "    <changefreq>weekly</changefreq>\n",
                "    <priority>0.7</priority>\n",
                "  </url>\n",
            ]
        )
    lines.append("</urlset>\n")
    SITEMAP.write_text("".join(lines), encoding="utf-8")


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
                (r"Oltre \d+ giochi cooperativi", f"Oltre {floored} giochi cooperativi"),
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
    write_sitemap(games)
    update_game_counters(len(games))
    print(f"Built {len(games)} static game pages in {GAMES_DIR}")
    print(f"Updated sitemap: {SITEMAP}")
    print(f"Wrote canonical catalog artifact: {artifact_path}")
    print(f"Wrote public catalog export: {public_export_path}")


if __name__ == "__main__":
    main()
