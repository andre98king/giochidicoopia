# AI Collaboration Log — coophubs.net

Data ultimo aggiornamento: **2026-03-25 (v2)**

---

## Analisi Stato Progetto

### ✅ Completato (Feb-Mar 2026)

**Core features:**
- ✅ Catalogo **551 giochi** coerente (games.js) con dati Steam/itch.io
- ✅ Filtri raggruppati (Special: all/trending/free, Genere, Modalità)
- ✅ Sistema "Giochi Già Giocati" (localStorage + localStorage_notes)
- ✅ Note personali per giochi completati
- ✅ Modale per dettagli gioco con link store
- ✅ Routing statico: `games/<id>.html` (551 pagine per SEO)
- ✅ I18n IT/EN completo
- ✅ Sitemap.xml + robots.txt
- ✅ Mobile responsive (CSS grid + flex)

**Affiliate monetization:**
- ✅ Instant Gaming (IG): 3% commission, link tracking setup
- ✅ GameBillet (GB): 5% commission, link tracking setup
- ✅ Scraper prezzi IG/GB: 12x optimized (semafori, 10min per 334 games)
- ✅ IG discount fixed: navigate to product page for `.discounted`
- ✅ Price compare modal con 2-3 store alterniativi
- ✅ CJ Affiliate + 7 pending (Fanatical, G2A, Gameseal, GAMIVO, K4G, Kinguin)

**UX & Polish:**
- ✅ Mobile toolbar compatto (genre/mode filters collassati dietro toggle)
- ✅ Ko-fi float nascosto su mobile
- ✅ Admin button rimosso (non più necessario)
- ✅ Card layout omogeneo (altezze/spaziature uniformi)
- ✅ Played toggle visibile e interattivo (✓ cerchio, top-left, z-index 15)
- ✅ Note button ✎ su card giocate
- ✅ Filter alignment corretto (full-width rows)
- ✅ Cache busting implementato (?v=20260319-mob)

**Infrastruttura:**
- ✅ GitHub Pages hosting (statico)
- ✅ Cloudflare DNS + proxy + HTTPS
- ✅ GitHub Actions pipeline: aggiornamento giochi (lunedì), free games (giornaliero)
- ✅ Python scraper: auto_update.py, build_static_pages.py, validate_catalog.py, fetch_free_games.py

---

## 🚨 Known Issues

| Problema | Severity | Note |
|----------|----------|------|
| GameBillet coverage basso | ⚠️ High | 4 giochi (residuo vecchio run) — fix camoufox committato, serve run completa per misurare coverage reale |
| Gameseal discount=0 | ⚠️ Medium | CJ API non restituisce salePrice — link attivi ma sconto sempre 0 |
| GOG partner ID | ⚠️ Low | ID non ancora ottenuto (architettura pronta in app.js) |
| WinGameStore in review | ℹ️ Info | Link scaduto, email support inviata 2026-03-18 |
| Green Man Gaming | ℹ️ Info | Approvato su Impact.com, solo search fallback (no direct link per gioco) |
| games.js stale | ℹ️ Info | Fermo al 21/03 — aggiornamento atteso al prossimo workflow (domani) |

---

## 📊 Roadmap (Next steps)

### Fase 1: Completa coverage affiliate (Urgenza: MEDIA)

**Obiettivo**: Massimizzare commission + click-through

1. **Gameseal (CJ Affiliate)**
   - Implementare mapping game <→ Gameseal product ID
   - Attualmente ~15 games, target 100+
   - Link structure: CJ tracking + Gameseal domain

2. **GOG Partner ID**
   - Ottenere GOG partner ID
   - Aggiungere a AFFILIATE.gog (già pronto in app.js)
   - Test su giochi GOG esclusivi

3. **Fanatical, G2A, K4G, Kinguin**
   - Status check con CJ Affiliate
   - Implementare se approvati
   - Priority: Fanatical (più noto in EU)

