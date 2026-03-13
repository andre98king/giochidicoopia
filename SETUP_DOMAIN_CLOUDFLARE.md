# Setup Dominio Personalizzato + Cloudflare + GitHub Pages

Guida pratica per collegare un dominio custom al sito, configurare Cloudflare come DNS/proxy e gestire HTTPS.

---

## Panoramica

```
Utente → Cloudflare (DNS + proxy + HTTPS) → GitHub Pages (hosting statico)
```

Cloudflare si mette davanti a GitHub Pages: gestisce DNS, certificato SSL, caching e protezione DDoS. GitHub Pages continua a servire i file statici.

---

## Fase 1 — Acquista il dominio

Compra un dominio da un registrar. Opzioni consigliate:

| Registrar | Note |
|-----------|------|
| **Cloudflare Registrar** | Prezzo a costo, DNS già integrato — salti la fase 3 |
| Porkbun | Economico, interfaccia semplice |
| Namecheap | Popolare, molte estensioni disponibili |

Non serve un dominio costoso. `.com`, `.it`, `.games` vanno tutti bene.

---

## Fase 2 — Aggiorna i file nel repository

### 2a. File `CNAME`

Il file `CNAME` nella root del repo dice a GitHub Pages quale dominio custom usare.
Apri il file `CNAME` e sostituisci tutto il contenuto con una sola riga — il tuo dominio, senza `https://`:

```
coophubs.net
```

Nessun commento, nessuna riga vuota, solo il dominio.

### 2b. Aggiorna gli URL hardcoded

~~Gia fatto~~ — Tutti gli URL sono stati aggiornati a `https://coophubs.net`. File coinvolti:

**index.html** (5 occorrenze):
- riga canonical: `<link rel="canonical" href="...">`
- riga og:image: `<meta property="og:image" content="...">`
- riga og:url: `<meta property="og:url" content="...">`
- Schema.org url: `"url": "..."`
- Schema.org target: `"target": "...?q=..."`

**sitemap.xml** (1 occorrenza):
- `<loc>...</loc>`

**robots.txt** (1 occorrenza):
- `Sitemap: ...`

Totale: **7 sostituzioni** in **3 file**. Tutte dello stesso URL base.

---

## Fase 3 — Configura Cloudflare DNS

> Se hai comprato il dominio da Cloudflare Registrar, il DNS è già configurato. Vai al punto 3b.

### 3a. Aggiungi il sito a Cloudflare

