#!/usr/bin/env python3
"""
generate_hub_pages_en.py
========================
Genera le versioni EN delle 5 hub pages SEO.
Output: en/best-coop-games-2026.html, en/local-coop-games.html, etc.
Aggiorna anche hreflang IT e sitemap.xml.

Uso:
  python3 scripts/generate_hub_pages_en.py
"""
from __future__ import annotations
import re, sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
import catalog_data

ROOT   = catalog_data.ROOT
EN_DIR = ROOT / "en"
SITE   = "https://coophubs.net"
TODAY  = date.today().isoformat()
ASSET_VERSION = "20260327"

# ─── Hub page definitions ──────────────────────────────────────────────────────

HUBS = [
    {
        "it_file":    "migliori-giochi-coop-2026.html",
        "en_slug":    "best-coop-games-2026",
        "title":      "Best Co-op Games 2026 for PC | CoopHubs",
        "desc":       "The best cooperative games for PC in 2026: top-rated new releases and classics still actively played, selected for co-op quality.",
        "og_title":   "Best Co-op Games 2026 for PC",
        "og_desc":    "New releases and timeless classics: the must-play co-op games in 2026, selected for quality and real player activity.",
        "kicker":     "Curated Selection",
        "h1":         "Best Co-op Games 2026 for PC",
        "subtitle":   "New releases and timeless classics: the must-play co-op games in 2026, selected for quality and real player activity.",
        "body": [
            "Finding the right co-op game in 2026 isn't easy: Steam lists thousands of titles and top-rated classics often overshadow quality new releases.",
            "This list uses two distinct criteria. The first section covers games released from 2022 onwards with a high Steam rating — modern titles like Split Fiction, R.E.P.O., Baldur's Gate 3 and Schedule I, representing the best of co-op in the last three years. The second section includes only classics still actively played in 2026, measured by real concurrent players: Stardew Valley, Left 4 Dead 2, Terraria, Don't Starve Together — old but not forgotten.",
            "Each card shows game mode, player count and a link to the price comparison page.",
        ],
        "sections": [
            "New Releases — from 2022 to 2026",
            "Still Alive Classics — most played in 2026",
        ],
    },
    {
        "it_file":    "giochi-coop-local.html",
        "en_slug":    "local-coop-games",
        "title":      "Best Local Co-op Games for PC | CoopHubs",
        "desc":       "The best local co-op, couch and split screen games for PC in 2026 — play together with whoever is next to you.",
        "og_title":   "Best Local Co-op Games for PC",
        "og_desc":    "Play with who's next to you: the best local co-op, couch and split screen titles for PC in 2026.",
        "kicker":     "Couch &amp; Split Screen",
        "h1":         "Best Local Co-op Games for PC",
        "subtitle":   "Play with who's next to you: the best local co-op, couch and split screen titles for PC in 2026.",
        "body": [
            "Local co-op has a charm no internet connection can replicate: playing side by side, on the same screen or with controllers in hand — no ping, no disconnections, no explaining rules through chat.",
            "This list collects the best local co-op games on PC in 2026, selected for the quality of the shared gaming experience. You'll find split screen, shared screen and couch co-op titles — some designed for couples, others for groups of up to four players around the same TV or monitor.",
            "From co-op platformers like Rayman Legends to puzzle games like Unrailed!, from action games like Cuphead to survival games like Don't Starve Together, local co-op covers every genre. Each card shows the maximum number of players supported locally and the average Steam rating.",
        ],
        "sections": [],
    },
    {
        "it_file":    "giochi-coop-2-giocatori.html",
        "en_slug":    "2-player-coop-games",
        "title":      "Best 2-Player Co-op Games for PC | CoopHubs",
        "desc":       "The best co-op games for 2 players on PC in 2026: games designed for couples and friends, online or local.",
        "og_title":   "Best 2-Player Co-op Games for PC",
        "og_desc":    "Co-op games designed for two: online or local, perfect for couples and friends.",
        "kicker":     "Couple &amp; Duo",
        "h1":         "Best 2-Player Co-op Games for PC",
        "subtitle":   "Co-op games designed for two: online or local, perfect for couples and friends.",
        "body": [
            "Some co-op games are built exactly for two players — not as a compromise on group multiplayer, but as an experience designed around a pair.",
            "This list features the best 2-player co-op games on PC in 2026, selected from titles supporting a maximum of 2 players with a high Steam rating. From co-op platformers like It Takes Two and Cuphead — true genre masterpieces — to puzzlers like Portal 2, from roguelites like Roboquest to adventure games like We Were Here.",
            "Many of these titles support both online and local co-op: you can play with your partner on the couch or with a friend far away in the same session. The game mode is shown on each card so you know what to expect before you start.",
        ],
        "sections": [],
    },
    {
        "it_file":    "giochi-coop-free.html",
        "en_slug":    "free-coop-games",
        "title":      "Best Free Co-op Games for PC | CoopHubs",
        "desc":       "The best free-to-play cooperative games for PC in 2026 — play together without spending a penny.",
        "og_title":   "Best Free Co-op Games for PC",
        "og_desc":    "Co-op without spending anything: the best free cooperative games for PC in 2026.",
        "kicker":     "Free to Play",
        "h1":         "Best Free Co-op Games for PC",
        "subtitle":   "Co-op without spending anything: the best free cooperative games for PC in 2026.",
        "body": [
            "Playing together doesn't have to cost anything. Steam has dozens of free cooperative games — some pure free-to-play, others that went free after years of paid success.",
            "This list collects the best free co-op games for PC in 2026, ranked by quality according to Steam players. From tactical shooters like Rainbow Six Siege to cooperative battle royales, from card games like Legends of Runeterra to MMOs with group content.",
            "All titles in this list are downloadable and playable for free on PC, no initial purchase required. Some have cosmetic microtransactions or optional premium content, but the core co-op mode is accessible to everyone. The Steam rating reflects average player satisfaction — a good starting point to decide where to begin.",
        ],
        "sections": [],
    },
    {
        "it_file":    "giochi-coop-indie.html",
        "en_slug":    "indie-coop-games",
        "title":      "Best Indie Co-op Games for PC | CoopHubs",
        "desc":       "The best independent co-op games for PC in 2026: creativity, originality and dozens of hours to play together.",
        "og_title":   "Best Indie Co-op Games for PC",
        "og_desc":    "The best independent titles with co-op mode: creativity, originality and dozens of hours together.",
        "kicker":     "Indie Co-op",
        "h1":         "Best Indie Co-op Games for PC",
        "subtitle":   "The best independent titles with co-op mode: creativity, originality and dozens of hours together.",
        "body": [
            "Indie games have transformed the co-op landscape. While major publishers focus on live service and battle royale, independent developers keep experimenting: asymmetric mechanics, cooperative narratives, hybrid genres that wouldn't exist anywhere else.",
            "This list collects the best indie co-op games for PC in 2026, selected from independent titles with the highest Steam ratings. You'll find games like Stardew Valley — which redefined cooperative farm sims — Vampire Survivors, Deep Rock Galactic and dozens of other titles worth discovering.",
            "The indie co-op catalogue is vast and constantly growing: new titles release every week, many of them surprisingly high quality. This list updates regularly tracking Steam ratings, so you can always find something worthwhile without spending hours searching.",
        ],
        "sections": [],
    },
]

