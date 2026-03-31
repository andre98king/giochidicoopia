# Architettura — Co-op Games Hub

## Panoramica

Il sito è un **catalogo statico SEO-friendly** che usa tecniche SPA-like per la navigazione client-side, pur essendo ospitato su GitHub Pages senza backend.

---

## Struttura del Sito

### Pagine Principali

| Pagina | File | Descrizione |
|--------|------|-------------|
| Homepage | `index.html` | Catalogo principale con filtri, ricerca e rendering dinamico |
| Pagina gioco (SEO) | `games/<id>.html` | 334 pagine statiche pre-renderizzate per ogni gioco |
| Giochi gratis | `free.html` | Sezione dedicata alle offerte gratuite con countdown |
| About | `about.html` | Pagina informativa sul progetto |
| Privacy | `privacy.html` | Policy privacy |
| Contatti | `contact.html` | Pagina contatti |

### Asset

```
assets/
├── app.js          # Logica principale: filtri, rendering, modal, ruota random
├── games.js        # Database giochi legacy (~334 giochi)
├── free_games.js   # Feed giochi gratuiti (aggiornato giornalmente)
├── i18n.js         # Sistema traduzioni IT/EN
├── style.css       # Tutti gli stili del sito
├── particles.js    # Animazione background canvas
├── *.png           # Favicon, icone PWA, logo
└── *.svg           # Favicon SVG, logo
```

### Dati

```
data/
├── catalog.public.v1.json   # Catalogo pubblico (usato da app.js)
├── catalog.games.v1.json    # Catalogo completo (admin)
├── hub_editorial.json       # Contenuti editoriali (featured indie)
├── seo_overrides.json       # Override meta title/description
├── backfill_candidates.json # Giochi da aggiungere
└── _nocoop_flagged.json     # Giochi segnalati come non-coop
```

---

## Pattern Architetturali

### 1. SPA-like con Rendering Client-Side

L'app.js carica il catalogo JSON e renderizza le card dinamicamente:

- **Caricamento dati**: Fetch verso `data/catalog.public.v1.json` con fallback a `games.js`
- **Rendering**: Funzione `renderGames()` che genera HTML delle card
- **Infinite scroll**: IntersectionObserver carica le card a chunk (40 iniziali + 30 per scroll)
- **Stato globale**: Variabili in memoria (`catalogGames`, `activeFilters`, `searchQuery`)

### 2. Filtri Client-Side

I filtri sono implementati interamente in JavaScript:

```javascript
// Filtri per categoria (AND logic)
const matchesCat = normalFilters.length === 0 || 
  normalFilters.every(c => game.categories.includes(c));

// Filtri per modalità (AND logic)
const matchesMode = matchesModeFilters(game);

// Filtri combinati
return matchesCat && matchesMode && matchesSearch && matchesYear;
```

**Tipi di filtri**:
- **Genre**: horror, action, puzzle, rpg, survival, factory, roguelike, sport, strategy, indie
- **Speciali**: all, trending, free
- **Modalità**: online, local, split-screen, crossplay
- **Giocatori**: 2, 4+
- **Anno**: 2024+, 2020-2023, 2015-2019, pre-2015

### 3. Sistema traduzioni (i18n)

Il file `i18n.js` contiene:
- Dizionario IT/EN
- Funzione `t()` per tradurre chiavi
- Bottone toggle lingua con evento `langchange`
- Attributi `data-i18n` e `data-i18n-placeholder` per binding automatico

### 4. Modal Interattivo

Le card aprono un modal con dettagli completi:
- Immagine, titolo, tags, rating, players
- Descrizione (italiano o inglese)
- Link store (Steam, Epic, itch.io)
- Link affiliati (Instant Gaming, GameBillet, GMG, Gameseal, Kinguin, GAMIVO)
- Note personali (localStorage)
- Badge "giocato" (localStorage)

### 5. Ruota Random

Canvas-based spinning wheel per suggerimento casuale:
- Campiona dai giochi filtrati attivi
- Animazione CSS/JS con easing
- Click sul risultato apre il modal

---

## Gestione Dati

### games.js (Legacy)

```javascript
const games = [
  {
    id: 1,
    title: "ELDEN RING NIGHTREIGN",
    categories: ["action", "rpg", "survival"],
    genres: ["action", "rpg", "survival"],
    coopMode: ["online"],
    maxPlayers: 3,
    crossplay: false,
    players: "1-3",
    releaseYear: 2025,
    image: "https://...",
    description: "...",
    description_en: "...",
    steamUrl: "https://...",
    rating: 74,
    ccu: 163599,
    trending: true,
    igUrl: "...",
    igDiscount: 31,
    gbUrl: "...",
    gbDiscount: 33,
  },
  // ... ~334 giochi
];
```

### catalog.public.v1.json (Nuovo)

```json
{
  "games": [...],
  "featuredIndieId": 180,
  "updatedAt": "2026-03-31T..."
}
```

### free_games.js

```javascript
const freeGames = [
  {
    title: "Game Title",
    store: "epic",
    storeUrl: "https://...",
    imageUrl: "https://...",
    freeUntil: "2026-04-01T23:59:00Z"
  },
  // ... ~10-20 giochi gratuiti attivi
];
```

---

## Routing e URL

### Struttura URL

```
https://coophubs.net/                      → Homepage
https://coophubs.net/games/<id>.html       → Pagina gioco statico (SEO)
https://coophubs.net/free.html             → Pagina giochi gratuiti
https://coophubs.net/about.html            → About
https://coophubs.net/contact.html          → Contatti
https://coophubs.net/privacy.html          → Privacy
```

### Routing Nativo (Link)

Le pagine `games/<id>.html` sono **statiche pre-generate**:
- Generate dallo script `scripts/build_static_pages.py`
- Ogni gioco ha una pagina HTML con:
  - Meta tags ottimizzati (title, description, og:image)
  - Schema.org VideoGame JSON-LD
  - Canonical e hreflang per i18n SEO
  - Contenuto statico (nessun JS per il rendering)

### Navigazione SPA (Modal)

Il click su una card apre un modal **senza cambiamento URL**:
- ID gioco passato a `openModal(id)`
- Contenuto generato dinamicamente via JavaScript
- Focus trap e keyboard navigation per accessibilità

### Wheel Navigation

La ruota random naviga verso il modal del gioco selezionato:
- Click sul risultato → `closeWheelModal()` + `openModal(winner.id)`

---

## Pipeline di Build

### Script Python

| Script | Funzione |
|--------|----------|
| `build_static_pages.py` | Genera `games/*.html` da `catalog.games.v1.json` |
| `auto_update.py` | Aggiorna dati giochi da Steam/IGDB (GitHub Actions, lunedì) |
| `fetch_free_games.py` | Fetch RSS feed giochi gratuiti (giornaliero) |
| `validate_catalog.py` | Valida catalogo post-build |
| `steam_catalog_source.py` | Adapter per dati Steam |
| `itch_catalog_source.py` | Adapter per dati itch.io |

### GitHub Actions

- **Auto-update**: Workflow settimanale (lunedì) per aggiornare catalogo
- **Free games**: Workflow giornaliero per feed offerte gratuite

---

## Note Tecniche

- **Nessun framework**: JS vanilla, nessun React/Vue/Svelte
- **Nessun backend**: Hosting statico puro (GitHub Pages)
- **Cache busting**: Query param `?v=20260327` su asset
- **Lazy loading**: Immagini con `loading="lazy"` + IntersectionObserver
- **localStorage**: Per stato "giocato" e note personali
- **Accessibility**: ARIA labels, keyboard navigation, skip links
