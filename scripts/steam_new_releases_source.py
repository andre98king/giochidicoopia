#!/usr/bin/env python3
"""
Steam New Releases source adapter.

Usa la Steam Store search API per trovare giochi co-op usciti di recente,
bypassando il lag di SteamSpy (che impiega settimane ad indicizzare nuovi titoli).

Flusso:
1. Steam Store search API (sort_by=Released_DESC + category co-op)
   → restituisce direttamente giochi co-op ordinati per data uscita, no API key
2. appdetails per qualità + metadati completi
3. Qualità: positive reviews + metacritic (no CCU — giochi nuovi non l'hanno)
"""

from __future__ import annotations

import datetime
import json
import time
import urllib.request
import urllib.parse
from typing import Any


APPDETAILS_URL   = "https://store.steampowered.com/api/appdetails"
STORE_SEARCH_URL = "https://store.steampowered.com/search/results/"

REQUEST_DELAY    = 1.2     # secondi tra chiamate appdetails
NEW_RELEASES_DAYS = 90     # finestra temporale giochi recenti
MAX_SEARCH_COUNT = 50      # risultati per query Steam Store search
MAX_CANDIDATES   = 120     # max candidati totali da esaminare per run

# Steam category IDs per la search (categoria2 nell'URL)
# 9=Co-op, 38=Online Co-op, 39=Local Co-op
COOP_SEARCH_CATEGORIES = [9, 38, 39]

# Steam category IDs che indicano co-op nei metadati appdetails
COOP_CATEGORY_IDS = {9, 38, 39}

# Soglie qualità per giochi senza CCU (nuovi)
MIN_REVIEWS_NEW_RELEASE = 30   # recensioni positive minime
MIN_RATING_NEW_RELEASE  = 70   # rating % minimo


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
            print(f"    ⚠ Steam API {url[:70]}: {exc}")
            return None

    def fetch_recent_coop_appids(self, days: int = NEW_RELEASES_DAYS) -> list[int]:
        """
        Usa la Steam Store search per trovare giochi co-op recenti.
        Non richiede API key. Ordina per data uscita (più recente prima).
        """
        seen: set[int] = set()
        appids: list[int] = []
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)

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
            page_stopped = False
            for item in items:
                appid = item.get("id")
                if not appid or appid in seen:
                    continue
                # Controlla data se presente nel risultato search
                # (spesso non c'è, quindi accettiamo e filtriamo dopo con appdetails)
                seen.add(appid)
                appids.append(appid)
                # Se la release_string indica anno molto vecchio, smetti di cercare
                release_str = item.get("release_date") or item.get("released") or ""
                if release_str:
                    for fmt in ("%d %b, %Y", "%b %d, %Y", "%d %B, %Y"):
                        try:
                            dt = datetime.datetime.strptime(str(release_str).strip(), fmt)
                            if dt < cutoff:
                                page_stopped = True
                            break
                        except ValueError:
                            continue
                if page_stopped:
                    break

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
        """Verifica se il gioco ha categorie co-op su Steam."""
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
        # Steam usa formati come "5 Mar, 2026" o "Mar 5, 2026"
        for fmt in ("%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y"):
            try:
                release_dt = datetime.datetime.strptime(date_str.strip(), fmt)
                cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
                return release_dt >= cutoff
            except ValueError:
                continue
        return False

    def quality_ok(self, sd: dict[str, Any]) -> tuple[bool, str]:
        """Controlla qualità minima per un nuovo gioco senza CCU."""
        rec = sd.get("recommendations", {}) or {}
        positive = rec.get("total", 0) or 0
        metacritic = (sd.get("metacritic") or {}).get("score", 0) or 0
        if positive < MIN_REVIEWS_NEW_RELEASE and metacritic < 70:
            return False, f"poche recensioni ({positive}) e metacritic basso ({metacritic})"
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
    Usa Steam Store search (no API key richiesta) + appdetails per qualità.
    Restituisce candidati con dati completi pronti per auto_update.
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

        # Solo giochi, non DLC/software/video
        if sd.get("type") != "game":
            continue

        name = sd.get("name", "")
        if not name:
            continue

        # Skip parole chiave indesiderate
        name_lower = name.lower()
        if any(w in name_lower for w in skip_words):
            continue

        # Deduplicazione per titolo
        if name_lower.strip() in existing_titles:
            continue

        # Deve essere uscito recentemente
        if not source.is_recent(sd, NEW_RELEASES_DAYS):
            not_recent_count += 1
            if not_recent_count <= 3:
                rel = (sd.get("release_date") or {}).get("date", "?")
                print(f"    ✗ non recente: {name} ({rel})")
            continue

        # Deve avere co-op (conferma con appdetails, non solo search)
        if not source.is_coop(sd):
            not_coop_count += 1
            continue

        # Qualità
        ok, reason = source.quality_ok(sd)
        if not ok:
            print(f"    ✗ {name}: {reason}")
            continue

        # Data uscita
        release = sd.get("release_date", {}) or {}
        release_date = release.get("date", "")

        # Immagine
        image = sd.get("header_image", "")

        # Modalità co-op
        cat_ids = {c.get("id") for c in sd.get("categories", [])}
        coop_mode = []
        if 38 in cat_ids or 9 in cat_ids:
            coop_mode.append("online")
        if 39 in cat_ids:
            coop_mode.append("local")
        if not coop_mode:
            coop_mode = ["online"]

        # Descrizione
        desc_en = sd.get("short_description", "") or ""
        import re
        desc_en = re.sub(r"<[^>]+>", " ", desc_en)
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
