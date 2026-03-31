# Problemi Noti e Aree di Miglioramento — Co-op Games Hub

Questo documento elenca i problemi tecnici, il technical debt, le limitazioni attuali e i rischi del progetto.

---

## 1. Problemi Critici (Alta Priorità)

### 1.1 Cache Hit Rate Estremamente Basso

**Problema**: Il cache hit rate di Cloudflare è al **6.9%**, molto al di sotto del target del 90%+.

**Impatto**: 
- Tempo di caricamento elevato per gli utenti
- Costi Cloudflare potenzialmente più alti
- Esperienza utente degradata

**Causa probabile**: Nessuna Cache Rule configurata per forzare il caching di tutto il sito.

**Mitigazione**:
- Creare una Cloudflare Cache Rule con Edge TTL: 7 giorni
- Verificare che `_headers` sia configurato correttamente
- Monitorare il cache hit rate dopo la fix

**Riferimento**: `project_roadmap_state.md` sezione 1

---

### 1.2 Traffico Organico Molto Basso

**Problema**: Solo **6 click/mese** da Google Search Console nonostante 13.6k PageViews totali.

**Impatto**:
- Il sito non sta convertendo il traffico diretto/organico in ricerche
- Le pagine non vengono indicizzate correttamente
- Basso ROI SEO

**Causa probabile**:
- Sitemap reinviata il 30/03, stato "In attesa di elaborazione"
- SEO score GEO basso (82/100)
- Meta description/titoli potrebbero non essere ottimali per alcune keyword

**Mitigazione**:
- Monitorare l'indicizzazione nelle prossime settimane
- Verificare che le pagine non abbiano errori di scansione
- Aggiungere più contenuti editoriali nelle hub pages

**Riferimento**: `project_roadmap_state.md` sezione 3

---

### 1.3 Gameseal Mostrano Sempre 0% Sconto

**Problema**: Molti giochi su Gameseal mostrano "0%" come sconto invece del valore reale.

**Impatto**:
- Perdita di potenziale revenue da affiliazione
- Segnalazione errata agli utenti
- Mancata valorizzazione dell'offerta

**Causa**: Probabilmente il parsing dei dati da Gameseal o l'API CJ Affiliate non restituisce correttamente i valori di sconto.

**Mitigazione**:
- Investigare `scripts/fetch_gameseal_prices.py`
- Verificare la risposta dell'API CJ
- Potenzialmente rimuovere Gameseal come store se non funziona

**Riferimento**: `project_roadmap_state.md` sezione 2

---

## 2. Technical Debt

### 2.1 Duplicazione Dati del Catalogo

**Problema**: Esistono **tre copie** dei dati dei giochi:
- `assets/games.js` (~20.000 righe, legacy)
- `data/catalog.games.v1.json` (completo)
- `data/catalog.public.v1.json` (pubblico)

**Impatto**:
- Manutenzione complessa
- Rischio di inconsistenza tra le copie
- Dimensione del bundle JS elevata

**Causa storica**: Evoluzione graduale del progetto senza migrazione completa.

**Possibile soluzione**:
- Deprecare `games.js` definitivamente
- Usare solo `catalog.public.v1.json` come fonte unica
- Aggiornare `app.js` per caricare sempre da JSON

---

### 2.2 Script Python Grandi e Accoppiati

**Problema**: Alcuni script sono estremamente grandi:
- `auto_update.py`: ~39KB
- `build_static_pages.py`: ~51KB
- `build_hub_pages.py`: ~45KB

**Impatto**:
- Difficile da mantenere e debuggare
- Testing manuale居多
- Un singolo errore può bloccare l'intera pipeline

**Possibili miglioramenti**:
- Splittare in moduli più piccoli
- Aggiungere testing automatizzato con pytest
- Documentare meglio le funzioni con docstring

---

### 2.3 Link Affiliati Hardcoded in app.js

**Problema**: I link affiliati sono definiti come costanti in `assets/app.js` (linee 688-696).

