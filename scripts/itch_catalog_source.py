"""
itch_catalog_source.py
======================
Adapter per aggiungere giochi co-op da itch.io al catalogo.

Strategia:
- Feed RSS per tag (no API key, 25 giochi/pagina, paginabile)
  Usato per discovery: co-op, local-multiplayer, cooperative, split-screen
- API key itch.io (opzionale) per dettagli aggiuntivi se disponibile

I feed RSS danno molti più risultati della search API (max 10/query).
"""

from __future__ import annotations

import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from steam_catalog_source import derive_genres

# Feed RSS itch.io per tag co-op (no API key richiesta)
COOP_RSS_FEEDS = [
    "https://itch.io/games/tag-co-op.xml",
    "https://itch.io/games/tag-local-multiplayer.xml",
    "https://itch.io/games/tag-cooperative.xml",
    "https://itch.io/games/tag-split-screen.xml",
    "https://itch.io/games/tag-online-co-op.xml",
]

# Deduplicazione per coopMode in base al tag
TAG_TO_COOP_MODE = {
    "local-multiplayer": ["local"],
    "split-screen": ["local", "split"],
    "co-op": ["online", "local"],
    "cooperative": ["online", "local"],
    "online-co-op": ["online"],
}

REQUEST_DELAY = 1.0
MIN_DESC_LEN = 30


def _fetch_rss(url: str) -> list[dict[str, Any]]:
    """Fetch and parse an itch.io RSS feed. Returns list of game dicts."""
    time.sleep(REQUEST_DELAY)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/rss+xml, application/xml"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
    except Exception as exc:
        print(f"    ⚠ itch.io RSS {url[:60]}: {exc}")
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        print(f"    ⚠ itch.io RSS parse error: {exc}")
        return []

    # Estrai tag dal feed URL (es. "co-op" da tag-co-op.xml)
    tag_match = re.search(r"tag-([^/]+)\.xml", url)
    feed_tag = tag_match.group(1) if tag_match else "co-op"
    coop_modes = TAG_TO_COOP_MODE.get(feed_tag, ["online", "local"])

    games = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")

        # itch.io RSS include "[Free] [Windows] [Tag]" nel titolo — rimuoviamo
        raw_title = (title_el.text or "").strip() if title_el is not None else ""
        title = re.sub(r"\s*\[[^\]]*\]", "", raw_title).strip()
        link = (link_el.text or "").strip() if link_el is not None else ""
        raw_desc = (desc_el.text or "") if desc_el is not None else ""

        if not title or not link:
            continue

        # Pulisci descrizione HTML dal RSS
        desc = re.sub(r"<[^>]+>", "", raw_desc)
        desc = re.sub(r"\s+", " ", desc).strip()[:320]

        # Estrai immagine dal campo description HTML (itch.io la include come <img>)
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_desc)
        image = img_match.group(1) if img_match else ""

        games.append({
            "title": title,
            "itchUrl": link,
            "description": desc,
            "image": image,
            "coopModes": coop_modes,
        })

    return games


class ItchCatalogSource:
    def __init__(self, api_key: str, fetch_fn, max_games: int = 10):
        self.api_key = api_key
        self.fetch_fn = fetch_fn
        self.max_games = max_games

    def fetch_games(
        self,
        existing_itch_urls: set,
        next_id: int,
        existing_titles: set | None = None,
    ) -> list[dict]:
        """
        Fetch co-op games from itch.io RSS feeds.
        Falls back to search API if RSS returns nothing.
        """
        all_games: dict[str, dict] = {}  # url → game

        # Fase 1: RSS feed per tag (fonte principale)
        for feed_url in COOP_RSS_FEEDS:
            items = _fetch_rss(feed_url)
            for item in items:
                url = item["itchUrl"]
                if url and url not in all_games:
                    all_games[url] = item
            print(f"    RSS {feed_url.split('tag-')[1].replace('.xml','')}: {len(items)} giochi")

        # Fase 2: search API (solo se API key disponibile e RSS scarso)
        if self.api_key and len(all_games) < 20:
            print(f"    RSS scarso ({len(all_games)}), integro con search API...")
            for query in ["co-op", "cooperative multiplayer", "local co-op"]:
                url = f"https://itch.io/api/1/{self.api_key}/search/games?query={query.replace(' ', '+')}"
                data = self.fetch_fn(url) or {}
                for g in data.get("games", []):
                    gurl = g.get("url", "")
                    if gurl and gurl not in all_games:
                        short_text = (g.get("short_text") or "").strip()
                        all_games[gurl] = {
                            "title": g.get("title", ""),
                            "itchUrl": gurl,
                            "description": short_text,
                            "image": g.get("cover_url") or g.get("cover") or "",
                            "coopModes": ["online", "local"],
                        }

        # Filtra e costruisci lista finale
        added = []
        seen_titles = set(existing_titles or [])

        for game_url, info in all_games.items():
            if len(added) >= self.max_games:
                break

            title = info.get("title", "").strip()
            desc = info.get("description", "").strip()
            itch_url = info.get("itchUrl", "")

            if not title or not itch_url:
                continue
            if itch_url in existing_itch_urls:
                continue
            if title.lower().strip() in seen_titles:
                continue
            if len(desc) < MIN_DESC_LEN:
                continue

            coop_modes = info.get("coopModes", ["online", "local"])
            is_local = "local" in coop_modes or "split" in coop_modes
            cats = ["indie"]
            if is_local:
                cats.append("splitscreen")

            added.append({
                "id":             next_id,
                "igdbId":         0,
                "title":          title,
                "categories":     cats,
                "genres":         derive_genres(cats),
                "coopMode":       coop_modes,
                "maxPlayers":     4,
                "crossplay":      False,
                "players":        "2-4",
                "image":          info.get("image", ""),
                "description":    desc,
                "description_en": desc,
                "personalNote":   "",
                "played":         False,
                "steamUrl":       "",
                "gogUrl":         "",
                "epicUrl":        "",
                "itchUrl":        itch_url,
                "ccu":            0,
                "trending":       False,
                "rating":         0,
            })
            seen_titles.add(title.lower().strip())
            existing_itch_urls.add(itch_url)
            next_id += 1

        return added
