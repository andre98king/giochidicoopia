# Roadmap — Co-op Games Hub

Documento di riferimento per lo sviluppo del sito. Aggiornare dopo ogni task completato.
Ultima analisi: 2026-03-25

---

## Stato attuale

| Area | Stato |
|------|-------|
| Catalogo giochi | **538 giochi**, pipeline multi-source (Steam, itch.io) |
| Pagine statiche | 538 pagine in `games/` + sitemap |
| Internazionalizzazione | IT/EN su pagine principali + hreflang |
| Giochi gratuiti | Workflow giornaliero (Epic, Steam, GOG) |
| SEO | canonical, OG, JSON-LD con Organization/logo, sitemap, hreflang |
| SEO Audit | **91/100** (Technical 92, Content 88, Schema 95, Sitemap 98, Mobile 95, GEO 82) |
| Security Headers | **A** su securityheaders.com (Cloudflare Transform Rule) |
| Logo/Favicon | Gamepad SVG + PNG (32/48/180/192/512) — Organization schema per Google |
| Monetizzazione | IG+GB+GMG+Gameseal+Kinguin+GAMIVO attivi, Ko-fi, UTM tracking |
| Crossplay | 86 giochi marcati, filtro UI attivo (dati non verificati) |
| Scraper affiliati | IG+GB con anti-DLC, concurrency, ~8min per 385 giochi con Steam URL |
| Analytics | ✅ Cloudflare Web Analytics attivo |
| AI Crawler Policy | robots.txt blocca GPTBot, ClaudeBot, Google-Extended, Bytespider, PerplexityBot, CCBot |

### Problemi noti

| Problema | Impatto | Dettaglio |
|----------|---------|-----------|
| **198 giochi con CCU 0** | Alto | 36.8% del catalogo — ordinamento "trending" inaffidabile |
| ~~Nessuna paginazione~~ | ✅ Fixato | Infinite scroll: 40 card iniziali + batch 30 |
| **releaseYear non esiste** | Info | Campo assente da games.js — va aggiunto via pipeline |
| ~~isFree/isIndie sempre false~~ | ✅ NON è un bug | Usano `categories.includes('free'/'indie')` — 39 free, 260 indie |
| ~~Cache bust disallineato~~ | ✅ Fixato | Tutte le pagine ora `?v=20260320` |

---

## Fonti dati disponibili

Pipeline attuale: **SteamSpy → Steam Store API → itch.io**

| Fonte | Uso attuale | Co-op? | Chiave | Limite free |
|-------|------------|--------|--------|-------------|
| Steam Store API | ✅ Descrizioni, immagini, categorie, is_free | Sì (categorie) | No | ~40 req/min |
| SteamSpy | ✅ CCU, rating, tag co-op, top100 | Sì (tag) | No | ~1 req/sec |
| itch.io | ✅ Giochi indie non-Steam | No (ricerca testo) | Sì (gratuita) | Permissivo |
| **IGDB** (Twitch) | ❌ Da integrare | **Sì — strutturato** | Sì (Twitch OAuth) | 500 req/mese |
| **RAWG** | ❌ Da valutare | Parziale (tag) | Sì (gratuita) | 20.000 req/mese |

### Priorità integrazione

1. **IGDB** — unica fonte con `multiplayer_modes` strutturato (maxPlayers, splitscreen, crossplay). Richiede registrazione Twitch (gratuita).
2. **RAWG** — fallback per giochi non-Steam. 20K req/mese generosi.

---

## 🔴 Priorità URGENTE — Fix immediati

### ~~U.1 Fix isFree/isIndie~~ ✅ NON ERA UN BUG (2026-03-20)
- Verificato: il sistema usa `categories.includes('free'/'indie')`, non campi boolean
- 39 giochi free, 260 indie — tutto funzionante
- Corretto CLAUDE.md che documentava campi inesistenti

### ~~U.2 Paginazione / lazy rendering~~ ✅ FATTO (2026-03-20)
- Infinite scroll con IntersectionObserver: 40 card iniziali, batch di 30 allo scroll
- Riduzione 93% del DOM iniziale (40 vs 538 card)
- Filtri e ricerca funzionano correttamente con lazy rendering

