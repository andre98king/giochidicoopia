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

### 2026-03-14 - Codex

- Eseguita una nuova analisi del progetto per definire una roadmap realistica prima di altre implementazioni.
- Stato confermato:
  - sito statico compatibile con GitHub Pages
  - workflow automatico attivo con `auto_update.py` + `build_static_pages.py`
  - 311 pagine statiche gioco generate in `games/`
  - `robots.txt`, `CNAME` e `sitemap.xml` coerenti con `https://coophubs.net`
- Rischi e gap principali emersi:
  - manca ancora un test visuale/manuale reale di home, pagine informative e pagine statiche gioco
  - footer ancora con anno `2025`, da aggiornare per credibilita
  - pagine informative (`about.html`, `contact.html`, `privacy.html`) restano solo in italiano
  - le pagine gioco statiche sono SEO-friendly in italiano, ma non esiste ancora una vera strategia SEO bilingue con pagine dedicate o `hreflang`
  - `privacy.html` menziona analytics/cookie opzionali, ma nel codice non risultano script analytics o banner consenso
  - esiste `manifest.json`, ma non risulta una registrazione `serviceWorker`; PWA quindi solo parziale
  - il filtro `mode_crossplay` esiste nelle traduzioni ma non e attivo nella configurazione filtri di `app.js`
- Roadmap consigliata:
  - Priorita 1: QA e credibilita immediata
    - test browser desktop/mobile
    - controllo pagine statiche generate
    - aggiornamento anno footer
    - verifica finale dei link interni e delle CTA store
  - Priorita 2: coerenza contenuti e policy
    - riallineare `privacy.html` a cio che il sito fa davvero
    - chiarire eventuale uso futuro di analytics o affiliazioni
    - rifinire eventuali testi hardcoded residui
  - Priorita 3: internazionalizzazione reale
    - decidere se mantenere solo UI bilingue oppure introdurre anche pagine informative e SEO bilingue
    - se si punta al mercato EN, valutare pagine statiche dedicate o strategia `hreflang`
  - Priorita 4: UX e filtri
    - valutare attivazione reale filtro crossplay
    - rifinire filtri mobile e dettaglio pagine gioco
  - Priorita 5: crescita tecnica prudente
    - migliorare validazioni del generatore statico
    - eventuale PWA vera solo se utile, senza aggiungere complessita inutile
- Se intervieni dopo questa nota, leggere prima `CLAUDE.md` e poi questa roadmap per mantenere la stessa priorita di esecuzione.

### 2026-03-14 - Codex - Step roadmap 1

- Avviata la prima implementazione della roadmap partendo dalla credibilita immediata del sito.
- Corretto il footer con anno `2026` nelle pagine principali:
  - `index.html`
  - `game.html`
  - `about.html`
  - `contact.html`
  - `privacy.html`
- Aggiornato anche il template del generatore in `build_static_pages.py` usando `CURRENT_YEAR = datetime.date.today().year`, cosi le pagine statiche gioco non restano bloccate all'anno precedente dopo i rebuild.
- Eseguito `python3 build_static_pages.py` dopo la modifica:
  - rigenerate 311 pagine statiche in `games/`
  - `sitemap.xml` aggiornato dal generatore
- Verifica tecnica rapida:
  - campioni controllati `games/1.html`, `games/50.html`, `games/311.html` con footer `2026`
  - conteggio pagine statiche confermato: 311
- Ancora da fare in questa priorita:
  - test visuale reale in browser desktop/mobile
  - controllo manuale home + una pagina informativa + una pagina gioco statica dopo deploy o server locale

### 2026-03-14 - Codex - Step roadmap 2

