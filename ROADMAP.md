# Roadmap — Co-op Games Hub

Documento di riferimento per lo sviluppo del sito. Aggiornare dopo ogni task completato.
Ultima analisi: 2026-03-18

---

## Stato attuale

| Area | Stato |
|------|-------|
| Catalogo giochi | **520 giochi**, pipeline multi-source (Steam, itch.io, GOG, IGDB, new releases) |
| Pagine statiche | 520 pagine in `games/` + sitemap |
| Internazionalizzazione | IT/EN completo su tutte le pagine principali + hreflang |
| Giochi gratuiti | Workflow giornaliero funzionante (Epic, Steam, GOG) |
| SEO | Ottimo — canonical, OG, JSON-LD, sitemap, robots.txt, hreflang, font self-hosted |
| PageSpeed Mobile | 93 performance, 100 SEO, 100 Best Practices, 92 Accessibility |
| Monetizzazione | Ko-fi footer ✅, UTM tracking ✅, CJ/Fanatical pending ⏳, GOG pending ⏳ |
| Crossplay | **86 giochi marcati**, filtro UI **attivo** |
| Font | Self-hosted (no Google Fonts) ✅ |
| Ruota random | Risultato cliccabile ✅ |

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
| IsThereAnyDeal | ❌ Feature futura | No | Sì (gratuita) | Permissivo |
| OpenCritic | ❌ Opzionale | No | No | ~25 req/min |
| Co-Optimus | ❌ No API (scraping bloccato da CF) | **Sì — autoritativo** | N/A | N/A |

### Pipeline consigliata (con IGDB)

```
SteamSpy (candidati co-op, CCU, rating)
  → Steam Store API (descrizione, immagini, categorie)
    → IGDB (arricchimento: maxPlayers reale, coopMode preciso)
      → games.js
```

### Priorità integrazione

1. **IGDB** — unica fonte con `multiplayer_modes` strutturato (`onlinecoopmax`, `offlinecoopmax`, `splitscreen`). Risolve il problema crossplay e maxPlayers. Richiede registrazione Twitch (gratuita) + GitHub Secret.
2. **RAWG** — fallback per giochi non-Steam (GOG-only, Epic-only). 20K req/mese molto generosi.
3. **IsThereAnyDeal** — aggiunge badge "in offerta" / prezzo storico sulle card. Feature UX, non catalogo.
4. **OpenCritic** — voto critica accanto al rating utenti Steam. Copertura parziale per indie.

---

## Bug e fix urgenti

### 🔴 Fix già applicato (2026-03-17)
- `catalog_data.py` cercava `games.js` in root → spostato in `assets/` dopo refactoring
- Fix: `GAMES_JS = ROOT / "assets" / "games.js"` — pipeline ora funzionante

---

## Priorità 1 — Qualità dati catalogo

### 1.1 Verifica crossplay (parzialmente fatto)
- ✅ Filtro UI attivato, 86 giochi marcati (da IGDB/SteamSpy)
- ⚠️ Dati non verificati manualmente — possibili falsi positivi
- Rivalutare con verifica campione su SteamDB o Co-Optimus
- **File**: `assets/games.js`

### 1.2 Fix giochi con CCU zero
- Alcuni giochi potrebbero avere `ccu: 0` — dato mancante o non aggiornato
- Verificare se il workflow li aggiorna correttamente con il nuovo pipeline multi-source
- **File**: `scripts/auto_update.py`, `assets/games.js`

### ~~1.3 Aggiorna contatore in homepage~~ ✅ FATTO
- Contatore aggiornato a "500+" in meta description e UI

### 1.4 Verifica campi isFree e isIndie
- Nel JS risultano sempre `false` — verificare se vengono settati dinamicamente o mancano
- **File**: `assets/games.js`, `scripts/auto_update.py`

---

## Priorità 2 — UX e filtri

### ~~2.1 Attivare filtro crossplay~~ ✅ FATTO
- Filtro UI attivato, badge crossplay nelle card/modal

### 2.2 Paginazione o lazy loading ⚠️ URGENTE
- **520 giochi** tutti renderizzati subito — molto pesante su mobile
- Valutare: infinite scroll, paginazione a 50 card, o virtual list
- **File**: `assets/app.js`