4. **Check WinGameStore + Green Man Gaming approval**
   - Status sulle email: approvazione entro 5gg?
   - Se approved: integrare nei link del modal

---

### Fase 2: SEO & Traffic (Urgenza: MEDIA)

**Obiettivo**: Aumentare organic traffic

1. **Internal linking**
   - Link da cards tra giochi correlati (stesso genere/modalità)
   - Schema.json markup per game reviews (structured data)
   - Breadcrumb nav su pagine game statiche

2. **Meta descriptions**
   - Audit corrente meta descriptions (games/<id>.html)
   - Renderizzare da games.js description_it (120-160 char)
   - Verificare unicità

3. **Heading hierarchy**
   - Audit h1-h3 structure per pagina
   - Assicurare un solo h1 per pagina
   - Logica h2 per sottosezioni

4. **Rich snippets**
   - Game schema.json (GamePlayMode, numberOfPlayers, etc.)
   - Breadcrumb schema
   - ReviewRating schema per rating Steam

---

### Fase 3: Features UX (Urgenza: BASSA)

**Obiettivo**: Engagement e usability

1. **Collections personali**
   - Salvare custom liste di giochi (wishlist, "da comprare", etc.)
   - Export/import JSON
   - Storage: localStorage (come played games)

2. **Advanced filters**
   - Filter per price range (da scraper affiliates)
   - Filter per release year range
   - Filter per player count exact
   - Combinare filtri con AND (già fatto, verificare UX)

3. **Social sharing**
   - Share button per game (Twitter, Reddit)
   - Share wishlist
   - URL param per preset (e.g. `?genre=horror&mode=online`)

4. **Notifications**
   - Alert quando gioco entra in sconto (IG/GB scraper monitoring)
   - "New games" notifiche
   - Optional: email digest settimanale (richiede backend minimo)

---

### Fase 4: Monitoring & Maintenance (ONGOING)

**Obiettivo**: Salute progetto

1. **Scraper health**
   - Monitor IG/GB DOM changes (monthly audit)
   - Fallback strategy se APIs cambiano
   - Log errors + retry logic

2. **Analytics**
   - ✅ Cloudflare Analytics già attivo (privacy-first, no cookies, zero-config)
   - Track affiliate clicks: verificare se CF registra click su link esterni
   - Monthly report su revenue affiliate (da pannelli IG/GB/CJ)

3. **Content freshness**
   - Review giochi new/removed monthly (Steam API)
   - Validate affiliate URLs (200 HTTP check)
   - Check CCU trends (giochi dead removal candidate)

4. **Performance monitoring**
   - PageSpeed Insights (target >90 mobile, >95 desktop)
   - Lighthouse audit (monthly)
   - Asset size monitoring

---

## 💰 Revenue Projection (Estimate basato su dati storici)

| Canale | Stato | Commissione | Est. Games | Est. Click/mese | Est. Revenue/mese |
|--------|-------|-------------|-----------|-----------------|-------------------|
| Instant Gaming | ✅ Active | 3% | 250+ | ~300 | ~$50-80 |
| GameBillet | ✅ Active | 5% | 200+ | ~150 | $30-50 |
| Gameseal (CJ) | 🔄 Partial | varia | ~15 | ~30 | $5-15 |
| Epic (pending CC) | ⏳ Ready | varia | ~80 | ~40 | $20-40 |
| GOG (pending ID) | ⏳ Ready | varia | ~120 | ~60 | $30-60 |
| Fanatical + others | ⏳ CJ pending | varia | ~100 | ~50 | $20-40 |
| **TOTALE** | - | - | - | **~630** | **$155-285** |

**Note**: Stime conservative, reale dipende da click-through rate (CTR) e conversion

---

## 📝 Log Modifiche

### 2026-03-19 (Today)

