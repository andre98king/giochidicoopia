#!/usr/bin/env python3
"""
Steam New Releases source adapter.

Usa la Steam Store search API per trovare giochi co-op usciti di recente,
bypassando il lag di SteamSpy (che impiega settimane ad indicizzare nuovi titoli).

Flusso:
1. Steam Store search (sort_by=Released_DESC + category co-op, json=1)
   → items con name + logo URL da cui estraiamo l'appid
2. appdetails → qualità + data uscita + co-op verificato
3. Filtra: recente (90g) + co-op + qualità (reviews/metacritic)

Non richiede API key.
"""

from __future__ import annotations

import datetime
import html as html_mod
import json
import re
import time
import urllib.request
import urllib.parse
from typing import Any


APPDETAILS_URL   = "https://store.steampowered.com/api/appdetails"
STORE_SEARCH_URL = "https://store.steampowered.com/search/results"

REQUEST_DELAY    = 1.2     # secondi tra chiamate appdetails
NEW_RELEASES_DAYS = 90     # finestra temporale giochi recenti
MAX_SEARCH_COUNT = 100     # risultati per query Steam Store search
MAX_CANDIDATES   = 120     # max candidati totali da esaminare per run

# Steam category IDs per la search (category2 nell'URL)
COOP_SEARCH_CATEGORIES = [9, 38, 39]

# Steam category IDs che indicano co-op nei metadati appdetails
COOP_CATEGORY_IDS = {9, 38, 39}

# Soglie qualità per giochi senza CCU (nuovi)
MIN_REVIEWS_NEW_RELEASE = 30
MIN_RATING_NEW_RELEASE  = 70


class SteamNewReleasesSource:
    def __init__(self, api_key: str = "", delay: float = REQUEST_DELAY) -> None:
        self.api_key = api_key
        self.delay = delay

    def _get(self, url: str, params: dict[str, str] | None = None) -> Any | None:
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        time.sleep(self.delay)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            print(f"    ⚠ Steam search {url[:70]}: {exc}")
            return None

    def _get_appid_from_item(self, item: dict) -> int | None:
        """Estrae l'appid dall'URL del logo (unico campo con l'appid)."""
        logo = item.get("logo") or item.get("header_image") or ""
        match = re.search(r"/apps/(\d+)/", logo)
        if match:
            return int(match.group(1))
        return None

    def fetch_recent_coop_appids(self, days: int = NEW_RELEASES_DAYS) -> list[int]:
        """
        Usa la Steam Store search per trovare giochi co-op recenti.
        Estratto appid dall'URL del logo in ogni risultato.
        """
        seen: set[int] = set()
        appids: list[int] = []

        for cat_id in COOP_SEARCH_CATEGORIES:
            params = {
                "sort_by":  "Released_DESC",
                "category1": "998",       # 998 = Games
                "category2": str(cat_id),
                "json":      "1",
                "count":     str(MAX_SEARCH_COUNT),
                "start":     "0",
            }
            data = self._get(STORE_SEARCH_URL, params)
            if not data:
                continue
            items = data.get("items") or []
            for item in items:
                appid = self._get_appid_from_item(item)
                if appid and appid not in seen:
                    seen.add(appid)
                    appids.append(appid)

            print(f"    Cat {cat_id}: {len(items)} risultati")

        return appids

    def fetch_appdetails(self, appid: int) -> dict[str, Any] | None:
        """Fetch Steam appdetails per un singolo gioco."""
        params = {"appids": str(appid), "l": "english", "cc": "us"}
        data = self._get(APPDETAILS_URL, params)
        if not data:
            return None
        info = data.get(str(appid), {})
        if not info.get("success"):
            return None
        return info.get("data")

    def is_coop(self, sd: dict[str, Any]) -> bool:
        """Verifica co-op dalle categorie appdetails."""
        cat_ids = {c.get("id") for c in sd.get("categories", [])}
        return bool(cat_ids & COOP_CATEGORY_IDS)

    def is_recent(self, sd: dict[str, Any], days: int = NEW_RELEASES_DAYS) -> bool:
        """Verifica che il gioco sia stato rilasciato entro il periodo specificato."""
        release = sd.get("release_date") or {}
        if release.get("coming_soon"):
            return False
        date_str = release.get("date", "")
        if not date_str:
            return False
        for fmt in ("%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y"):
            try:
                release_dt = datetime.datetime.strptime(date_str.strip(), fmt)
                cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
                return release_dt >= cutoff
            except ValueError:
                continue
        return False

    def quality_ok(self, sd: dict[str, Any]) -> tuple[bool, str]:
        """Controlla qualità minima per un nuovo gioco."""
        rec = sd.get("recommendations", {}) or {}
        positive = rec.get("total", 0) or 0
        metacritic = (sd.get("metacritic") or {}).get("score", 0) or 0
        if positive < MIN_REVIEWS_NEW_RELEASE:
            return False, f"poche recensioni ({positive} < {MIN_REVIEWS_NEW_RELEASE})"
        return True, "ok"


