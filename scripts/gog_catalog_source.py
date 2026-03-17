#!/usr/bin/env python3
"""
GOG catalog source adapter.

Usa l'API non ufficiale di GOG (stessa usata dal sito) per trovare giochi
co-op su Windows non presenti nel catalogo.

Non richiede API key. Rate limit permissivo (~1 req/sec per sicurezza).

GOG è usato solo per giochi GOG-only (senza Steam App ID in IGDB).
Per i giochi che hanno sia Steam che GOG, Steam rimane la fonte primaria.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import Any


GOG_CATALOG_URL = "https://catalog.gog.com/v1/catalog"
GOG_PRODUCT_URL = "https://www.gog.com/en/game/{slug}"
GOG_CDN_IMAGE = "https://images.gog-statics.com/{image_id}.jpg"

REQUEST_DELAY = 1.2
PAGE_LIMIT = 48     # GOG API max per pagina
MAX_PAGES = 5       # max pagine da scansionare per run
MIN_RATING = 3.5    # su 5 stelle (GOG usa rating 1-5)


class GogCatalogSource:
    def __init__(self, delay: float = REQUEST_DELAY) -> None:
        self.delay = delay

    def _get(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any] | None:
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"
        time.sleep(self.delay)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            print(f"    ⚠ GOG {url[:60]}: {exc}")
            return None

    def fetch_coop_games(self, page: int = 1) -> list[dict[str, Any]]:
        """Fetch one page of co-op Windows games from GOG catalog."""
        # Co-op su GOG è in features (slug: coop), non in tags o genres
        params = {
            "productType": "in:game",
            "systems": "in:windows",
            "features": "in:coop",
            "order": "desc:rating",
            "limit": str(PAGE_LIMIT),
            "page": str(page),
        }
        data = self._get(GOG_CATALOG_URL, params)
        if not data:
            return []
        return data.get("products", [])

    def extract_game_info(self, product: dict[str, Any]) -> dict[str, Any] | None:
        """Convert a GOG catalog product into a candidate dict."""
        title = product.get("title", "")
        slug = product.get("slug", "")
        if not title or not slug:
            return None

        # Rating: GOG usa reviewsRating (0-100) o reviewsCount
        rating_raw = product.get("reviewsRating", 0) or 0

        # Image: GOG ha coverHorizontal o coverVertical
        image_id = (
            product.get("coverHorizontal")
            or product.get("coverVertical")
            or ""
        )
        # Normalizza URL immagine GOG
        image_url = ""
        if image_id:
            # Rimuove prefisso https:// se già presente
            if image_id.startswith("https://"):
                image_url = image_id
            else:
                image_url = f"https:{image_id}"
            # Assicura estensione jpg e dimensione ottimale
            if not any(ext in image_url for ext in (".jpg", ".png", ".webp")):
                image_url += ".jpg"

        gog_url = f"https://www.gog.com/en/game/{slug}"

        # Tags per categorie
        tags = [t.get("slug", "") for t in (product.get("tags") or [])]

        return {
            "title": title,
            "slug": slug,
            "gogUrl": gog_url,
            "image": image_url,
            "rating_gog": rating_raw,
            "tags": tags,
        }


def fetch_gog_candidates(
    existing_titles: set[str],
    existing_gog_urls: set[str],
    existing_igdb_ids: set[int],
    max_games: int = 20,
) -> list[dict[str, Any]]:
    """
    Fetch GOG co-op games not already in the catalog.
    Returns candidates with basic info — caller enriches with IGDB/descriptions.
    """
    source = GogCatalogSource()
    candidates: list[dict[str, Any]] = []

    for page in range(1, MAX_PAGES + 1):
        if len(candidates) >= max_games:
            break

        print(f"    GOG pagina {page}...", end=" ", flush=True)
        products = source.fetch_coop_games(page)

        if not products:
            print("nessun risultato")
            break

        new_in_page = 0
        for product in products:
            info = source.extract_game_info(product)
            if not info:
                continue

            # Deduplicazione
            title_lower = info["title"].lower().strip()
            if title_lower in existing_titles:
                continue
            if info["gogUrl"] in existing_gog_urls:
                continue

            # Qualità minima
            if info["rating_gog"] > 0 and info["rating_gog"] < MIN_RATING * 20:
                continue

            candidates.append(info)
            existing_titles.add(title_lower)
            existing_gog_urls.add(info["gogUrl"])
            new_in_page += 1

            if len(candidates) >= max_games:
                break

        print(f"{new_in_page} nuovi (tot: {len(candidates)})")

        if len(products) < PAGE_LIMIT:
            break  # ultima pagina

    return candidates
