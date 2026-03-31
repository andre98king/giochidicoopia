# Stack Tecnologico — Co-op Games Hub

## Tecnologie Principali

### Frontend (Statico)
- **HTML5** — Markup semantico, SEO-ready, hreflang i18n
- **CSS3** — CSS custom properties, grid/flexbox, animazioni, responsive (mobile-first)
- **JavaScript ES6+** — Moduli, async/await, IntersectionObserver per lazy loading e infinite scroll

### Backend (Assente)
Nessun backend server-side. Il sito è interamente statico.

### Pipeline (Python)
- **Python 3.11** — Script di automazione per data update e build
- Nessun framework (no Flask, FastAPI, Django)

---

## Dipendenze

### Frontend
Nessuna dipendenza esterna. Il sito usa solo:
- Font self-hosted (Space Grotesk, JetBrains Mono) — GDPR compliant
- Canvas API nativa per background particles
- Browser native APIs (IntersectionObserver, localStorage, fetch)

### Python Pipeline (`scripts/requirements.txt`)

```
httpx>=0.27.0          # HTTP client moderno
requests>=2.31.0      # HTTP client classico
beautifulsoup4>=4.12.0 # HTML parsing
lxml>=5.0.0           # Parser backend
feedparser>=6.0.0    # RSS feed parsing
deep-translator>=1.11.0 # Auto-traduzione EN→IT
tenacity>=9.0.0       # Retry/backoff
```

### Node.js
**Assente.** Nessun `package.json`, nessun npm in produzione.

---

## Tool di Sviluppo

### IDE
- Qualsiasi editor con syntax highlighting HTML/CSS/JS/Python
- (Opzionale) VS Code, PyCharm

### Pipeline Automatizzata
- **GitHub Actions** — Workflow per auto-update giornaliero
- **Git** — Version control

### Validazione
- `scripts/validate_catalog.py` — Validazione catalogo dopo build
- `scripts/validate_free_games.py` — Validazione feed giochi gratuiti

---

## Hosting e Deployment

### Hosting
- **GitHub Pages** — Hosting statico principale
- **Cloudflare** — DNS, proxy, HTTPS, security headers

### Deployment
- Push automatico su branch `main` → GitHub Pages
- Cloudflare proxy per dominio custom `coophubs.net`

### Build Output
```
/index.html           # Homepage
/assets/app.js        # Logica frontend
/assets/style.css     # Stili
/assets/i18n.js       # Traduzioni IT/EN
/assets/games.js      # Database giochi (~334)
/games/*.html         # 334 pagine statiche per SEO
/data/*.json         # Cataloghi esportati
/sitemap.xml         # Sitemap per crawler
/robots.txt          # SEO crawler config
```

---

## Struttura File Chiave

| File | Ruolo |
|------|-------|
| `index.html` | Homepage con catalogo e filtri |
| `assets/app.js` | Logica filtri, rendering, routing |
| `assets/style.css` | Tutti gli stili del sito |
| `assets/i18n.js` | Sistema traduzioni IT/EN |
| `assets/games.js` | Database giochi (legacy) |
| `scripts/*.py` | Pipeline Python per data update |
| `.github/workflows/*.yml` | GitHub Actions |

---

## Note

- Il sito è ottimizzato per performance (lazy loading, cache busting)
- Nessun tracking analytics attivo (GDPR-compliant by design)
- Self-hosted fonts per evitare Google Fonts CDN