**Impatto**:
- Aggiornare un ID affiliato richiede modifiche al codice
- Non c'è logging di quali link vengono cliccati
- Difficile da mantenere multi-store

**Possibili miglioramenti**:
- Spostare in un file di configurazione JSON
- Aggiungere parametri UTM automatizzati
- Potenzialmente caricare da un endpoint configurabile

---

## 3. Limitazioni Attuali

### 3.1 Nessun Analytics Reale

**Problema**: Il sito non ha Google Analytics, Matomo o altri strumenti di tracciamento.

**Impatto**:
- Non si può misurare il comportamento degli utenti
- Non si possono A/B testare modifiche
- Difficile ottimizzare conversioni

**Razionale**: Scelta intenzionale per GDPR compliance (nessun tracking, nessun cookie).

**Workaround attuale**: 
- Google Search Console per dati organici limitati
- Cloudflare Analytics per pageviews
- `fetch_analytics.py` per dati GSC

---

### 3.2 Hub Editorial Content Incompleto

**Problema**: Solo **1 di 5** hub pages ha contenuto editoriale completo:
- `migliori-giochi-coop-2026` — ✓ completo
- `giochi-coop-local` — ✗ non completo
- `giochi-coop-2-giocatori` — ✗ non completo
- `giochi-coop-free` — ✗ non completo
- `indie` — ✗ non completo

**Impatto**:
- Le pagine senza contenuto hanno meno autorità semantica
- Tempo di permanenza utente più basso
- Potenziale SEO inferiore

**Riferimento**: `project_roadmap_state.md` sezione 1.2

---

### 3.3 Dati Crossplay Non Verificati

**Problema**: Il campo `crossplay` è un booleano che potrebbe non essere accurato per tutti i giochi.

**Impatto**:
- Utenti potrebbero aspettarsi crossplay che non funziona
- Filtro crossplay potrebbe essere inaffidabile

**Causa**: Dati derivati da Steam/IGDB senza verifica manuale sistematica.

**Possibile soluzione**: Aggiungere disclaimer o nota di verifica.

---

### 3.4 Pipeline Update Non Automatizzata Completamente

**Problema**: Alcuni aggiornamenti richiedono intervento manuale:
- Aggiunta nuovi giochi
- Correzione errori nei dati
- Approvazione nuovi partner affiliate

**Impatto**: Operazioni ripetitive consumano tempo.

**Attuale**: 
- Workflow GitHub per update automatico (settimanale)
- Workflow per giochi gratuiti (giornaliero)

---

## 4. Aree di Miglioramento

### 4.1 Performance

| Area | Stato | Note |
|------|-------|------|
| Lazy loading immagini | ✓ Implementato | IntersectionObserver |
| Cache busting | ✓ Implementato | `?v=DATE` |
| Minificazione CSS/JS | ✗ Non implementato | Potrebbe ridurre dimensione |
| WebP images | ✗ Non implementato | Steam CDN usato, non controllabile |
| Service Worker | ✗ Non implementato | Non necessario per statico |

---

### 4.2 SEO

| Area | Stato | Note |
|------|-------|------|
| Meta description dinamiche | ✓ Implementato | Con override |
| Schema.org VideoGame | ✓ Implementato | Su pagine statiche |
| hreflang | ✓ Implementato | IT/EN/x-default |
| Sitemap | ✓ Funzionante | 10.720 URL (forse troppo grande) |
| Robots.txt | ✓ Aggiornato | Blocca AI crawler |
| GEO score | ⚠️ 82/100 | Più basso di altri parametri |

---

### 4.3 Monetizzazione

| Area | Stato | Note |
|------|-------|------|
| Instant Gaming | ✓ Attivo | 3% commissione |
| GameBillet | ✓ Attivo | 5% commissione |
| Green Man Gaming | ✓ Attivo | Impact.com |
| Gameseal | ⚠️ Bug sconti | Da investigare |
| GOG | ⏳ In attesa | Applicazione inviata 2026-03-18 |
| MacGameStore | ⏳ Approvato | 5%, non integrato |
| Fanatical | ⏳ Approvato | Non integrato |

