#!/usr/bin/env python3
"""
Genera le pagine hub SEO per keyword strategiche co-op.

5 pagine statiche nella root del sito:
  - migliori-giochi-coop-2026.html
  - giochi-coop-local.html
  - giochi-coop-2-giocatori.html
  - giochi-coop-free.html
  - giochi-coop-indie.html

Utilizzo:
    python3 scripts/build_hub_pages.py
"""
from __future__ import annotations

import html as html_mod
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog_data

ASSET_VERSION = "20260326"
SITE_URL = "https://coophubs.net"

# ─── Definizioni hub pages ──────────────────────────────────────────────────

def _select_top(games: list[dict], *, key_fn, top: int = 40) -> list[dict]:
    return sorted(games, key=key_fn)[:top]


def _rating_ccu_key(g: dict):
    return (-g.get("rating", 0), -g.get("ccu", 0))


HUB_DEFS = [
    {
        "slug": "migliori-giochi-coop-2026",
        "title_tag": "Migliori Giochi Co-op 2026 per PC | CoopHubs",
        "meta_desc": "I migliori giochi cooperativi per PC nel 2026: nuove uscite con alto rating Steam e classici ancora attivissimi, selezionati per qualità dell'esperienza co-op.",
        "og_title": "Migliori Giochi Co-op 2026 per PC",
        "h1": "Migliori Giochi Co-op 2026 per PC",
        "kicker": "Selezione curata",
        "subtitle": "Nuove uscite e classici senza tempo: i co-op da non perdere nel 2026, selezionati per qualità e attività reale dei giocatori.",
        "intro": (
            "Trovare il gioco co-op giusto nel 2026 non è semplice: Steam conta migliaia di titoli "
            "e i classici con voti altissimi spesso oscurano le uscite recenti di qualità."
            "\n\n"
            "Questa lista usa due criteri distinti. "
            "La prima sezione raccoglie i giochi usciti dal 2022 in poi con rating elevato su Steam — "
            "titoli moderni come Split Fiction, R.E.P.O., Baldur's Gate 3 e Schedule I, "
            "che rappresentano il meglio del co-op negli ultimi tre anni. "
            "La seconda sezione include solo i classici che sono ancora attivamente giocati nel 2026, "
            "misurati dai giocatori concorrenti reali: Stardew Valley, Left 4 Dead 2, Terraria, "
            "Don't Starve Together — vecchi ma non dimenticati."
            "\n\n"
            "Ogni scheda indica modalità di gioco, numero di giocatori e link alla pagina con confronto prezzi."
        ),
        "schema_name": "Migliori Giochi Co-op 2026 per PC",
        "sections_fn": lambda games: [
            (
                "Nuove uscite — dal 2022 al 2026",
                _select_top(
                    [g for g in games if g.get("releaseYear", 0) >= 2022 and g.get("rating", 0) >= 85],
                    key_fn=_rating_ccu_key,
                    top=24,
                ),
            ),
            (
                "Classici ancora vivi — i più giocati nel 2026",
                _select_top(
                    [g for g in games
                     if g.get("releaseYear", 0) < 2022
                     and g.get("ccu", 0) >= 5000
                     and g.get("rating", 0) >= 90],
                    key_fn=lambda g: -g.get("ccu", 0),
                    top=12,
                ),
            ),
        ],
    },
    {
        "slug": "giochi-coop-local",
        "title_tag": "Giochi Co-op Locale per PC — Divano e Split Screen | CoopHubs",
        "meta_desc": "I migliori giochi co-op locale per PC: divano, split screen e shared-screen. Gioca con chi hai accanto senza bisogno di connessione internet.",
        "og_title": "Giochi Co-op Locale per PC — Divano e Split Screen",
        "h1": "Migliori Giochi Co-op Locale per PC",
        "kicker": "Divano & Split Screen",
        "subtitle": "Gioca con chi hai accanto: i migliori titoli co-op locale, divano e split screen per PC.",
        "intro": (
            "Il co-op locale ha un fascino che nessuna connessione internet riesce a replicare: "
            "si gioca fianco a fianco, sullo stesso schermo o con controller in mano, "
            "senza ping, senza disconnessioni, senza fare a turni per spiegare le regole via chat."
            "\n\n"
            "Questa lista raccoglie i migliori giochi co-op locale disponibili su PC nel 2026, "
            "selezionati per qualità dell'esperienza di gioco condivisa. "
            "Trovi titoli in split screen, shared screen e couch co-op — alcuni pensati per coppie, "
            "altri per gruppi fino a quattro giocatori intorno alla stessa TV o monitor."
            "\n\n"
            "Dai platform cooperativi come Rayman Legends ai puzzle game come Unrailed!, "
            "dai giochi d'azione come Cuphead ai survival game come Don't Starve Together, "
            "il co-op locale copre tutti i generi. "
            "Ogni scheda indica il numero massimo di giocatori supportati in locale "
            "e il rating medio dei giocatori Steam, così puoi scegliere senza sorprese."
        ),
        "schema_name": "Giochi Co-op Locale per PC — Divano e Split Screen",
        "filter_fn": lambda games: _select_top(
            [g for g in games if "local" in g.get("coopMode", []) and g.get("rating", 0) > 0],
            key_fn=_rating_ccu_key,
            top=48,
        ),
    },
    {
        "slug": "giochi-coop-2-giocatori",
        "title_tag": "Giochi Co-op per 2 Giocatori PC — Coppia e Duo | CoopHubs",
        "meta_desc": "I migliori giochi co-op per 2 giocatori su PC: perfetti per coppie, amici o partner. Online e locale, dal platform all'avventura.",
        "og_title": "Giochi Co-op per 2 Giocatori PC",
        "h1": "Migliori Giochi Co-op per 2 Giocatori",
        "kicker": "Coppia & Duo",
        "subtitle": "Giochi co-op progettati per essere vissuti in due: online o locale, perfetti per coppie e amici.",
        "intro": (
            "Alcuni giochi co-op sono pensati esattamente per giocare in due: "
            "non come compromesso rispetto al multiplayer di gruppo, "
            "ma come esperienza progettata intorno alla coppia di giocatori."
            "\n\n"
            "In questa lista trovi i migliori giochi co-op per 2 giocatori su PC nel 2026, "
            "selezionati tra titoli con massimo 2 giocatori supportati e un rating alto su Steam. "
            "Si va dai platform cooperativi come It Takes Two e Cuphead — veri capolavori del genere — "
            "ai puzzle come Portal 2, dai roguelite come Roboquest agli adventure come We Were Here."
            "\n\n"
            "Molti di questi titoli supportano sia il co-op online che quello locale: "
            "puoi giocare con il partner sul divano o con un amico lontano dalla stessa sessione. "
            "La modalità di gioco è indicata su ogni scheda, così sai già prima cosa aspettarti."
        ),
        "schema_name": "Giochi Co-op per 2 Giocatori PC",
        "filter_fn": lambda games: _select_top(
            [g for g in games if g.get("maxPlayers", 4) <= 2 and g.get("rating", 0) > 0],
            key_fn=_rating_ccu_key,
            top=40,
        ),
    },
    {
        "slug": "giochi-coop-free",
        "title_tag": "Giochi Co-op Gratis per PC — Free to Play 2026 | CoopHubs",
        "meta_desc": "I migliori giochi co-op gratuiti per PC nel 2026: free to play con modalità cooperativa online, senza pagare nulla per iniziare.",
        "og_title": "Giochi Co-op Gratis per PC — Free to Play 2026",
        "h1": "Migliori Giochi Co-op Gratis per PC",
        "kicker": "Free to Play",
        "subtitle": "Co-op senza spendere nulla: i migliori giochi cooperativi gratuiti per PC nel 2026.",
        "intro": (
            "Giocare insieme non deve costare niente. "
            "Su Steam esistono decine di giochi cooperativi gratuiti — alcuni free to play puri, "
            "altri passati al modello gratuito dopo anni di successo a pagamento."
            "\n\n"
            "Questa lista raccoglie i migliori giochi co-op gratis per PC nel 2026, "
            "ordinati per qualità secondo i giocatori Steam. "
            "Si va dagli sparatutto tattici come Rainbow Six Siege ai battle royale cooperativi, "
            "dai giochi di carte come Legends of Runeterra agli MMO con contenuti di gruppo."
            "\n\n"
            "Tutti i titoli in questa lista sono scaricabili e giocabili gratuitamente su PC, "
            "senza acquisto iniziale richiesto. "
            "Alcuni hanno microtransazioni cosmetiche o contenuti premium opzionali, "
            "ma la modalità co-op di base è accessibile a chiunque. "
            "Il rating Steam indica la soddisfazione media dei giocatori — un buon punto di partenza "
            "per decidere da dove cominciare."
        ),
        "schema_name": "Giochi Co-op Gratis per PC — Free to Play 2026",
        "filter_fn": lambda games: sorted(
            [g for g in games if "free" in g.get("categories", []) and g.get("rating", 0) > 0],
            key=_rating_ccu_key,
        ),
    },
    {
        "slug": "giochi-coop-indie",
        "title_tag": "Migliori Giochi Co-op Indie per PC 2026 | CoopHubs",
        "meta_desc": "I migliori giochi co-op indie per PC nel 2026: titoli indipendenti con modalità cooperativa, selezionati per qualità e originalità.",
        "og_title": "Migliori Giochi Co-op Indie per PC 2026",
        "h1": "Migliori Giochi Co-op Indie per PC",
        "kicker": "Indie Co-op",
        "subtitle": "I migliori titoli indipendenti con modalità co-op: creatività, originalità e decine di ore in compagnia.",
        "intro": (
            "I giochi indie hanno cambiato il panorama del co-op. "
            "Mentre i grandi publisher si concentrano su live service e battle royale, "
            "gli sviluppatori indipendenti continuano a sperimentare: "
            "meccaniche asimmetriche, narrazioni cooperative, generi ibridi che non esisterebbero altrove."
            "\n\n"
            "Questa lista raccoglie i migliori giochi co-op indie per PC nel 2026, "
            "selezionati tra i titoli indipendenti con il rating più alto su Steam. "
            "Trovi giochi come Stardew Valley — che ha ridefinito il farm sim cooperativo — "
            "Vampire Survivors, Deep Rock Galactic e decine di altri titoli che vale la pena scoprire."
            "\n\n"
            "Il catalogo indie co-op è vasto e in continua crescita: "
            "ogni settimana escono nuovi titoli, molti dei quali sorprendono per qualità. "
            "Questa lista si aggiorna regolarmente tenendo traccia dei rating Steam, "
            "così puoi sempre trovare qualcosa di valido senza dover passare ore a cercare."
        ),
        "schema_name": "Migliori Giochi Co-op Indie per PC 2026",
        "filter_fn": lambda games: _select_top(
            [g for g in games if "indie" in g.get("categories", []) and g.get("rating", 0) > 0],
            key_fn=_rating_ccu_key,
            top=48,
        ),
    },
]


