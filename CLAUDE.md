# Co-op Games Hub — Istruzioni per AI

Questo file è letto automaticamente da Claude Code e da Aider (via `.aider.conf.yml`).
Contiene tutto ciò che serve per lavorare correttamente su questo progetto.

---

## Cos'è il progetto

Sito statico **coophubs.net** — catalogo di videogiochi cooperativi per PC.
Hosting: **GitHub Pages** + Cloudflare (DNS, proxy, HTTPS). Dominio già configurato e funzionante.

Stack: HTML + CSS + JavaScript puro, Python per la pipeline dati automatica.
Nessun backend. Nessun framework. Nessun runtime Node in produzione.

---

## File principali

| File | Ruolo |
|------|-------|
| `index.html` | Homepage con catalogo e filtri |
| `app.js` | Logica filtri, rendering card, routing verso pagine statiche |
| `games.js` | Database giochi (~334 giochi), oggetti JS |
| `i18n.js` | Sistema traduzioni IT/EN |
| `style.css` | CSS unico del sito |
| `game.html` | Fallback legacy (noindex + canonical verso pagina statica) |
| `free.html` | Pagina giochi gratuiti |
| `free_games.js` | Dati giochi gratuiti, aggiornati via workflow giornaliero |
| `games/<id>.html` | 334 pagine statiche per ogni gioco (SEO) |

## Pipeline Python

| Script | Ruolo |
|--------|-------|
| `auto_update.py` | Aggiornamento automatico giochi (GitHub Actions, lunedì) |
| `build_static_pages.py` | Genera `games/<id>.html` + `sitemap.xml` |
| `validate_catalog.py` | Valida il catalogo dopo il build |
| `fetch_free_games.py` | Aggiorna i giochi gratuiti (GitHub Actions, ogni giorno) |
| `steam_catalog_source.py` | Adapter Steam |
| `itch_catalog_source.py` | Adapter itch.io |
| `catalog_data.py` | Layer I/O dati catalogo |
| `catalog_config.py` | Configurazione pipeline |

---

## Regole obbligatorie

1. **Nessun backend** — niente Express, Flask, FastAPI o qualsiasi server. Il sito è e resta statico.
2. **Nessun npm/Node** — `package.json` non deve esistere. Nessuna dipendenza npm.
3. **Compatibilità GitHub Pages** — tutto deve funzionare su hosting statico puro.
4. **Modifiche mirate** — tocca solo i file necessari al task. Niente refactoring non richiesti.
5. **Non fare commit o push autonomamente** — proponi le modifiche, aspetta conferma dell'utente.
6. **Preserva gli ID giochi** — ogni gioco in `games.js` ha un ID numerico fisso. Non spostare, rinumerare o eliminare senza motivo esplicito.
7. **Aggiorna `AI_COLLABORATION.md`** dopo modifiche non banali — aggiungi una voce nel log con data e descrizione.

---

## Regole architetturali

- Tratta il progetto come un catalogo/directory statico.
- Evita logica duplicata tra file diversi.
- Usa HTML semantico.
- Mantieni CSS leggibile e organizzato in `style.css`.
- Mantieni JavaScript modulare e prevedibile.
- Se i dati sono in JSON o oggetti JS, mantieni struttura pulita e scalabile.

## Regole SEO

- Ogni pagina importante deve avere `title` e `meta description` sensati.
- Mantieni gerarchia corretta degli heading (un solo `h1` per pagina).
- Aggiungi `alt` text alle immagini rilevanti.
- File SEO statici: `robots.txt` e `sitemap.xml` già presenti e configurati.

## Regole UX

- Il mobile è prioritario.
- La navigazione deve restare chiara e immediata.
- Evita popup invasivi e monetizzazione aggressiva.
- Dai priorità a leggibilità, fiducia e utilità.

## Regole monetizzazione

- Monetizzazione leggera e non invasiva.
- CTA affiliate discrete, sezioni supporto/donazioni, blocchi utili.
- Niente banner aggressivi, autoplay o pulsanti ingannevoli.

## Tono del sito

- Indipendente, utile e affidabile.
- Testi chiari, sintetici, orientati all'utente.
- Niente linguaggio pompato o marketing finto.

---

## Struttura dati gioco (games.js)

```js
{
  id: 1,                          // ID fisso, non cambiare
  title: "Nome Gioco",
  categories: ["action", "indie"],
  genres: ["action"],
  coopMode: ["online", "local"],  // online | local | sofa
  maxPlayers: 4,
  crossplay: false,               // true solo se verificato con certezza
  players: "1-4",
  image: "https://shared.cloudflare.steamstatic.com/...",
  description: "...",             // italiano
  description_en: "...",          // inglese
  steamUrl: "https://store.steampowered.com/app/APPID/",
  releaseYear: 2023,
  rating: "molto positivo",
  ccu: 12000,
  tags: ["tag1", "tag2"],
  isFree: false,
  isIndie: false
}
```

---

## Collaborazione AI

### Team

| Agente | Ruolo |
|--------|-------|
| **Claude Code** | Leader tecnico — decisioni architetturali, QA, review, fix mirati |
| **Aider + Ollama** (qwen2.5-coder:14b, GPU Vulkan) | Task delegati — coding ripetitivo, refactoring meccanico, generazione dati |
| Gemini CLI | Fallback — quota API limitata, usare Ollama come default |

### Limiti operativi di Aider + qwen2.5-coder:14b

- Contesto massimo: **32K token** (esteso a 65K con configurazione num_ctx)
- `assets/games.js` (~94K token) è **troppo grande** — non passarlo mai direttamente ad aider
- Per modifiche a `games.js` usare Claude Code oppure passare solo l'oggetto gioco specifico
- File adatti ad aider: `app.js`, `style.css`, `i18n.js`, `particles.js`, script Python singoli
- Aider usa il formato "whole file" con Ollama — riscrive l'intero file, usare su file piccoli/medi

### Regole di collaborazione

- Leggere sempre `AI_COLLABORATION.md` prima di intervenire.
- Aggiornare `AI_COLLABORATION.md` dopo modifiche rilevanti (sezione log con data).
- Non sovrascrivere lavoro altrui senza prima leggere lo stato corrente.
- Non lasciare decisioni importanti solo in chat — salvarle nei file del progetto.
- Segnalare sempre se una conclusione è confermata o solo un'ipotesi.

### Cosa NON deve mai fare nessuna AI

- Creare `package.json`, `index.js`, `server.js` o qualsiasi file backend
- Installare pacchetti npm o avviare un server locale come soluzione permanente
- Fare commit o push senza conferma esplicita dell'utente
- Creare file con nomi placeholder (es. `path/to/filename.js`)
- Modificare `.github/workflows/` senza approvazione esplicita

---

## Checklist prima di modificare

- Funziona ancora su GitHub Pages?
- È più semplice o più manutenibile di prima?
- Migliora davvero SEO, UX, struttura o monetizzazione?
- Sto aggiungendo complessità inutile?

## Output atteso dopo un task

- Riassumi cosa hai cambiato
- Elenca i file toccati
- Segnala passaggi manuali rimasti
- Evidenzia tutto ciò che può influenzare deploy, SEO o dominio
