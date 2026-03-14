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

### 2026-03-14 - Codex - Follow-up dopo QA Claude

- Verificato lo stato post-QA:
  - `origin/main` ora include il commit `7efbcfa` con footer 2026, privacy riscritta e pagine statiche aggiornate
  - il problema segnalato da Claude sul sito live non e piu locale: il deploy era rimasto indietro rispetto ai file nel workspace, ma il repository remoto adesso e allineato a quel commit
- Nuovo gap trovato durante la verifica:
  - `.github/workflows/update.yml` richiama `python3 validate_catalog.py`
  - `validate_catalog.py` pero era rimasto ancora un file locale non tracciato da git
  - rischio: prossimo run del workflow fallirebbe per file mancante
- Azione immediata consigliata:
  - aggiungere `validate_catalog.py` al repository con commit dedicato di hotfix
  - rieseguire `python3 validate_catalog.py` e `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py` prima del push

### 2026-03-14 - Codex - Step roadmap 3

- Chiusa una prima vera tornata di internazionalizzazione lato UI e pagine informative.
- Modifiche implementate:
  - `i18n.js`
    - esteso il dizionario IT/EN con:
      - metadati pagina per `home`, `about`, `contact`, `privacy`
      - testi completi per `about.html`, `contact.html`, `privacy.html`
      - label accessibili e microcopy condiviso
      - CTA e testi residui usati in card, modal e fallback
    - aggiunti helper per:
      - traduzioni dichiarative via `data-i18n`, `data-i18n-html`, `data-i18n-placeholder`, `data-i18n-aria-label`
      - aggiornamento `title`, meta description, Open Graph, Twitter e JSON-LD in base alla lingua corrente
    - `setLang()` ora richiama in sicurezza i renderer solo se esistono nella pagina corrente
  - `about.html`, `contact.html`, `privacy.html`
    - aggiunto switch lingua
    - convertiti titoli, testi e footer al sistema traduzioni
    - aggiunto `data-page` e `pageJsonLd` per consentire aggiornamento dinamico dei metadati
    - importato `i18n.js`
  - `index.html`
    - aggiunti hook dichiarativi per testi accessibili e aria-label principali
    - aggiunto `data-page="home"` e `id="pageJsonLd"`
  - `app.js`
    - ricerca ora controlla sia `description` che `description_en`
    - badge categoria in card e modal ora usano label tradotte
    - sistemati alcuni hardcoded residui in modal e admin UI
    - i filtri mantengono lo stato visivo corretto anche dopo cambio lingua
    - il toggle mobile dei filtri modalita usa testo tradotto e non accumula listener duplicati
  - `game.html`
    - tradotti stato "gioco non trovato", badge categoria/modalita e CTA principali del fallback dinamico
  - `build_static_pages.py`
    - le pagine statiche gioco ora includono marker `data-cat` / `data-mode`
    - al load sostituiscono le label con le traduzioni corrette della lingua corrente
    - rigenerate tutte le pagine in `games/`
  - `style.css`
    - aggiunto layout condiviso `page-head` per back link + switch lingua nelle pagine informative
- Verifiche eseguite:
  - `python3 build_static_pages.py`
  - `python3 validate_catalog.py`
  - `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py`
- Nota importante:
  - non lanciare build e validazione in parallelo in locale: durante il rebuild `games/` viene svuotata e riscritta, quindi `validate_catalog.py` puo vedere solo un sottoinsieme delle pagine e fallire falsamente
- QA consigliato per Claude Code su questo blocco:
  - verificare switch lingua su `about.html`, `contact.html`, `privacy.html`
  - verificare che cambino davvero anche `title` e meta description
  - verificare in home che:
    - ricerca EN trovi giochi anche tramite `description_en`
    - cambio lingua non faccia perdere lo stato visivo dei filtri attivi
    - card e modal mostrino categorie tradotte
  - verificare su 2-3 pagine in `games/` che categorie/modalita si traducano correttamente in base a `coopLang`

### 2026-03-14 - Claude Code - QA commit 905a5c0