# ─── Load catalog ──────────────────────────────────────────────────────────────

def load_catalog() -> dict[int, dict]:
    games = catalog_data.load_games()
    return {g["id"]: g for g in games}

# ─── Parse IT hub page ─────────────────────────────────────────────────────────

_CARD_RE = re.compile(
    r'<a class="hub-card" href="games/(\d+)\.html">\s*'
    r'<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*'
    r'<div class="hub-card-body">\s*'
    r'<div class="hub-card-top">\s*'
    r'<h3 class="hub-card-title">([^<]+)</h3>\s*'
    r'<span class="hub-rating">([^<]+)</span>',
    re.DOTALL,
)
_TAGS_RE = re.compile(r'<div class="hub-card-tags">(.*?)</div>', re.DOTALL)
_SECTION_RE = re.compile(r'<h2 class="hub-section-heading"><span>([^<]+)</span></h2>')
_COUNT_RE   = re.compile(r'<strong>(\d+)</strong>')


def parse_cards_with_sections(html: str) -> list[dict]:
    """Return cards preserving section boundaries (section=None if no sections)."""
    # Split by section headers
    parts = re.split(r'(<h2 class="hub-section-heading">.*?</h2>)', html, flags=re.DOTALL)
    current_section = None
    cards = []
    for part in parts:
        sh = _SECTION_RE.search(part)
        if sh:
            current_section = sh.group(1)
            continue
        for m in _CARD_RE.finditer(part):
            game_id = int(m.group(1))
            img     = m.group(2)
            title   = m.group(4)
            rating  = m.group(5)
            # Find tags block after this match
            tags_m = _TAGS_RE.search(part, m.end())
            tags_html = tags_m.group(1) if tags_m else ""
            cards.append({
                "id":      game_id,
                "img":     img,
                "title":   title,
                "rating":  rating,
                "tags":    tags_html,
                "section": current_section,
            })
    return cards


