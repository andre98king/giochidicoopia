#!/usr/bin/env python3
"""
Aggiorna igUrl/igDiscount, gbUrl/gbDiscount, kgUrl/kgDiscount, gmvUrl/gmvDiscount
in games.js tramite HTTP scraping (httpx + BeautifulSoup).

Siti supportati:
  - Instant Gaming  (Nuxt.js SSR — httpx + BeautifulSoup)
  - GameBillet      (SSR — httpx + BeautifulSoup)
  - Kinguin         (React SPA — wrap CJ deep link su URL esistente, no search)
  - GAMIVO          (React SPA — wrap CJ deep link su URL esistente, no search)

Utilizzo:
    python3 scripts/fetch_affiliate_prices.py
"""
from __future__ import annotations

import asyncio
import difflib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog_data

# ─── Costanti affiliato ────────────────────────────────────────────────────────
AFFILIATE_IG  = "gamer-ddc4a8"
AFFILIATE_GB  = "fb308ca0-647e-4ce7-9e80-74c2c591eac1"
AFFILIATE_KG  = "https://www.tkqlhce.com/click-101708519-15734285"   # CJ Kinguin
AFFILIATE_GMV = "https://www.tkqlhce.com/click-101708519-15839605"   # CJ GAMIVO INT

# ─── Concorrenza e timeout ─────────────────────────────────────────────────────
IG_CONCURRENCY = 8
GB_CONCURRENCY = 5
TIMEOUT        = 15.0   # secondi per richiesta HTTP
RETRY_ATTEMPTS = 2      # tentativi extra su 429/503

# ─── URL ──────────────────────────────────────────────────────────────────────
IG_SEARCH = "https://www.instant-gaming.com/en/search/?query={}"
GB_SEARCH = "https://www.gamebillet.com/allproducts?q={}&adv=true"
GB_BASE   = "https://www.gamebillet.com"

LOG_FILE        = ROOT / "data" / "scraper_log.jsonl"
FUZZY_THRESHOLD = 0.85

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # Accept-Encoding omesso: httpx gestisce decompressione automaticamente
}

DLC_KEYWORDS = {
    "dlc", "pack", "season pass", "expansion", "soundtrack", "bundle",
    "starter pack", "upgrade", "supporter", "collector", "skin",
    "costume", "cosmetic", "chapter", "episode",
}


# ─── Logging ──────────────────────────────────────────────────────────────────

def _log_event(event_type: str, game_id: int, title: str, store: str, data: dict | None = None) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "type": event_type,
                 "game_id": game_id, "title": title, "store": store}
        if data:
            entry.update(data)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ─── HTTP helper ──────────────────────────────────────────────────────────────

async def _get(client: httpx.AsyncClient, url: str) -> httpx.Response | None:
    """GET con retry su 429/503."""
    for attempt in range(1 + RETRY_ATTEMPTS):
        try:
            r = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=TIMEOUT)
            if r.status_code == 429 or r.status_code == 503:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return r
        except (httpx.TimeoutException, httpx.ConnectError):
            if attempt < RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_DELAY)
    return None


# ─── Title matching ───────────────────────────────────────────────────────────

