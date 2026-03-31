# Integrazioni Esterne — Co-op Games Hub

## Servizi Esterni

### Steam API
- **Steam Store** — Link diretti ai giochi
- **SteamSpy** — Dati CCU (concurrent users) per trending
- **Steam API** — Rating, descrizioni, immagini
- **IGDB (Internet Games Database)** — Metadati giochi, discovery nuovi titoli

### Other Game Stores
- **Epic Games Store** — Link diretti
- **itch.io** — RSS feed per indie games
- **GOG.com** — Dati giochi (in pipeline)

### Hosting & CDN
- **GitHub Pages** — Hosting statico del sito
- **Cloudflare** — DNS, proxy, HTTPS, security headers
- **Cloudflare Images** — CDN per immagini giochi ( Steam shared static)

---

## Link Affiliazione

### Programmi Attivi

| Store | Stato | Commissione | ID Affiliato |
|-------|-------|-------------|-------------|
| **Instant Gaming** | Attivo | 3% | `gamer-ddc4a8` |
| **GameBillet** | Attivo | 5% | `fb308ca0-647e-4ce7-9e80-74c2c591eac1` |
| **Green Man Gaming** | Attivo (Impact) | 5%/2% | `https://greenmangaming.sjv.io/qWzoQy` |
| **Gameseal** | Attivo (CJ) | varia | `https://www.tkqlhce.com/click-101708519-17170422` |
| **Kinguin** | Attivo (CJ) | varia | `https://www.tkqlhce.com/click-101708519-15734285` |
| **GAMIVO** | Attivo (CJ) | varia | `https://www.tkqlhce.com/click-101708519-15839605` |

### Programmi in Approvazione

| Store | Stato |
|-------|-------|
| **GOG** | Application inviata (2026-03-18) |
| **MacGameStore** | Approvato (5%) |
| **WinGameStore** | Link scaduto (email support 2026-03-18) |

### Implementazione nel Codice

I link affiliazione sono definiti in `assets/app.js`:

```javascript
const AFFILIATE = {
  gog:  ,           // In attesa
  ig:   gamer-ddc4a8,
  gb:   fb308ca0-647e-4ce7-9e80-74c2c591eac1,
  gmg:  https://greenmangaming.sjv.io/qWzoQy,
  gameseal: https://www.tkqlhce.com/click-101708519-17170422,
  kinguin: https://www.tkqlhce.com/click-101708519-15734285,
  gamivo:  https://www.tkqlhce.com/click-101708519-15839605,
};
```

I link usano `rel="sponsored"` come da best practice SEO.

---

## Analytics

### Analytics Attivi
**Nessuno.** Il sito non usa:
- Google Analytics
- Matomo/Piwik
- Hotjar
- Pixel Facebook

Il sito è **GDPR-compliant by design** — nessun tracking, nessun cookie.

### Motivazione
Dalla privacy policy: preferenze salvate in locale (localStorage), nessun analytics attivo.

---

## SEO

### Structured Data
- **WebSite** — Homepage
- **Organization** — Editore
- **SearchAction** — Barra ricerca
- **VideoGame** — Pagine singole giochi

### Sitemap
- ~555+ URL con hreflang it/en/x-default
- Generata automaticamente da `scripts/build_static_pages.py`

### robots.txt
Blocca crawler AI training (GPTBot, ClaudeBot, Google-Extended, Bytespider, PerplexityBot, CCBot)
Mantiene indexing per Googlebot/Bingbot.

---

## Altre Integrazioni

### Impact.com
- **Site verification**: `19bc31b9-e3f1-4c40-b5bf-c454cd450868`
- Username: `coophubs`
- Usato per Green Man Gaming

### Ko-fi
- **Link**: `https://ko-fi.com/coophubs`
- Pulsante floating + strip nel footer
- Unica forma di monetizzazione attiva

### Google Search Console
- Proprietà: `sc-domain:coophubs.net` (domain property)
- MCP configurato in locale (`/home/andrea/.claude/mcp-gsc/`)

---

## Note

- Nessun backend = nessun dato utente memorizzato server-side
- Preferenze utente (giocati, note) salvate in localStorage browser
- Nessun PII trasmesso a terze parti
- Link esterni (store) usano `rel="noopener noreferrer"`
