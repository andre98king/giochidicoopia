# Struttura del Progetto — Co-op Games Hub

## File Tree

```
giochidicoopia/                           # Root del progetto (repo Git)
│
├── .github/
│   └── workflows/                        # GitHub Actions
│       ├── auto-update.yml               # Update catalogo (settimanale)
│       └── fetch-free-games.yml          # Fetch giochi gratis (giornaliero)
│
├── .planning/
│   └── codebase/                         # Documentazione architettura
│       ├── ARCHITECTURE.md               # Questo file
│       ├── STACK.md                      # Stack tecnologico
│       └── INTEGRATIONS.md               # Integrazioni esterne
│
├── assets/                               # Asset statici (CSS, JS, immagini)
│   ├── app.js                            # Logica principale (1189 righe)
│   ├── games.js                          # Database giochi legacy (~334 giochi)
│   ├── free_games.js                    # Feed giochi gratuiti
│   ├── i18n.js                          # Traduzioni IT/EN
│   ├── style.css                         # Tutti gli stili
│   ├── particles.js                      # Animazione canvas background
│   ├── logo-512.png                      # Logo PNG 512x512
│   ├── icon-*.png                        # Icone PWA (32, 48, 180, 192)
│   ├── logo.svg                          # Logo SVG
│   ├── favicon.svg                       # Favicon SVG
│   └── og-image.jpg                      # Open Graph image
│
├── data/                                 # Dati del catalogo
│   ├── catalog.public.v1.json            # Catalogo pubblico (consumato da app.js)
│   ├── catalog.games.v1.json             # Catalogo completo (admin)
│   ├── hub_editorial.json                # Contenuti editoriali
│   ├── seo_overrides.json                # Override meta tags
│   ├── backfill_candidates.json          # Giochi da aggiungere
│   └── _nocoop_flagged.json              # Giochi non-coop segnalati
│
├── games/                                # Pagine statiche SEO (~334 file)
│   ├── 1.html                            # ELDEN RING NIGHTREIGN
│   ├── 2.html                            # Rust
│   ├── 4.html                            # HELLDIVERS 2
│   ├── ...                               # (ogni gioco ha la sua pagina)
│   └── 615.html                          # Ultimo gioco
│
├── scripts/                              # Pipeline Python
│   ├── auto_update.py                    # Update catalogo settimanale
│   ├── build_static_pages.py             # Genera pages/*.html + sitemap
│   ├── build_hub_pages.py                # Genera hub pages
│   ├── fetch_free_games.py               # Fetch RSS feed giochi gratis
│   ├── fetch_affiliate_prices.py         # Fetch prezzi affiliati
│   ├── fetch_analytics.py               # Fetch analytics
│   ├── fetch_gameseal_prices.py          # Fetch prezzi Gameseal
│   ├── validate_catalog.py               # Validazione catalogo
│   ├── validate_free_games.py            # Validazione feed gratuiti
│   ├── discover_backfill.py              # Scoperta giochi da aggiungere
│   ├── generate_hub_pages_en.py          # Genera hub pages EN
│   ├── steam_catalog_source.py           # Adapter Steam
│   ├── itch_catalog_source.py            # Adapter itch.io
│   ├── catalog_data.py                   # Layer I/O dati
│   └── catalog_config.py                 # Configurazione pipeline
│
│   ├── requirements.txt                  # Dipendenze Python
│   └── __pycache__/                      # Cache Python compilato
│
├── .claude/                              # Configurazioni Claude
│   └── mcp-gsc/                          # Google Search Console MCP
│
├── .vscode/                              # Settings VS Code
│
├── index.html                            # Homepage principale
├── free.html                             # Pagina giochi gratuiti
├── about.html                            # Pagina about
├── contact.html                          # Pagina contatti
├── privacy.html                          # Pagina privacy
├── game.html                             # Legacy fallback (noindex)
│
├── sitemap.xml                           # Sitemap (555+ URL)
├── robots.txt                            # Configurazione crawler
├── manifest.json                        # PWA manifest
├── CNAME                                 # Dominio custom (coophubs.net)
├── _headers                              # Cloudflare headers
│
├── .gitignore                           # Esclusioni Git
├── .env                                 # Variabili ambiente
├── CLAUDE.md                            # Istruzioni per AI
├── README.md                            # README progetto
├── ROADMAP_STATUS.md                    # Stato roadmap
├── LICENSE                              # Licenza MIT
│
└── .aider.tags.cache.v4/                # Cache Aider (gitignored)
```

