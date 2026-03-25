#!/usr/bin/env python3
"""
Shared Steam/SteamSpy adapter helpers for catalog ingestion.

This module keeps the source-specific HTTP and parsing logic in one place so
the update pipeline can evolve toward multiple adapters without duplicating
network helpers across scripts.
"""

from __future__ import annotations

import html as html_mod
import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


DEFAULT_USER_AGENT = "Mozilla/5.0"
DEFAULT_TIMEOUT_SECONDS = 15

GENRE_CATS = {
    "horror",
    "action",
    "puzzle",
    "rpg",
    "survival",
    "factory",
    "roguelike",
    "sport",
    "strategy",
}


class SteamCatalogSource:
    def __init__(
        self,
        delay: float = 1.5,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.delay = delay
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch_json(self, url: str) -> Any | None:
        time.sleep(self.delay)

        @retry(
            retry=retry_if_exception_type((urllib.error.URLError, TimeoutError, OSError)),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            stop=stop_after_attempt(3),
            reraise=False,
        )
        def _do_request() -> Any:
            request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))

        try:
            return _do_request()
        except Exception as exc:
            print(f"    ⚠ ERR {url[:70]}: {exc}")
            return None

    def fetch_steam_desc(self, appid: str, lang: str) -> tuple[dict[str, Any] | None, str | None]:
        cc = "it" if lang == "italian" else "us"
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={lang}&cc={cc}"
        data = self.fetch_json(url)
        if not data:
            return None, None
        info = data.get(str(appid), {})
        if not info.get("success"):
            return None, None
        steam_data = info.get("data", {})
        description = clean_text(steam_data.get("short_description", ""))
        if not description or len(description) < 25:
            description = clean_text(steam_data.get("detailed_description", ""))[:320]
        return steam_data, description if len(description) >= 25 else None


def parse_release_year(release_date: dict | None) -> int:
    """Extract year from Steam release_date dict, e.g. {'coming_soon': False, 'date': 'Feb 8, 2018'} → 2018."""
    if not release_date or release_date.get("coming_soon"):
        return 0
    date_str = release_date.get("date", "")
    if not date_str:
        return 0
    match = re.search(r"\b((?:19|20)\d{2})\b", date_str)
    return int(match.group(1)) if match else 0


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:320]


def appid_from_url(url: str) -> str:
    match = re.search(r"/app/(\d+)", url or "")
    return match.group(1) if match else ""


def calc_rating(positive: int | None, negative: int | None) -> int:
    total = (positive or 0) + (negative or 0)
    if total < 10:
        return 0
    return round((positive or 0) / total * 100)


def derive_genres(categories: list[str]) -> list[str]:
    return [category for category in categories if category in GENRE_CATS]


def derive_coop_modes(steam_categories: list[str]) -> list[str]:
    modes = []
    has_online = any("online" in category and ("co-op" in category or "multi" in category) for category in steam_categories)
    has_local = any(
        ("local" in category and ("co-op" in category or "multi" in category)) or "couch" in category
        for category in steam_categories
    )
    has_split = any("split" in category for category in steam_categories)
    if has_online or (not has_local and not has_split):
        modes.append("online")
    if has_local or has_split:
        modes.append("local")
    if has_split:
        modes.append("split")
    return modes if modes else ["online"]


def derive_crossplay(steam_categories: list[str]) -> bool:
    return any("cross-platform" in category for category in steam_categories)


def parse_max_players(players_label: str) -> int:
    if not players_label:
        return 4
    numbers = re.findall(r"\d+", players_label)
    return max(int(number) for number in numbers) if numbers else 4


def derive_players_label(steam_categories: list[str], default: str = "1-4") -> str:
    for category in steam_categories:
        match = re.search(r"(\d+)", category)
        if match and "player" in category.lower():
            players = int(match.group(1))
            return f"1-{players}" if players > 1 else "1-2"
    return default