1. Vai su [dash.cloudflare.com](https://dash.cloudflare.com)
2. Clicca **Add a site** → inserisci il dominio → scegli il piano **Free**
3. Cloudflare ti mostrerà due nameserver (es. `ada.ns.cloudflare.com`, `bob.ns.cloudflare.com`)
4. Vai nel pannello del tuo registrar → cambia i nameserver con quelli di Cloudflare
5. Torna su Cloudflare → clicca **Check nameservers**
6. La propagazione può richiedere da pochi minuti a 24 ore

### 3b. Aggiungi i record DNS

Vai su Cloudflare → il tuo dominio → **DNS → Records** → aggiungi:

| Tipo | Nome | Contenuto | Proxy |
|------|------|-----------|-------|
| `CNAME` | `@` | `andre98king.github.io` | Arancione (proxy attivo) |
| `CNAME` | `www` | `andre98king.github.io` | Arancione (proxy attivo) |

Note:
- Il record `@` è l'apex domain (es. `coophubs.net` senza www)
- Cloudflare supporta CNAME sull'apex tramite **CNAME flattening** — funziona correttamente
- Il proxy arancione attiva caching, SSL edge e protezione Cloudflare

---

## Fase 4 — Configura GitHub Pages

1. Vai su GitHub → repo `giochidicoopia` → **Settings** → **Pages**
2. Sotto **Source** verifica che sia impostato il branch `main` e la cartella `/` (root)
3. Sotto **Custom domain** inserisci il tuo dominio (es. `coophubs.net`)
4. GitHub verificherà il DNS. Se i nameserver sono già propagati, vedrai un check verde
5. Spunta **Enforce HTTPS**

> Se "Enforce HTTPS" è grigio, attendi qualche minuto — GitHub deve generare il certificato. Con Cloudflare proxy attivo, potrebbe servire fino a 30 minuti.

---

## Fase 5 — Configura Cloudflare SSL e sicurezza

### SSL/TLS

- Vai su **SSL/TLS → Overview**
- Imposta la modalità su **Full (strict)**
  - Full (strict) significa: Cloudflare → HTTPS → GitHub Pages (che ha un cert valido)
  - NON usare "Flexible" — causa loop di redirect

### Edge Certificates

- Vai su **SSL/TLS → Edge Certificates**
- Attiva **Always Use HTTPS** (redirect automatico da http a https)
- Attiva **Automatic HTTPS Rewrites** (riscrive link http nel contenuto)

### Rocket Loader — DISABILITA

- Vai su **Speed → Optimization → Content Optimization**
- **Disabilita Rocket Loader**
- Motivo: il sito carica `games.js` → `i18n.js` → `app.js` in ordine preciso con `defer`. Rocket Loader può rompere questa sequenza e causare errori JS

---

## Fase 6 — Redirect www ↔ apex (opzionale)

Se vuoi che `www.coophubs.net` redirecti a `coophubs.net` (o viceversa):

1. Vai su Cloudflare → **Rules → Redirect Rules**
2. Crea una regola:
   - **When**: hostname equals `www.coophubs.net`
   - **Then**: Dynamic redirect → `https://coophubs.net/${http.request.uri.path}`
   - **Status code**: 301 (permanente)

---

## Fase 7 — Caching (opzionale)

Impostazioni consigliate in Cloudflare → **Caching → Configuration**:

| Impostazione | Valore consigliato | Motivo |
|--------------|-------------------|--------|
| Browser Cache TTL | 4 ore | Buon compromesso tra aggiornamenti e performance |
| Caching Level | Standard | Sufficiente per un sito statico |
| Always Online | Attivo | Mostra versione cached se GitHub Pages è down |

Per `games.js` (282 KB, aggiornato settimanalmente): il cache default di Cloudflare è già adeguato. GitHub Actions fa push → Cloudflare invalida automaticamente al prossimo request.

---

## Fase 8 — Verifica finale

Dopo aver completato tutto, controlla:

- [ ] `https://coophubs.net` carica il sito correttamente
- [ ] `https://www.coophubs.net` redirecta all'apex (se hai configurato la regola)
- [ ] `http://coophubs.net` redirecta a `https://` automaticamente
- [ ] Lucchetto HTTPS visibile nel browser
- [ ] Filtri, ricerca, ruota random e cambio lingua funzionano
- [ ] Social sharing mostra titolo e descrizione corretti (testa su https://opengraph.xyz)
- [ ] `sitemap.xml` e `robots.txt` mostrano il nuovo dominio

---

## Riepilogo — Cosa toccare e dove

| Cosa | Dove | Tipo |
|------|------|------|
| Scrivere dominio nel file `CNAME` | Nel repo | File |
| Sostituire URL base (7 occorrenze) | `index.html`, `sitemap.xml`, `robots.txt` | File |
| Aggiungere record DNS | Cloudflare dashboard | Manuale |
| Impostare custom domain | GitHub Settings → Pages | Manuale |
| SSL Full (strict) | Cloudflare SSL/TLS | Manuale |
| Disabilitare Rocket Loader | Cloudflare Speed | Manuale |
| Always Use HTTPS | Cloudflare SSL/TLS | Manuale |
| Redirect www → apex | Cloudflare Rules | Manuale (opzionale) |

---

## Troubleshooting

**"Enforce HTTPS" è grigio su GitHub Pages**
→ Il certificato non è ancora pronto. Attendi 15-30 minuti. Se il DNS non è propagato, GitHub non può generare il cert.

**Loop di redirect infinito**
→ Cloudflare SSL è impostato su "Flexible" invece di "Full (strict)". Cambialo.

**Il sito carica ma JS non funziona**
→ Rocket Loader è attivo. Disabilitalo.

**404 su GitHub Pages dopo aver impostato il dominio**
→ Il file `CNAME` manca o contiene commenti/righe vuote. Deve contenere SOLO il dominio.

**DNS non propagato dopo ore**
→ Verifica i nameserver con `dig coophubs.net NS`. Se non puntano a Cloudflare, il registrar non ha ancora aggiornato.
