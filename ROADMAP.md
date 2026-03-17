# Roadmap — Co-op Games Hub

Documento di riferimento per lo sviluppo del sito. Aggiornare dopo ogni task completato.
Ultima analisi: 2026-03-17

---

## Stato attuale

| Area | Stato |
|------|-------|
| Catalogo giochi | 326 giochi, pipeline automatica settimanale |
| Pagine statiche | 326 pagine in `games/` + sitemap |
| Internazionalizzazione | IT/EN completo su tutte le pagine principali |
| Giochi gratuiti | Workflow giornaliero funzionante (Epic, Steam, GOG) |
| SEO | Buono — canonical, OG, JSON-LD, sitemap, robots.txt |
| PageSpeed Mobile | 93 performance, 100 SEO, 100 Best Practices |
| Monetizzazione | Non ancora implementata |
| Crossplay | 31 giochi marcati, ma dati non verificati — UI nascosta |

---

## Bug e fix urgenti

### 🔴 Fix già applicato (2026-03-17)
- `catalog_data.py` cercava `games.js` in root → spostato in `assets/` dopo refactoring
- Fix: `GAMES_JS = ROOT / "assets" / "games.js"` — pipeline ora funzionante

---

## Priorità 1 — Qualità dati catalogo

### 1.1 Verifica e fix dati crossplay
- 31 giochi marcati `crossplay: true` ma non verificati sistematicamente
- Attivare il filtro crossplay solo dopo verifica manuale o con fonte affidabile (SteamSpy/IGDB)
- **File**: `assets/games.js`, `assets/app.js` (ri-attivare filtro UI)

### 1.2 Fix giochi con CCU zero
- 31 giochi con `ccu: 0` — dato mancante o non aggiornato
- Verificare se il workflow li aggiorna correttamente
- **File**: `scripts/auto_update.py`, `assets/games.js`

### 1.3 Aggiorna contatore in homepage
- `index.html` dice "300+" ma il catalogo è a 326
- Aggiornare a "325+" o rendere il contatore dinamico da JS
- **File**: `index.html`, `assets/app.js`

### 1.4 Verifica campi isFree e isIndie
- Nel JS risultano sempre `false` — verificare se vengono settati dinamicamente o mancano
- **File**: `assets/games.js`, `scripts/auto_update.py`

---

## Priorità 2 — UX e filtri

### 2.1 Attivare filtro crossplay (dopo verifica dati)
- Il filtro è presente nel codice ma nascosto (`e1a38e1`)
- Attivare quando i dati sono affidabili
- **File**: `assets/app.js`, `assets/i18n.js`

### 2.2 Paginazione o lazy loading
- Tutti i 326 giochi vengono renderizzati subito — pesante su mobile
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

### 3.3 Hreflang per SEO bilingue
- Aggiungere `<link rel="alternate" hreflang="it/en">` nelle pagine statiche
- Utile se si punta al mercato internazionale
- **File**: `scripts/build_static_pages.py`

### 3.4 Immagine OG personalizzata per gioco
- Le pagine gioco usano l'immagine Steam come OG — va bene
- Valutare OG image generata con titolo sovrapposto (richiede script)

---

## Priorità 4 — Monetizzazione leggera

### 4.1 Link affiliati Steam/Humble Bundle
- Aggiungere parametro affiliato agli URL store (es. `?partner=coophubs`)
- Verificare programmi affiliazione disponibili
- **File**: `scripts/build_static_pages.py`, `assets/app.js`

### 4.2 Banner "Supporta il progetto"
- Sezione discreta in footer o sidebar con Ko-fi / Buy Me a Coffee
- **File**: `index.html`, `assets/style.css`

### 4.3 Newsletter opzionale
- CTA discreta per raccogliere email (Mailchimp embed o simile)
- Solo se si vuole costruire un pubblico diretto

---

## Priorità 5 — Tecnica e infrastruttura

### 5.1 Ottimizzazione og-image.png
- `og-image.png` pesa 395KB — ridurre a <100KB senza perdita visibile
- **File**: `assets/og-image.png`

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
