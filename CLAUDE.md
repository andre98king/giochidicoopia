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

## Programmi affiliate attivi (stato 2026-03-19)

| Store | Stato | Commissione | Note |
|-------|-------|-------------|------|
| **Instant Gaming** | Attivo | 3% | Link: `?igr=gamer-ddc4a8` — in `AFFILIATE.ig` (app.js) |
| **GameBillet** | Attivo | 5% | Link: `?affiliate=fb308ca0-...` — in `AFFILIATE.gb` (app.js) |
| **Green Man Gaming** | Approvato | 5%/2% | Impact.com username: coophubs |
| **MacGameStore** | Approvato | 5% | Stesso account di WinGameStore |
| **Gameseal** | Approvato (CJ) | varia | Non ancora integrato nel codice |
| **WinGameStore** | Link scaduto | 5% | Email support inviata 2026-03-18 |
| **GOG** | Application inviata | varia | Email a affiliate@gog.com 2026-03-18 |
| **CJ Affiliate** | Attivo | varia | Fanatical, G2A, GAMIVO, GOG INT, K4G, Kinguin (pending) |

### Architettura affiliate nel codice

- **`assets/app.js`** → oggetto `AFFILIATE` (riga ~585) + funzione `buildPriceCompare()` + `addUtm()`
- **`scripts/build_static_pages.py`** → costanti `AFFILIATE_*` (riga ~104) + `render_store_links()`
- Link "Prezzi alternativi" (IG + GameBillet) appaiono nel modal e nelle pagine statiche solo se il gioco ha `steamUrl`
- GOG: parametri già predisposti, attivabili riempiendo le costanti
- Epic rimosso (programma solo per creator, non per siti web)
- I link usano `rel="sponsored"` come da best practice SEO

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
  categories: ["action", "indie"],// "free" e "indie" usati come categorie speciali
  genres: ["action"],
  coopMode: ["online", "local"],  // online | local | sofa
  maxPlayers: 4,
  crossplay: false,               // true solo se verificato con certezza
  players: "1-4",
  image: "https://shared.cloudflare.steamstatic.com/...",
  description: "...",             // italiano
  description_en: "...",          // inglese
  steamUrl: "https://store.steampowered.com/app/APPID/",
  rating: 74,                     // intero 0-100 (da Steam)
  ccu: 12000,                     // concurrent users (da SteamSpy)
  trending: false,                // true se in top trending
  igUrl: "...",                   // URL Instant Gaming con affiliato
  igDiscount: 40,                 // sconto % su IG
  gbUrl: "...",                   // URL GameBillet con affiliato
  gbDiscount: 25                  // sconto % su GB
}
```

> **Nota**: "free" e "indie" sono valori nell'array `categories`, NON campi boolean separati.
> Il filtro "Gratis" usa `categories.includes('free')`. Non esistono campi `isFree`/`isIndie`.

---

## Collaborazione AI

### Team

| Agente | Ruolo |
|--------|-------|
| **Claude Code** | Leader tecnico — decisioni architetturali, QA, review, fix mirati |
| **Aider + Ollama** (qwen2.5-coder:14b, GPU Vulkan) | Task delegati — coding ripetitivo, refactoring meccanico, generazione dati |
| Gemini CLI | Fallback — quota API limitata, usare Ollama come default |

### Setup locale Aider (config non in repo)

`.aider.conf.yml` e `.aider.model.settings.yml` sono gitignored — vanno creati in locale.
Crea `.aider.conf.yml` nella root del progetto con questo contenuto:

```yaml
model: ollama/qwen2.5-coder:14b      # oppure deepseek-coder-v2:16b
openai-api-base: http://localhost:11434/v1
openai-api-key: ollama
weak-model: ollama/qwen2.5-coder:7b
read:
  - CLAUDE.md
  - AI_COLLABORATION.md
auto-commits: false
auto-lint: false
pretty: true
show-model-warnings: false
```

Hardware disponibile (RX 9070 XT 16GB VRAM + 16GB RAM):
- `qwen2.5-coder:14b` — ~9GB VRAM, veloce, buono per file medi
- `deepseek-coder-v2:16b` — ~9GB VRAM, più preciso nell'editing
- `qwen3-coder:30b` — ~18GB VRAM+RAM, potente per task complessi

### Limiti operativi di Aider con Ollama

- `assets/games.js` (~94K token) è **troppo grande** — non passarlo mai ad aider, allucinaverifica i numeri
- File adatti: `app.js`, `style.css`, `i18n.js`, `particles.js`, script Python singoli
- Aider usa "whole file" format con Ollama — riscrive l'intero file, usare su file piccoli/medi
- Verifica sempre l'output prima di accettare modifiche

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