### 2.3 Filtro per anno di uscita
- Campo `releaseYear` già presente in tutti i giochi
- Aggiungere slider o range filter (es. 2020-2026)
- **File**: `assets/app.js`, `assets/i18n.js`, `assets/style.css`

### 2.4 Pagina gioco: link a recensioni/community
- Aggiungere link a SteamDB, HowLongToBeat, OpenCritic
- **File**: `scripts/build_static_pages.py`, `game.html`

### 2.5 Ricerca migliorata
- Attuale ricerca: solo per titolo
- Valutare ricerca per genere/tag/descrizione
- **File**: `assets/app.js`

---

## Priorità 3 — SEO e contenuti

### 3.1 Pagine informative in inglese
- `about.html`, `contact.html`, `privacy.html` sono solo in italiano
- Valutare versioni EN dedicate o traduzione inline con i18n
- **File**: `about.html`, `contact.html`, `privacy.html`, `assets/i18n.js`

### 3.2 Blog o sezione "Guide co-op"
- Contenuto editoriale per SEO long-tail ("migliori giochi co-op horror 2025")
- Pagine statiche generate o scritte manualmente in `guides/`
- Bassa priorità — solo se si vuole puntare su traffico organico

### ~~3.3 Hreflang per SEO bilingue~~ ✅ FATTO
- Hreflang `it/en` aggiunto nelle pagine statiche

### 3.4 Immagine OG personalizzata per gioco
- Le pagine gioco usano l'immagine Steam come OG — va bene
- Valutare OG image generata con titolo sovrapposto (richiede script)

---

## Priorità 4 — Monetizzazione leggera

### ~~4.1 Link affiliati con UTM~~ ✅ FATTO
- UTM tracking implementato in `app.js`
- Parametri affiliato Epic/GOG pronti nel codice (`app.js`)

### ~~4.2 Ko-fi footer~~ ✅ FATTO
- Ko-fi button nel footer con link a ko-fi.com/coophubs

### 4.3 Attivare link affiliati reali
- **CJ / Fanatical**: account attivo, application in pending review — attendere approvazione
- **GOG**: email inviata a affiliate@gog.com, attendere risposta e ottenere `pp=` partner ID
- **Epic**: Creator Code non ancora ottenuto — applicare su dev.epicgames.com/affiliate
- Una volta ottenuti i codici, inserirli in `app.js` dove già ci sono i placeholder
- **File**: `assets/app.js`

### 4.4 Newsletter opzionale
- CTA discreta per raccogliere email (Mailchimp embed o simile)
- Solo se si vuole costruire un pubblico diretto — bassa priorità

---

## Priorità 5 — Tecnica e infrastruttura

### ~~5.1 Ottimizzazione og-image.png~~ ✅ FATTO
- OG image ottimizzata (commit `48c963d`)

### 5.2 Versioning assets dinamico
- Attualmente versione hardcoded `?v=20260314-cachefix1` in tutti i file HTML
- Rendere dinamico tramite build script o hash
- **File**: tutti gli HTML, `scripts/build_static_pages.py`

### 5.3 PWA completa (bassa priorità)
- `manifest.json` presente ma nessun service worker
- Aggiungere SW solo se si vuole funzionalità offline reale

### 5.4 Analytics leggeri
- Cloudflare Web Analytics (zero cookie, GDPR-friendly, gratuito)
- Aggiungere script nei `<head>` di tutte le pagine
- **File**: tutti gli HTML, `scripts/build_static_pages.py`

---

## Note architetturali

- **Non introdurre backend** — il sito resta statico su GitHub Pages
- **Pipeline Python**: `scripts/auto_update.py` → lunedì 6:00 UTC
- **Giochi gratuiti**: `scripts/fetch_free_games.py` → ogni giorno 7:00 UTC
- **Rebuild pagine**: dopo ogni modifica a `games.js` eseguire `python3 scripts/build_static_pages.py`
- **Validate**: sempre `python3 scripts/validate_catalog.py` dopo rebuild

---

## Changelog roadmap

| Data | Modifica |
|------|----------|
| 2026-03-17 | Creazione roadmap — analisi completa sito |
| 2026-03-17 | Fix critico: `catalog_data.py` path `assets/games.js` |
| 2026-03-18 | Aggiornamento completo: catalogo 520 giochi, nuovi adapter, monetizzazione avanzata, crossplay attivo, CJ affiliate live |