- Eseguito il secondo blocco di fix puntando su coerenza contenuti + guardrail tecnici.
- Modifiche chiuse:
  - `privacy.html` riscritta per riflettere il comportamento reale del sito
    - chiarito uso effettivo di `localStorage` (`coopLang`, `coopAdminData`)
    - rimosse affermazioni fuorvianti su analytics attivi, cookie opzionali e link affiliati gia in uso
    - mantenuti solo riferimenti coerenti con il sito attuale: hosting statico, link esterni a store, nessun backend proprietario
  - aggiunto `validate_catalog.py`
    - valida `games.js`
    - controlla coerenza tra catalogo, pagine statiche generate e `sitemap.xml`
    - emette warning se il dataset crossplay e ancora completamente vuoto
  - aggiornato `.github/workflows/update.yml`
    - dopo `build_static_pages.py` ora esegue `python3 validate_catalog.py` prima del commit automatico
  - corretto il dato mancante `description_en` per `Moving Out 2` in `games.js`
- Eseguito dopo le modifiche:
  - `python3 build_static_pages.py`
  - `python3 validate_catalog.py`
  - `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py`
- Risultato verifiche:
  - validazione passata con `311` giochi e `311` pagine statiche
  - warning intenzionale rimasto: nessun gioco attualmente marcato come `crossplay`
- Nota operativa:
  - durante i test locali non lanciare build e validazione in parallelo, perche il check sulle pagine statiche deve partire dopo la fine del rebuild
  - nel workflow GitHub Actions non c'e problema: gli step sono gia sequenziali
- Prossimo passo consigliato per Claude Code:
  - QA manuale reale di `index.html`, `privacy.html` e almeno 2 pagine in `games/`
  - verifica copy, leggibilita mobile, link store e coerenza percepita della nuova privacy policy

### 2026-03-14 - Claude Code - QA manuale reale

- Eseguito QA live su `https://coophubs.net/` dopo deploy. Pagine testate: homepage, `privacy.html`, `games/1.html`, `games/50.html`, `games/100.html`.
- **Problema critico trovato: 321 file locali (Codex) mai pushati.**
  - Includono: footer anno 2025→2026, privacy riscritta, validate_catalog.py nel workflow, fix Moving Out 2, sitemap rigenerata
  - Il sito live mostra ancora la versione precedente (footer 2025, privacy vecchia)
  - Causa: Codex ha fatto le modifiche localmente ma non ha pushato

- Problemi trovati ordinati per gravita:

  1. **CRITICO — Modifiche Codex non pushate** (321 file)
     - Footer anno sbagliato (2025 vs 2026) su tutto il sito live
     - Privacy policy live ancora con riferimenti a analytics/cookie/affiliati inesistenti
     - Fix: commit e push dei file locali
     - File: tutti (games/, index.html, privacy.html, about.html, contact.html, game.html, build_static_pages.py, .github/workflows/update.yml, AI_COLLABORATION.md, sitemap.xml, games.js)

  2. **MEDIO — Privacy live incoerente con sito reale**
     - La versione live menziona "strumenti di analisi", "cookie opzionali", "link affiliati" — nessuno di questi esiste
     - La versione locale (Codex) e gia corretta e allineata al comportamento reale
     - Fix: pushare la versione locale

  3. **BASSO — Accenti mancanti nella privacy live**
     - "e" al posto di "e'" in vari punti ("il Sito e un progetto", "conformita")
     - La versione locale (Codex) ha lo stesso problema ma testo piu coerente nel contenuto
     - Fix futuro: correggere gli accenti nella privacy riscritta

  4. **BASSO — Cloudflare Email Obfuscation**
     - L'email in contact.html viene offuscata da Cloudflare (cdn-cgi/l/email-protection)
     - Il link mailto dovrebbe comunque funzionare (decodifica client-side)
     - Fix opzionale: disattivare Scrape Shield > Email Obfuscation su Cloudflare

- Verifiche positive:
  - Homepage: filtri, footer, SEO meta, structured data presenti e corretti
  - Pagine gioco statiche: titolo, immagine, descrizione, link Steam/Epic funzionanti
  - game.html: fallback con noindex, canonical verso pagina statica
  - sitemap.xml: 322 URL nel formato corretto
  - robots.txt: punta alla sitemap corretta
  - Skip link: correttamente nascosta fino al focus

- Decisione: pushare le modifiche Codex locali come prossimo step immediato
- Feature in design: sezione "Giochi Gratis" con spec approvata in `docs/superpowers/specs/2026-03-14-free-weekly-games-design.md`
