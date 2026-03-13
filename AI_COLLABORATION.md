# AI Collaboration Notes

Questo file serve come punto di handoff condiviso tra Codex e Claude Code.

## Scopo

- lasciare contesto utile direttamente nel progetto
- evitare decisioni perse in chat
- rendere chiaro cosa e stato fatto, cosa e in corso e cosa va verificato

## Regole di collaborazione

- Salvare sempre le modifiche nei file del progetto, non lasciarle solo in chat.
- Aggiornare questo file dopo modifiche non banali o quando si scopre qualcosa di importante.
- Scrivere note brevi, concrete e verificabili.
- Segnalare sempre se una conclusione e confermata o solo un'ipotesi da controllare.
- Non sovrascrivere lavoro altrui senza prima leggere lo stato corrente del file e dei file toccati.

## Stato progetto

- Progetto: sito statico "Co-op Games Hub"
- Hosting target: GitHub Pages / dominio custom
- Stack: HTML, CSS, JavaScript, Python per aggiornamento dati
- File principali: `index.html`, `app.js`, `games.js`, `i18n.js`, `style.css`, `game.html`, `auto_update.py`

## Note utili correnti

- Rispettare sempre le regole definite in `CLAUDE.md`.
- Preferire modifiche piccole, leggibili e compatibili con hosting statico.
- Se una modifica influenza SEO, dominio, deploy o struttura dati, annotarlo qui.

## Log condiviso

### 2026-03-13 - Codex

- Creato questo file come canale di handoff tra agenti.
- Aggiornato `CLAUDE.md` per richiamare esplicitamente questo file come punto di collaborazione condiviso.
- Intenzione: usarlo per lasciare decisioni tecniche, stato dei lavori e punti da verificare.
- Implementata una prima tornata di fix statici a basso rischio:
  - creato `contact.html`
  - aggiunti link `about` e `contact` nel footer della home
  - aggiunti link `about`, `contact` e `privacy` nel footer di `game.html`
  - aggiunto footer anche a `privacy.html`
  - aggiunte voci footer nel sistema traduzioni (`i18n.js`)
  - aggiunte `about.html` e `contact.html` in `sitemap.xml`
  - aggiornato `README.md` da `196+` a `300+` giochi
- Seconda tornata sulla credibilità del sito:
  - riscritta `about.html` con testo editoriale più credibile e diretto
  - aggiornata `contact.html` con email `coophubs@gmail.com`
  - allineato il testo breve del footer nelle pagine principali
- Terza tornata lato metadati e SEO statico:
  - aggiunti metadati `description`, `theme-color`, Open Graph e Twitter su `about.html`, `contact.html` e `privacy.html`
  - aggiunto JSON-LD leggero su pagine informative
  - migliorati fallback SEO di `game.html` con `robots`, canonical, Open Graph e Twitter più completi
- Quarta tornata per SEO reale delle schede gioco:
  - creato `build_static_pages.py` per generare pagine statiche in `games/<id>.html`
  - aggiornati i link del sito verso le nuove pagine statiche
  - trasformato `game.html` in fallback legacy con `noindex` e canonical verso la pagina statica
  - aggiornato il workflow GitHub Actions per rigenerare pagine statiche e sitemap
  - eseguito localmente `build_static_pages.py`: generate 311 pagine statiche e nuova `sitemap.xml`
- Verifica eseguita:
  - controllo automatico dei riferimenti locali nelle pagine HTML: nessun link statico mancante
- Punti ancora aperti:
  - `about.html`, `contact.html`, `CLAUDE.md` e `AI_COLLABORATION.md` vanno controllati lato versionamento/publish nel repository.
  - Fare un test visuale in browser di home, pagina gioco statica e pagine informative.

## Handoff rapido per Claude Code

- Obiettivo completato: migliorare la credibilita del sito e sistemare la base SEO senza introdurre backend o framework.
- Pagine informative:
  - `about.html` riscritta con tono piu credibile e semplice.
  - `contact.html` creata/aggiornata con email `coophubs@gmail.com`.
  - `privacy.html` allineata con footer coerente.
- Footer:
  - link presenti in ordine `Sul progetto` -> `Contatti` -> `Privacy Policy`
  - testo breve: "Coophubs e un progetto indipendente dedicato alla scoperta di giochi cooperativi per PC."
- SEO schede gioco:
  - nuovo script `build_static_pages.py`
  - genera pagine statiche in `games/<id>.html`
  - `app.js` ora linka alle pagine statiche
  - `game.html` e fallback legacy con `noindex` e canonical verso la pagina statica
  - `sitemap.xml` ora usa gli URL statici sotto `games/`
  - workflow GitHub Actions aggiornato per rigenerare pagine statiche e sitemap
- Output generato localmente:
  - eseguito `python3 build_static_pages.py`
  - generate 311 pagine in `games/`
- Verifiche gia fatte:
  - controllo automatico riferimenti HTML statici: nessun link mancante
- File chiave da leggere per capire il lavoro:
  - `AI_COLLABORATION.md`
  - `CLAUDE.md`
  - `build_static_pages.py`
  - `app.js`
  - `game.html`
  - `.github/workflows/update.yml`
- Prossimo passo consigliato:
  - test visuale reale delle pagine statiche e controllo publish/versionamento dei file nuovi o ancora untracked
