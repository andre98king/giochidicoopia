# Free Games — Design Spec

## Obiettivo
Aggiungere al sito una sezione che mostra i giochi attualmente gratuiti su Epic Games, Steam, GOG e Humble Bundle, con countdown FOMO e link diretto per riscattarli.

## Vincoli
- Sito statico su GitHub Pages, nessun backend
- Nessuna modifica alla struttura dati giochi esistente
- Compatibilita mobile prioritaria
- Pattern coerente con architettura esistente (games.js, auto_update.py)
- Solo librerie Python stdlib + `requests` + `beautifulsoup4` (nessun headless browser)

## Architettura

### Dati: `fetch_free_games.py` + `free_games.js`
Nuovo script Python eseguito da GitHub Actions con cron giornaliero (`0 7 * * *`).

**Dipendenze**: `requests`, `beautifulsoup4` (installate via `pip install` nel workflow).

Interroga le API/feed di:
- **Epic Games**: GraphQL API (`store-site-backend-official.ol.epicgames.com`) — API pubblica, la piu affidabile
- **Steam**: Store API (`store.steampowered.com/api`) — filtra per `is_free` + controllo promo temporanee. Endpoint non documentato ma stabile.
- **GOG**: scraping pagina giveaway con `requests` + `BeautifulSoup`
- **Humble Bundle**: scraping pagina free games con `requests` + `BeautifulSoup`

Scrive `free_games.js` con struttura:
```js
const freeGames = [
  {
    title: "Control",
    store: "epic",           // epic | steam | gog | humble
    imageUrl: "https://...", // immagine 16:9
    storeUrl: "https://...", // link diretto allo store
    freeUntil: "2026-03-20T16:00:00Z" // ISO timestamp fine offerta
  }
];
```

Regole dello script:
- Rimuove automaticamente offerte scadute
- **Fallback completo**: se nessuna API risponde, mantiene il file precedente intatto
- **Fallback parziale**: se solo alcuni store falliscono, mantiene le entry precedenti per quegli store e aggiorna gli altri
- `daysLeft` non viene salvato nel file, viene calcolato client-side in tempo reale
- Log chiaro per ogni store: successo, fallback, errore

### Banner homepage
Posizionato tra i filtri e la griglia giochi in `index.html`.

Componenti:
- Titolo sezione: "Gratis Ora" (i18n)
- Riga di card scorrevoli orizzontalmente (CSS `overflow-x: auto`, scroll-snap)
- Link "Vedi tutte le offerte" che porta a `free.html`
- Appare solo se `freeGames.length > 0`

Ogni card mostra:
- Immagine gioco (16:9, lazy loading)
- Badge store in alto a sinistra (colore per store: Epic=blu, Steam=nero, GOG=viola, Humble=arancione)
- Titolo gioco
- Countdown FOMO calcolato client-side da `freeUntil`:
  - `> 1 giorno`: "Scade tra X giorni"
  - `< 24h`: "Ultime Xh!" (testo rosso)
  - `< 1h`: "Ultima ora!" (pulse animation, `prefers-reduced-motion` respected)
  - Scaduto: card nascosta automaticamente
- Bottone "Riscatta gratis" con link diretto (`target="_blank" rel="noopener"`)

**Countdown refresh**: `setInterval` ogni 60 secondi. Quando un gioco entra nella fascia < 1h, l'intervallo per quella card scende a 1 secondo. Cleanup con `clearInterval` non necessario (pagina statica, no SPA navigation).

**Accessibilita**:
- Countdown con `aria-live="polite"` per screen reader
- Testo rosso urgenza con contrasto >= 4.5:1 su sfondo scuro
- Pulse animation rispetta `prefers-reduced-motion: reduce`

Responsive:
- Mobile: swipe orizzontale, card larghe ~80% schermo
- Desktop: 3-4 card visibili

### Cross-link con catalogo
Se un gioco gratuito e anche presente in `games.js`, la card nel catalogo principale mostra un badge "Gratis ora!" in overlay. Matching basato su titolo (case-insensitive, trim).

### Pagina dedicata: `free.html`
Pagina scritta a mano, stessa struttura di `about.html`/`contact.html` (layout, back link, footer).

`build_static_pages.py` NON gestisce `free.html` — e un file manuale come `about.html`.

