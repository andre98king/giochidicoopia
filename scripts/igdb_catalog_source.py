#!/usr/bin/env python3
"""
IGDB catalog source adapter.

Funzioni:
1. ENRICHMENT  — arricchisce i giochi esistenti con multiplayer_modes strutturati
                 (onlinecoopmax, offlinecoopmax, splitscreen, lancoop) e salva igdbId.
2. DISCOVERY   — trova nuovi giochi co-op PC non ancora nel catalogo.

IGDB è la fonte canonica per deduplicazione cross-platform: ogni gioco ha un igdbId
univoco che collega Steam, GOG, Epic e altri store.

Credenziali (env var / GitHub Secrets):
    IGDB_CLIENT_ID      — Twitch app Client ID
    IGDB_CLIENT_SECRET  — Twitch app Client Secret

Registrazione: https://dev.twitch.tv/console → Register Your Application
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any


TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_BASE_URL = "https://api.igdb.com/v4"

# external_games.category = 1 → Steam, 5 → GOG
IGDB_STEAM_CATEGORY = 1
IGDB_GOG_CATEGORY = 5

# IGDB platform IDs
IGDB_PC_PLATFORM = 6       # PC (Windows)
IGDB_MAC_PLATFORM = 14
IGDB_LINUX_PLATFORM = 3

# IGDB game_modes: 1=Single player, 2=Multiplayer, 3=Co-operative, 4=Split screen, 5=MMO
IGDB_COOP_MODE = 3

# IGDB category: 0=main_game, 8=remake, 9=remaster (exclude DLC, expansion, etc.)
IGDB_MAIN_GAME_CATEGORIES = (0, 8, 9)

# Rate limit: 4 req/sec → 0.35s safe margin
REQUEST_DELAY = 0.35

# Batch sizes
APPID_BATCH_SIZE = 20
DISCOVERY_BATCH_SIZE = 10   # smaller for discovery (heavier queries)
DISCOVERY_LIMIT = 500       # max IGDB games to scan per run
DISCOVERY_MIN_RATING = 55   # IGDB rating (0-100) minimo — soglia bassa perché
                             # filtriamo ulteriormente con Steam reviews in auto_update


class IgdbCatalogSource:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None

    # ─────────────── Authentication ───────────────

    def _authenticate(self) -> str:
        url = (
            f"{TWITCH_TOKEN_URL}"
            f"?client_id={self.client_id}"
            f"&client_secret={self.client_secret}"
            f"&grant_type=client_credentials"
        )
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data["access_token"]

    @property
    def token(self) -> str:
        if not self._token:
            self._token = self._authenticate()
        return self._token

    # ─────────────── Low-level HTTP ───────────────

    def _post(self, endpoint: str, query: str) -> list[dict[str, Any]] | None:
        time.sleep(REQUEST_DELAY)
        url = f"{IGDB_BASE_URL}/{endpoint}"
        req = urllib.request.Request(
            url,
            data=query.encode("utf-8"),
            headers={
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "text/plain",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            print(f"    ⚠ IGDB {endpoint} HTTP {exc.code}: {exc.reason}")
            return None
        except Exception as exc:
            print(f"    ⚠ IGDB {endpoint}: {exc}")
            return None

    # ─────────────── Enrichment queries ───────────────

    def fetch_appid_to_igdb_id(self, appids: list[str]) -> dict[str, int]:
        """Resolve Steam App IDs → IGDB game IDs.

        Tenta prima con uid come interi (non quotati), poi come stringhe.
        IGDB non è consistente sulla rappresentazione interna.
        """
        # uid va come intero (non quotato) e senza filtro category:
        # il campo category in IGDB external_games per Steam è spesso null/0,
        # quindi category=1 esclude tutti i risultati.
        uid_values = ", ".join(appids)
        query = (
            f"fields uid, game; "
            f"where uid = ({uid_values}); "
            f"limit {len(appids) * 3};"
        )
        results = self._post("external_games", query) or []
        return {
            str(item["uid"]): item["game"]
            for item in results
            if "uid" in item and "game" in item
        }

    def fetch_multiplayer_modes(self, igdb_ids: list[int]) -> dict[int, list[dict]]:
        """Fetch multiplayer_modes for a list of IGDB game IDs."""
        ids_str = ", ".join(str(i) for i in igdb_ids)
        query = (
            "fields id, "
            "multiplayer_modes.onlinecoop, multiplayer_modes.onlinecoopmax, "
            "multiplayer_modes.offlinecoop, multiplayer_modes.offlinecoopmax, "
            "multiplayer_modes.splitscreen, multiplayer_modes.lancoop, "
            "multiplayer_modes.dropin; "
            f"where id = ({ids_str}); "
            f"limit {len(igdb_ids)};"
        )
        results = self._post("games", query) or []
        return {
            item["id"]: item.get("multiplayer_modes") or []
            for item in results
            if "id" in item
        }

    def enrich_catalog(self, games: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Returns {steam_appid: {maxPlayers, coopMode, igdbId}} for games with IGDB data.
        """
        from steam_catalog_source import appid_from_url

        appid_list = [
            appid_from_url(g.get("steamUrl", ""))
            for g in games
            if appid_from_url(g.get("steamUrl", ""))
        ]

        enrichment: dict[str, dict[str, Any]] = {}

        for i in range(0, len(appid_list), APPID_BATCH_SIZE):
            batch = appid_list[i : i + APPID_BATCH_SIZE]
            batch_num = i // APPID_BATCH_SIZE + 1
            total = (len(appid_list) + APPID_BATCH_SIZE - 1) // APPID_BATCH_SIZE
            print(f"    IGDB enrichment {batch_num}/{total} ({len(batch)} IDs)...", end=" ", flush=True)

            appid_to_igdb = self.fetch_appid_to_igdb_id(batch)
            if not appid_to_igdb:
                print("nessun match")
                continue

            igdb_ids = list(set(appid_to_igdb.values()))
            igdb_to_modes = self.fetch_multiplayer_modes(igdb_ids)

            found = 0
            for aid, igdb_id in appid_to_igdb.items():
                modes_list = igdb_to_modes.get(igdb_id, [])
                parsed = _parse_multiplayer_modes(modes_list)
                entry: dict[str, Any] = {"igdbId": igdb_id}
                if parsed:
                    entry.update(parsed)
                    found += 1
                enrichment[aid] = entry

            print(f"{found}/{len(appid_to_igdb)} con multiplayer_modes")

        return enrichment

    # ─────────────── Discovery queries ───────────────

    def discover_coop_games(
        self,
        existing_igdb_ids: set[int],
        existing_steam_appids: set[str],
        existing_titles: set[str],
        max_games: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Query IGDB for co-op PC games not already in the catalog.
        Returns a list of raw candidates ready for further enrichment.
        Each candidate has: igdbId, title, steamAppId (if any), gogId (if any),
        coopMode, maxPlayers, rating.
        """
        candidates: list[dict[str, Any]] = []
        offset = 0

        while len(candidates) < max_games and offset < DISCOVERY_LIMIT:
            batch_size = min(DISCOVERY_BATCH_SIZE, DISCOVERY_LIMIT - offset)
            print(f"    IGDB discovery offset={offset}...", end=" ", flush=True)

            # Query: co-op PC games sorted by rating desc
            # Nota: category filter rimosso (molti giochi non hanno category set in IGDB)
            query = (
                "fields id, name, rating, rating_count, "
                "game_modes, platforms, "
                "external_games.uid, external_games.category; "
                f"where game_modes = ({IGDB_COOP_MODE}) "
                f"& platforms = ({IGDB_PC_PLATFORM}) "
                f"& rating != null "
                f"& rating_count > 5; "
                f"sort rating desc; "
                f"limit {batch_size}; "
                f"offset {offset};"
            )
            results = self._post("games", query) or []

            if not results:
                print("fine risultati")
                break

            new_in_batch = 0
            for item in results:
                igdb_id = item.get("id")
                title = item.get("name", "")
                rating = item.get("rating") or 0

                if not igdb_id or not title:
                    continue

                # Deduplication checks
                if igdb_id in existing_igdb_ids:
                    continue
                if title.lower().strip() in existing_titles:
                    continue

                # Extract external IDs
                steam_appid = None
                gog_id = None
                for ext in item.get("external_games") or []:
                    cat = ext.get("category")
                    uid = ext.get("uid", "")
                    if cat == IGDB_STEAM_CATEGORY and uid.isdigit():
                        steam_appid = uid
                    elif cat == IGDB_GOG_CATEGORY and uid:
                        gog_id = uid

                # Skip if Steam App ID already in catalog
                if steam_appid and steam_appid in existing_steam_appids:
                    continue

                # Quality filter
                if rating > 0 and rating < DISCOVERY_MIN_RATING:
                    continue

                candidates.append({
                    "igdbId": igdb_id,
                    "title": title,
                    "rating_igdb": round(rating),
                    "steamAppId": steam_appid,
                    "gogId": gog_id,
                })
                existing_igdb_ids.add(igdb_id)
                new_in_batch += 1

                if len(candidates) >= max_games:
                    break

            print(f"{new_in_batch} nuovi candidati (tot: {len(candidates)})")
            offset += batch_size

            if len(results) < batch_size:
                break  # no more pages

        return candidates


# ─────────────── Parsing helpers ───────────────

def _parse_multiplayer_modes(modes_list: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not modes_list:
        return None

    online_max = 0
    offline_max = 0
    has_online = False
    has_offline = False
    has_split = False
    has_lan = False

    for mode in modes_list:
        if not isinstance(mode, dict):
            continue
        if mode.get("onlinecoop"):
            has_online = True
        if mode.get("offlinecoop"):
            has_offline = True
        if mode.get("splitscreen"):
            has_split = True
        if mode.get("lancoop"):
            has_lan = True
        online_max = max(online_max, mode.get("onlinecoopmax") or 0)
        offline_max = max(offline_max, mode.get("offlinecoopmax") or 0)

    if not (has_online or has_offline or has_split or has_lan):
        return None

    coop_modes: list[str] = []
    if has_online:
        coop_modes.append("online")
    if has_offline or has_split or has_lan:
        coop_modes.append("local")
    if has_split:
        coop_modes.append("split")
    if not coop_modes:
        coop_modes = ["online"]

    max_players = max(online_max, offline_max)
    if max_players <= 1:
        max_players = 0

    return {
        "maxPlayers": max_players,
        "coopMode": coop_modes,
    }


# ─────────────── Pipeline integration ───────────────

def enrich_games_with_igdb(
    games: list[dict[str, Any]],
    client_id: str,
    client_secret: str,
) -> int:
    """
    Enriches games in-place: coopMode, maxPlayers, igdbId.
    Returns number of games enriched.
    """
    from steam_catalog_source import appid_from_url

    print("  Autenticazione IGDB (Twitch OAuth)...")
    source = IgdbCatalogSource(client_id, client_secret)
    try:
        _ = source.token
        print("  ✓ Token ottenuto")
    except Exception as exc:
        print(f"  ⛔ Autenticazione IGDB fallita: {exc}")
        return 0

    enrichment = source.enrich_catalog(games)
    if not enrichment:
        print("  Nessun dato IGDB trovato")
        return 0

    enriched = 0
    for g in games:
        aid = appid_from_url(g.get("steamUrl", ""))
        if not aid or aid not in enrichment:
            continue
        data = enrichment[aid]

        # Salva igdbId per deduplicazione futura
        if data.get("igdbId") and not g.get("igdbId"):
            g["igdbId"] = data["igdbId"]

        # coopMode: IGDB è la fonte più affidabile
        if data.get("coopMode"):
            g["coopMode"] = data["coopMode"]

        # maxPlayers: solo se IGDB ha un valore reale
        igdb_max = data.get("maxPlayers", 0)
        if igdb_max > 1:
            g["maxPlayers"] = igdb_max
            current_players = g.get("players", "1-4")
            if current_players in ("1-4", "2-4", "1-2", ""):
                g["players"] = f"1-{igdb_max}"

        enriched += 1

    return enriched
