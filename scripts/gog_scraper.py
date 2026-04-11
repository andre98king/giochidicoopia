#!/usr/bin/env python3
"""
GOG Store Scraper - Fixed version with better selectors.
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


def extract_games_from_page(html):
    """Extract games from GOG search page."""
    soup = BeautifulSoup(html, "lxml")
    games = []

    # Find product tiles
    tiles = soup.select(".product-tile")

    for tile in tiles:
        game = {}

        # Get title - look in multiple places
        title_elem = tile.select_one(".product-tile__title")
        if not title_elem:
            title_elem = tile.select_one('[class*="title"]')
        if not title_elem:
            title_elem = tile.select_one("a")

        if title_elem:
            # Clean up the text - sometimes prices/tags are concatenated
            text = title_elem.get_text(strip=True)
            # Extract game name (before any price or tag)
            match = re.match(r"^([A-Za-z0-9\s\:\-\'\.]+)", text)
            if match:
                game["title"] = match.group(1).strip()
            else:
                game["title"] = text[:50]  # fallback

        # Get price
        price_elem = tile.select_one('[class*="price"]')
        if price_elem:
            game["price"] = price_elem.get_text(strip=True)

        # Get link
        link = tile.select_one("a")
        if link:
            href = link.get("href", "")
            if "/product/" in href:
                game["url"] = f"https://www.gog.com{href}"
                game["product_id"] = href.split("/product/")[-1].split("?")[0]

        # Get discount
        discount = tile.select_one('[class*="discount"]')
        if discount:
            game["discount"] = discount.get_text(strip=True)

        if game.get("title"):
            games.append(game)

    return games


def search_coop_games(scraper, search_terms, max_pages=2):
    """Search GOG for co-op games."""
    all_games = []

    for term in search_terms:
        print(f'Searching "{term}"...')

        for page in range(1, max_pages + 1):
            url = f"https://www.gog.com/en/games"
            params = {"search": term, "page": page}

            try:
                resp = scraper.get(url, params=params, timeout=15)

                if resp.status_code != 200:
                    break

                games = extract_games_from_page(resp.text)

                if not games:
                    break

                all_games.extend(games)
                print(f"  Found {len(games)} games (page {page})")

                time.sleep(1)

            except Exception as e:
                print(f"  Error: {e}")
                break

    # Deduplicate
    seen = set()
    unique = []
    for g in all_games:
        if g["title"] not in seen:
            seen.add(g["title"])
            unique.append(g)

    return unique


def main():
    print("=== GOG Store Scraper ===")
    print()

    scraper = create_scraper()

    # Search terms
    search_terms = ["coop", "co-op", "multiplayer", "local"]

    games = search_coop_games(scraper, search_terms, max_pages=2)

    print(f"\nTotal unique games: {len(games)}")

    # Save results
    with open("data/gog_coop_games.json", "w") as f:
        json.dump(games, f, indent=2)
    print(f"Saved to data/gog_coop_games.json")

    # Show sample
    print("\nSample games:")
    for g in games[:20]:
        title = g.get("title", "N/A")[:35]
        price = g.get("price", "N/A")
        print(f"  {title} | {price}")


if __name__ == "__main__":
    main()
