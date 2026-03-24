#!/usr/bin/env python3
"""
Aggiorna gsUrl/gsDiscount in games.js tramite CJ Product Catalog API (Gameseal).

Utilizza la CJ GraphQL API su ads.api.cj.com per cercare giochi su Gameseal,
ottenere il link diretto al prodotto con tracking CJ incluso e il prezzo.

Utilizzo:
    python3 scripts/fetch_gameseal_prices.py
    # Legge CJ_API_TOKEN da .env o variabile d'ambiente

Dipendenze: requests (già in requirements.txt)
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Carica .env se esiste
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            v = v.split("#")[0].strip()  # rimuovi commenti inline
            os.environ.setdefault(k.strip(), v)

import catalog_data

# ─── Configurazione CJ ────────────────────────────────────────────────────────
CJ_API_TOKEN             = os.environ.get("CJ_API_TOKEN", "")
CJ_PUBLISHER_COMPANY_ID  = os.environ.get("CJ_PUBLISHER_COMPANY_ID", "7903980")
CJ_WEBSITE_ID            = os.environ.get("CJ_WEBSITE_ID", "101708519")  # pid per linkCode
CJ_GAMESEAL_COMPANY_ID   = os.environ.get("CJ_GAMESEAL_COMPANY_ID", "7571703")
CJ_ENDPOINT              = "https://ads.api.cj.com/query"

DELAY          = 0.4   # secondi tra chiamate API (rate limit: 500/5min)
PREFERRED_CURR = "EUR"
PLATFORM_DENY  = re.compile(r"\b(ps[345]|playstation|xbox|switch|nintendo|gog|epic)\b", re.I)
# Priorità lingua: 0=nessun prefisso (globale), 1=en, 2=it, 99=altro
LANG_RANK = {"": 0, "en": 1, "it": 2}


def _cj_headers() -> dict:
    return {
        "Authorization": f"Bearer {CJ_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _title_match(cj_title: str, game_title: str) -> bool:
    def clean(t: str) -> str:
        t = t.lower()
        t = re.sub(r"\s*[-–:]\s*(europe|us|canada|global|row|worldwide|key|gift card|account).*", "", t)
        t = re.sub(r"[^a-z0-9 ]", "", t)
        return t.strip()
    a, b = clean(cj_title), clean(game_title)
    return a == b or a.startswith(b) or b.startswith(a)


def _is_pc_steam(title: str) -> bool:
    """Ritorna True se il titolo sembra essere un gioco PC/Steam (non console)."""
    t = title.lower()
    if PLATFORM_DENY.search(t):
        return False
    # Accetta sia titoli con "(PC)" o "Steam" espliciti, sia titoli senza piattaforma
    return True


def _lang_rank(click_url: str) -> int:
    """Estrae il prefisso lingua dal link Gameseal nell'URL CJ e restituisce il rank."""
    from urllib.parse import urlparse, unquote
    try:
        # click_url contiene url=https%3A%2F%2Fgameseal.com%2Fen%2F...
        parsed = urlparse(click_url)
        inner_url = ""
        for part in parsed.query.split("&"):
            if part.startswith("url="):
                inner_url = unquote(part[4:])
                break
        if not inner_url:
            return 99
        path = urlparse(inner_url).path.lstrip("/")
        # Primo segmento del path: "en", "it", "fr", ecc. o direttamente il slug
        first = path.split("/")[0] if "/" in path else ""
        # Se è lungo 2 caratteri è un codice lingua; altrimenti è il slug (nessun prefisso)
        lang = first if len(first) == 2 else ""
        return LANG_RANK.get(lang, 99)
    except Exception:
        return 99


def _parse_price(amount: str | None) -> float:
    if not amount:
        return 0.0
    m = re.search(r"[\d.]+", str(amount).replace(",", ""))
    return float(m.group()) if m else 0.0