### ~~U.3 Cache bust sincronizzato~~ ✅ FATTO (2026-03-20)
- Allineato tutto a `?v=20260320`: index.html, about, contact, free, privacy, game, build_static_pages.py
- Rigenerato tutte le 538 game pages

### ~~U.4 Cloudflare Web Analytics~~ ✅ GIÀ ATTIVO
- Iniettato automaticamente dal proxy Cloudflare, non serve snippet nel codice
- Dati visibili su dash.cloudflare.com → Web Analytics

---

## Priorità 1 — Qualità dati catalogo

### ~~1.1 Fix 198 giochi con CCU zero~~ ✅ MITIGATO (2026-03-20)
- 46/198 erano giochi Steam con CCU mancante: aggiunto fallback SteamSpy per appdetails singolo
- 152/198 sono giochi non-Steam (itch.io, GOG, IGDB) senza fonte CCU — CCU 0 inevitabile
- Sort "Più giocati ora" funziona correttamente: CCU 0 finisce in fondo
- Il fallback verrà eseguito alla prossima run della pipeline (lunedì)
- **File**: `scripts/auto_update.py`

### 1.2 Verifica crossplay (parzialmente fatto)
- ✅ Filtro UI attivato, 86 giochi marcati
- ⚠️ Dati non verificati manualmente — possibili falsi positivi
- **File**: `assets/games.js`

### ~~1.3 Aggiorna contatore in homepage~~ ✅ FATTO

### ~~1.4 Rimozione giochi obsoleti~~ ✅ FATTO (2026-03-19)
- Rimossi: GTA V Enhanced, EA FC 24, NBA 2K24, F1 24, Farming Simulator 19

### ~~1.5 Aggiungere releaseYear ai giochi~~ ✅ FATTO (2026-03-20)
- `parse_release_year()` in `steam_catalog_source.py` estrae anno da Steam API
- Pipeline auto_update.py popola releaseYear per nuovi giochi + batch backfill esistenti
- 387/549 giochi hanno releaseYear (162 non-Steam senza fonte)

---

## Priorità 2 — UX e filtri

### ~~2.1 Attivare filtro crossplay~~ ✅ FATTO

### ~~2.2 Filtro per anno di uscita~~ ✅ FATTO (2026-03-20)
- Select dropdown con fasce: 2024–2025, 2020–2023, 2015–2019, Prima del 2015
- Sort "Più recenti" per ordinare per anno
- i18n IT/EN completo

### ~~2.3 Pagina gioco: link a recensioni/community~~ ✅ FATTO (2026-03-20)
- Link a SteamDB, HowLongToBeat, ProtonDB, PCGamingWiki su tutte le game pages con Steam URL
- Sezione "Risorse esterne" con i18n IT/EN

### ~~2.4 Ricerca migliorata~~ ✅ GIÀ FATTO
- La ricerca già copre titolo, descrizione (IT+EN) e categorie — non solo titolo

### ~~2.5 Bottone Compra unico~~ ✅ FATTO (2026-03-19)

### ~~2.6 Fix contatore "Giocati da me"~~ ✅ FATTO (2026-03-19)

### ~~2.7 Fix overlap Ko-fi / scroll-top~~ ✅ FATTO (2026-03-19)

---

## Priorità 3 — SEO e contenuti

### ~~3.1 Pagine informative in inglese~~ ✅ GIÀ FATTO
- Tutte le pagine usano `data-i18n` + traduzioni EN complete in `i18n.js`
- `setLang()` aggiorna title, meta description, OG, JSON-LD, `html lang` dinamicamente

### 3.2 Blog o sezione "Guide co-op"
- Contenuto editoriale per SEO long-tail ("migliori giochi co-op horror 2026")
- Bassa priorità — solo se si vuole traffico organico

### ~~3.3 Hreflang per SEO bilingue~~ ✅ FATTO