def translate_tags(tags_html: str) -> str:
    """Translate IT-only tag words to EN."""
    return (tags_html
            .replace("Locale", "Local")
            .replace("giocatori", "players")
            .replace("(locale)", "(local)")
            .replace("Divano", "Couch"))


# ─── Render helpers ───────────────────────────────────────────────────────────

def render_card(card: dict, catalog: dict[int, dict]) -> str:
    game    = catalog.get(card["id"], {})
    desc_en = (game.get("description_en") or game.get("description") or "")
    desc_en = re.sub(r"\s+", " ", desc_en).strip()
    if len(desc_en) > 160:
        desc_en = desc_en[:157].rsplit(" ", 1)[0] + "…"
    tags = translate_tags(card["tags"])
    title_attr = card["title"].replace("'", "&#x27;").replace('"', "&quot;")
    return (
        f'    <a class="hub-card" href="../games/en/{card["id"]}.html">\n'
        f'      <img src="{card["img"]}" alt="{title_attr}" loading="lazy" width="460" height="215">\n'
        f'      <div class="hub-card-body">\n'
        f'        <div class="hub-card-top">\n'
        f'          <h3 class="hub-card-title">{card["title"]}</h3>\n'
        f'          <span class="hub-rating">{card["rating"]}</span>\n'
        f'        </div>\n'
        f'        <div class="hub-card-tags">{tags}</div>\n'
        f'        <p class="hub-card-desc">{desc_en}</p>\n'
        f'      </div>\n'
        f'    </a>\n'
    )


def render_cards_block(cards: list[dict], catalog: dict, hub: dict) -> str:
    sections = hub.get("sections", [])
    if not sections:
        # Single grid
        html = '    <div class="hub-grid" aria-label="Games">\n'
        for c in cards:
            html += render_card(c, catalog)
        html += "    </div>\n"
        return html

    # Multi-section
    html = ""
    current = None
    grid_open = False
    for c in cards:
        sec = c.get("section")
        if sec != current:
            if grid_open:
                html += "    </div>\n\n"
            current = sec
            # Find EN section name by index
            it_sections = [c2.get("section") for c2 in cards if c2.get("section")]
            it_unique = list(dict.fromkeys(it_sections))
            idx = it_unique.index(sec) if sec in it_unique else 0
            en_label = sections[idx] if idx < len(sections) else sec
            html += f'    <h2 class="hub-section-heading"><span>{en_label}</span></h2>\n'
            html += f'    <div class="hub-grid" aria-label="{en_label}">\n'
            grid_open = True
        html += render_card(c, catalog)
    if grid_open:
        html += "    </div>\n"
    return html


# ─── Page renderer ────────────────────────────────────────────────────────────

