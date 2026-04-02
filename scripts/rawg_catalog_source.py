#!/usr/bin/env python3
"""
RAWG catalog source adapter.

Usa l'API ufficiale di RAWG per trovare giochi co-op su PC disponibili su Steam
non presenti nel catalogo.

Richiede RAWG_API_KEY (rawg.io/apidocs).
Filtra per: piattaforma PC (id=4), store Steam (id=1), tag cooperative.
I candidati restituiti hanno sempre steam_appid → quality_gate.validate() li verifica.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any


RAWG_API_BASE = "https://api.rawg.io/api"
# platform id 4 = PC, store id 1 = Steam, tag slug = cooperative
RAWG_COOP_PARAMS = {
    "platforms": "4",
    "stores": "1",
    "tags": "cooperative",
    "ordering": "-rating",
    "page_size": "40",
}


class RawgCatalogSource:
    def __init__(self, api_key: str, delay: float = 1.0) -> None:
        self.api_key = api_key
        self.delay = delay

    def _get(self, endpoint: str, params: dict[str, str] | None = None) -> dict[str, Any] | None:
        all_params = {"key": self.api_key, **(params or {})}
        qs = urllib.parse.urlencode(all_params)
        url = f"{RAWG_API_BASE}/{endpoint}?{qs}"
        time.sleep(self.delay)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "coophubs-rawg/1.0", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            print(f"    ⚠ RAWG {endpoint}: {exc}")
            return None

    def _extract_steam_appid(self, stores: list[dict]) -> str | None:
        """Estrae lo Steam app ID dalla lista stores del gioco RAWG."""
        for s in stores or []:
            store_id = s.get("store", {}).get("id")
            url = s.get("url", "")
            if store_id == 1 and url:
                # URL formato: https://store.steampowered.com/app/APPID/...
                import re
                m = re.search(r"/app/(\d+)", url)
                if m:
                    return m.group(1)
        return None

    def discover_coop_games(
        self,
        existing_steam_appids: set[str],
        existing_titles: set[str],
        max_games: int = 20,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Trova giochi co-op PC su Steam tramite RAWG.

        Ritorna lista di candidati normalizzati:
          {title, steam_appid, rawg_id, rating_rawg, source}
        Solo giochi con steam_appid noto e non già in catalogo.
        """
        candidates: list[dict[str, Any]] = []
        seen_appids: set[str] = set()

        for page in range(1, max_pages + 1):
            if len(candidates) >= max_games:
                break
            params = {**RAWG_COOP_PARAMS, "page": str(page)}
            data = self._get("games", params)
            if not data:
                break
            results = data.get("results", [])
            if not results:
                break

            for game in results:
                if len(candidates) >= max_games:
                    break

                title = (game.get("name") or "").strip()
                rawg_id = game.get("id")
                if not title or not rawg_id:
                    continue

                # Recupera stores per estrarre steam_appid (non incluso nel listing)
                detail = self._get(f"games/{rawg_id}", {"stores": "1"})
                if not detail:
                    continue
                stores = detail.get("stores", [])
                steam_appid = self._extract_steam_appid(stores)
                if not steam_appid:
                    continue

                if steam_appid in existing_steam_appids:
                    continue
                if steam_appid in seen_appids:
                    continue
                if title.lower().strip() in existing_titles:
                    continue

                seen_appids.add(steam_appid)
                rating_rawg = game.get("rating", 0) or 0

                candidates.append({
                    "title": title,
                    "steam_appid": steam_appid,
                    "rawg_id": rawg_id,
                    "rating_rawg": round(float(rating_rawg), 2),
                    "igdb_id": None,
                    "gog_url": None,
                    "ccu": 0,
                    "source": "rawg",
                })

        return candidates