def _clean_title(t: str) -> str:
    """Pulizia standard per confronto titoli da pagine store."""
    t = t.lower()
    t = re.sub(r"\s*[-–]\s*(europe|us|canada|global|row|worldwide|latam|america).*", "", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return t.strip()


def _clean_compact(t: str) -> str:
    """Pulizia compatta: rimuove tutto tranne lettere e numeri.
    Usata per confronti URL slug dove apostrofi diventano spazi
    (es. "Garry's" → title "garrys", slug "garry s" → entrambi "garrysmod")."""
    return re.sub(r"[^a-z0-9]", "", t.lower())


def _has_subtitle(store_title: str, game_title: str) -> bool:
    gt = game_title.lower().strip()
    st = store_title.lower().strip()
    if not st.startswith(gt):
        return False
    rest = st[len(gt):].strip()
    return rest[:1] in (":", "-", "–")


def _title_match(store_title: str, game_title: str) -> str | None:
    """Restituisce 'exact', 'partial' o None. Scarta DLC/espansioni."""
    a, b = _clean_title(store_title), _clean_title(game_title)
    if a == b:
        return "exact"
    if any(kw in a for kw in DLC_KEYWORDS) or any(kw in b for kw in DLC_KEYWORDS):
        return None
    if _has_subtitle(store_title, game_title) or _has_subtitle(game_title, store_title):
        return None
    if a.startswith(b) or b.startswith(a):
        return "partial"
    if difflib.SequenceMatcher(None, a, b).ratio() >= FUZZY_THRESHOLD:
        return "partial"
    return None


def _ig_url_valid(url: str, game_title: str) -> bool:
    """True se l'URL IG punta al gioco base (non DLC/spin-off).

    Estrae il titolo dallo slug URL e verifica:
    1. Nessun DLC_KEYWORD nel titolo slug
    2. Il titolo del gioco è riconoscibile nel slug (normalizzazione compatta)
    3. Le parole extra dopo il titolo sono solo suffissi di edizione ("* edition")
    """
    # Estrai la parte titolo dall'URL: /ID-buy-[steam-]TITLE-pc...
    m = re.search(r"/\d+-(?:buy|download)-(?:steam-)?(.+?)-(?:pc|mac)(?:-|/|$)", url)
    if not m:
        return True  # URL non riconoscibile, lascia passare
    slug = m.group(1).replace("-", " ")

    # 1. DLC keyword nello slug → sicuramente sbagliato
    if any(kw in slug for kw in DLC_KEYWORDS):
        return False

    # 2. Il titolo del gioco deve essere riconoscibile nel slug (confronto compatto)
    game_compact = _clean_compact(game_title)
    slug_compact = _clean_compact(slug)
    if not slug_compact.startswith(game_compact):
        return False

    # 3. Parole extra dopo il titolo: ok solo se terminano con "edition"
    extra = slug_compact[len(game_compact):]
    if not extra:
        return True
    return bool(re.match(r"^[a-z0-9]*(edition)+[a-z0-9]*$", extra))


# ─── Affiliate URL builders ───────────────────────────────────────────────────

def _ig_affiliate(url: str) -> str:
    if not url:
        return ""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}igr={AFFILIATE_IG}"


def _gb_affiliate(slug: str) -> str:
    if not slug:
        return ""
    return f"{GB_BASE}/{slug.lstrip('/')}?affiliate={AFFILIATE_GB}"


def _kg_affiliate(product_url: str) -> str:
    if not product_url:
        return ""
    return f"{AFFILIATE_KG}?url={quote(product_url, safe='')}"


def _gmv_affiliate(product_url: str) -> str:
    if not product_url:
        return ""
    return f"{AFFILIATE_GMV}?url={quote(product_url, safe='')}"


# ─── Instant Gaming ───────────────────────────────────────────────────────────
# NOTA: la search page IG è Vue.js SPA (non SSR) — non restituisce dati senza
# browser. fetch_ig aggiorna solo il discount sui URL esistenti già validati.


async def fetch_ig(client: httpx.AsyncClient, sem: asyncio.Semaphore, game: dict) -> tuple[str, int]:
    """Aggiorna igDiscount per giochi con igUrl già valido.
    Restituisce ("", 0) se l'URL manca, è invalido, o la fetch fallisce.
    La pulizia degli URL invalidi avviene in process_game tramite _ig_url_valid."""
    existing = game.get("igUrl", "")
    if not existing:
        return "", 0

    product_url = re.sub(r"[?&]igr=[^&]*", "", existing).rstrip("?&")
    title, game_id = game["title"], game["id"]

    async with sem:
        try:
            r = await _get(client, product_url)
            if r is None or r.status_code != 200:
                return _ig_affiliate(product_url), game.get("igDiscount", 0)

            soup = BeautifulSoup(r.text, "lxml")
            # Priorità: .discounted (classe specifica IG) > primo elemento con % nel testo
            disc_el = soup.select_one(".discounted, .discount-percent")
            if not disc_el:
                for el in soup.select("[class*='discount']"):
                    if re.search(r"\d+\s*%", el.get_text(strip=True)):
                        disc_el = el
                        break
            discount = 0
            if disc_el:
                m = re.search(r"(\d+)", disc_el.get_text(strip=True))
                discount = int(m.group(1)) if m else 0

            _log_event("found", game_id, title, "ig", {"discount": discount, "url": product_url[:100]})
            return _ig_affiliate(product_url), discount

        except Exception as e:
            print(f"  ⚠️  IG errore '{title}': {e}")
            _log_event("error", game_id, title, "ig", {"error": str(e)[:100]})
    return "", 0


