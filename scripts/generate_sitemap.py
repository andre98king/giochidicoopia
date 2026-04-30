#!/usr/bin/env python3
"""
Generate a sitemap.xml file for the coophubs.net website.

This script creates a sitemap based on the game catalog data,
which can be submitted to search engines for better SEO.
"""

import json
import pathlib
from datetime import datetime
from urllib.parse import urljoin

# Import our catalog data module
import catalog_data

# Constants
BASE_URL = "https://www.coophubs.net"
SITEMAP_PATH = pathlib.Path(__file__).parent.parent / "sitemap.xml"
PRIORITY_MAP = {
    "home": 1.0,
    "game": 0.9,
    "category": 0.8,
    "hub": 0.7,
    "other": 0.5
}
CHANGEFREQ_MAP = {
    "home": "daily",
    "game": "weekly",
    "category": "weekly",
    "hub": "monthly",
    "other": "monthly"
}

def load_games():
    """Load games using the existing catalog_data module."""
    return catalog_data.load_games()

def generate_sitemap():
    """Generate the sitemap.xml content."""
    games = load_games()
    
    # Start building the sitemap XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    
    # Add homepage
    lines.append("  <url>")
    lines.append(f"    <loc>{BASE_URL}/</loc>")
    lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
    lines.append(f"    <changefreq>{CHANGEFREQ_MAP['home']}</changefreq>")
    lines.append(f"    <priority>{PRIORITY_MAP['home']}</priority>")
    lines.append("  </url>")
    
    # Add game pages
    for game in games:
        lines.append("  <url>")
        lines.append(f"    <loc>{BASE_URL}/game/{game['slug']}/</loc>")
        lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
        lines.append(f"    <changefreq>{CHANGEFREQ_MAP['game']}</changefreq>")
        lines.append(f"    <priority>{PRIORITY_MAP['game']}</priority>")
        lines.append("  </url>")
    
    # Add category pages (unique categories)
    categories = set()
    for game in games:
        categories.update(game["categories"])
    
    for category in sorted(categories):
        # Simple slugification for category URL
        category_slug = category.lower().replace(" ", "-").replace("&", "and")
        lines.append("  <url>")
        lines.append(f"    <loc>{BASE_URL}/category/{category_slug}/</loc>")
        lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
        lines.append(f"    <changefreq>{CHANGEFREQ_MAP['category']}</changefreq>")
        lines.append(f"    <priority>{PRIORITY_MAP['category']}</priority>")
        lines.append("  </url>")
    
    # Add hub pages (coop hubs like local-coop, online-coop, etc.)
    hub_pages = [
        "local-coop",
        "online-coop", 
        "split-screen",
        "couch-coop",
        "family-games",
        "party-games",
        "retro-games",
        "indie-games"
    ]
    
    for hub in hub_pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{BASE_URL}/hub/{hub}/</loc>")
        lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
        lines.append(f"    <changefreq>{CHANGEFREQ_MAP['hub']}</changefreq>")
        lines.append(f"    <priority>{PRIORITY_MAP['hub']}</priority>")
        lines.append("  </url>")
    
    # Close the URL set
    lines.append("</urlset>")
    
    return "\n".join(lines)

def main():
    """Main function to generate and save the sitemap."""
    print("Generating sitemap for coophubs.net...")
    
    try:
        sitemap_content = generate_sitemap()
        
        # Write to file
        with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
            f.write(sitemap_content)
        
        print(f"✅ Sitemap generated successfully at {SITEMAP_PATH}")
        print(f"📊 Contains {len(load_games())} game URLs plus category and hub pages")
        
    except Exception as e:
        print(f"❌ Error generating sitemap: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())