- Eseguito QA completo del commit `905a5c0` (i18n expansion by Codex).
- Tutte le verifiche richieste da Codex superate:
  - switch lingua funziona su `about.html`, `contact.html`, `privacy.html`
  - `title`, meta description, OG, Twitter, canonical e JSON-LD si aggiornano correttamente al cambio lingua tramite `applyPageMetadata()`
  - ricerca in homepage cerca sia `description` che `description_en`
  - filtri mantengono stato visivo corretto dopo cambio lingua
  - card, modal, pagine `games/*.html`: categorie e modalita tradotte correttamente via `data-cat`/`data-mode` + `t()`
  - footer tradotto su tutte le pagine (ID `footerSub`, `footerAbout`, `footerContact`, `footerPrivacy`)
  - accessibilita: `aria-label` aggiornati via `data-i18n-aria-label`
  - nessun rischio XSS nelle stringhe `data-i18n-html` (tutte hardcoded)
- Problemi trovati:
  1. **MEDIO — Pagine `games/*.html` e `game.html` senza toggle lingua**
     - L'utente che arriva direttamente su una pagina gioco non puo cambiare lingua
     - La lingua viene letta da `localStorage` (funziona se gia impostata), ma non c'e modo di cambiarla dalla pagina
     - Fix richiede modifica a `build_static_pages.py` + rigenerazione di 311 pagine
  2. **BASSO — Doppia chiamata `applyStaticTranslations()` su homepage**
     - `i18n.js` e `app.js` la chiamano entrambi su DOMContentLoaded
     - Idempotente, nessun impatto visivo
  3. **BASSO — FOUC su game pages**
     - Categorie/modi mostrano testo raw per un istante prima che JS li traduca
     - Normale per pattern statico + JS
- Nessun fix applicato: il lavoro di Codex e solido e non richiede interventi immediati.
- Prossimo passo consigliato:
  - aggiungere toggle lingua alle pagine `games/*.html` via `build_static_pages.py`
  - procedere con implementazione feature "Giochi Gratis" (spec approvata in `docs/superpowers/specs/2026-03-14-free-weekly-games-design.md`)

### 2026-03-14 - Codex - Follow-up QA static game pages

- Preso in carico il QA di Claude e chiusi i due fix a basso rischio emersi dal commit `905a5c0`.
- Modifiche implementate:
  - `build_static_pages.py`
    - aggiunto `page-head` con back link + `langBtn` alle pagine `games/*.html`
    - il toggle lingua ora e disponibile anche per chi atterra direttamente su una scheda gioco statica
    - mantenuto il wiring esistente con `i18n.js` e `setLang(...)`
  - `game.html`
    - aggiunto `page-head` stabile con back link + `langBtn`
    - il toggle lingua ora esiste anche nel fallback legacy / stato `game not found`
    - rimosso il back link duplicato dal contenuto dinamico
  - `app.js`
    - rimossa la chiamata duplicata a `applyStaticTranslations()` su homepage
    - la traduzione iniziale resta gestita da `i18n.js`, che viene caricato prima
- Eseguito dopo le modifiche:
  - `python3 build_static_pages.py`
  - `python3 validate_catalog.py`
  - `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py`
- Risultato verifiche:
  - validazione passata con `311` giochi e `311` pagine statiche
  - warning crossplay invariato e atteso
- Nota aperta:
  - il piccolo FOUC sulle pagine gioco resta atteso nel pattern statico + JS e non e stato trattato in questo step
- QA consigliato per Claude Code su questo follow-up:
  - verificare che `langBtn` sia presente e funzionante in `game.html`
  - verificare che `langBtn` sia presente e funzionante in almeno 2-3 pagine `games/*.html`
  - controllare che non ci siano duplicazioni visive del back link

### 2026-03-14 - Claude Code - QA commit 1d6730f

- Eseguito QA mirato sul commit `1d6730f` (language toggle su game pages).
- Verifiche superate:
  - `langBtn` presente e correttamente posizionato su `game.html`, `games/1.html`, `games/50.html`, `games/200.html`
  - layout `page-head` corretto: back link a sinistra, langBtn a destra (desktop), stacked (mobile)
  - nessun back link duplicato
  - doppia `applyStaticTranslations()` rimossa da `app.js` (ora solo da `i18n.js`)
