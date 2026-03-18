#!/usr/bin/env python3
"""
Aggiorna igUrl e igDiscount in games.js tramite scraping Instant Gaming.

Usa Playwright (browser reale) perché il sito è renderizzato via Vue.js.
Lancia una sessione singola con pagine concorrenti per minimizzare il tempo.

Utilizzo:
    python3 scripts/fetch_ig_prices.py
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

AFFILIATE_ID = "gamer-ddc4a8"
CONCURRENCY  = 5      # pagine parallele
DELAY        = 1.2    # secondi tra batch
TIMEOUT_NAV  = 18000  # ms navigazione
TIMEOUT_SEL  = 8000   # ms attesa selector
IG_SEARCH    = "https://www.instant-gaming.com/en/search/?query={}"


def _affiliate_url(href: str) -> str:
    if not href:
        return ""
    sep = "&" if "?" in href else "?"
    return f"{href}{sep}igr={AFFILIATE_ID}"


def _title_match(ig_title: str, game_title: str) -> bool:
    """Confronto titolo tollerante: rimuove suffissi regione e punteggiatura."""
    def clean(t: str) -> str:
        t = t.lower()
        # rimuovi suffissi tipo "- Europe & US & Canada", "- Global", etc.
        t = re.sub(r"\s*[-–]\s*(europe|us|canada|global|row|worldwide|latam|america).*", "", t)
        t = re.sub(r"[^a-z0-9 ]", "", t)
        return t.strip()

    a = clean(ig_title)
    b = clean(game_title)
    return a == b or a.startswith(b) or b.startswith(a)


async def fetch_one(page, game: dict) -> tuple[str, int]:
    """Restituisce (igUrl, igDiscount) per un gioco. Stringa vuota se non trovato."""
    title = game["title"]
    url = IG_SEARCH.format(quote(title))
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        # Attendi che almeno un item sia presente, oppure vai avanti se non arriva
        try:
            await page.wait_for_selector(".item", timeout=TIMEOUT_SEL)
        except Exception:
            return "", 0

        items = await page.evaluate("""() => {
            const results = [];
            for (const el of document.querySelectorAll('.item')) {
                const link = el.querySelector('a.cover, a[href*="/buy-"]');
                const titleEl = el.querySelector('.title, [class*="title"]');
                const discountEl = el.querySelector('.discount, [class*="discount"]');
                if (!link || !titleEl) continue;
                results.push({
                    href: link.href || '',
                    title: titleEl.textContent.trim(),
                    discount: discountEl ? discountEl.textContent.trim() : ''
                });
            }
            return results;
        }""")

        # Trova il primo risultato Steam con titolo compatibile
        for item in items:
            if "steam" not in item["href"].lower():
                continue
            if not _title_match(item["title"], title):
                continue
            raw_discount = re.search(r"(\d+)", item["discount"] or "")
            discount = int(raw_discount.group(1)) if raw_discount else 0
            ig_url = _affiliate_url(item["href"])
            return ig_url, discount

    except Exception as e:
        print(f"  ⚠️  Errore per '{title}': {e}")

    return "", 0


async def run() -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ playwright non installato. Esegui: pip install playwright && playwright install chromium")
        sys.exit(1)

    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()

    # Filtra solo giochi con steamUrl (gli altri non sono su IG)
    targets = [g for g in games if g.get("steamUrl")]
    print(f"🔍 Cerco prezzi IG per {len(targets)} giochi con Steam URL...")

    updated = 0
    start = time.time()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            locale="en-US",
        )

        # Processa in batch da CONCURRENCY pagine
        for i in range(0, len(targets), CONCURRENCY):
            batch = targets[i : i + CONCURRENCY]
            pages = [await context.new_page() for _ in batch]

            results = await asyncio.gather(
                *[fetch_one(pages[j], batch[j]) for j in range(len(batch))],
                return_exceptions=True,
            )

            for j, result in enumerate(results):
                game = batch[j]
                if isinstance(result, Exception):
                    ig_url, ig_discount = "", 0
                else:
                    ig_url, ig_discount = result

                # Aggiorna solo se abbiamo trovato qualcosa
                if ig_url:
                    game["igUrl"]      = ig_url
                    game["igDiscount"] = ig_discount
                    # Riporta sul game originale nella lista games
                    for orig in games:
                        if orig["id"] == game["id"]:
                            orig["igUrl"]      = ig_url
                            orig["igDiscount"] = ig_discount
                            break
                    updated += 1
                    print(f"  ✓ [{game['id']}] {game['title']}: {ig_url} (-{ig_discount}%)")

            for p in pages:
                await p.close()

            elapsed = time.time() - start
            done = min(i + CONCURRENCY, len(targets))
            print(f"  Progresso: {done}/{len(targets)} — {elapsed:.0f}s")
            await asyncio.sleep(DELAY)

        await context.close()
        await browser.close()

    print(f"\n✅ Trovati {updated}/{len(targets)} giochi su IG")
    catalog_data.write_legacy_games_js(games, featured_id)
    catalog_data.write_catalog_artifact(games)
    catalog_data.write_public_catalog_export(games)
    print("💾 games.js aggiornato")


if __name__ == "__main__":
    asyncio.run(run())