Contenuto:
- Carica `free_games.js` con `<script defer>`
- Card grandi con immagine, badge store, countdown, link "Riscatta gratis"
- Ordinate per scadenza piu vicina
- Se zero giochi: messaggio "Nessuna offerta gratuita al momento. Torna domani!"
- SEO completo: title, meta description, canonical, OG
- Aggiunta manualmente in `sitemap.xml`

**Ordine caricamento script in `free.html`:**
```html
<script src="free_games.js" defer></script>
<script src="i18n.js" defer></script>
<script src="particles.js" defer></script>
<!-- inline script wrapped in DOMContentLoaded -->
```

**Ordine caricamento script in `index.html`:**
```html
<script src="games.js" defer></script>
<script src="free_games.js" defer></script>  <!-- NUOVO -->
<script src="i18n.js" defer></script>
<script src="particles.js" defer></script>
<script src="app.js" defer></script>
```
`free_games.js` viene caricato prima di `app.js`, quindi `freeGames` e disponibile quando `app.js` esegue.

### Navigazione
- Link a `free.html` aggiunto nel footer di tutte le pagine (accanto a Sul progetto, Contatti, Privacy)
- Link "Vedi tutte le offerte" nel banner homepage

### GitHub Actions: `free_games.yml`
Workflow **separato** da `update.yml` (che resta settimanale e invariato).

```yaml
name: Update Free Games
on:
  schedule:
    - cron: '0 7 * * *'  # Ogni giorno alle 7 UTC
  workflow_dispatch:

jobs:
  update-free:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4.2.2

      - name: Set up Python
        uses: actions/setup-python@v5.6.0
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests beautifulsoup4

      - name: Fetch free games
        run: python3 fetch_free_games.py

      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add free_games.js
          if git diff --staged --quiet; then
            echo "Nessuna modifica da committare."
          else
            git commit -m "🎁 Auto-update giochi gratuiti [skip ci]"
            git push
          fi
```

**Nota**: `sitemap.xml` NON viene rigenerato da questo workflow. `free.html` viene aggiunta manualmente una sola volta alla sitemap.

### i18n
Nuove chiavi in `i18n.js`:
- `free_now`: "Gratis Ora" / "Free Now"
- `expires_in_days`: "Scade tra {n} giorni" / "Expires in {n} days"
- `last_hours`: "Ultime {n}h!" / "Last {n}h!"
- `last_hour`: "Ultima ora!" / "Last hour!"
- `claim_free`: "Riscatta gratis" / "Claim free"
- `see_all_offers`: "Vedi tutte le offerte" / "See all offers"
- `no_free_games`: "Nessuna offerta gratuita al momento. Torna domani!" / "No free offers right now. Check back tomorrow!"
- `free_now_badge`: "Gratis ora!" / "Free now!"

## File coinvolti

| File | Azione | Note |
|---|---|---|
| `fetch_free_games.py` | Nuovo | Script fetch API/scraping |
| `free_games.js` | Nuovo (generato) | Dati giochi gratis |
| `free.html` | Nuovo (manuale) | Pagina dedicata |
| `.github/workflows/free_games.yml` | Nuovo | Cron giornaliero |
| `app.js` | Modifica | Render banner, countdown, badge catalogo |
| `index.html` | Modifica | Script tag `free_games.js` + contenitore banner |
| `i18n.js` | Modifica | Nuove chiavi |
| `style.css` | Modifica | Stili banner, card free, badge, countdown |
| `sitemap.xml` | Modifica | Aggiunta `free.html` (una tantum) |
| Footer tutte le pagine | Modifica | Link a `free.html` |

File NON modificati: `games.js`, `game.html`, `games/`, `auto_update.py`, `update.yml`, `build_static_pages.py`

## Rischi
- **API Epic Games**: la piu affidabile, raramente cambia. Rischio basso.
- **Steam free-to-keep**: endpoint non documentato, potrebbe cambiare. Rischio medio.
- **GOG/Humble scraping**: struttura HTML puo cambiare. Rischio medio-alto. Mitigato: fallback parziale.
- **Commit giornaliero**: ~1 commit/giorno al repo, trascurabile.
- **Zero giochi gratis**: la sezione non appare, nessun impatto UX.
