"""
html_fragments.py — Static HTML string constants extracted from build_static_pages.py.

Templates use {placeholder} syntax for dynamic values; callers can substitute with
str.format_map() or explicit .format(**kwargs).

IMPORTANT — brace-escaping rules:
  • HTML_INLINE_STYLES and HTML_RELATED_CARD contain CSS/JS literal { } braces.
    These constants must NOT be used with .format(); embed them directly in the
    output string or concatenate before/after the formatted head/footer strings.
  • HTML_HEAD_IT, HTML_HEAD_EN, HTML_FOOTER_IT, HTML_FOOTER_EN, HTML_SCRIPTS_IT,
    HTML_SCRIPTS_EN contain no CSS/JS braces and are safe for .format_map().
  • SCRIPT_GAME_TRANSLATIONS contains JS braces escaped as {{ / }}; use .format()
    with the single placeholder {game_data_json}.

Placeholder reference
─────────────────────
  {title}          HTML-escaped page title
  {description}    HTML-escaped meta description (≤160 chars)
  {canonical_url}  Canonical URL for this page
  {it_url}         URL of the Italian version (games/<id>.html)
  {en_url}         URL of the English version (games/en/<id>.html)
  {image}          OG / Twitter preview image URL
  {jsonld}         Serialised JSON-LD payload (no surrounding <script> tags)
  {asset_version}  Cache-busting version string, e.g. "20260327"
  {current_year}   Four-digit year, e.g. 2026
  {game_data_json} JSON-serialised GAME_DATA object for the inline page script
  {game_id}        Numeric game ID used to build href links
  {img_html}       Optional <img> tag for a related-game card (empty string = no image)
  {game_title}     HTML-escaped game title used inside a card
  {cards}          Pre-rendered HTML for all related-game cards (concatenated)
  {section_title}  Section heading: "Giochi simili" or "Similar Games"
"""

# ══════════════════════════════════════════════════════════════════════════════
# 1. HTML_INLINE_STYLES
#    The <style> block embedded in every game page <head>.
#    Identical between IT and EN pages — no placeholders.
#    Do NOT call .format() on this constant; braces are literal CSS.
# ══════════════════════════════════════════════════════════════════════════════

HTML_INLINE_STYLES = """\
  <style>
    .game-page { max-width: 800px; margin: 0 auto; padding: 30px 20px 60px; position: relative; z-index: 1; }
    .game-back { display: inline-flex; align-items: center; gap: 6px; color: var(--accent); text-decoration: none; font-weight: 600; margin-bottom: 24px; transition: color 0.25s; }
    .game-back:hover { color: #a78bfa; }
    .page-head .game-back { margin-bottom: 0; }
    .game-hero-img { width: 100%; max-height: 360px; object-fit: cover; border-radius: var(--radius); margin-bottom: 24px; display: block; }
    .game-title { font-size: clamp(1.6rem, 4vw, 2.4rem); font-weight: 800; letter-spacing: -1px; margin-bottom: 12px; }
    .game-meta { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 20px; }
    .game-section { margin-bottom: 24px; }
    .game-section-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text2); margin-bottom: 8px; font-weight: 600; }
    .game-desc { color: var(--text2); font-size: 1rem; line-height: 1.7; }
    .game-note { background: rgba(124,106,255,0.08); border: 1px solid rgba(124,106,255,0.2); border-radius: var(--radius); padding: 16px; }
    .game-note p { color: #b0b8e8; font-style: italic; line-height: 1.65; }
    .game-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 24px; }
    .game-info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
    .game-info-card { background: var(--bg3); border: 1px solid var(--border); border-radius: 12px; padding: 14px; text-align: center; }
    .game-info-value { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: var(--accent); }
    .game-info-label { font-size: 0.72rem; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
    .related-card { background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; transition: border-color 0.25s, transform 0.2s; overflow: hidden; }
    .related-card:hover { border-color: var(--accent); transform: translateY(-2px); }
    .ext-links { display: flex; gap: 10px; flex-wrap: wrap; }
    .ext-link { display: inline-flex; align-items: center; gap: 4px; padding: 8px 14px; background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; color: var(--text2); text-decoration: none; font-size: 0.82rem; font-weight: 500; transition: border-color 0.25s, color 0.25s; }
    .ext-link:hover { border-color: var(--accent); color: var(--accent); }
  </style>"""