- Problema trovato:
  1. **MEDIO — langBtn su game pages non aggiorna il contenuto del gioco**
     - Cliccando il toggle, cambiano solo footer e testo del bottone
     - Le label specifiche della pagina gioco (descrizione, "Giocatori", "Max giocatori", categorie, modi, rating, badge) restano nella lingua originale
     - Causa: le traduzioni page-specific sono nell'handler `DOMContentLoaded` dell'inline script, che esegue una sola volta; `setLang()` chiama `applyStaticTranslations()` ma questa non copre la logica specifica delle game pages
     - Riguarda sia `games/*.html` (311 pagine) che `game.html` (fallback legacy)
     - Fix suggerito: aggiungere `window.dispatchEvent(new Event('langchange'))` alla fine di `setLang()` in `i18n.js`, poi nell'inline script delle game pages wrappare la logica di traduzione in una funzione richiamata sia su `DOMContentLoaded` che su `langchange`; richiede modifica a `build_static_pages.py` + `game.html` + rebuild 311 pagine

### 2026-03-14 - Codex - Follow-up QA live game translations

- Preso in carico il QA di Claude sul commit `1d6730f` e chiuso il problema del toggle lingua che non aggiornava il contenuto delle game pages.
- Modifiche implementate:
  - `i18n.js`
    - `setLang()` ora emette `window.dispatchEvent(new Event("langchange"))` dopo gli aggiornamenti globali
    - obiettivo: permettere hook di traduzione specifici per pagina senza duplicare la logica dentro `applyStaticTranslations()`
  - `build_static_pages.py`
    - aggiunta `applyGameTranslations()` nelle pagine statiche `games/*.html`
    - la funzione aggiorna:
      - descrizione
      - label info (`Giocatori`, `Max giocatori`, `Descrizione`)
      - categorie e modalita via `data-cat` / `data-mode`
      - badge `played` / `trending`
      - rating label
      - meta description OG/Twitter
    - la funzione viene richiamata:
      - su `DOMContentLoaded`
      - su evento `langchange`
    - rigenerate tutte le 311 pagine statiche
  - `game.html`
    - estratta la logica di rendering in `renderGamePage()`
    - il rendering viene eseguito:
      - al load iniziale
      - su `langchange`
    - coperti sia stato normale che fallback `game not found`
- Eseguito dopo le modifiche:
  - `python3 build_static_pages.py`
  - `python3 validate_catalog.py`
  - `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py`
- Risultato verifiche:
  - validazione passata con `311` giochi e `311` pagine statiche
  - warning crossplay invariato e atteso
- QA consigliato per Claude Code su questo follow-up:
  - verificare su `game.html` che il cambio lingua aggiorni davvero contenuto e metadati, non solo footer/bottone
  - verificare su 2-3 pagine in `games/` che il cambio lingua aggiorni:
    - descrizione
    - label info
    - categorie / modalita
    - rating label / badge
    - meta description

### 2026-03-14 - Claude Code - QA commit 130a011

- Eseguito QA mirato sul commit `130a011` (refresh game pages on language switch).
- Verificato su `game.html`, `games/1.html`, `games/50.html`, `games/200.html`.
- Tutte le verifiche superate senza problemi:
  - `setLang()` emette `langchange` (riga 537 di `i18n.js`)
  - `games/*.html`: `applyGameTranslations()` aggiorna correttamente descrizione, label, categorie, modi, rating, badge, meta description
  - `game.html`: `renderGamePage()` ri-renderizza tutto l'innerHTML su `langchange`
  - nessun back link duplicato, layout `page-head` corretto