# ─── GameBillet ───────────────────────────────────────────────────────────────

async def fetch_gb(client: httpx.AsyncClient, sem: asyncio.Semaphore, game: dict) -> tuple[str, int]:
    """Restituisce (gbUrl, gbDiscount) via httpx + BeautifulSoup."""
    title, game_id = game["title"], game["id"]
    async with sem:
        try:
            r = await _get(client, GB_SEARCH.format(quote(title)))
            if r is None or r.status_code != 200:
                reason = f"http_{r.status_code}" if r else "timeout"
                _log_event("not_found", game_id, title, "gb", {"reason": reason})
                return "", 0  # gbUrl esistente preservata dal caller

            soup = BeautifulSoup(r.text, "lxml")
            exact_match = partial_match = None

            for heading in soup.select("h3 a, h4 a, .product-title a, .game-title a"):
                result = _title_match(heading.get_text(strip=True), title)
                if not result:
                    continue
                href = heading.get("href", "")
                slug_m = re.search(r"gamebillet\.com/(.+)", href)
                if not slug_m:
                    continue
                slug = slug_m.group(1).split("?")[0]

                # Sconto: cerca nel card padre
                card = heading.find_parent(class_=re.compile(r"product|item|card"))
                disc_el = card.select_one(".price-discount, .discount") if card else None
                discount = 0
                if disc_el:
                    m = re.search(r"(\d+)", disc_el.get_text())
                    discount = int(m.group(1)) if m else 0

                entry = (_gb_affiliate(slug), discount)
                if result == "exact":
                    _log_event("found", game_id, title, "gb", {"discount": discount, "match": "exact"})
                    return entry
                if not partial_match:
                    partial_match = entry

            if partial_match:
                _log_event("found", game_id, title, "gb", {"discount": partial_match[1], "match": "partial"})
                return partial_match
            _log_event("not_found", game_id, title, "gb", {"reason": "no_match"})

        except Exception as e:
            print(f"  ⚠️  GB errore '{title}': {e}")
            _log_event("error", game_id, title, "gb", {"error": str(e)[:100]})
    return "", 0


# ─── Kinguin + GAMIVO (SPA — solo wrap URL esistente) ─────────────────────────

_CJ_DOMAINS = re.compile(r"(tkqlhce|dpbolvw|kqzyfj|anrdoezrs|jdoqocy|qksrv)\.(?:com|net)")

def resolve_kg(game: dict) -> tuple[str, int]:
    """Wrappa kgUrl esistente in CJ deep link. Nessuna HTTP — SPA non scrapabile.
    Se kgUrl è già un CJ deep link (qualsiasi dominio CJ), lo restituisce invariato."""
    existing = game.get("kgUrl", "")
    if not existing:
        return "", 0
    # Già un CJ deep link (fetch_gameseal_prices lo ha popolato) — non ri-avvolgere
    if _CJ_DOMAINS.search(existing) and "/click-" in existing:
        return existing, game.get("kgDiscount", 0)
    # URL prodotto raw — avvolgi con tracking CJ homepage Kinguin
    if not existing:
        return "", 0
    return _kg_affiliate(existing), game.get("kgDiscount", 0)


def resolve_gmv(game: dict) -> tuple[str, int]:
    """Wrappa gmvUrl esistente in CJ deep link. Nessuna HTTP — SPA non scrapabile."""
    existing = game.get("gmvUrl", "")
    if not existing:
        return "", 0
    if _CJ_DOMAINS.search(existing) and "/click-" in existing:
        return existing, game.get("gmvDiscount", 0)
    return _gmv_affiliate(existing), game.get("gmvDiscount", 0)


# ─── Runner ───────────────────────────────────────────────────────────────────