---

## Organizzazione Directory

### `/` (Root)

Contiene le pagine HTML principali e i file di configurazione del sito.

### `/assets`

Tutti gli asset necessari al frontend:
- **JS**: Logica applicativa (`app.js`), dati (`games.js`, `free_games.js`), traduzioni (`i18n.js`), effetti (`particles.js`)
- **CSS**: Unico file `style.css` con tutto il design
- **Immagini**: Favicon, logo, icone PWA, OG image

### `/data`

Dati strutturati del catalogo:
- JSON esportati dalla pipeline Python
- File di override per SEO
- Log e candidati per backfill

### `/games`

Pagine statiche HTML generate automaticamente:
- 334 pagine `games/<id>.html`
- Una per ogni gioco nel catalogo
- Contenuto pre-renderizzato con meta tags SEO

### `/scripts`

Script Python per automazione:
- Build e generazione pagine
- Fetch dati da Steam, itch.io, feed RSS
- Validazione e verifica
- Update automatico

### `/.github/workflows`

Configurazione CI/CD:
- Workflow settimanale per update catalogo
- Workflow giornaliero per giochi gratuiti

---

## File Principali e Loro Scopo

### Pagina Home

| File | Scopo |
|------|-------|
| `index.html` | Homepage con toolbar filtri, grid giochi, modals, footer |

### Logica Frontend

| File | Scopo |
|------|-------|
| `assets/app.js` | Core: filtri, rendering card, modal, ruota random, affiliate |
| `assets/i18n.js` | Traduzioni IT/EN, funzione `t()` |
| `assets/particles.js` | Background canvas animation |
| `assets/style.css` | Tutto il CSS (design system, componenti, responsive) |

### Dati

| File | Scopo |
|------|-------|
| `assets/games.js` | Database legacy (~334 giochi, fallback) |
| `data/catalog.public.v1.json` | Catalogo pubblico (principale) |
| `data/catalog.games.v1.json` | Catalogo completo (admin) |
| `assets/free_games.js` | Feed offerte gratuite |

### Pagine Statiche

| File | Scopo |
|------|-------|
| `games/<id>.html` | 334 pagine SEO per ogni gioco |
| `free.html` | Pagina dedicata offerte gratuite |
| `about.html` | Info progetto |
| `contact.html` | Contatti |
| `privacy.html` | Privacy policy |

### Pipeline

| File | Scopo |
|------|-------|
| `scripts/build_static_pages.py` | Genera pagine statiche + sitemap |
| `scripts/auto_update.py` | Update automatico catalogo |
| `scripts/fetch_free_games.py` | Fetch feed giochi gratuiti |

### Configurazione

| File | Scopo |
|------|-------|
| `sitemap.xml` | Sitemap per crawler (555+ URL) |
| `robots.txt` | Configurazione crawler (blocca AI training) |
| `manifest.json` | PWA manifest |
| `_headers` | Cloudflare security headers |

---

## Dipendenze File

```
index.html
├── assets/style.css
├── assets/app.js
├── assets/i18n.js
├── assets/particles.js
└── assets/free_games.js (async)

app.js
├── data/catalog.public.v1.json (fetch)
└── games.js (fallback)

build_static_pages.py
├── data/catalog.games.v1.json
└── templates/*.html

games/<id>.html (statico)
├── ../assets/style.css
├── ../assets/app.js
└── ../assets/i18n.js
```

---

## Note

- Il repo è la **root del sito** (non una subdirectory)
- GitHub Pages serve dalla root (`/`)
- Cloudflare fa proxy su `coophubs.net`
- Nessuna sottodirectory speciale per lingua (`/en` è un URL virtuale, non una cartella)
