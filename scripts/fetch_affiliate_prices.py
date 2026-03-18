#!/usr/bin/env python3
"""
Aggiorna igUrl/igDiscount e gbUrl/gbDiscount in games.js tramite scraping.

Siti supportati:
  - Instant Gaming  (Vue.js, richiede browser reale)
  - GameBillet      (SSR con Cloudflare, richiede browser reale)

Usa Playwright con pagine concorrenti per minimizzare il tempo totale.

Utilizzo:
    python3 scripts/fetch_affiliate_prices.py
"""
from __future__ import annotations

import asyncio
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog_data

AFFILIATE_IG = "gamer-ddc4a8"
AFFILIATE_GB = "fb308ca0-647e-4ce7-9e80-74c2c591eac1"

CONCURRENCY = 5
DELAY       = 1.2    # secondi tra batch
TIMEOUT_NAV = 18000
TIMEOUT_SEL = 8000

IG_SEARCH = "https://www.instant-gaming.com/en/search/?query={}"
GB_SEARCH = "https://www.gamebillet.com/search?q={}"
GB_BASE   = "https://www.gamebillet.com"


def _ig_affiliate(href: str) -> str:
    if not href:
        return ""
    sep = "&" if "?" in href else "?"
    return f"{href}{sep}igr={AFFILIATE_IG}"


def _gb_affiliate(slug: str) -> str:
    if not slug:
        return ""
    slug = slug.lstrip("/")
    return f"{GB_BASE}/{slug}?affiliate={AFFILIATE_GB}"


def _title_match(ig_title: str, game_title: str) -> bool:
    def clean(t: str) -> str:
        t = t.lower()
        t = re.sub(r"\s*[-–]\s*(europe|us|canada|global|row|worldwide|latam|america).*", "", t)
        t = re.sub(r"[^a-z0-9 ]", "", t)
        return t.strip()
    a, b = clean(ig_title), clean(game_title)
    return a == b or a.startswith(b) or b.startswith(a)


# ───────────────────────── Instant Gaming ─────────────────────────

async def fetch_ig(page, game: dict) -> tuple[str, int]:
    """Restituisce (igUrl, igDiscount). Stringa vuota se non trovato."""
    title = game["title"]
    try:
        await page.goto(IG_SEARCH.format(quote(title)),
                        wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        try:
            await page.wait_for_selector(".item", timeout=TIMEOUT_SEL)
        except Exception:
            return "", 0

        items = await page.evaluate("""() => {
            const out = [];
            for (const el of document.querySelectorAll('.item')) {
                const link     = el.querySelector('a.cover, a[href*="/buy-"]');
                const titleEl  = el.querySelector('.title, [class*="title"]');
                const discEl   = el.querySelector('.discount, [class*="discount"]');
                if (!link || !titleEl) continue;
                out.push({
                    href:     link.href || '',
                    title:    titleEl.textContent.trim(),
                    discount: discEl ? discEl.textContent.trim() : ''
                });
            }
            return out;
        }""")

        for item in items:
            if "steam" not in item["href"].lower():
                continue
            if not _title_match(item["title"], title):
                continue
            m = re.search(r"(\d+)", item["discount"] or "")
            discount = int(m.group(1)) if m else 0
            return _ig_affiliate(item["href"]), discount

    except Exception as e:
        print(f"  ⚠️  IG errore '{title}': {e}")
    return "", 0


# ───────────────────────── GameBillet ─────────────────────────────

async def fetch_gb(page, game: dict) -> tuple[str, int]:
    """Restituisce (gbUrl, gbDiscount). Stringa vuota se non trovato."""
    title = game["title"]
    try:
        await page.goto(GB_SEARCH.format(quote(title)),
                        wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        try:
            await page.wait_for_selector("h3 a", timeout=TIMEOUT_SEL)
        except Exception:
            return "", 0

        items = await page.evaluate("""() => {
            const out = [];
            const headings = document.querySelectorAll('h3 a');
            for (const h of headings) {
                const card     = h.closest('[class]') || h.parentElement?.parentElement;
                const saleEl   = card ? card.querySelector('a[href="#"]') : null;
                const saleText = saleEl ? saleEl.textContent.trim() : '';
                out.push({
                    href:     h.href || '',
                    title:    h.textContent.trim(),
                    saleText: saleText
                });
            }
            return out;
        }""")

        for item in items:
            if not _title_match(item["title"], title):
                continue
            # Estrai slug dall'URL assoluto (es. https://www.gamebillet.com/valheim-z → valheim-z)
            slug_match = re.search(r"gamebillet\.com/(.+)", item["href"])
            if not slug_match:
                continue
            slug = slug_match.group(1).split("?")[0]
            m = re.search(r"(\d+)", item["saleText"] or "")
            discount = int(m.group(1)) if m else 0
            return _gb_affiliate(slug), discount

    except Exception as e:
        print(f"  ⚠️  GB errore '{title}': {e}")
    return "", 0


# ───────────────────────── Runner ─────────────────────────────────

async def run() -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ playwright non installato. Esegui: pip install playwright && playwright install chromium")
        sys.exit(1)

    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()

    targets = [g for g in games if g.get("steamUrl")]
    print(f"🔍 Cerco prezzi affiliati per {len(targets)} giochi con Steam URL...")

    ig_found = gb_found = 0
    start = time.time()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        for i in range(0, len(targets), CONCURRENCY):
            batch = targets[i : i + CONCURRENCY]
            # Per ogni gioco: apri 2 pagine parallele (IG + GB)
            ig_pages = [await ctx.new_page() for _ in batch]
            gb_pages = [await ctx.new_page() for _ in batch]

            ig_results = await asyncio.gather(
                *[fetch_ig(ig_pages[j], batch[j]) for j in range(len(batch))],
                return_exceptions=True,
            )
            gb_results = await asyncio.gather(
                *[fetch_gb(gb_pages[j], batch[j]) for j in range(len(batch))],
                return_exceptions=True,
            )

            for j, game in enumerate(batch):
                ig_url, ig_disc = ig_results[j] if not isinstance(ig_results[j], Exception) else ("", 0)
                gb_url, gb_disc = gb_results[j] if not isinstance(gb_results[j], Exception) else ("", 0)

                for orig in games:
                    if orig["id"] != game["id"]:
                        continue
                    if ig_url:
                        orig["igUrl"] = ig_url
                        orig["igDiscount"] = ig_disc
                        ig_found += 1
                    if gb_url:
                        orig["gbUrl"] = gb_url
                        orig["gbDiscount"] = gb_disc
                        gb_found += 1
                    if ig_url or gb_url:
                        label = f"IG:-{ig_disc}%" if ig_url else "IG:—"
                        label += f"  GB:-{gb_disc}%" if gb_url else "  GB:—"
                        print(f"  ✓ [{game['id']}] {game['title']}: {label}")
                    break

            for p in ig_pages + gb_pages:
                await p.close()

            elapsed = time.time() - start
            done = min(i + CONCURRENCY, len(targets))
            print(f"  Progresso: {done}/{len(targets)} — {elapsed:.0f}s")
            await asyncio.sleep(DELAY)

        await ctx.close()
        await browser.close()

    print(f"\n✅ IG: {ig_found}/{len(targets)}  GB: {gb_found}/{len(targets)}")
    catalog_data.write_legacy_games_js(games, featured_id)
    catalog_data.write_catalog_artifact(games)
    catalog_data.write_public_catalog_export(games)
    print("💾 games.js aggiornato")


if __name__ == "__main__":
    asyncio.run(run())
