#!/usr/bin/env python3
"""
Co-optimus scraper - FINAL VERSION

Testing Summary (2026-04-01):
- cloudscraper: WORKS (bypasses Cloudflare on main pages)
- AJAX endpoint /ajax/ajax_games.php: BLOCKED (403 + Cloudflare)
- Individual game pages /game/ID: 404 (not accessible)
- Direct scraping: NOT POSSIBLE with current methods

This script documents what we tried and serves as reference.
"""

import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import time


def create_scraper():
    """Create a configured cloudscraper session."""
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )


def test_main_pages(scraper):
    """Test which main pages are accessible."""
    print("\n=== Testing Main Pages ===")

    pages = [
        ("/index.php", "Home"),
        ("/games.php", "All Games"),
        ("/games.php?system=4", "PC Games"),
        ("/games.php?alltime=true", "Top Rated"),
        ("/games.php?newadditions=true", "New Additions"),
        ("/reviews.php", "Reviews"),
    ]

    results = {}
    for path, name in pages:
        try:
            resp = scraper.get(f"https://www.co-optimus.com{path}", timeout=15)
            results[name] = (resp.status_code, len(resp.text))
            print(f"{name}: {resp.status_code} ({len(resp.text)} bytes)")
        except Exception as e:
            results[name] = (str(e), 0)
            print(f"{name}: ERROR - {e}")

    return results


def test_ajax_endpoints(scraper):
    """Test AJAX endpoints."""
    print("\n=== Testing AJAX Endpoints ===")

    endpoints = [
        ("/ajax/ajax_games.php?system=4", "Games list"),
        ("/ajax/ajax_gameInfo.php?id=1", "Game info"),
        ("/ajax/ajax_classic_games.php", "Classic games"),
    ]

    results = {}
    for path, name in endpoints:
        try:
            resp = scraper.get(f"https://www.co-optimus.com{path}", timeout=15)
            results[name] = (resp.status_code, len(resp.text))
            print(f"{name}: {resp.status_code} ({len(resp.text)} bytes)")
            if resp.status_code == 200:
                print(f"  Content: {resp.text[:100]}...")
        except Exception as e:
            results[name] = (str(e), 0)
            print(f"{name}: ERROR - {e}")

    return results


def test_game_ids(scraper):
    """Test individual game pages."""
    print("\n=== Testing Game Pages ===")

    for game_id in [1, 10, 50, 100, 2948]:
        try:
            resp = scraper.get(f"https://www.co-optimus.com/game/{game_id}", timeout=10)
            title_match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE)
            title = title_match.group(1) if title_match else "No title"
            print(f"Game {game_id}: {resp.status_code} - {title[:60]}")
        except Exception as e:
            print(f"Game {game_id}: ERROR - {e}")


def test_search(scraper):
    """Test search functionality."""
    print("\n=== Testing Search ===")

    queries = ["portal", "left 4 dead", "borderlands", "diablo"]

    for query in queries:
        url = f"https://www.co-optimus.com/search.php?q={query}"
        try:
            resp = scraper.get(url, timeout=10)
            has_results = "result_row" in resp.text
            print(
                f"Search '{query}': {resp.status_code} ({len(resp.text)} bytes, results: {has_results})"
            )
        except Exception as e:
            print(f"Search '{query}': ERROR - {e}")


def analyze_page_structure(scraper):
    """Analyze a page to find any game data patterns."""
    print("\n=== Analyzing Page Structure ===")

    resp = scraper.get("https://www.co-optimus.com/games.php?system=4")
    soup = BeautifulSoup(resp.text, "lxml")

    # Check for any embedded data
    scripts = soup.find_all("script")
    print(f"Total scripts: {len(scripts)}")

    for s in scripts:
        txt = s.string or ""
        if "result_row" in txt or "gameData" in txt or "games =" in txt[:100]:
            print(f"  Found script with potential game data")
            print(f"  Content preview: {txt[:200]}")
            break

    # Check for any data attributes
    data_elements = soup.find_all(attrs={"data-game": True})
    print(f"Elements with data-game: {len(data_elements)}")

    return soup


def test_rss_feed(scraper):
    """Test RSS feed for game data."""
    print("\n=== Testing RSS Feed ===")

    try:
        resp = scraper.get("https://feeds.feedburner.com/Co-optimus", timeout=10)
        print(f"RSS status: {resp.status_code} ({len(resp.text)} bytes)")

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")
            print(f"RSS items: {len(items)}")

            # Check for game-related items
            game_items = [i for i in items if "game" in i.get_text().lower()[:100]]
            print(f"Game-related items: {len(game_items)}")
    except Exception as e:
        print(f"RSS error: {e}")


def main():
    print("Co-optimus Scraper - Diagnostic Tool")
    print("=" * 50)

    scraper = create_scraper()

    # Run all tests
    test_main_pages(scraper)
    test_ajax_endpoints(scraper)
    test_game_ids(scraper)
    test_search(scraper)
    analyze_page_structure(scraper)
    test_rss_feed(scraper)

    print("\n" + "=" * 50)
    print("CONCLUSION:")
    print("- Main pages: Accessible via cloudscraper")
    print("- AJAX data: BLOCKED (403 + Cloudflare)")
    print("- Individual games: Not accessible")
    print("- Alternative sources needed for game data")


if __name__ == "__main__":
    main()
