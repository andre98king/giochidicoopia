#!/usr/bin/env python3
"""
Steam New Releases source adapter.

Usa la Steam Web API ufficiale per trovare giochi co-op usciti di recente,
bypassando il lag di SteamSpy (che impiega settimane ad indicizzare nuovi titoli).

Flusso:
1. IStoreService/GetAppList con last_appid=BASELINE → salta appid vecchi,
   parte direttamente dai giochi recenti (appid alti = nuovi)
2. appdetails → filtra per categorie co-op + data uscita
3. Qualità: positive reviews + metacritic (no CCU — giochi nuovi non l'hanno)

Richiede: STEAM_API_KEY env var (https://steamcommunity.com/dev/apikey)
"""

from __future__ import annotations

import datetime
import json
import time
import urllib.request
import urllib.parse
from typing import Any


STEAM_API_BASE = "https://api.steampowered.com"
APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"

REQUEST_DELAY    = 1.2     # secondi tra chiamate appdetails
NEW_RELEASES_DAYS = 90     # finestra temporale giochi recenti
MAX_APPLIST_RESULTS = 5000 # max app per pagina IStoreService
MAX_CANDIDATES   = 150     # max candidati da esaminare per run

# Appid minimo di partenza: salta giochi vecchi, parti dai recenti.
# StS2 (Mar 2026) = 2868840 → appid > 2.5M = ultimi ~6 mesi circa
APPID_BASELINE = 2_500_000

# Steam category IDs che indicano co-op
COOP_CATEGORY_IDS = {9, 38, 39}   # Co-op, Online Co-op, Local Co-op

# Soglie qualità per giochi senza CCU (nuovi)
MIN_REVIEWS_NEW_RELEASE = 30   # recensioni positive minime
MIN_RATING_NEW_RELEASE  = 70   # rating % minimo


class SteamNewReleasesSource:
    def __init__(self, api_key: str, delay: float = REQUEST_DELAY) -> None:
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

    def fetch_recent_appids(self, days: int = NEW_RELEASES_DAYS) -> list[int]:
        """
        Usa IStoreService/GetAppList partendo da APPID_BASELINE per trovare
        giochi recenti (appid alto = gioco nuovo). Pagina finché necessario.
        """
        cutoff_ts = int((datetime.datetime.now() - datetime.timedelta(days=days)).timestamp())
        all_appids: list[int] = []
        last_appid = APPID_BASELINE

        while True:
            params = {
                "key":              self.api_key,
                "include_games":    "1",
                "include_dlc":      "0",
                "include_software": "0",
                "include_videos":   "0",
                "include_hardware": "0",
                "last_time_modified": str(cutoff_ts),
                "last_appid":       str(last_appid),
                "max_results":      str(MAX_APPLIST_RESULTS),
            }
            data = self._get(f"{STEAM_API_BASE}/IStoreService/GetAppList/v1/", params)
            if not data:
                break
            response = data.get("response", {})
            apps = response.get("apps", [])
            if not apps:
                break

            for a in apps:
                if "appid" in a:
                    all_appids.append(a["appid"])

            have_more = response.get("have_more_results", False)
            if not have_more:
                break
            # Aggiorna il cursore per la prossima pagina
            last_appid = max(a["appid"] for a in apps if "appid" in a)
            print(f"    Pagina con {len(apps)} app, last_appid={last_appid}, continua...")

        return all_appids

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
    Usa IStoreService/GetAppList con last_appid per saltare giochi vecchi.
    Restituisce candidati con dati completi pronti per auto_update.
    """
    if not api_key:
        print("  Steam New Releases: saltato (nessun STEAM_API_KEY)")
        return []

    source = SteamNewReleasesSource(api_key)

    print(f"  Fetch app recenti da Steam API (appid > {APPID_BASELINE:,}, ultimi {NEW_RELEASES_DAYS} giorni)...")
    appids = source.fetch_recent_appids(NEW_RELEASES_DAYS)
    print(f"  App trovate (appid > {APPID_BASELINE:,}): {len(appids)}")

    if not appids:
        return []

    # Ordina per appid decrescente: appid più alti = giochi più recenti
    appids.sort(reverse=True)

    # Filtra già noti e blacklist prima delle chiamate appdetails
    to_check = [
        a for a in appids
        if str(a) not in existing_appids and str(a) not in blacklist_appids
    ][:MAX_CANDIDATES]

    print(f"  Da esaminare (non nel DB, non in blacklist): {len(to_check)}")
    if to_check:
        print(f"  Range appid: {to_check[-1]} – {to_check[0]}")

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

        # Deve avere co-op
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