# ─── HTML helpers ────────────────────────────────────────────────────────────

def esc(s: Any) -> str:
    return html_mod.escape(str(s or ""), quote=True)


def _mode_label(mode: str) -> str:
    return {"online": "Online", "local": "Locale", "split": "Split Screen"}.get(mode, mode)


def _render_card(game: dict) -> str:
    title = game.get("title", "")
    gid = game.get("id", "")
    image = game.get("image", "")
    rating = game.get("rating", 0)
    _raw_desc = (game.get("description") or game.get("description_en") or "")
    if len(_raw_desc) > 130:
        desc = _raw_desc[:130].rsplit(" ", 1)[0] + "…"
    else:
        desc = _raw_desc
    modes = game.get("coopMode", [])
    players = game.get("players", "")

    mode_tags = " ".join(
        f'<span class="hub-tag">{_mode_label(m)}</span>' for m in modes
    )
    rating_html = f'<span class="hub-rating">{rating}%</span>' if rating else ""
    players_html = f'<span class="hub-tag hub-tag-players">{esc(players)} giocatori</span>' if players else ""

    return f"""    <a class="hub-card" href="games/{esc(gid)}.html">
      <img src="{esc(image)}" alt="{esc(title)}" loading="lazy" width="460" height="215">
      <div class="hub-card-body">
        <div class="hub-card-top">
          <h3 class="hub-card-title">{esc(title)}</h3>
          {rating_html}
        </div>
        <div class="hub-card-tags">{mode_tags}{players_html}</div>
        <p class="hub-card-desc">{esc(desc)}</p>
      </div>
    </a>"""


