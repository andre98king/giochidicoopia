# Giochi di Co-op

## Scopo del progetto
Questo progetto è un sito statico dedicato alla scoperta di videogiochi cooperativi.
Gli obiettivi sono:
- aiutare gli utenti a trovare giochi co-op in modo rapido e chiaro
- mantenere il sito veloce, semplice e facile da aggiornare
- restare pienamente compatibile con GitHub Pages
- preparare il progetto per dominio personalizzato, Cloudflare, SEO e monetizzazione leggera

## Principi fondamentali
- Mantieni il sito statico finché non esiste un motivo forte per fare il contrario.
- Preferisci HTML, CSS e JavaScript semplici invece di aggiungere complessità inutile.
- Non introdurre backend, database o dipendenze server-side se non richiesto esplicitamente.
- Non rompere la compatibilità con GitHub Pages.
- Migliora il design esistente senza rifare tutto da zero se non serve.
- Dai priorità a chiarezza, velocità e manutenibilità.

## Stile di lavoro
Quando lavori su questo progetto:
1. Analizza prima la struttura esistente.
2. Riusa ciò che funziona già.
3. Fai modifiche mirate e con il minimo impatto possibile.
4. Preserva il comportamento attuale, salvo chiari miglioramenti.
5. Preferisci soluzioni pronte per un progetto reale, non demo o mockup.

## Collaborazione tra agenti
- Claude Code e il leader tecnico del progetto.
- Ollama locale (qwen2.5-coder:14b su GPU Vulkan) e il secondo agente per task delegati.
- Claude Code: decisioni architetturali, QA, review, fix mirati, pianificazione task.
- Ollama: refactor meccanici, generazione bulk, task isolati delegati via `ai-delegate`.
- Gemini CLI disponibile come fallback (quota API limitata).
- Quando fai modifiche non banali, salvale sempre nei file del progetto.
- Usa `AI_COLLABORATION.md` per lasciare handoff, decisioni, stato dei lavori e verifiche aperte.
- Prima di intervenire, leggi `AI_COLLABORATION.md` se esiste gia e aggiornarlo dopo cambiamenti rilevanti.

## Regole architetturali
- Tratta questo progetto come un catalogo/directory statico.
- Se i dati dei giochi sono in JSON o oggetti JS, mantieni una struttura pulita e scalabile.
- Evita logica duplicata tra file diversi.
- Rendi coerenti i componenti UI riutilizzabili.
- Usa HTML semantico quando possibile.
- Mantieni CSS leggibile e organizzato.
- Mantieni JavaScript modulare, chiaro e prevedibile.

## Vincoli GitHub Pages
- Tutto deve funzionare su hosting statico.
- Nessun rendering server-side.
- Nessuna API server-only.
- Nessuna assunzione di runtime Node in produzione.
- Gestisci bene path relativi e assoluti in modo che il sito funzioni sia su github.io sia con un futuro dominio personalizzato.

## Regole SEO
- Ogni pagina importante deve avere title e meta description sensati.
- Mantieni gerarchia corretta degli heading.
- Aggiungi alt text alle immagini rilevanti.
- Migliora la crawlability senza complicare il progetto.
- Se servono file SEO, preferisci soluzioni statiche semplici come robots.txt e sitemap.xml.

## Regole UX
- Il mobile conta.
- La navigazione deve restare chiara e immediata.
- Evita popup invasivi, disordine e monetizzazione aggressiva.
- Dai priorità a leggibilità, fiducia e utilità.

## Regole monetizzazione
- La monetizzazione deve essere leggera e non invasiva.
- Preferisci CTA affiliate discrete, sezioni supporto/donazioni e blocchi utili.
- Non aggiungere banner aggressivi, autoplay o pulsanti ingannevoli.
- Se inserisci placeholder affiliati, etichettali chiaramente.

## Tono del sito
- Il sito deve sembrare indipendente, utile e affidabile.
- I testi devono essere chiari, sintetici e orientati all'utente.
- Evita linguaggio troppo pompato o marketing finto.

## Controlli prima di modificare
Chiediti sempre:
- Funziona ancora su GitHub Pages?
- È più semplice o più manutenibile di prima?
- Migliora davvero SEO, UX, struttura o preparazione alla monetizzazione?
- Sto aggiungendo complessità inutile?

## Output atteso
Quando completi un task:
- riassumi cosa hai cambiato
- elenca i file toccati
- segnala eventuali passaggi manuali rimasti
- evidenzia tutto ciò che può influenzare deploy, SEO o dominio