# ══════════════════════════════════════════════════════════════════════════════
# 2. HTML_HEAD_IT / HTML_HEAD_EN
#    Complete <head> block (DOCTYPE → </head>) excluding the <style> block.
#    Append HTML_INLINE_STYLES + "\n</head>" when assembling the full page.
#
#    Differences between IT and EN:
#      • <html lang="...">: "it" vs "en" (EN also adds data-default-lang="en")
#      • <link rel="canonical">: points to IT URL vs EN URL
#      • og:url: IT URL vs EN URL
#      • Asset path prefix: "../assets/" vs "../../assets/"
# ══════════════════════════════════════════════════════════════════════════════

HTML_HEAD_IT = """\
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#7c6aff">
  <meta name="color-scheme" content="dark">
  <link rel="canonical" href="{it_url}">
  <link rel="alternate" hreflang="it" href="{it_url}">
  <link rel="alternate" hreflang="en" href="{en_url}">
  <link rel="alternate" hreflang="x-default" href="{it_url}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Coophubs">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{it_url}">
  <meta property="og:image" content="{image}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{image}">

  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/icon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../assets/icon-180.png">
  <link rel="stylesheet" href="../assets/style.css?v={asset_version}">
  <script type="application/ld+json">
  {jsonld}
  </script>"""

HTML_HEAD_EN = """\
<!DOCTYPE html>
<html lang="en" data-default-lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#7c6aff">
  <meta name="color-scheme" content="dark">
  <link rel="canonical" href="{en_url}">
  <link rel="alternate" hreflang="it" href="{it_url}">
  <link rel="alternate" hreflang="en" href="{en_url}">
  <link rel="alternate" hreflang="x-default" href="{it_url}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Coophubs">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{en_url}">
  <meta property="og:image" content="{image}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{image}">

  <link rel="icon" type="image/svg+xml" href="../../assets/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="../../assets/icon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../../assets/icon-180.png">
  <link rel="stylesheet" href="../../assets/style.css?v={asset_version}">
  <script type="application/ld+json">
  {jsonld}
  </script>"""


# ══════════════════════════════════════════════════════════════════════════════
# 3. HTML_FOOTER_IT / HTML_FOOTER_EN
#    The <footer> element only. Script tags are in HTML_SCRIPTS_IT/EN below.
#
#    Differences IT vs EN:
#      • Link hrefs use "../" (IT) vs "../../" (EN) prefix
#      • Default visible text is Italian vs English
#        (both versions keep data-i18n attributes for JS runtime switching)
#    Placeholder: {current_year}
# ══════════════════════════════════════════════════════════════════════════════

HTML_FOOTER_IT = """\
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
      <div class="footer-copy" data-i18n="footer_copy">&copy; {current_year} — Dati da Steam &amp; SteamSpy</div>
    </div>
  </footer>"""

HTML_FOOTER_EN = """\
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
      <div class="footer-copy" data-i18n="footer_copy">&copy; {current_year} — Data from Steam &amp; SteamSpy</div>
    </div>
  </footer>"""


# ══════════════════════════════════════════════════════════════════════════════
# 4. HTML_SCRIPTS_IT / HTML_SCRIPTS_EN
#    The two deferred <script src> tags that load i18n and particles.
#    Placeholder: {asset_version}
#    These come immediately before the inline <script> block (SCRIPT_GAME_TRANSLATIONS).
# ══════════════════════════════════════════════════════════════════════════════