def search_gameseal(session, title: str) -> tuple[str, int]:
    """
    Cerca 'title' su Gameseal via CJ GraphQL API.
    Restituisce (gsUrl, gsDiscount) oppure ("", 0) se non trovato.
    gsUrl include il tracking CJ.
    """
    query = """
    {
      products(
        companyId: "%s"
        partnerIds: ["%s"]
        keywords: ["%s"]
        limit: 50
      ) {
        resultList {
          id
          title
          linkCode(pid: "%s") { clickUrl }
          price { amount currency }
          salePrice { amount currency }
        }
      }
    }
    """ % (
        CJ_PUBLISHER_COMPANY_ID,
        CJ_GAMESEAL_COMPANY_ID,
        title.replace('"', '\\"'),
        CJ_WEBSITE_ID,
    )

    try:
        resp = session.post(CJ_ENDPOINT, json={"query": query}, headers=_cj_headers(), timeout=15)
        if resp.status_code == 401:
            print("❌ CJ API: token non valido o scaduto (401)")
            sys.exit(1)
        if resp.status_code != 200:
            print(f"  ⚠️  CJ API {resp.status_code} per '{title}'")
            return "", 0

        data = resp.json()
        products = (data.get("data") or {}).get("products", {}).get("resultList") or []

        # Candidati: titolo match + piattaforma PC/Steam
        candidates = [
            p for p in products
            if _title_match(p.get("title", ""), title) and _is_pc_steam(p.get("title", ""))
        ]

        if not candidates:
            return "", 0

        # Ordina: prima lingua (no-prefix > en > it > altro), poi EUR
        def _score(p):
            lang = _lang_rank((p.get("linkCode") or {}).get("clickUrl", ""))
            is_eur = (p.get("price") or {}).get("currency") == PREFERRED_CURR
            return (lang, 0 if is_eur else 1)

        candidates.sort(key=_score)
        best = candidates[0]

        click_url = (best.get("linkCode") or {}).get("clickUrl", "")
        if not click_url:
            return "", 0

        price = _parse_price((best.get("price") or {}).get("amount"))
        sale_price = _parse_price((best.get("salePrice") or {}).get("amount"))

        # Gameseal (grey market): CJ API non fornisce salePrice — discount=0 è atteso
        if price > 0 and sale_price > 0 and sale_price < price:
            discount = round((price - sale_price) / price * 100)
        else:
            discount = 0

        return click_url, discount

    except Exception as e:
        print(f"  ⚠️  CJ API errore '{title}': {e}")
    return "", 0


def run() -> None:
    try:
        import requests
    except ImportError:
        print("❌ requests non installato. Esegui: pip install requests")
        sys.exit(1)

    if not CJ_API_TOKEN:
        print("❌ CJ_API_TOKEN mancante. Aggiungilo a .env o come variabile d'ambiente.")
        sys.exit(1)

    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()

    targets = [g for g in games if g.get("steamUrl")]
    print(f"🔍 Cerco prezzi Gameseal (CJ API) per {len(targets)} giochi con Steam URL...")

    gs_found = 0
    gs_updated = 0
    start = time.time()

    import requests as _requests
    session = _requests.Session()

    for i, game in enumerate(targets, 1):
        gs_url, gs_disc = search_gameseal(session, game["title"])

        for orig in games:
            if orig["id"] != game["id"]:
                continue
            old_url = orig.get("gsUrl", "")
            orig["gsUrl"] = gs_url
            orig["gsDiscount"] = gs_disc
            if gs_url:
                gs_found += 1
                if gs_url != old_url:
                    gs_updated += 1
                    disc_str = f"-{gs_disc}%" if gs_disc else "0%"
                    print(f"  ✓ [{game['id']}] {game['title']}: {disc_str}")
            break

        if i % 50 == 0:
            elapsed = time.time() - start
            print(f"  Progresso: {i}/{len(targets)} — {elapsed:.0f}s")

        time.sleep(DELAY)

    elapsed = time.time() - start
    print(f"\n✅ Gameseal trovati: {gs_found}/{len(targets)} ({gs_updated} nuovi) — {elapsed:.0f}s")
    catalog_data.write_legacy_games_js(games, featured_id)
    catalog_data.write_catalog_artifact(games)
    catalog_data.write_public_catalog_export(games)
    print("💾 games.js aggiornato")


if __name__ == "__main__":
    run()