- **Commit f880f0a**: `fix(ux): mobile toolbar compatta + scraper IG ottimizzato`
  - Mobile toolbar: genre/mode filters collassati dietro toggle
  - Ko-fi float nascosto su mobile
  - Scraper IG: navigazione a product page per `.discounted`
  - Scraper IG/GB: semaphore concurrency (IG=8, GB=5), 12x speedup
  - Cache bust version: `20260319-mob`
  - Test: Brotato -60%, Elden Ring -22%, Rust -92% ✅

### 2026-03-18

- **Commit a669512**: `fix(ui): move Gratis to special row, fix played toggle visibility, homogenize cards`
  - Filtro "Gratis" spostato in filterSpecial (accanto all/trending)
  - Bottone ✓ "Giochi Già Giocati": visibile (z-index 15, top-left, glass effect)
  - Note button ✎ su card giocate
  - Card layout omogeneo (rimosso margin-top: auto da .card-desc)
  - Filter alignment: full-width rows

- **Commit 051a329**: `fix(ui): remove admin button, fix filter alignment, improve played/note UX`
  - Admin button rimosso (HTML + CSS + JS)
  - Filter container: width 100% (full-width rows)
  - Played toggle: z-index 15, positioned top-left con cerchio 30px

---

## 🤝 Collaboration Notes

- **Andrea** (owner): decisioni, testing, deploy
- **Claude Code**: tech lead, code review, roadmap, fix prioritizzazione
- **Aider + Ollama**: task delegati (coding ripetitivo, scraper fixes, refactoring meccanico)

**Prossima sync**: Fase 1 in corso — GB scraper fix, poi Gameseal + GOG

---

## Log 2026-03-25 (v5) — FASE 5 Performance + verifica FASE 4

### FASE 4 UX (verificata)
- **Focus trap**: codice verificato — Escape chiude modal, Tab ciclico sui focusable elements
- **Swipe-to-dismiss**: codice verificato — touchstart/touchend con threshold 80px
- **aria-expanded**: 4 occorrenze su genre/mode toggle

### FASE 5 Performance
- **sizes attribute**: aggiunto a card-img e modal-img → `sizes="(max-width: 600px) 100vw, 460px"`
- **Cache busting**: aggiornato a `?v=20260325` per index.html
- **Timer cleanup**: freeSectionTimer e freeBadgeTimer già gestiti con clearTimeout

### Note tecniche
- Lazy rendering: già presente con IntersectionObserver (40 iniziali + batch 30)
- Test browser: Playwright installato, 551 giochi caricati nel DOM
- MCP Servers: Playwright, GitHub, GSC attivi
- Skills: 16 SEO skills caricate, superpowers plugin abilitato

### Affiliate
- **Kinguin (CJ)**: AFFILIATE.kinguin = `click-101708519-15734285`, 6% nuovi utenti
- **GAMIVO INT (CJ)**: AFFILIATE.gamivo = `click-101708519-10660651`
- **Fix Kinguin/GAMIVO**: i link search andavano alla homepage (SPA non gestisce redirect CJ). Fix: fallback a homepage store via CJ se non esiste `game.kgUrl`/`game.gmvUrl`. Struttura dati: `kgUrl`, `kgDiscount`, `gmvUrl`, `gmvDiscount` (da aggiungere via scraper futuro)
- Declinati su CJ: GearUP, hero-wars.com, Safeshell VPN
- Pending: Fanatical, GOG.COM INT, K4G (CJ), WinGameStore (link scaduto)

### FASE 3 SEO — JSON-LD VideoGame (tutte le 551 pagine statiche)
- Aggiunto: `aggregateRating` (senza ratingCount — nessun dato reale disponibile, si attiva se `game.totalReviews > 0`)
- Aggiunto: `playMode` → `["SinglePlayer","CoOp","MultiPlayer"]` da `coopMode`
- Aggiunto: `numberOfPlayers` → `QuantitativeValue` con min/max parsati da `game.players`
- Aggiunto: `datePublished`, `operatingSystem`, `applicationCategory: "Game"`, `offers` con steamUrl
- Descrizione EN usata per schema (più utile per Google)

