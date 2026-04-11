#!/usr/bin/env python3
"""
Multi-source cross-reference: Catalog + Steam + IGDB + RAWG + GOG

Cross-validate game data from multiple sources to improve quality.
"""

import json
import re
import os
from difflib import SequenceMatcher


def parse_catalog():
    """Parse games.js to extract basic info."""
    with open("assets/games.js", "r") as f:
        content = f.read()

    games = []
    pattern = r'id:\s*(\d+),\s*\n\s*igdbId:\s*\d+,\s*\n\s*title:\s*"([^"]+)"'

    for m in re.finditer(pattern, content):
        games.append({"id": int(m.group(1)), "title": m.group(2)})

    return games


def load_steam_data():
    with open("data/steam_coop_games.json", "r") as f:
        return json.load(f)


def load_igdb_data():
    with open("data/igdb_coop_games.json", "r") as f:
        return json.load(f)


def load_rawg_data():
    with open("data/rawg_coop_games.json", "r") as f:
        return json.load(f)


def load_gog_data():
    with open("data/gog_coop_games.json", "r") as f:
        return json.load(f)


def normalize_title(title):
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def similarity(a, b):
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def find_matches(sources, catalog):
    results = []

    for source_name, source_data in sources.items():
        source_matches = []
        no_matches = []

        for item in source_data:
            title = item.get("name") or item.get("title", "")
            if not title:
                continue

            best_match = None
            best_score = 0

            for cat in catalog:
                score = similarity(title, cat["title"])
                if score > best_score and score >= 0.6:
                    best_score = score
                    best_match = cat

            if best_match:
                source_matches.append(
                    {
                        "source": source_name,
                        "source_title": title,
                        "catalog_title": best_match["title"],
                        "catalog_id": best_match["id"],
                        "score": best_score,
                        "data": item,
                    }
                )
            else:
                no_matches.append({"source": source_name, "title": title, "data": item})

        results.append(
            {"source": source_name, "matched": source_matches, "no_match": no_matches}
        )

    return results


def main():
    print("=" * 60)
    print("MULTI-SOURCE CROSS-REFERENCE")
    print("=" * 60)
    print()

    print("Loading data sources...")
    catalog = parse_catalog()
    print(f"  Catalog: {len(catalog)} games")

    steam = load_steam_data()
    print(f"  Steam: {len(steam)} games")

    igdb = load_igdb_data()
    print(f"  IGDB: {len(igdb)} games")

    rawg = load_rawg_data()
    print(f"  RAWG: {len(rawg)} games")

    gog = load_gog_data()
    print(f"  GOG: {len(gog)} games")
    print()

    sources = {"steam": steam, "igdb": igdb, "rawg": rawg, "gog": gog}
    results = find_matches(sources, catalog)

    print("CROSS-REFERENCE RESULTS")
    print("-" * 40)

    total_matched = 0
    total_no_match = 0

    for r in results:
        matched = len(r["matched"])
        no_match = len(r["no_match"])
        total_matched += matched
        total_no_match += no_match

        print(f"{r['source'].upper()}:")
        print(f"  Matched: {matched}")
        print(f"  Not in catalog: {no_match}")
        print()

    print(f"TOTAL: {total_matched} matched, {total_no_match} not in catalog")
    print()

    # Collect new games
    all_new_games = []
    for r in results:
        for nm in r["no_match"]:
            all_new_games.append(
                {"source": nm["source"], "title": nm["title"], "data": nm["data"]}
            )

    # Deduplicate
    seen = set()
    unique_new = []
    for g in all_new_games:
        norm = normalize_title(g["title"])
        if norm not in seen:
            seen.add(norm)
            unique_new.append(g)

    print(f"Potential new games to add: {len(unique_new)}")

    output = {
        "summary": {
            "catalog_size": len(catalog),
            "steam_count": len(steam),
            "igdb_count": len(igdb),
            "rawg_count": len(rawg),
            "gog_count": len(gog),
            "total_matched": total_matched,
            "total_new": total_no_match,
        },
        "matched_by_source": results,
        "potential_new_games": unique_new,
    }

    with open("data/multi_cross_reference.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to data/multi_cross_reference.json")

    print("\nSample NEW GAMES:")
    for g in unique_new[:10]:
        print(f"  [{g['source']}] {g['title'][:40]}")


if __name__ == "__main__":
    main()