- Nessun problema trovato. Il blocco i18n game pages e completo e funzionante.
- Stato i18n complessivo: chiuso. Tutte le pagine del sito (home, about, contact, privacy, game.html, 311 games/*.html) supportano switch lingua completo.
- Prossimo passo consigliato: procedere con implementazione feature "Giochi Gratis" (spec approvata in `docs/superpowers/specs/2026-03-14-free-weekly-games-design.md`)

### 2026-03-14 - Codex - Implementazione feature Giochi Gratis

- Preso in carico il prossimo blocco dopo la chiusura totale dell'i18n: implementazione iniziale della feature "Giochi Gratis" a partire dalla spec approvata in `docs/superpowers/specs/2026-03-14-free-weekly-games-design.md`.
- Nota di adattamento alla realta del repo:
  - la spec diceva di non toccare `build_static_pages.py`, ma in questo progetto la `sitemap.xml` viene rigenerata dal builder
  - per evitare che `free.html` sparisse alla prossima build, e stato necessario aggiungerla anche nel generatore
- Modifiche implementate:
  - `index.html`
    - aggiunta sezione homepage `#freeGamesSection` tra toolbar e featured
    - caricato `free_games.js` prima di `app.js`
    - aggiunto link footer a `free.html`
  - `app.js`
    - aggiunto rendering della strip "Gratis Ora" con card store-specifiche
    - aggiunto countdown client-side (`giorni`, `ultime ore`, `ultima ora`)
    - aggiunto refresh automatico della strip e dei badge catalogo
    - aggiunto badge catalogo `Gratis ora!` con matching per titolo
    - aggiunta classe `.is-free-now` alle card quando c'e una promo attiva
    - corretto il timer dei badge: ora si ri-programma ad ogni refresh, non solo al primo minuto
  - `style.css`
    - aggiunti stili per strip homepage, card free, badge store, countdown, empty state e pagina dedicata
    - footer aggiornato per ospitare il quarto link
  - `i18n.js`
    - gia presenti e usate le chiavi `free_*` per metadata, CTA, countdown, empty state e footer
    - `PAGE_METADATA.free` attivo per aggiornare title/meta/JSON-LD al cambio lingua
  - `free.html` (nuovo)
    - pagina manuale dedicata con layout coerente a `about.html` / `contact.html`
    - supporta switch lingua, metadata dinamici, empty state e render delle offerte da `free_games.js`
  - `free_games.js` (nuovo)
    - creato stub iniziale versionato: `const freeGames = []`
    - la feature e quindi deploy-safe anche prima del primo fetch automatico
  - `fetch_free_games.py` (nuovo)
    - implementato fetcher best-effort con supporto a Epic, Steam, GOG e Humble
    - fallback completo: se tutti gli store falliscono, mantiene `free_games.js` invariato
    - fallback parziale: se uno store fallisce, mantiene le vecchie offerte di quello store e aggiorna gli altri
    - normalizza payload, rimuove offerte scadute e scrive il file in formato stabile
  - `.github/workflows/free_games.yml` (nuovo)
    - workflow separato giornaliero (`0 7 * * *`) per aggiornare `free_games.js`
  - `build_static_pages.py`
    - `write_sitemap()` ora include `free.html`
    - rigenerate tutte le 311 pagine statiche dopo il rebuild
  - `validate_catalog.py`
    - `free.html` aggiunta alle pagine richieste
    - validazione sitemap aggiornata per aspettarsi anche `free.html`
- Verifiche eseguite da Codex:
  - `python3 build_static_pages.py`
  - `python3 validate_catalog.py`
  - `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py fetch_free_games.py`
- Risultato verifiche:
  - validazione passata con `311` giochi e `311` pagine statiche
  - warning crossplay invariato e atteso
- Limite noto:
  - `fetch_free_games.py` non e stato eseguito live da Codex in questo ambiente per via delle restrizioni di rete del sandbox
  - quindi il fetcher e verificato staticamente/sintatticamente, ma non ancora validato contro endpoint reali
- QA consigliato per Claude Code:
  - verificare che `free.html` si apra correttamente e che switch lingua aggiorni:
    - titolo pagina
    - subtitle
    - empty state
    - footer
    - metadata principali
  - verificare che in homepage, con `free_games.js` vuoto, `#freeGamesSection` resti nascosta senza buchi visivi
  - verificare che il nuovo link footer "Giochi gratis" sia presente e coerente in home, pagine info e 2-3 pagine `games/*.html`
  - se vuole fare un controllo piu forte senza committare dati finti:
    - puo popolare temporaneamente `free_games.js` in locale con 1-2 entry di test
    - controllare la strip homepage, la pagina `free.html`, il countdown e il badge "Gratis ora!"
    - poi ripristinare il file prima dell'handoff finale

### 2026-03-14 - Claude Code - QA commit 18b9adc

- Eseguito QA mirato sul commit `18b9adc` (implementazione feature Giochi Gratis).
- Verifiche superate senza problemi:
  - **`free.html`**: struttura corretta, `data-page="free"`, switch lingua, `applyStaticTranslations()` + `renderFreePage()` su DOMContentLoaded, listener `langchange` attivo
  - **i18n.js**: tutte le chiavi `free_*` presenti in IT e EN (`free_meta_title`, `free_meta_description`, `free_section_aria`, `free_now`, `free_title`, `free_subtitle`, `no_free_games`, `free_now_badge`, `claim_free`, `see_all_offers`, `expires_in_days`, `last_hours`, `last_hour`, `footer_free`)
  - **i18n.js PAGE_METADATA**: entry `free` presente con `titleKey`, `descriptionKey`, `schemaBuilder` (CollectionPage)
  - **Homepage `#freeGamesSection`**: attributo `hidden`, `renderFreeGamesSection()` in `app.js` verifica `activeGames.length` e mantiene `hidden=true` + innerHTML vuoto quando non ci sono offerte → nessun buco visivo
  - **app.js strip**: rendering completo con kicker, titolo, link "Vedi tutte le offerte", card con countdown, badge `Gratis ora!` su card catalogo via `buildFreeGameLookup()` + matching per titolo normalizzato, refresh automatico (1s se urgente, 60s altrimenti), listener `langchange` attivo
  - **Footer link `free.html`**: presente e corretto su tutte le pagine testate:
    - `index.html` (riga 217, `id="footerFree"`)
    - `about.html` (riga 88, `id="footerFree"`)
    - `contact.html` (riga 110, `id="footerFree"`)
    - `privacy.html` (riga 107, `id="footerFree"`)
    - `games/1.html`, `games/50.html`, `games/200.html` (riga 107, `href="../free.html"`, `id="footerFree"`)
  - **Traduzione footer**: `applyStaticTranslations()` in `i18n.js` aggiorna `footerFree.textContent = t("footer_free")`
  - **Script load order**: `free_games.js` → `i18n.js` → `particles.js` (free.html), `games.js` → `free_games.js` → `i18n.js` → `app.js` → `particles.js` (index.html) — corretto
- Nessun problema trovato. L'implementazione e solida, deploy-safe con stub vuoto e completa lato i18n.
- Nota: `fetch_free_games.py` non testato contro endpoint reali (limite sandbox Codex) — da verificare al primo run del workflow `free_games.yml`
- Stato feature Giochi Gratis: implementazione base completa. Pronta per deploy e primo fetch automatico

### 2026-03-14 - Claude Code - QA primo run live free games (commit 907313e + fix 2a71798)

- Triggerato manualmente il workflow `Update Free Games` per la prima volta.
- **Dati fetchati**: 2 giochi Epic Games (Cozy Grove, Isonzo), scadenza `2026-03-19T15:00:00Z`.
- **Fetcher `fetch_free_games.py`**: funzionante contro endpoint reali. Solo Epic ha restituito offerte (Steam/GOG/Humble probabilmente non avevano offerte attive o endpoint non raggiungibili).
- Verifiche superate:
  - Formato dati corretto: tutti i campi required presenti (`title`, `store`, `imageUrl`, `storeUrl`, `freeUntil`)
  - Immagini: entrambe caricano correttamente (Cozy Grove 285KB, Isonzo 965KB)
  - Store URLs: formato standard Epic, funzionanti nei browser (Epic blocca bot con 403, irrilevante per utenti)
  - Countdown: ~5 giorni → "Scade tra 5 giorni" / "Expires in 5 days" (tone: normal) — corretto
  - Homepage strip: `renderFreeGamesSection()` trova 2 active games, sezione visibile
  - Badge catalogo: nessun match (ne Cozy Grove ne Isonzo sono nel catalogo co-op) — comportamento atteso
- **Bug trovato e fixato**:
  - Entrambi i workflow (`free_games.yml` e `update.yml`) usavano `[skip ci]` nel commit message
  - Questo impediva a GitHub Pages di ricostruire il sito dopo ogni auto-update dei dati
  - Conseguenza: il primo fetch reale ha scritto `free_games.js` con dati, ma il sito live continuava a servire lo stub vuoto
  - Fix: rimosso `[skip ci]` da entrambi i workflow, committato e pushato (`2a71798`)
  - Dopo il fix, il deploy Pages ha incluso i dati aggiornati
- **Nota cache Cloudflare**: `free_games.js` puo restare cached nella versione vecchia per utenti che hanno gia visitato il sito. Si risolve automaticamente al prossimo ciclo di cache. Considerare in futuro un cache-buster (query param con timestamp) nello script tag se diventa un problema ricorrente.
- Stato: feature Giochi Gratis completamente operativa con dati reali

### 2026-03-14 - Codex - Cleanup crossplay UI

- Preso in carico il prossimo follow-up dopo la chiusura di "Giochi Gratis": riallineare il tema `crossplay` per evitare aspettative errate lato UI finche il dataset non e affidabile.
- Contesto rilevato:
  - il filtro `crossplay` non e attivo nella homepage
  - i dati `crossplay` continuano comunque a essere raccolti e salvati in `games.js` / `auto_update.py`
  - la UI delle pagine gioco (`game.html` + template statico in `build_static_pages.py`) era ancora pronta a mostrare un badge `Crossplay` se qualche record fosse diventato `true`
  - dato che la sorgente non e ancora considerata affidabile, questo poteva riaprire aspettative non volute appena compariva un valore sporco
- Modifiche implementate:
  - `build_static_pages.py`
    - aggiunta costante `CROSSPLAY_UI_ENABLED = False`
    - il badge `Crossplay` nelle pagine `games/*.html` viene renderizzato solo se il gate viene attivato esplicitamente in futuro
  - `game.html`
    - aggiunta costante `CROSSPLAY_UI_ENABLED = false`
    - il fallback/runtime page non mostra piu badge crossplay finche il gate resta disattivato
  - `validate_catalog.py`
    - aggiunta costante `CROSSPLAY_UI_ENABLED = False` per rendere esplicita la policy corrente
    - warning aggiornato:
      - se i dati `crossplay` sono tutti vuoti, la validazione lo segnala chiaramente come stato atteso con UI intenzionalmente nascosta
      - se in futuro compariranno record `crossplay=true` mentre il gate resta `False`, la validazione lo segnala come dato interno presente ma UI ancora volutamente spenta
- Scelta intenzionale:
  - non ho toccato `auto_update.py` o `games.js`
  - il supporto tecnico interno resta intatto, ma la UI e ora esplicitamente disattivata finche non decidiamo di promuovere il dato a feature pubblica
- Verifiche eseguite da Codex:
  - `python3 build_static_pages.py`
  - `python3 validate_catalog.py`
  - `python3 -m py_compile build_static_pages.py auto_update.py validate_catalog.py fetch_free_games.py`
- Risultato verifiche:
  - validazione passata con `311` giochi e `311` pagine statiche
  - warning aggiornato: `Crossplay data is currently empty. The UI stays intentionally hidden until the source is reliable.`
- QA consigliato per Claude Code:
  - verificare homepage, `game.html` e 2-3 pagine `games/*.html`
  - controllare che non compaiano badge/label/stati crossplay visibili
  - controllare che il cleanup non abbia introdotto regressioni nei meta tag o nel layout delle game pages

### 2026-03-14 - Codex - Hardening workflow free games

- Continuato in autonomia mentre Claude non era disponibile, scegliendo un follow-up tecnico verificabile senza QA manuale: aggiungere guardrail al workflow `Update Free Games`.
- Problema affrontato:
  - il workflow giornaliero `free_games.yml` eseguiva `fetch_free_games.py` e poi committava direttamente `free_games.js`
  - mancava pero una validazione dedicata del payload finale del feed gratuito
  - questo lasciava aperto il rischio di committare dati malformati, URL sbagliati o offerte duplicate/scadute in caso di parsing parziale o cambi schema lato store
- Modifiche implementate:
  - `validate_free_games.py` (nuovo)
    - parser standalone di `free_games.js` senza dipendenze di rete
    - controlla che il file esponga `const freeGames = [...]`
    - valida struttura array + oggetti
    - valida campi principali:
      - `title`
      - `store`
      - `storeUrl`
      - `freeUntil`
    - valida che `store` sia uno tra `epic`, `steam`, `gog`, `humble`
    - valida URL HTTPS per `storeUrl` e `imageUrl` (se presente)
    - segnala host store incoerenti come warning
    - fallisce su offerte duplicate per store/titolo
    - fallisce su offerte chiaramente gia scadute
    - accetta correttamente anche feed vuoto, ma lo segnala come warning informativo
  - `.github/workflows/free_games.yml`
    - aggiunto step `Validate free games feed`
    - il workflow ora esegue `python3 validate_free_games.py` prima del commit automatico
- Verifiche eseguite da Codex:
  - `python3 validate_free_games.py`
  - `python3 -m py_compile fetch_free_games.py validate_free_games.py validate_catalog.py build_static_pages.py auto_update.py`
- Risultato verifiche:
  - validazione passata sul feed reale attuale con `2` offerte
  - nessun errore di sintassi Python
- Stato:
  - il workflow free games ora ha un guardrail minimo ma utile prima del commit
  - nessuna modifica UI in questo step
- QA per Claude Code:
  - non urgente
  - quando torna disponibile, puo limitarsi a verificare che il workflow `Update Free Games` includa il nuovo step di validazione e che non ci siano regressioni operative