HTML_SCRIPTS_IT = """\
  <script src="../assets/i18n.js?v={asset_version}" defer></script>
  <script src="../assets/particles.js?v={asset_version}" defer></script>"""

HTML_SCRIPTS_EN = """\
  <script src="../../assets/i18n.js?v={asset_version}" defer></script>
  <script src="../../assets/particles.js?v={asset_version}" defer></script>"""


# ══════════════════════════════════════════════════════════════════════════════
# 5. SCRIPT_GAME_TRANSLATIONS
#    The inline <script> block that handles i18n switching on individual game
#    pages. Identical between IT and EN pages.
#
#    Placeholder: {game_data_json}
#      → pass the output of json_for_script({"description": ..., "description_en": ...})
#
#    All JavaScript { } braces are doubled ({{ / }}) so this constant is safe
#    to use with str.format(game_data_json=...).
# ══════════════════════════════════════════════════════════════════════════════

SCRIPT_GAME_TRANSLATIONS = """\
  <script>
    const GAME_DATA = {game_data_json};

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
  </script>"""


# ══════════════════════════════════════════════════════════════════════════════
# 6. HTML_CARD_TEMPLATE / HTML_RELATED_SECTION
#    Building blocks for the "related games" grid rendered at page bottom.
#
#    HTML_RELATED_CARD — one card <a> element.
#      Placeholders: {game_id}, {game_title}, {img_html}
#      {img_html} = a full <img> tag string, or "" when the game has no image.
#
#    HTML_RELATED_SECTION — outer grid wrapper.
#      Placeholders: {section_title}, {cards}
#      {section_title} = "Giochi simili" (IT) or "Similar Games" (EN)
#      {cards} = concatenated HTML_RELATED_CARD strings
#
#    Do NOT call .format() on HTML_RELATED_CARD directly — it contains CSS
#    inline styles with literal { }. Use .replace() for the placeholders, or
#    build the card via f-string interpolation instead (as the original does).
# ══════════════════════════════════════════════════════════════════════════════

# Per-card anchor block. Literal CSS braces present — use .replace(), not .format().
#   PLACEHOLDER_GAME_ID    → numeric game ID (e.g. "42")
#   PLACEHOLDER_GAME_TITLE → HTML-escaped game title
#   PLACEHOLDER_IMG_HTML   → "<img ...>" tag, or "" for image-less games
HTML_RELATED_CARD = (
    '<a href="PLACEHOLDER_GAME_ID.html" class="related-card" style="text-decoration:none;color:inherit">'
    "PLACEHOLDER_IMG_HTML"
    '<div style="padding:10px;font-size:0.85rem;font-weight:600;line-height:1.3">PLACEHOLDER_GAME_TITLE</div>'
    "</a>"
)

# Image tag used inside HTML_RELATED_CARD when game["image"] is truthy.
# Replace PLACEHOLDER_IMG_SRC and PLACEHOLDER_GAME_TITLE before embedding.
HTML_RELATED_CARD_IMG = (
    '<img src="PLACEHOLDER_IMG_SRC" alt="PLACEHOLDER_GAME_TITLE"'
    ' loading="lazy" style="width:100%;height:120px;object-fit:cover;border-radius:8px 8px 0 0">'
)

# Grid wrapper for the related-games section.
# Placeholders: {section_title}, {cards}  — safe for .format().
HTML_RELATED_SECTION = (
    '<div class="game-section" style="margin-top:36px">'
    '<div class="game-section-title" id="relatedTitle">{section_title}</div>'
    '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px">'
    "{cards}"
    "</div></div>"
)


# ══════════════════════════════════════════════════════════════════════════════
# 7. SCRIPT_ANALYTICS
#    No analytics or third-party tracking script exists in build_static_pages.py.
#    This constant is a documented placeholder for future use.
# ══════════════════════════════════════════════════════════════════════════════

SCRIPT_ANALYTICS = ""  # Not implemented — no tracking script in the current build