CSS_BLOCK = """  <style>
    .hub-page { max-width: 1200px; margin: 0 auto; padding: 30px 20px 80px; position: relative; z-index: 1; }
    .hub-intro { background: linear-gradient(135deg, rgba(124,106,255,0.08), rgba(124,106,255,0.03)); border: 1px solid rgba(124,106,255,0.15); border-radius: 20px; padding: 28px 32px; margin-bottom: 40px; }
    .hub-kicker { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--accent); margin-bottom: 10px; }
    .hub-h1 { font-size: clamp(1.7rem, 4vw, 2.6rem); font-weight: 800; letter-spacing: -1.5px; margin-bottom: 8px; line-height: 1.15; }
    .hub-subtitle { color: var(--text2); font-size: 1rem; line-height: 1.65; margin-bottom: 0; }
    .hub-body { margin-top: 18px; }
    .hub-body p { color: var(--text2); font-size: 0.96rem; line-height: 1.75; margin-bottom: 12px; }
    .hub-body p:last-child { margin-bottom: 0; }
    .hub-count { color: var(--text2); font-size: 0.85rem; margin-bottom: 20px; }
    .hub-count strong { color: var(--text); }
    .hub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
    .hub-card { display: flex; flex-direction: column; background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; text-decoration: none; color: inherit; transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s; }
    .hub-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(124,106,255,0.15); }
    .hub-card img { width: 100%; height: 160px; object-fit: cover; display: block; background: var(--bg3); }
    .hub-card-body { padding: 14px 16px 16px; display: flex; flex-direction: column; flex: 1; gap: 8px; }
    .hub-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
    .hub-card-title { font-size: 0.95rem; font-weight: 700; line-height: 1.3; flex: 1; }
    .hub-rating { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700; color: var(--accent); white-space: nowrap; padding: 2px 6px; background: rgba(124,106,255,0.1); border-radius: 6px; }
    .hub-card-tags { display: flex; flex-wrap: wrap; gap: 5px; }
    .hub-tag { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 7px; border-radius: 5px; background: var(--bg3); color: var(--text2); }
    .hub-tag-players { color: var(--accent2); background: rgba(236,72,153,0.08); }
    .hub-card-desc { font-size: 0.82rem; color: var(--text2); line-height: 1.55; flex: 1; }
    .hub-section-heading { font-size: 1rem; font-weight: 700; color: var(--text); margin: 36px 0 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
    .hub-section-heading span { color: var(--accent); }
    @media (max-width: 600px) {
      .hub-intro { padding: 20px; }
      .hub-grid { grid-template-columns: 1fr; }
    }
  </style>"""


def render_page(hub: dict, cards: list[dict], catalog: dict) -> str:
    en_url  = f"{SITE}/en/{hub['en_slug']}.html"
    it_url  = f"{SITE}/{hub['it_file']}"
    count   = len(cards)
    body_paras = "".join(f"      <p>{p}</p>\n" for p in hub["body"])
    cards_html  = render_cards_block(cards, catalog, hub)

    return f"""<!DOCTYPE html>
<html lang="en" data-default-lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{hub['title']}</title>
  <meta name="description" content="{hub['desc']}">
  <meta name="theme-color" content="#7c6aff">
  <meta name="color-scheme" content="dark">
  <link rel="canonical" href="{en_url}">
  <link rel="alternate" hreflang="en" href="{en_url}">
  <link rel="alternate" hreflang="it" href="{it_url}">
  <link rel="alternate" hreflang="x-default" href="{it_url}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Coophubs">
  <meta property="og:title" content="{hub['og_title']}">
  <meta property="og:description" content="{hub['og_desc']}">
  <meta property="og:url" content="{en_url}">
  <meta property="og:image" content="{SITE}/assets/og-image.jpg">
  <meta property="og:locale" content="en_US">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{hub['og_title']}">
  <meta name="twitter:description" content="{hub['og_desc']}">
  <meta name="twitter:image" content="{SITE}/assets/og-image.jpg">

  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/icon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../assets/icon-180.png">
  <link rel="stylesheet" href="../assets/style.css?v={ASSET_VERSION}">

  <script id="pageJsonLd" type="application/ld+json">
  {{"@context": "https://schema.org", "@type": "CollectionPage", "name": "{hub['og_title']}", "url": "{en_url}", "description": "{hub['desc']}", "inLanguage": "en"}}
  </script>
{CSS_BLOCK}
</head>
<body data-page="hub">
  <canvas id="bgCanvas" class="bg-canvas" aria-hidden="true"></canvas>

  <main class="hub-page">
    <div class="page-head">
      <a href="../" class="back-link">&larr; Back to catalog</a>
      <div class="page-head-actions">
        <button class="btn-lang" id="langBtn" onclick="setLang('it')" aria-label="Switch language">🇮🇹 IT</button>
      </div>
    </div>

    <section class="hub-intro" aria-label="Introduction">
      <div class="hub-kicker">{hub['kicker']}</div>
      <h1 class="hub-h1">{hub['h1']}</h1>
      <p class="hub-subtitle">{hub['subtitle']}</p>
      <div class="hub-body">
{body_paras}      </div>
    </section>

    <p class="hub-count"><strong>{count}</strong> selected games — updated 2026</p>

{cards_html}
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">Co-op Games Hub</div>
      <div class="footer-sub">Coophubs is an independent project dedicated to discovering co-op games for PC.</div>
      <div class="footer-links">
        <a href="../about.html">About</a>
        <a href="../contact.html">Contact</a>
        <a href="../free.html">Free games</a>
        <a href="../privacy.html">Privacy Policy</a>
      </div>
      <div class="footer-support">
        <a href="https://ko-fi.com/coophubs" class="btn-kofi" target="_blank" rel="noopener noreferrer">☕ Support the project</a>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-copy">&copy; 2026 — Data from Steam &amp; SteamSpy</div>
    </div>
  </footer>

  <script src="../assets/i18n.js?v={ASSET_VERSION}" defer></script>
  <script src="../assets/particles.js?v={ASSET_VERSION}" defer></script>
</body>
</html>
"""