### ~~3.4 Logo reale e favicon~~ ✅ FATTO (2026-03-19)

---

## Priorità 4 — Monetizzazione

### ~~4.1 Link affiliati con UTM~~ ✅ FATTO
### ~~4.2 Ko-fi footer~~ ✅ FATTO

### 4.3 Link affiliati — stato partner

| Store | Stato | Note |
|-------|-------|------|
| **Instant Gaming** | ✅ Attivo | 3%, scraper con anti-DLC |
| **GameBillet** | ✅ Attivo | 5%, scraper attivo |
| **Green Man Gaming** | ✅ Approvato | 5%/2%, Impact.com redirect |
| **MacGameStore** | ✅ Approvato | 5% |
| **Gameseal** | ✅ Approvato (CJ) | `tkqlhce.com` redirect |
| **WinGameStore** | ⚠️ Link scaduto | Email inviata 2026-03-18 |
| **GOG** | ⏳ Application inviata | Email 2026-03-18 |
| **Epic** | ❌ Rimosso | Solo per creator, non per siti web |
| **Fanatical** | ⏳ Pending (CJ) | |
| **Kinguin** | ⏳ Pending (CJ) | |

- Follow-up email previsto: 2026-03-25 (WinGameStore, GOG)
- **File**: `assets/app.js` (oggetto `AFFILIATE`), `scripts/build_static_pages.py`

### ~~4.4 Fix scraper anti-DLC~~ ✅ FATTO (2026-03-20)
- `_title_match()` con keyword DLC + rilevamento sottotitoli
- Scraper rieseguito con successo: 312/385 giochi IG trovati

### 4.5 Newsletter opzionale — bassa priorità

---

## Priorità 5 — Tecnica e infrastruttura

### ~~5.1 Ottimizzazione og-image.png~~ ✅ FATTO

### 5.2 PWA completa (bassa priorità)
- `manifest.json` presente con icone reali, nessun service worker
- Solo se si vuole funzionalità offline

---

## Note architetturali

- **Non introdurre backend** — il sito resta statico su GitHub Pages
- **Pipeline Python**: `scripts/auto_update.py` → lunedì 6:00 UTC
- **Giochi gratuiti**: `scripts/fetch_free_games.py` → ogni giorno 7:00 UTC
- **Scraper prezzi**: `scripts/fetch_affiliate_prices.py` → manuale, ~8min
- **Rebuild pagine**: dopo ogni modifica a `games.js` → `python3 scripts/build_static_pages.py`
- **Validate**: sempre `python3 scripts/validate_catalog.py` dopo rebuild

---

## Changelog roadmap

| Data | Modifica |
|------|----------|
| 2026-03-17 | Creazione roadmap — analisi completa sito |
| 2026-03-17 | Fix critico: `catalog_data.py` path `assets/games.js` |
| 2026-03-18 | Catalogo 520 giochi, nuovi adapter, monetizzazione, crossplay, CJ affiliate |
| 2026-03-19 | Bottone Compra, badge sconto, Epic rimosso, giochi obsoleti, logo, fix overlap, scraper anti-DLC |
| 2026-03-20 | Revisione roadmap: corretto analytics (non fatto), releaseYear (non esiste), isFree/isIndie (non è un bug — usano categories). Fix cache bust sync, infinite scroll (40+30 batch), aggiornato CLAUDE.md |
| 2026-03-20 | SEO: "Giochi simili" (3228 internal links) + "Risorse esterne" (SteamDB, HLTB, ProtonDB, PCGamingWiki) su tutte le game pages. Sitemap re-inviata a GSC. Task 2.3 e 2.4 completati |
| 2026-03-20 | Task 1.5 + 2.2: releaseYear aggiunto alla pipeline (387/549 Steam games). Filtro anno + sort "Più recenti" in homepage con i18n IT/EN |
| 2026-03-25 | SEO Audit completo (91/100). robots.txt aggiornato: blocca AI training crawlers. Security Headers configurati su Cloudflare (score A). FASE 5 Performance completata (sizes attribute, cache busting v=20260325) |