### FASE 3 SEO — Hreflang sitemap
- Sitemap ora ha `xmlns:xhtml` + `<xhtml:link>` IT/EN/x-default per tutti i 551 giochi
- HTML hreflang già corretto (stessa URL per entrambe le lingue, JS i18n)
- Metodo raccomandato per siti 500+ pagine

### FASE 4 UX
- **Focus trap modal**: Tab ciclico dentro modal, Escape chiude, focus ripristinato all'elemento precedente
- **Swipe-to-dismiss**: swipe down ≥80px su overlay chiude modal (mobile)
- **aria-expanded**: aggiunto su toggle genre filters e mode filters (accessibilità screen reader)

### Repo cleanup
- Rimossi da git: 4 PNG screenshot (~1.3MB) + `data/coop_validation_report.json`
- `.gitignore` aggiornato: `*-desktop.png`, `*-mobile.png`, `ext-links-*.png`, `related-games-*.png`

### Note tecniche
- Co-Optimus API: bloccata da Cloudflare Managed Challenge — non usabile senza browser automation per 551 chiamate
- IGDB già copre lo stesso dato: 401/551 giochi con igdbId, 197 con "split" coopMode
- `totalReviews` non è ancora in games.js — quando aggiunto, `ratingCount` in aggregateRating si attiva automaticamente

### Stato roadmap
- FASE 0: ✅ completa
- FASE 1: ✅ IG, GB, GMG, Gameseal, Kinguin, GAMIVO attivi
- FASE 2: ✅ retry tenacity, fallback camoufox, trending ricalibirato (54 giochi)
- FASE 3: ✅ JSON-LD + hreflang sitemap
- FASE 4: ✅ focus trap + swipe + aria-expanded (verificato via test)
- FASE 5: ✅ sizes attribute immagini, cache busting aggiornato
- TODO prossima sessione: SEO audit con skill /seo

---

## Log 2026-03-25 (v3) — Integrazione Kinguin + GAMIVO

- **Kinguin (CJ)**: aggiunto a `AFFILIATE` in app.js + `AFFILIATE_KINGUIN` in build_static_pages.py — deep link CJ ID 15734285, commissione 6% nuovi utenti
- **GAMIVO INT (CJ)**: aggiunto a `AFFILIATE` in app.js + `AFFILIATE_GAMIVO` in build_static_pages.py — deep link CJ ID 10660651
- **CSS**: aggiunti `.btn-kinguin` (viola) e `.btn-gamivo` (blu) in style.css
- Entrambi visibili solo su giochi con `steamUrl`, nessun badge sconto (no scraper ancora)
- Pattern CJ: `https://www.tkqlhce.com/click-101708519-{ID}?url=encodeURIComponent(searchUrl)`
- Declinati su CJ: GearUP, hero-wars.com, Safeshell VPN (fuori target)
- Pending: Fanatical, GOG.COM INT, K4G (CJ), WinGameStore (link scaduto)

---

## Log 2026-03-25 (v2) — Audit critico + roadmap + fix

- **Audit critico**: analisi 3 agenti paralleli su pipeline, frontend, database
  - Database: 551 giochi (non 334), GB coverage 0.7% (4 giochi), trending 41.6% (229/551)
  - Pipeline: nessun retry HTTP, camoufox senza fallback, build_static_pages ricrea tutto
  - Frontend: app.js 1133 righe, no DOM virtualization, no focus trap modal
- **Fix trending**: soglia `MIN_CCU_TRENDING` 800 → 10.000 (229 → 54 giochi trending, top ~10%)
- **Fix retry**: aggiunto tenacity retry+backoff in `steam_catalog_source.py` (3 tentativi, backoff 2-30s)
- **Fix camoufox fallback**: run() ora logga + salva dati IG se camoufox crasha invece di sys.exit()
- **Roadmap** salvata in `/home/andrea/.claude/plans/wiggly-leaping-crystal.md`