def _render_page(defn: dict, games: list[dict], sections: list[tuple[str, list[dict]]] | None = None) -> str:
    slug = defn["slug"]
    canonical = f"{SITE_URL}/{slug}.html"
    intro_paragraphs = "".join(
        f"      <p>{esc(p.strip())}</p>\n" for p in defn["intro"].split("\n\n") if p.strip()
    )

    if sections:
        count = sum(len(g) for _, g in sections)
        sections_html_parts = []
        for sec_title, sec_games in sections:
            cards = "\n".join(_render_card(g) for g in sec_games)
            sections_html_parts.append(
                f'    <h2 class="hub-section-heading"><span>{esc(sec_title)}</span></h2>\n'
                f'    <div class="hub-grid" aria-label="{esc(sec_title)}">\n{cards}\n    </div>'
            )
        grid_html = "\n\n".join(sections_html_parts)
        content_html = f'    <p class="hub-count"><strong>{count}</strong> giochi selezionati — aggiornati al 2026</p>\n\n{grid_html}'
    else:
        cards_html = "\n".join(_render_card(g) for g in games)
        count = len(games)
        content_html = (
            f'    <p class="hub-count"><strong>{count}</strong> giochi selezionati — aggiornati al 2026</p>\n\n'
            f'    <section class="hub-grid" aria-label="Giochi">\n{cards_html}\n    </section>'
        )

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": defn["schema_name"],
        "url": canonical,
        "description": defn["meta_desc"],
    }
    import json
    schema_json = json.dumps(schema, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{esc(defn["title_tag"])}</title>
  <meta name="description" content="{esc(defn["meta_desc"])}">
  <meta name="theme-color" content="#7c6aff">
  <meta name="color-scheme" content="dark">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="it" href="{canonical}">
  <link rel="alternate" hreflang="x-default" href="{canonical}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Coophubs">
  <meta property="og:title" content="{esc(defn["og_title"])}">
  <meta property="og:description" content="{esc(defn["meta_desc"])}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE_URL}/assets/og-image.jpg">
  <meta property="og:locale" content="it_IT">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(defn["og_title"])}">
  <meta name="twitter:description" content="{esc(defn["meta_desc"])}">
  <meta name="twitter:image" content="{SITE_URL}/assets/og-image.jpg">

  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="assets/icon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="assets/icon-180.png">
  <link rel="stylesheet" href="assets/style.css?v={ASSET_VERSION}">

  <script id="pageJsonLd" type="application/ld+json">
  {schema_json}
  </script>

  <style>
    .hub-page {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px 80px; position: relative; z-index: 1; }}
    .hub-intro {{ background: linear-gradient(135deg, rgba(124,106,255,0.08), rgba(124,106,255,0.03)); border: 1px solid rgba(124,106,255,0.15); border-radius: 20px; padding: 28px 32px; margin-bottom: 40px; }}
    .hub-kicker {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--accent); margin-bottom: 10px; }}
    .hub-h1 {{ font-size: clamp(1.7rem, 4vw, 2.6rem); font-weight: 800; letter-spacing: -1.5px; margin-bottom: 8px; line-height: 1.15; }}
    .hub-subtitle {{ color: var(--text2); font-size: 1rem; line-height: 1.65; margin-bottom: 0; }}
    .hub-body {{ margin-top: 18px; }}
    .hub-body p {{ color: var(--text2); font-size: 0.96rem; line-height: 1.75; margin-bottom: 12px; }}
    .hub-body p:last-child {{ margin-bottom: 0; }}
    .hub-count {{ color: var(--text2); font-size: 0.85rem; margin-bottom: 20px; }}
    .hub-count strong {{ color: var(--text); }}
    .hub-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }}
    .hub-card {{ display: flex; flex-direction: column; background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; text-decoration: none; color: inherit; transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s; }}
    .hub-card:hover {{ border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(124,106,255,0.15); }}
    .hub-card img {{ width: 100%; height: 160px; object-fit: cover; display: block; background: var(--bg3); }}
    .hub-card-body {{ padding: 14px 16px 16px; display: flex; flex-direction: column; flex: 1; gap: 8px; }}
    .hub-card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }}
    .hub-card-title {{ font-size: 0.95rem; font-weight: 700; line-height: 1.3; flex: 1; }}
    .hub-rating {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700; color: var(--accent); white-space: nowrap; padding: 2px 6px; background: rgba(124,106,255,0.1); border-radius: 6px; }}
    .hub-card-tags {{ display: flex; flex-wrap: wrap; gap: 5px; }}
    .hub-tag {{ font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 7px; border-radius: 5px; background: var(--bg3); color: var(--text2); }}
    .hub-tag-players {{ color: var(--accent2); background: rgba(236,72,153,0.08); }}
    .hub-card-desc {{ font-size: 0.82rem; color: var(--text2); line-height: 1.55; flex: 1; }}
    .hub-section-heading {{ font-size: 1rem; font-weight: 700; color: var(--text); margin: 36px 0 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
    .hub-section-heading span {{ color: var(--accent); }}
    @media (max-width: 600px) {{
      .hub-intro {{ padding: 20px; }}
      .hub-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body data-page="hub">
  <canvas id="bgCanvas" class="bg-canvas" aria-hidden="true"></canvas>

  <main class="hub-page">
    <div class="page-head">
      <a href="./" class="back-link">&larr; Torna al catalogo</a>
      <div class="page-head-actions">
        <button class="btn-lang" id="langBtn" onclick="setLang(currentLang === 'it' ? 'en' : 'it')" aria-label="Cambia lingua">🇬🇧 EN</button>
      </div>
    </div>

    <section class="hub-intro" aria-label="Introduzione">
      <div class="hub-kicker">{esc(defn["kicker"])}</div>
      <h1 class="hub-h1">{esc(defn["h1"])}</h1>
      <p class="hub-subtitle">{esc(defn["subtitle"])}</p>
      <div class="hub-body">
{intro_paragraphs}      </div>
    </section>

{content_html}
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">Co-op Games Hub</div>
      <div class="footer-sub">Coophubs è un progetto indipendente dedicato alla scoperta di giochi cooperativi per PC.</div>
      <div class="footer-links">
        <a href="about.html">Sul progetto</a>
        <a href="contact.html">Contatti</a>
        <a href="free.html">Giochi gratis</a>
        <a href="privacy.html">Privacy Policy</a>
      </div>
      <div class="footer-support">
        <a href="https://ko-fi.com/coophubs" class="btn-kofi" target="_blank" rel="noopener noreferrer">☕ Supporta il progetto</a>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-copy">&copy; 2026 — Dati da Steam &amp; SteamSpy</div>
    </div>
  </footer>

  <script src="assets/i18n.js?v={ASSET_VERSION}" defer></script>
  <script src="assets/particles.js?v={ASSET_VERSION}" defer></script>
</body>
</html>"""


# ─── Entry point ─────────────────────────────────────────────────────────────

def run() -> list[str]:
    """Genera tutte le hub pages. Restituisce la lista degli slug generati."""
    games = catalog_data.load_games()
    generated: list[str] = []

    for defn in HUB_DEFS:
        slug = defn["slug"]

        if "sections_fn" in defn:
            sections = defn["sections_fn"](games)
            total = sum(len(g) for _, g in sections)
            if total == 0:
                print(f"  ⚠ {slug}: nessun gioco selezionato, skip")
                continue
            content = _render_page(defn, [], sections=sections)
            label = f"{total} giochi in {len(sections)} sezioni"
        else:
            selected = defn["filter_fn"](games)
            if not selected:
                print(f"  ⚠ {slug}: nessun gioco selezionato, skip")
                continue
            content = _render_page(defn, selected)
            label = f"{len(selected)} giochi"

        out = ROOT / f"{slug}.html"
        if out.exists() and out.read_text(encoding="utf-8") == content:
            print(f"  ✓ {slug}.html — invariata ({label})")
        else:
            out.write_text(content, encoding="utf-8")
            print(f"  ✓ {slug}.html — scritta ({label})")

        generated.append(slug)

    return generated


if __name__ == "__main__":
    print("🏗  Generazione hub pages SEO...")
    slugs = run()
    print(f"✅ {len(slugs)} pagine hub generate")
