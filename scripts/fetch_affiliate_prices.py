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
GB_SEARCH = "https://www.gamebillet.com/allproducts?q={}&adv=true"
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


DLC_KEYWORDS = {'dlc', 'pack', 'season pass', 'expansion', 'soundtrack',
                'bundle', 'starter pack', 'upgrade', 'supporter', 'collector',
                'skin', 'costume', 'cosmetic', 'chapter', 'episode'}


def _clean_title(t: str) -> str:
    t = t.lower()
    t = re.sub(r"\s*[-–]\s*(europe|us|canada|global|row|worldwide|latam|america).*", "", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return t.strip()


def _has_subtitle(ig_title: str, game_title: str) -> bool:
    """Controlla se ig_title ha un sottotitolo (:, -) dopo la parte che matcha game_title."""
    gt_lower = game_title.lower().strip()
    ig_lower = ig_title.lower().strip()
    if not ig_lower.startswith(gt_lower):
        return False
    rest = ig_lower[len(gt_lower):].strip()
    return rest.startswith(":") or rest.startswith("-") or rest.startswith("–")


def _title_match(ig_title: str, game_title: str) -> str | None:
    """Restituisce 'exact', 'partial' o None. Scarta match che puntano a DLC."""
    a, b = _clean_title(ig_title), _clean_title(game_title)
    if a == b:
        return "exact"
    if a.startswith(b):
        extra = a[len(b):].strip()
        if any(kw in extra for kw in DLC_KEYWORDS):
            return None  # DLC keyword trovata
        # Se il titolo originale ha un sottotitolo (: o -), è probabilmente un DLC/espansione
        if _has_subtitle(ig_title, game_title):
            return None
        return "partial"
    if b.startswith(a):
        return "partial"
    return None


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

            exact_match = None
            partial_match = None
            for item in items:
                if "steam" not in item["href"].lower():
                    continue
                result = _title_match(item["title"], title)
                if result == "exact":
                    exact_match = item["href"]
                    break
                if result == "partial" and not partial_match:
                    partial_match = item["href"]
            product_url = exact_match or partial_match or ""

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

        exact_match = None
        partial_match = None
        for item in items:
            result = _title_match(item["title"], title)
            if not result:
                continue
            slug_match = re.search(r"gamebillet\.com/(.+)", item["href"])
            if not slug_match:
                continue
            slug = slug_match.group(1).split("?")[0]
            m_disc = re.search(r"(\d+)", item["saleText"] or "")
            discount = int(m_disc.group(1)) if m_disc else 0
            entry = (_gb_affiliate(slug), discount)
            if result == "exact":
                return entry
            if not partial_match:
                partial_match = entry
        if partial_match:
            return partial_match

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
    # Preferisce patchright (stealth anti-bot) se disponibile, fallback su playwright
    try:
        from patchright.async_api import async_playwright
        print("   Browser: patchright (stealth mode)")
    except ImportError:
        try:
            from playwright.async_api import async_playwright
            print("   Browser: playwright (standard)")
        except ImportError:
            print("❌ né patchright né playwright installati.")
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
