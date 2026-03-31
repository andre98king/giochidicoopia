# Convenzioni del Codebase

Questo documento definisce gli standard di codifica usati nel progetto Co-op Games Hub.

---

## 1. Style Guide CSS

### Convenzioni di Naming

- **Classi**: kebab-case (es. `.card-title`, `.btn-primary`)
- **Variabili CSS**: `--nome-variable` in `:root`
- **BEM-like**: usa `--` per varianti (es. `.btn-primary--large`)

### Organizzazione

1. **Font**: Self-hosted via `@font-face` (GDPR compliant, no Google Fonts CDN)
2. **Reset**: `*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }`
3. **Variables**: Definite in `:root` per colori, spacing, breakpoint
4. **Mobile-first**: Media queries a `640px`, `600px`

```css
:root {
  --bg: #08090d;
  --accent: #6b5ce0;
  --radius: 14px;
}
```

### Pattern Ricorrenti

- **Card**: `.card` con `.card-img-wrapper`, `.card-body`, `.card-footer`
- **Badge**: `.tag-{category}` per tag categorie
- **Button**: `.btn-{type}` (`.btn-primary`, `.btn-details`, `.btn-store`)
- **Modal**: `.modal-overlay`, `.modal` con transizioni CSS

---

## 2. Style Guide JavaScript

### Naming

| Tipo | Convenzione | Esempio |
|------|-------------|---------|
| Variabili | camelCase | `activeFilters`, `catalogGames` |
| Costanti | SCREAMING_SNAKE | `AFFILIATE`, `WHEEL_COLORS` |
| Funzioni | camelCase | `renderGames()`, `openModal()` |
| Private | prefix `_` | `_renderBatch()`, `_trapFocus()` |
| CSS selectors | kebab-case | `document.querySelector('.card-img')` |

### Struttura File

```javascript
// ===== SECURITY =====
function esc(str) { ... }  // HTML sanitizer

// ===== STATE =====
let activeFilters = new Set();
let catalogGames = [];

// ===== FILTER CONFIG =====
const filterGenres = [...];
const modeFilters = [...];

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async () => { ... });

// ===== RENDER =====
function renderGames() { ... }
```

### Pattern Utilizzati

- **XSS Protection**: sempre usare `esc()` per output utente
- **Template Literals**: per HTML inline con sicurezza
- **Async/Await**: per fetch e operazioni asincrone
- **Event Delegation**: per elementi dinamici
- **IntersectionObserver**: per infinite scroll e lazy loading

### ES6+ Features

- Arrow functions per callbacks
- Destructuring per oggetti
- `Set` per collezioni uniche
- `async/await` per operazioni async

---

## 3. Struttura Dati Gioco (games.js)

```javascript
{
  id: 1,                          // ID numerico fisso (NON modificare)
  title: "Nome Gioco",
  categories: ["action", "indie"], // Array, NON booleani
  genres: ["action"],             // (opzionale, legacy)
  coopMode: ["online", "local"],  // Array: "online" | "local" | "split"
  maxPlayers: 4,                  // Numero massimo giocatori
  players: "1-4",                // Stringa range per UI
  crossplay: false,              // Boolean, solo se verificato
  image: "https://shared.cloudflare.steamstatic.com/...",
  description: "...",            // Italiano
  description_en: "...",         // Inglese (OBBLIGATORIO)
  steamUrl: "https://store.steampowered.com/app/APPID/",
  rating: 74,                    // Intero 0-100 (Steam)
  ccu: 12000,                    // Concurrent users (SteamSpy)
  releaseYear: 2024,             // Anno di uscita
  trending: false,              // Boolean per badge
  igUrl: "...",                  // Instant Gaming (opzionale)
  igDiscount: 40,               // Sconto % (opzionale)
  gbUrl: "...",                 // GameBillet (opzionale)
  gbDiscount: 25,              // Sconto % (opzionale)
}
```

### Note Importanti

- `"free"` e `"indie"` sono **valori nell'array categories**, NON campi booleani
- Il filtro "Gratis" usa `categories.includes('free')`
- `coopMode` deve essere sincronizzato con `categories` (es. "splitscreen" in categories ↔ "split" in coopMode)

---

## 4. Convenzioni Git Commit

### Formato

```
<tipo>(scope): <descrizione>
```

### Tipi

| Tipo | Uso |
|------|-----|
| `feat:` | Nuove funzionalità |
| `fix:` | Bug fix |
| `chore:` | Manutenzione, refactor minori |
| `docs:` | Documentazione |
| `seo:` | Ottimizzazione motori ricerca |
| `cleanup:` | Rimozione codice unused |
| `🤖` (emoji) | Auto-update (bot) |

### Esempi

```
feat: aggiungi sistema note personali
fix: correggi app ID errati (DEVOUR/KeyWe)
seo: implementazione segnali E-E-A-T
chore: aggiorna .gitignore
🤖 Auto-update database giochi
docs: aggiornamento roadmap progetto
cleanup: rimuovi file duplicati
```

### Regole

- Descrizione breve (max 72 char)
- Italian per messaggiutente, English per tecnico
- Non fare push autonomamente — proporre modifiche

---

## 5. Convenzioni Python (scripts)

### Naming

- `snake_case` per funzioni e variabili
- `PascalCase` per classi (se usate)
- Costanti in `SCREAMING_SNAKE`

### Struttura

```python
#!/usr/bin/env python3
"""Docstring modulo."""

from __future__ import annotations
import collections
import json
import xml.etree.ElementTree as ET

# Imports locali
import build_static_pages
import catalog_data

def main() -> int:
    """Main function."""
    errors = []
    # ...
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

### Type Hints

```python
def short_list(items, limit: int = 10) -> str:
    items: list = list(items)
    # ...
```

---

## 6. Struttura File e Directory

```
assets/
  app.js           # Logica principale (filtri, render, modal)
  style.css        # Tutti gli stili
  i18n.js          # Traduzioni IT/EN
  particles.js     # Background animato

scripts/
  build_static_pages.py   # Genera pagine statiche + sitemap
  validate_catalog.py     # Validazione catalogo
  auto_update.py          # Update automatico giochi
  fetch_free_games.py     # Aggiorna giochi gratuiti
  catalog_data.py         # Layer I/O dati
  catalog_config.py       # Configurazione pipeline

games/
  {id}.html        # 334 pagine statiche SEO

data/
  catalog.json            # Catalogo canonico
  catalog.public.v1.json  # Export pubblico
```

---

## 7. Regole Generali

1. **Nessun backend** — solo statico
2. **Nessun npm** — solo vanilla JS
3. **Compatibilità GitHub Pages**
4. **Preserva ID giochi** — mai rinumerare
5. **XSS protection** — usa sempre `esc()`
6. **Mobile-first** — priorità UX mobile
7. **GDPR compliant** — no Google Fonts CDN, no analytics
