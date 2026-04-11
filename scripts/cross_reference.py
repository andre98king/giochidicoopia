#!/usr/bin/env python3
"""
Cross-reference Steam data with existing catalog to validate and enrich data.
"""

import json
import re
from difflib import SequenceMatcher


def load_catalog():
    """Load the games.js catalog."""
    with open("assets/games.js", "r") as f:
        content = f.read()

    # Extract games array from games.js (lowercase 'games')
    match = re.search(r"const games\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if match:
        # Replace single quotes with double quotes for valid JSON
        # But need to be careful with strings that contain quotes
        json_str = match.group(1)

        # Match keys that aren't already quoted
        def quote_key(m):
            key = m.group(1)
            return f'"{key}"'

        # Replace unquoted keys (word characters followed by colon)
        json_str = re.sub(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:", quote_key, json_str)

        # Replace single quotes around string values (not apostrophes in contractions)
        # This is tricky - let's try a simpler approach
        try:
            return json.loads(json_str)
        except:
            # Fallback: use regex to extract data manually
            games = []
            # Find all game objects
            game_pattern = r'\{[^}]*id:\s*(\d+)[^}]*title:\s*"([^"]+)"[^}]*\}'
            for m in re.finditer(game_pattern, content):
                games.append({"id": int(m.group(1)), "title": m.group(2)})
            return games

    return []


def load_steam_data():
    """Load Steam scraped data."""
    with open("data/steam_coop_games.json", "r") as f:
        return json.load(f)


def load_steam_details():
    """Load Steam detailed data."""
    with open("data/steam_coop_details.json", "r") as f:
        return json.load(f)


def normalize_title(title):
    """Normalize title for comparison."""
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def similarity(a, b):
    """Calculate title similarity."""
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def find_matches(steam_games, catalog_games):
    """Find matches between Steam games and catalog."""
    matches = []
    no_matches = []

    for steam in steam_games:
        best_match = None
        best_score = 0

        for cat in catalog_games:
            score = similarity(steam["title"], cat["title"])
            if score > best_score and score >= 0.6:  # 60% threshold
                best_score = score
                best_match = cat

        if best_match:
            matches.append({"steam": steam, "catalog": best_match, "score": best_score})
        else:
            no_matches.append(steam)

    return matches, no_matches


def analyze_gaps(steam_games, catalog_games):
    """Identify gaps in catalog based on Steam data."""
    catalog_titles = {normalize_title(g["title"]) for g in catalog_games}

    # Extract app IDs from catalog
    catalog_steam_ids = {}
    for g in catalog_games:
        if g.get("steamUrl"):
            match = re.search(r"/app/(\d+)", g["steamUrl"])
            if match:
                catalog_steam_ids[match.group(1)] = g

    gaps = {
        "missing_from_catalog": [],  # Steam games not in catalog
        "missing_steam_link": [],  # Catalog games without Steam link
        "potential_enrichment": [],  # Games where Steam has more data
    }

    for steam in steam_games:
        norm_title = normalize_title(steam["title"])

        # Check if title exists in catalog (fuzzy)
        found = False
        for cat in catalog_games:
            if similarity(steam["title"], cat["title"]) >= 0.7:
                found = True
                # Check if has Steam URL
                if not cat.get("steamUrl"):
                    gaps["missing_steam_link"].append(
                        {"steam": steam, "catalog_title": cat["title"]}
                    )
                break

        if not found:
            # Could be a new game to add
            if steam.get("app_id"):
                gaps["missing_from_catalog"].append(steam)

    # Check catalog games missing Steam links
    for cat in catalog_games:
        if cat.get("steamUrl") is None and cat.get("title"):
            # Could potentially find on Steam
            gaps["potential_enrichment"].append(cat)

    return gaps


def main():
    print("Cross-reference Analysis: Steam vs Catalog")
    print("=" * 50)

    # Load data
    catalog = load_catalog()
    steam_games = load_steam_data()
    steam_details = load_steam_details()

    print(f"Catalog games: {len(catalog)}")
    print(f"Steam games: {len(steam_games)}")
    print(f"Steam with details: {len(steam_details)}")

    # Find matches
    print("\n--- Finding Matches ---")
    matches, no_matches = find_matches(steam_games, catalog)

    print(f"Matched: {len(matches)}")
    print(f"Not in catalog: {len(no_matches)}")

    # Analyze gaps
    print("\n--- Gap Analysis ---")
    gaps = analyze_gaps(steam_games, catalog)

    print(f"Missing from catalog: {len(gaps['missing_from_catalog'])}")
    print(f"Missing Steam link in catalog: {len(gaps['missing_steam_link'])}")
    print(f"Potential enrichment: {len(gaps['potential_enrichment'])}")

    # Show some examples
    print("\n--- Sample Missing from Catalog (new games) ---")
    for g in gaps["missing_from_catalog"][:10]:
        print(f"  {g['title'][:50]} (ID: {g['app_id']}) - {g.get('price', 'N/A')}")

    print("\n--- Sample Missing Steam Link ---")
    for g in gaps["missing_steam_link"][:5]:
        print(f"  {g['catalog_title'][:40]} -> Steam ID: {g['steam'].get('app_id')}")

    # Save results
    results = {
        "summary": {
            "catalog_count": len(catalog),
            "steam_count": len(steam_games),
            "matched": len(matches),
            "missing": len(no_matches),
        },
        "matches": matches[:20],  # Top 20 matches
        "no_matches": no_matches[:50],  # Top 50 not in catalog
        "gaps": {
            "missing_from_catalog": gaps["missing_from_catalog"][:50],
            "missing_steam_link": gaps["missing_steam_link"][:20],
        },
    }

    with open("data/cross_reference_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved results to data/cross_reference_results.json")


if __name__ == "__main__":
    main()
