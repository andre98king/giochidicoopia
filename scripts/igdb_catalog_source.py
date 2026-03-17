#!/usr/bin/env python3
"""
IGDB catalog source adapter.

Uses the IGDB API (Twitch OAuth) to enrich the catalog with structured
multiplayer data: onlinecoopmax, offlinecoopmax, splitscreen, lancoop.

IGDB is the only public source with `multiplayer_modes` as structured fields,
so it provides the ground truth for maxPlayers and coopMode.

Requires env vars (or GitHub Secrets):
    IGDB_CLIENT_ID      — Twitch app Client ID
    IGDB_CLIENT_SECRET  — Twitch app Client Secret

Register at: https://dev.twitch.tv/console → Register Your Application
Then use the credentials here and as GitHub Secrets in the repo.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
IGDB_BASE_URL = "https://api.igdb.com/v4"

# external_games.category = 1 → Steam
IGDB_STEAM_CATEGORY = 1

# IGDB rate limit: 4 req/sec → 0.26s minimum; use 0.35 for safety
REQUEST_DELAY = 0.35

# How many Steam App IDs to resolve per API call (max 500, keep low)
BATCH_SIZE = 20


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

    # ─────────────── API helpers ───────────────

    def fetch_appid_to_igdb_id(self, appids: list[str]) -> dict[str, int]:
        """Resolve Steam App IDs → IGDB game IDs in one batch call."""
        quoted = ", ".join(f'"{aid}"' for aid in appids)
        query = (
            f"fields uid, game; "
            f"where uid = ({quoted}) & category = {IGDB_STEAM_CATEGORY}; "
            f"limit {len(appids)};"
        )
        results = self._post("external_games", query) or []
        return {
            item["uid"]: item["game"]
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

    # ─────────────── Public interface ───────────────

    def enrich_catalog(self, games: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Given the full list of game records, queries IGDB and returns:
          {steam_appid: {"maxPlayers": int, "coopMode": list[str]}}

        Only entries with actual IGDB multiplayer data are included.
        crossplay is NOT included — IGDB doesn't have reliable crossplay data.
        """
        from steam_catalog_source import appid_from_url  # local import to avoid circular deps

        # Build index of appid → game
        appid_list = []
        for g in games:
            aid = appid_from_url(g.get("steamUrl", ""))
            if aid:
                appid_list.append(aid)

        if not appid_list:
            return {}

        enrichment: dict[str, dict[str, Any]] = {}

        for i in range(0, len(appid_list), BATCH_SIZE):
            batch = appid_list[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(appid_list) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"    IGDB batch {batch_num}/{total_batches} ({len(batch)} app IDs)...", end=" ", flush=True)

            # Step 1: resolve Steam App IDs → IGDB game IDs
            appid_to_igdb = self.fetch_appid_to_igdb_id(batch)
            if not appid_to_igdb:
                print("nessun match")
                continue

            # Step 2: fetch multiplayer_modes
            igdb_ids = list(set(appid_to_igdb.values()))
            igdb_to_modes = self.fetch_multiplayer_modes(igdb_ids)

            # Step 3: build enrichment per appid
            found = 0
            for aid, igdb_id in appid_to_igdb.items():
                modes_list = igdb_to_modes.get(igdb_id, [])
                parsed = _parse_multiplayer_modes(modes_list)
                if parsed:
                    enrichment[aid] = parsed
                    found += 1

            print(f"{found}/{len(appid_to_igdb)} con dati multiplayer")

        return enrichment


# ─────────────── Parsing helpers ───────────────

def _parse_multiplayer_modes(modes_list: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Converts IGDB multiplayer_modes array into our catalog fields.
    Returns None if there's no useful co-op data.
    """
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
        max_players = 0  # 0 = unknown, let the existing value stay

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
    Enriches games in-place with IGDB multiplayer data.
    Only overwrites maxPlayers when IGDB provides a value > 1.
    Always overwrites coopMode when IGDB has data (it's the authoritative source).

    Returns the number of games enriched.
    """
    from steam_catalog_source import appid_from_url

    print("  Autenticazione IGDB (Twitch OAuth)...")
    source = IgdbCatalogSource(client_id, client_secret)

    # Verify credentials work before processing
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

        # coopMode: IGDB è la fonte più affidabile — sovrascriviamo sempre
        if data.get("coopMode"):
            g["coopMode"] = data["coopMode"]

        # maxPlayers: sovrascriviamo solo se IGDB ha un valore reale (>1)
        igdb_max = data.get("maxPlayers", 0)
        if igdb_max > 1:
            g["maxPlayers"] = igdb_max
            # Aggiorna anche il label players se era il valore di default
            current_players = g.get("players", "1-4")
            if current_players in ("1-4", "2-4", "1-2", ""):
                g["players"] = f"1-{igdb_max}"

        enriched += 1

    return enriched
