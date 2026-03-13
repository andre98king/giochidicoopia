# 🎮 Co-op Games Hub

A static website cataloguing the best PC co-op games, with automatic weekly updates.

**[→ Visit the site](https://coophubs.net)**

## Features

- **300+ co-op games** organized by category (Horror, Action, Puzzle, Splitscreen, RPG, Survival, Factory, Roguelike, Sport, Strategy)
- **Bilingual UI** — switch between Italian and English
- **Steam ratings** — color-coded review scores (Overwhelmingly Positive → Negative)
- **Live player counts** — trending badge for games with active communities
- **Random game wheel** — can't decide? let the wheel choose
- **Search & filters** — filter by category, sort by rating, popularity or A→Z
- **Admin mode** — password-protected panel to mark games as played and add personal notes

## Auto-update

Every Monday, a GitHub Actions workflow runs `auto_update.py` and `build_static_pages.py`, which:
1. Updates player counts (CCU) and trending status
2. Refreshes Steam review ratings
3. Adds up to 15 new trending co-op games (with IT + EN descriptions)
4. Regenerates static SEO-friendly game pages in `games/`
5. Updates `sitemap.xml`
6. Commits the updated files automatically

## Tech stack

- Pure HTML / CSS / JavaScript — no framework, no build step
- Python 3 scripts for data fetching (SteamSpy API + Steam Store API)
- GitHub Actions for scheduled updates
- GitHub Pages for hosting

## Local development

```bash
git clone https://github.com/andre98king/giochidicoopia.git
cd giochidicoopia
python3 -m http.server 8080
# open http://localhost:8080
```

## Manual database update

```bash
python3 auto_update.py
python3 build_static_pages.py
```
