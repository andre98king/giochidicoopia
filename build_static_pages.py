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
ASSET_VERSION = "20260314-cachefix1"
# Crossplay data is still collected internally, but the UI stays hidden until the source is trustworthy.
CROSSPLAY_UI_ENABLED = False


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


def render_store_links(game: dict) -> str:
    links = []
    if game["steamUrl"]:
        links.append(
            f'<a class="btn-primary" href="{esc(game["steamUrl"])}" target="_blank" '
            'rel="noopener noreferrer">Steam ↗</a>'
        )
    if game["epicUrl"]:
        links.append(
            f'<a class="btn-primary btn-epic-lg" href="{esc(game["epicUrl"])}" target="_blank" '
            'rel="noopener noreferrer">Epic Games ↗</a>'
        )
    if game["itchUrl"]:
        links.append(
            f'<a class="btn-store btn-itch" href="{esc(game["itchUrl"])}" target="_blank" '
            'rel="noopener noreferrer" style="padding:10px 20px;font-size:0.9rem">itch.io ↗</a>'
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
    image = game["image"] or f"{SITE_URL}/og-image.png"
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
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@600&display=swap">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
  <link rel="stylesheet" href="../style.css?v={ASSET_VERSION}">
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

  <script src="../i18n.js?v={ASSET_VERSION}" defer></script>
  <script src="../particles.js?v={ASSET_VERSION}" defer></script>
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


def main():
    games = load_games()
    artifact_path = catalog_data.write_catalog_artifact(games)
    public_export_path = catalog_data.write_public_catalog_export(games)
    write_pages(games)
    write_sitemap(games)
    print(f"Built {len(games)} static game pages in {GAMES_DIR}")
    print(f"Updated sitemap: {SITEMAP}")
    print(f"Wrote canonical catalog artifact: {artifact_path}")
    print(f"Wrote public catalog export: {public_export_path}")


if __name__ == "__main__":
    main()