async def run() -> None:
    games = catalog_data.load_games()
    featured_id, _ = catalog_data.load_legacy_catalog_bundle()
    games_by_id = {g["id"]: g for g in games}

    targets = [g for g in games if g.get("steamUrl")]
    total = len(targets)
    print(f"🔍 Cerco prezzi affiliati per {total} giochi con Steam URL...")
    print(f"   HTTP: httpx + BeautifulSoup  |  IG={IG_CONCURRENCY}  GB={GB_CONCURRENCY}  KG/GMV=URL wrap")

    ig_found = gb_found = kg_found = gmv_found = done_count = 0
    start = time.time()
    lock = asyncio.Lock()
    ig_sem = asyncio.Semaphore(IG_CONCURRENCY)
    gb_sem = asyncio.Semaphore(GB_CONCURRENCY)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        async def process_game(game: dict) -> None:
            nonlocal ig_found, gb_found, kg_found, gmv_found, done_count

            # Valida URL IG esistente prima della fetch
            existing_ig = game.get("igUrl", "")
            ig_valid = True
            if existing_ig:
                clean_ig = re.sub(r"[?&]igr=[^&]*", "", existing_ig).rstrip("?&")
                ig_valid = _ig_url_valid(clean_ig, game["title"])

            async def _skip_ig() -> tuple[str, int]:
                return "", 0

            ig_res, gb_res = await asyncio.gather(
                fetch_ig(client, ig_sem, game) if ig_valid else _skip_ig(),
                fetch_gb(client, gb_sem, game),
                return_exceptions=True,
            )
            ig_url,  ig_disc  = ig_res  if not isinstance(ig_res,  Exception) else ("", 0)
            gb_url,  gb_disc  = gb_res  if not isinstance(gb_res,  Exception) else ("", 0)
            kg_url,  kg_disc  = resolve_kg(game)
            gmv_url, gmv_disc = resolve_gmv(game)

            async with lock:
                orig = games_by_id[game["id"]]
                # Pulisci URL IG invalidi (DLC/spin-off) — meglio nessun link che link sbagliato
                if existing_ig and not ig_valid:
                    orig["igUrl"] = ""
                    orig["igDiscount"] = 0
                    _log_event("cleared", game["id"], game["title"], "ig",
                               {"reason": "invalid_url", "old": clean_ig[-60:]})
                elif ig_url:
                    orig["igUrl"] = ig_url;  orig["igDiscount"] = ig_disc;  ig_found += 1
                if gb_url:
                    orig["gbUrl"] = gb_url;  orig["gbDiscount"] = gb_disc;  gb_found += 1
                if kg_url:
                    orig["kgUrl"] = kg_url;  orig["kgDiscount"] = kg_disc;  kg_found += 1
                if gmv_url:
                    orig["gmvUrl"] = gmv_url; orig["gmvDiscount"] = gmv_disc; gmv_found += 1
                done_count += 1
                if ig_url or gb_url or kg_url or gmv_url:
                    label  = f"IG:-{ig_disc}%"    if ig_url  else "IG:—"
                    label += f"  GB:-{gb_disc}%"   if gb_url  else "  GB:—"
                    label += f"  KG:-{kg_disc}%"   if kg_url  else "  KG:—"
                    label += f"  GMV:-{gmv_disc}%" if gmv_url else "  GMV:—"
                    print(f"  ✓ [{game['id']}] {game['title']}: {label}")
                if done_count % 25 == 0:
                    elapsed = time.time() - start
                    rate = done_count / elapsed if elapsed > 0 else 0
                    eta = (total - done_count) / rate if rate > 0 else 0
                    print(f"  📊 {done_count}/{total} — {elapsed:.0f}s — ~{eta:.0f}s rimanenti")

        await asyncio.gather(*[process_game(g) for g in targets], return_exceptions=True)

    elapsed = time.time() - start
    print(f"\n✅ IG:{ig_found}/{total}  GB:{gb_found}/{total}  KG:{kg_found}/{total}  GMV:{gmv_found}/{total}  ⏱ {elapsed:.0f}s")
    catalog_data.write_legacy_games_js(games, featured_id)
    catalog_data.write_catalog_artifact(games)
    catalog_data.write_public_catalog_export(games)
    print("💾 games.js + catalog aggiornati")


if __name__ == "__main__":
    asyncio.run(run())
