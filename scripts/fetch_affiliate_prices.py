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

IG_CONCURRENCY = 8   # pagine IG simultanee
GB_CONCURRENCY = 5   # pagine GB simultanee
STAGGER        = 0.15  # secondi tra lancio task (anti-burst)
TIMEOUT_NAV    = 15000
TIMEOUT_SEL    = 6000

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
        # Step 1: trova URL prodotto (usa igUrl esistente o cerca)
        product_url = ""
        existing_ig = game.get("igUrl", "")
        if existing_ig:
            # Rimuovi parametro affiliato per ottenere URL pulito
            product_url = re.sub(r"[?&]igr=[^&]*", "", existing_ig)
        else:
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
                    if (!link || !titleEl) continue;
                    out.push({
                        href:  link.href || '',
                        title: titleEl.textContent.trim()
                    });
                }
                return out;
            }""")

            for item in items:
                if "steam" not in item["href"].lower():
                    continue
                if not _title_match(item["title"], title):
                    continue
                product_url = item["href"]
                break

        if not product_url:
            return "", 0

        # Step 2: visita pagina prodotto per estrarre lo sconto reale
        await page.goto(product_url,
                        wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        discount = await page.evaluate("""() => {
            const el = document.querySelector('.discounted');
            if (!el) return 0;
            const m = el.textContent.match(/(\\d+)/);
            return m ? parseInt(m[1]) : 0;
        }""")

        return _ig_affiliate(product_url), discount

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

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36"
)


async def run() -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ playwright non installato. Esegui: pip install playwright && playwright install chromium")
        sys.exit(1)

    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()
    games_by_id = {g["id"]: g for g in games}

    targets = [g for g in games if g.get("steamUrl")]
    total = len(targets)
    print(f"🔍 Cerco prezzi affiliati per {total} giochi con Steam URL...")
    print(f"   Concorrenza: IG={IG_CONCURRENCY}  GB={GB_CONCURRENCY}  (paralleli)")

    ig_found = gb_found = done_count = 0
    start = time.time()
    lock = asyncio.Lock()

    ig_sem = asyncio.Semaphore(IG_CONCURRENCY)
    gb_sem = asyncio.Semaphore(GB_CONCURRENCY)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ig_ctx = await browser.new_context(user_agent=_UA, locale="en-US")
        gb_ctx = await browser.new_context(user_agent=_UA, locale="en-US")

        async def process_game(game: dict) -> None:
            nonlocal ig_found, gb_found, done_count

            # IG e GB in parallelo per lo stesso gioco
            async def do_ig():
                async with ig_sem:
                    page = await ig_ctx.new_page()
                    try:
                        return await fetch_ig(page, game)
                    finally:
                        await page.close()

            async def do_gb():
                async with gb_sem:
                    page = await gb_ctx.new_page()
                    try:
                        return await fetch_gb(page, game)
                    finally:
                        await page.close()

            ig_res, gb_res = await asyncio.gather(
                do_ig(), do_gb(), return_exceptions=True
            )

            ig_url, ig_disc = ig_res if not isinstance(ig_res, Exception) else ("", 0)
            gb_url, gb_disc = gb_res if not isinstance(gb_res, Exception) else ("", 0)

            async with lock:
                orig = games_by_id[game["id"]]
                if ig_url:
                    orig["igUrl"] = ig_url
                    orig["igDiscount"] = ig_disc
                    ig_found += 1
                if gb_url:
                    orig["gbUrl"] = gb_url
                    orig["gbDiscount"] = gb_disc
                    gb_found += 1
                done_count += 1
                if ig_url or gb_url:
                    label = f"IG:-{ig_disc}%" if ig_url else "IG:—"
                    label += f"  GB:-{gb_disc}%" if gb_url else "  GB:—"
                    print(f"  ✓ [{game['id']}] {game['title']}: {label}")
                if done_count % 25 == 0:
                    elapsed = time.time() - start
                    rate = done_count / elapsed if elapsed > 0 else 0
                    eta = (total - done_count) / rate if rate > 0 else 0
                    print(f"  📊 {done_count}/{total} — {elapsed:.0f}s — ~{eta:.0f}s rimanenti")

        # Lancia tutti i task con stagger per evitare burst
        tasks = []
        for game in targets:
            tasks.append(asyncio.ensure_future(process_game(game)))
            await asyncio.sleep(STAGGER)

        await asyncio.gather(*tasks, return_exceptions=True)

        await ig_ctx.close()
        await gb_ctx.close()
        await browser.close()

    elapsed = time.time() - start
    print(f"\n✅ IG: {ig_found}/{total}  GB: {gb_found}/{total}  ⏱ {elapsed:.0f}s")
    catalog_data.write_legacy_games_js(games, featured_id)
    catalog_data.write_catalog_artifact(games)
    catalog_data.write_public_catalog_export(games)
    print("💾 games.js + catalog aggiornati")


if __name__ == "__main__":
    asyncio.run(run())