# ─── Update IT page hreflang ──────────────────────────────────────────────────

def update_it_hreflang(it_file: Path, en_slug: str) -> None:
    """Add hreflang EN link to IT hub page if not already present."""
    html = it_file.read_text(encoding="utf-8")
    en_url = f"{SITE}/en/{en_slug}.html"

    if f'hreflang="en"' in html:
        print(f"  {it_file.name}: hreflang EN già presente, skip")
        return

    # Insert after the last existing hreflang/canonical line
    insert = f'  <link rel="alternate" hreflang="en" href="{en_url}">\n'
    # Find x-default line and insert after it
    html = re.sub(
        r'(<link rel="alternate" hreflang="x-default"[^>]*>)',
        r'\1\n' + insert.rstrip('\n'),
        html,
    )
    it_file.write_text(html, encoding="utf-8")
    print(f"  {it_file.name}: aggiunto hreflang EN")


# ─── Update sitemap ───────────────────────────────────────────────────────────

def update_sitemap(hubs: list[dict]) -> None:
    sitemap = ROOT / "sitemap.xml"
    content = sitemap.read_text(encoding="utf-8")

    for hub in hubs:
        it_url = f"{SITE}/{hub['it_file']}"
        en_url = f"{SITE}/en/{hub['en_slug']}.html"

        # Check if EN already in sitemap
        if en_url in content:
            print(f"  sitemap: {hub['en_slug']} già presente, skip")
            continue

        # Update IT entry: add EN hreflang
        it_block_pattern = (
            rf'(<loc>{re.escape(it_url)}</loc>\n)'
        )
        en_hreflang = (
            f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>\n'
        )
        # Add EN link after existing IT hreflang line
        content = re.sub(
            rf'(hreflang="it" href="{re.escape(it_url)}"/>)',
            rf'\1\n{en_hreflang.rstrip()}',
            content,
        )

        # Add EN entry after IT entry block
        en_entry = (
            f"  <url>\n"
            f"    <loc>{en_url}</loc>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"{en_url}\"/>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"it\" href=\"{it_url}\"/>\n"
            f"    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{it_url}\"/>\n"
            f"    <lastmod>{TODAY}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.8</priority>\n"
            f"  </url>\n"
        )
        # Insert the EN entry right after the IT block closing tag
        content = re.sub(
            rf'(  <url>\s*<loc>{re.escape(it_url)}</loc>.*?</url>)',
            rf'\1\n{en_entry.rstrip()}',
            content,
            flags=re.DOTALL,
        )
        print(f"  sitemap: aggiunto {hub['en_slug']}")

    sitemap.write_text(content, encoding="utf-8")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    EN_DIR.mkdir(exist_ok=True)
    catalog = load_catalog()
    print(f"Catalogo: {len(catalog)} giochi")

    for hub in HUBS:
        it_path = ROOT / hub["it_file"]
        if not it_path.exists():
            print(f"SKIP {hub['it_file']} — file non trovato")
            continue

        it_html = it_path.read_text(encoding="utf-8")
        cards = parse_cards_with_sections(it_html)
        print(f"\n{hub['it_file']}: {len(cards)} cards trovate")

        out_path = EN_DIR / f"{hub['en_slug']}.html"
        page_html = render_page(hub, cards, catalog)
        out_path.write_text(page_html, encoding="utf-8")
        print(f"  → {out_path.relative_to(ROOT)}")

        update_it_hreflang(it_path, hub["en_slug"])

    print("\nAggiornamento sitemap...")
    update_sitemap(HUBS)
    print("\n✅ Done!")
    print(f"   File generati in: {EN_DIR}/")
    print(f"   Aggiungi 'en/' al git add nel workflow CI se necessario")


if __name__ == "__main__":
    main()