def fetch_steam_new_coop_games(
    api_key: str,
    existing_appids: set[str],
    existing_titles: set[str],
    blacklist_appids: set[str],
    skip_words: list[str],
    max_games: int = 20,
) -> list[dict[str, Any]]:
    """
    Trova giochi co-op usciti di recente su Steam non ancora nel catalogo.
    Usa Steam Store search (sort_by=Released_DESC) + appdetails per qualità.
    """
    source = SteamNewReleasesSource(api_key)

    print(f"  Ricerca giochi co-op recenti da Steam Store (ultimi {NEW_RELEASES_DAYS} giorni)...")
    appids = source.fetch_recent_coop_appids(NEW_RELEASES_DAYS)
    print(f"  App trovate dalla search: {len(appids)}")

    if not appids:
        return []

    # Filtra già noti e blacklist prima delle chiamate appdetails
    to_check = [
        a for a in appids
        if str(a) not in existing_appids and str(a) not in blacklist_appids
    ][:MAX_CANDIDATES]

    print(f"  Da esaminare (non nel DB, non in blacklist): {len(to_check)}")

    candidates = []
    examined = 0
    none_count = 0
    not_recent_count = 0
    not_coop_count = 0

    for appid in to_check:
        if len(candidates) >= max_games:
            break

        examined += 1
        sd = source.fetch_appdetails(appid)
        if not sd:
            none_count += 1
            continue

        if sd.get("type") != "game":
            continue

        name = sd.get("name", "")
        if not name:
            continue

        name_lower = name.lower()
        if any(w in name_lower for w in skip_words):
            continue

        if name_lower.strip() in existing_titles:
            continue

        if not source.is_recent(sd, NEW_RELEASES_DAYS):
            not_recent_count += 1
            if not_recent_count <= 3:
                rel = (sd.get("release_date") or {}).get("date", "?")
                print(f"    ✗ non recente: {name} ({rel})")
            continue

        if not source.is_coop(sd):
            not_coop_count += 1
            continue

        ok, reason = source.quality_ok(sd)
        if not ok:
            print(f"    ✗ {name}: {reason}")
            continue

        release = sd.get("release_date", {}) or {}
        release_date = release.get("date", "")
        image = sd.get("header_image", "")

        cat_ids = {c.get("id") for c in sd.get("categories", [])}
        coop_mode = []
        if 38 in cat_ids or 9 in cat_ids:
            coop_mode.append("online")
        if 39 in cat_ids:
            coop_mode.append("local")
        if not coop_mode:
            coop_mode = ["online"]

        desc_en = sd.get("short_description", "") or ""
        desc_en = re.sub(r"<[^>]+>", " ", desc_en)
        desc_en = html_mod.unescape(desc_en)
        desc_en = re.sub(r"\s+", " ", desc_en).strip()[:400]

        recommendations = (sd.get("recommendations") or {}).get("total", 0) or 0
        print(f"    ✓ {name} (appid {appid}, {release_date}, {recommendations} rec)")

        candidates.append({
            "appid":           str(appid),
            "name":            name,
            "image":           image,
            "description":     desc_en,
            "description_en":  desc_en,
            "steamUrl":        f"https://store.steampowered.com/app/{appid}/",
            "coopMode":        coop_mode,
            "releaseDate":     release_date,
            "recommendations": recommendations,
        })

    print(f"  Esaminati: {examined} | None: {none_count} | NonRecent: {not_recent_count} | NonCoop: {not_coop_count} | Candidati: {len(candidates)}")
    return candidates
