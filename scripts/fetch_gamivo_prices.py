#!/usr/bin/env python3
"""
fetch_gamivo_prices.py
======================
Aggiorna gmvUrl/gmvDiscount via CJ Product Catalog API.

Utilizzo:
    python3 scripts/fetch_gamivo_prices.py
    # Legge CJ_API_TOKEN da .env

 advertiser GAMIVO: 6086371
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog_data

# Load .env if exists
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            v = v.split("#")[0].strip()
            os.environ.setdefault(k.strip(), v)

CJ_API_TOKEN = os.environ.get("CJ_API_TOKEN", "")
CJ_PUBLISHER_COMPANY_ID = os.environ.get("CJ_PUBLISHER_COMPANY_ID", "7903980")
CJ_WEBSITE_ID = os.environ.get("CJ_WEBSITE_ID", "101708519")
CJ_GAMIVO_COMPANY_ID = "6086371"
CJ_ENDPOINT = "https://ads.api.cj.com/query"

DELAY = 0.4
PREFERRED_CURR = "EUR"


def _cj_headers() -> dict:
    return {
        "Authorization": f"Bearer {CJ_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _title_match(cj_title: str, game_title: str) -> bool:
    """Match title: rimuove suffissi comuni."""

    def clean(t: str) -> str:
        t = t.lower()
        t = re.sub(r"\s*[-–:]\s*(pc|steam|key|gift|global|eu|us).*", "", t)
        t = re.sub(r"[^a-z0-9 ]", "", t)
        return t.strip()

    a, b = clean(cj_title), clean(game_title)
    return a == b or a.startswith(b) or b.startswith(a)


def _cj_query(session, advertiser_id: str, keywords: str) -> list:
    """Esegue una query CJ GraphQL."""
    import requests

    query = """
    {
      products(
        companyId: "%s"
        partnerIds: ["%s"]
        keywords: ["%s"]
        limit: 20
      ) {
        resultList {
          id
          title
          linkCode(pid: "%s") { clickUrl }
          price { amount currency }
        }
      }
    }
    """ % (
        CJ_PUBLISHER_COMPANY_ID,
        advertiser_id,
        keywords.replace('"', '\\"'),
        CJ_WEBSITE_ID,
    )

    try:
        resp = session.post(
            CJ_ENDPOINT, json={"query": query}, headers=_cj_headers(), timeout=15
        )
        if resp.status_code != 200:
            return []
        return (resp.json().get("data") or {}).get("products", {}).get(
            "resultList"
        ) or []
    except Exception:
        return []


def search_gamivo(session, title: str) -> tuple[str, int]:
    """Cerca 'title' su GAMIVO via CJ GraphQL API."""
    try:
        products = _cj_query(session, CJ_GAMIVO_COMPANY_ID, title)

        candidates = [p for p in products if _title_match(p.get("title", ""), title)]
        if not candidates:
            return "", 0

        # Preferisci EUR
        candidates.sort(key=lambda p: (p.get("price", {}).get("currency") != "EUR", 0))
        best = candidates[0]

        click_url = (best.get("linkCode") or {}).get("clickUrl", "")
        if not click_url:
            return "", 0

        # GAMIVO non espone sconti nel feed - usa default 10%
        discount = 10

        return click_url, discount

    except Exception as e:
        print(f"  ⚠️  GAMIVO errore '{title}': {e}")
    return "", 0


def run():
    import requests

    if not CJ_API_TOKEN:
        print("❌ CJ_API_TOKEN mancante")
        return

    games = catalog_data.load_games()
    targets = [g for g in games if g.get("steamUrl")]
    print(f"🔍 Cerco GAMIVO per {len(targets)} giochi...")

    session = requests.Session()
    found = 0

    for i, game in enumerate(targets, 1):
        gmv_url, gmv_disc = search_gamivo(session, game["title"])
        time.sleep(DELAY)

        for g in games:
            if g["id"] == game["id"]:
                g["gmvUrl"] = gmv_url
                g["gmvDiscount"] = gmv_disc
                if gmv_url:
                    found += 1
                print(
                    f"  ✓ [{i}/{len(targets)}] {game['title'][:30]}: {'OK' if gmv_url else '—'}"
                )
                break

        if i % 50 == 0:
            print(f"  Progresso: {i}/{len(targets)}")

    print(f"\n✅ GAMIVO: {found}/{len(targets)}")

    # Verify the data was written
    print(f"Verifying: {sum(1 for g in games if g.get('gmvUrl'))} games have gmvUrl")

    # Save to disk
    catalog_data.write_legacy_games_js(games, None)
    print("💾 games.js aggiornato")

    # Double check after write
    print(f"After write: {sum(1 for g in games if g.get('gmvUrl'))} games have gmvUrl")


if __name__ == "__main__":
    run()