---

### 4.4 Accessibilità

| Area | Stato | Note |
|------|-------|------|
| Skip link | ✓ Presente | |
| ARIA labels | ✓ Presente | Su modals e bottoni |
| Keyboard navigation | ✓ Presente | Focus trap nel modal |
| Screen reader | ⚠️ Non testato | Non verificato con NVDA/VoiceOver |
| Color contrast | ✓ Buono | Dark theme con contrasto adeguato |

---

## 5. Rischi e Mitigazioni

### 5.1 Rischi Tecnici

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| API Steam/IGDB cambiano | Media | Alta | Aggiornare adapter regolarmente |
| GitHub Actions rate limits | Bassa | Media | Monitorare e usare caching |
| Cloudflare costi aumentano | Bassa | Media | Monitorare usage |
| Dominio scade | Bassa | Alta | Renew automatico |
| .env esposto accidentalmente | Bassa | Alta | gitignore corretto, mai committare |

---

### 5.2 Rischi SEO

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Penalty Google | Bassa | Alta | Seguire linee guida |
| Contenuto duplicato | Media | Media | Canonical URLs configurati |
| Pagine non indicizzate | Media | Alta | Monitorare GSC |
| Competitori superano | Media | Media | Aggiungere contenuti unici |

---

### 5.3 Rischi Legali

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Affiliate program chiuso | Bassa | Media | Diversificare partner |
| Cambiamento terms store | Media | Media | Monitorare comunicazioni |
| Copyright claim immagini | Bassa | Media | Usare Steam CDN (fair use implicito) |

---

### 5.4 Rischi Operativi

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Pipeline rotta | Media | Alta | Testing pre-deploy |
| Backup perso | Bassa | Critico | Git come source of truth |
| Perdita accesso account | Bassa | Alta | 2FA, backup codici |

---

## 6. Dipendenze Esterne

| Servizio | Tipo | Stato | Note |
|----------|------|-------|------|
| GitHub Pages | Hosting | ✓ Stable | Nessun downtime recente |
| Cloudflare | CDN/DNS | ✓ Stable | Proxy configurato |
| Steam | Dati | ✓ Stable | API soggetta a rate limits |
| IGDB | Dati | ✓ Stable | Token OAuth richiesto |
| itch.io | Dati | ✓ Stable | RSS feed |
| Instant Gaming | Affiliazione | ✓ Stable | Link working |
| GameBillet | Affiliazione | ✓ Stable | Link working |
| Impact.com | Affiliazione | ✓ Stable | GMG integrato |
| CJ Affiliate | Affiliazione | ⚠️ Problemi | Gameseal non funziona |

---

## 7. TODO Strategici

### Alta Priorità
- [ ] Implementare Cloudflare Cache Rule (target 90%+ hit rate)
- [ ] Investigare e fixare Gameseal sconti a 0%
- [ ] Completare hub editorial content per le 4 hub pages mancanti
- [ ] Verificare indicizzazione post-reinvio sitemap

### Media Priorità
- [ ] Integrare MacGameStore e Fanatical (se disponibili)
- [ ] Aggiungere mini-recensioni manuali per i top 20 trending
- [ ] Testare accessibilità con screen reader
- [ ] Considerare minificazione asset

### Bassa Priorità
- [ ] Aggiornare documentazione API per nuovi sviluppatori
- [ ] Aggiungere testing automatizzato (pytest)
- [ ] Implementare logging affiliate clicks (senza PII)
- [ ] Valutare migrazione da games.js a solo JSON

---

## 8. Note

- Il progetto è **ben strutturato** per essere un sito statico SEO-first
- Il technical debt è gestibile e non critico
- I principali rischi sono legati alle dipendenze esterne (API, affiliate)
- La scelta "no analytics" è un trade-off consapevole per privacy
- Il sito è **production-ready** ma ha margine di miglioramento in performance e monetizzazione

---

*Ultimo aggiornamento: 2026-03-31*
*Creato da: AI Codebase Analysis*