## Log 2026-03-25

- **Fix: workflow rotto da 3 giorni** — `import json` mancante in `auto_update.py` causava crash silenzioso in "Run update script" (NameError su `json.dumps`)
- **Fix: GameBillet URL** — `/allgames?search=` → `/allproducts?q=` (endpoint cambiato, vecchio URL restituiva 404)
- **Fix: headless browser Cloudflare** — sostituito patchright con **camoufox** (Firefox stealth, bypassa Cloudflare Turnstile a livello engine). Confermato: HELLDIVERS 2 trovato a 25% su GB. Camoufox usato per ENTRAMBI IG e GB (un solo browser, due context).
- **Fix CSS build_static_pages.py** — classe `affiliate-badge` → `affiliate-discount` nei link badge store
- **State: coverage GB** — era 4 giochi (residuo vecchio run), attesa run completa con fix

---

## Log 2026-03-25 (v5) — SEO Audit + Security Headers

- **SEO Audit completo**: Score 91/100 (Technical 92, Content 88, Schema 95, Sitemap 98, Mobile 95, GEO 82)
- **Fix: robots.txt** — Bloccati AI training crawler (GPTBot, ClaudeBot, Google-Extended, Bytespider, PerplexityBot, CCBot). Mantiene indexing per Googlebot/Bingbot
- **Verificato**: Sitemap 555+ URL con hreflang, VideoGame schema su game pages, WebSite+Organization+SearchAction su homepage
- **Verificato**: Lazy loading attivo (IntersectionObserver), sizes attribute su immagini, cache busting v=20260325
- **Config: Security Headers Cloudflare** — Response Header Transform Rule aggiunta con X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. SecurityHeaders.com score: **A** (CSP non implementato — rischio rottura sito)

---

## Log 2026-03-21/24

- **Sistema cross-validazione co-op** (commit 01afbda): `scripts/cross_validate_coop.py` — verifica tag co-op con Steam (categoria "Co-op") + IGDB (multiplayer_modes + game_modes mode 3). Produce `data/coop_validation_report.json`.
- **Whitelist + Blacklist**: `VERIFIED_COOP_APPIDS` (9 giochi verificati manualmente), `BLACKLIST_APPIDS` aggiornata (+7 giochi PvP: Pummel Party, Nidhogg 2, Worms Rumble, GTA IV, XCOM 2, SW Empire at War, X4)
- **Rimozione 7 giochi PvP** (549 → 542): Brawlhalla, Apex, For Honor, DotA 2, Paladins, Splitgate, Rocket League rimossi dal catalogo
- **Fix CI** (commit bb01320): coopMode/categories sync downgrade da error a warning in `validate_catalog.py`
- **Fix CI** (commit 62f11ae): path corretto `free_games.js`, resilienza IGDB nei workflow
- **Analytics**: confermato uso Cloudflare Analytics (no Plausible — nota: correggere roadmap)

---

## Log 2026-03-20

- **SEO: Related Games** — Aggiunta sezione "Giochi simili" a tutte le 538 game pages (3228 internal cross-links per crawl budget)
- **SEO: External Links** — SteamDB, HowLongToBeat, ProtonDB, PCGamingWiki su ogni game page con Steam URL
- **SEO: GSC** — Sitemap re-inviata, homepage re-indicizzata su Google Search Console
- **Data: CCU fallback** — auto_update.py ora interroga SteamSpy individualmente per 46 giochi Steam con CCU 0
- **Data: releaseYear** — `parse_release_year()` in steam_catalog_source.py, pipeline aggiornata, backfill 387/549 giochi Steam
- **UX: Filtro anno** — Select dropdown (2024–2025, 2020–2023, 2015–2019, <2015) + sort "Più recenti", i18n IT/EN
- **Roadmap**: task 1.1, 1.5, 2.2, 2.3, 2.4, 3.1 completati/verificati
