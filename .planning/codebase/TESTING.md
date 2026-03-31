# Testing e Validazione

Questo documento descrive come viene testato e validato il sito Co-op Games Hub.

---

## 1. Validazione Catalog Script

### Script: `scripts/validate_catalog.py`

Esegue validazioni automatiche sul catalogo:

### 1.1 Validazione Strutturale

- **Pagine obbligatorie**: verifica che `index.html`, `about.html`, `contact.html`, `free.html`, `privacy.html`, `game.html` esistano
- **Dimensione catalogo**: allerta se < 50 giochi
- **ID duplicati**: segnala game ID duplicati
- **Slug duplicati**: segnala canonical slug duplicati

### 1.2 Validazione Campi Obbligatori

Per ogni gioco verifica:
- `title` non vuoto
- `description` non vuota
- `categories` non vuoto
- Almeno un URL store valido (Steam, GOG, Epic, itch.io)
- `description_en` obbligatoria (warning se mancante)

### 1.3 Validazione Categorie

```python
ALLOWED_CATEGORIES = {
    "trending", "horror", "action", "puzzle", "splitscreen",
    "rpg", "survival", "factory", "roguelike", "sport",
    "strategy", "indie", "free"
}
```

Segnala categorie sconosciute.

### 1.4 Validazione Pagine Statiche

- Verifica che ogni gioco abbia una pagina `{id}.html`
- Verifica presenza `<link rel="canonical">`
- Verifica presenza di `const GAME_DATA =` (dati embedded)

### 1.5 Validazione Artifacts

- `catalog.json` (canonico)
- `catalog.public.v1.json` (export pubblico)

Verifica:
- `schemaVersion` corretto
- Game count corrisponda al catalogo
- `stats.games` corrisponda
- `featuredIndieId` sia valido

### 1.6 Validazione Sitemap

- Parsing XML della sitemap
- Verifica URL completi (it + en)
- Verifica pagine hub (`migliori-giochi-coop-2026.html`, etc.)

### 1.7 Quality Checks

| Check | Severità | Descrizione |
|-------|----------|-------------|
| Descrizioni corrotte | ERROR | URL o HTML entities nelle descrizioni |
| Immagini mancanti | ERROR | URL immagine mancante o non HTTPS |
| Short descriptions | WARNING | Descrizioni < 30 caratteri |
| IT=EN identical | WARNING | Descrizioni identiche (non tradotte) |
| Missing releaseYear | WARNING | Giochi Steam senza anno |
| coopMode/cats sync | WARNING | "splitscreen" in cats ma non "split" in coopMode |
| Single category | WARNING | Solo una categoria (escludendo "free") |

### 1.8 Affiliate Coverage

```python
ig_count = sum(1 for g in games if g.get("igUrl"))
gs_count = sum(1 for g in games if g.get("gsUrl"))
gb_count = sum(1 for g in games if g.get("gbUrl"))
```

Warning se:
- GameBillet coverage < 5 giochi
- Gameseal ha link ma 0 sconti

---

## 2. Validazione HTML/CSS

### HTML Semantico

- Un solo `<h1>` per pagina
- Title e meta description per ogni pagina
- Attributi `alt` sulle immagini
- ARIA labels per elementi interattivi
- Skip link per accessibilità

### CSS Validation

- Tutte le classi usano kebab-case
- Variabili in `:root` per theming
- Mobile-first con media queries
- Prefissi vendor minimi (solo per gradient/clip-path)

### SEO On-Page

- Canonical URLs
- Structured data (VideoGame, WebSite, Organization, SearchAction)
- hreflang per contenuti IT/EN

---

## 3. Verifica Link e Integrità

### Link Check

Il sito non ha un link checker automatico, ma:
- Validazione URL store in `validate_catalog.py`
- Verifica che pagine statiche abbiano canonical corretto

### Immagini

- Lazy loading con `loading="lazy"`
- Attributi `sizes` per responsive images
- Fallback placeholder per immagini mancanti (`onerror`)

---

## 4. CI/CD Workflow

### Workflow 1: Update Games Database

**File**: `.github/workflows/update.yml`

**Trigger**:
- Schedule: ogni giorno alle 6:00 UTC
- Manuale: `workflow_dispatch`

**Passi**:
1. Checkout repository
2. Setup Python 3.11
3. `pip install -r scripts/requirements.txt`
4. `python3 scripts/auto_update.py` (con secrets: ITCH_IO_KEY, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, STEAM_API_KEY)
5. `python3 scripts/fetch_affiliate_prices.py`
6. `python3 scripts/fetch_gameseal_prices.py` (con CJ_API_TOKEN)
7. `python3 scripts/build_static_pages.py`
8. `python3 scripts/build_hub_pages.py`
9. `python3 scripts/validate_catalog.py`
10. Commit + push automatico

**Branch**: `main`

### Workflow 2: Update Free Games

**File**: `.github/workflows/free_games.yml`

**Trigger**:
- Schedule: ogni giorno alle 7:00 UTC
- Manuale

**Passi**:
1. Checkout
2. Setup Python
3. `pip install requests beautifulsoup4`
4. `python3 scripts/fetch_free_games.py`
5. `python3 scripts/validate_free_games.py`
6. Commit + push automatico

### Validazione Scripts

#### `validate_free_games.py`

- Verifica JSON valido
- Verifica campi obbligatori per ogni offerta
- Verifica date non scadute

---

## 5. Testing Manuale

### Checklist Pre-Deploy

- [ ] `validate_catalog.py` passa senza errori
- [ ] Tutte le pagine statiche generano correttamente
- [ ] Sitemap aggiornata
- [ ] No 404 su link interni
- [ ] Mobile responsive funziona

### Test Browser

- Chrome/Firefox/Safari
- Mobile (iOS/Android)
- Dark mode (il sito è dark-only)

### SEO Test

- Verifica title e meta description
- Verifica canonical URLs
- Verifica structured data (Schema.org)
- Lighthouse audit

---

## 6. Deployment

### Hosting

- **GitHub Pages** + Cloudflare (DNS, proxy, HTTPS)
- Dominio: `coophubs.net`

### Build

Il sito è interamente statico:
- No server-side rendering
- No build step locale necessario
- GitHub Actions genera automaticamente pagine statiche

### Cache

- Cache busting via `?v=DATE` parameter
- Service worker non implementato (non necessario per statico)

---

## 7. Monitoraggio

### SEO Audit (2026-03-25)

- **Score**: 91/100
- Technical: 92
- Content: 88
- Schema: 95
- Sitemap: 98
- Mobile: 95
- GEO: 82

### Security Headers

Configurate via Cloudflare Response Header Transform Rule:
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy

Score: **A** su securityheaders.com

---

## 8. Risorse Utili

| Risorsa | URL |
|---------|-----|
| Homepage | https://coophubs.net |
| Sitemap | https://coophubs.net/sitemap.xml |
| Robots | https://coophubs.net/robots.txt |
| GitHub Actions | https://github.com/.../actions |
| Google Search Console | sc-domain:coophubs.net |
