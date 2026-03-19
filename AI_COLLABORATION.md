# AI Collaboration Log — coophubs.net

Data ultimo aggiornamento: **2026-03-19**

---

## Analisi Stato Progetto

### ✅ Completato (Feb-Mar 2026)

**Core features:**
- ✅ Catalogo 334 giochi coerente (games.js) con dati Steam/itch.io
- ✅ Filtri raggruppati (Special: all/trending/free, Genere, Modalità)
- ✅ Sistema "Giochi Già Giocati" (localStorage + localStorage_notes)
- ✅ Note personali per giochi completati
- ✅ Modale per dettagli gioco con link store
- ✅ Routing statico: `games/<id>.html` (334 pagine per SEO)
- ✅ I18n IT/EN completo
- ✅ Sitemap.xml + robots.txt
- ✅ Mobile responsive (CSS grid + flex)

**Affiliate monetization:**
- ✅ Instant Gaming (IG): 3% commission, link tracking setup
- ✅ GameBillet (GB): 5% commission, link tracking setup
- ✅ Scraper prezzi IG/GB: 12x optimized (semafori, 10min per 334 games)
- ✅ IG discount fixed: navigate to product page for `.discounted`
- ✅ Price compare modal con 2-3 store alterniativi
- ✅ CJ Affiliate + 7 pending (Fanatical, G2A, Gameseal, GAMIVO, K4G, Kinguin)

**UX & Polish:**
- ✅ Mobile toolbar compatto (genre/mode filters collassati dietro toggle)
- ✅ Ko-fi float nascosto su mobile
- ✅ Admin button rimosso (non più necessario)
- ✅ Card layout omogeneo (altezze/spaziature uniformi)
- ✅ Played toggle visibile e interattivo (✓ cerchio, top-left, z-index 15)
- ✅ Note button ✎ su card giocate
- ✅ Filter alignment corretto (full-width rows)
- ✅ Cache busting implementato (?v=20260319-mob)

**Infrastruttura:**
- ✅ GitHub Pages hosting (statico)
- ✅ Cloudflare DNS + proxy + HTTPS
- ✅ GitHub Actions pipeline: aggiornamento giochi (lunedì), free games (giornaliero)
- ✅ Python scraper: auto_update.py, build_static_pages.py, validate_catalog.py, fetch_free_games.py

---

## 🚨 Known Issues (Nessuno critico)

| Problema | Severity | Note |
|----------|----------|------|
| Gameseal coverage basso | ⚠️ Medium | ~15 games trovati via CJ API, manca mapping many-to-one |
| GOG partner ID | ⚠️ Low | ID non ancora ottenuto (architettura pronta in app.js) |
| WinGameStore in review | ℹ️ Info | Approvazione entro 5gg lavorativi |
| Green Man Gaming in review | ℹ️ Info | Impact.com approval pending |

---

## 📊 Roadmap (Next steps)

### Fase 1: Completa coverage affiliate (Urgenza: MEDIA)

**Obiettivo**: Massimizzare commission + click-through

1. **Gameseal (CJ Affiliate)**
   - Implementare mapping game <→ Gameseal product ID
   - Attualmente ~15 games, target 100+
   - Link structure: CJ tracking + Gameseal domain

2. **GOG Partner ID**
   - Ottenere GOG partner ID
   - Aggiungere a AFFILIATE.gog (già pronto in app.js)
   - Test su giochi GOG esclusivi

3. **Fanatical, G2A, K4G, Kinguin**
   - Status check con CJ Affiliate
   - Implementare se approvati
   - Priority: Fanatical (più noto in EU)

4. **Check WinGameStore + Green Man Gaming approval**
   - Status sulle email: approvazione entro 5gg?
   - Se approved: integrare nei link del modal

---

### Fase 2: SEO & Traffic (Urgenza: MEDIA)

**Obiettivo**: Aumentare organic traffic

1. **Internal linking**
   - Link da cards tra giochi correlati (stesso genere/modalità)
   - Schema.json markup per game reviews (structured data)
   - Breadcrumb nav su pagine game statiche

2. **Meta descriptions**
   - Audit corrente meta descriptions (games/<id>.html)
   - Renderizzare da games.js description_it (120-160 char)
   - Verificare unicità

3. **Heading hierarchy**
   - Audit h1-h3 structure per pagina
   - Assicurare un solo h1 per pagina
   - Logica h2 per sottosezioni

4. **Rich snippets**
   - Game schema.json (GamePlayMode, numberOfPlayers, etc.)
   - Breadcrumb schema
   - ReviewRating schema per rating Steam

---

### Fase 3: Features UX (Urgenza: BASSA)

**Obiettivo**: Engagement e usability

1. **Collections personali**
   - Salvare custom liste di giochi (wishlist, "da comprare", etc.)
   - Export/import JSON
   - Storage: localStorage (come played games)

2. **Advanced filters**
   - Filter per price range (da scraper affiliates)
   - Filter per release year range
   - Filter per player count exact
   - Combinare filtri con AND (già fatto, verificare UX)

3. **Social sharing**
   - Share button per game (Twitter, Reddit)
   - Share wishlist
   - URL param per preset (e.g. `?genre=horror&mode=online`)

4. **Notifications**
   - Alert quando gioco entra in sconto (IG/GB scraper monitoring)
   - "New games" notifiche
   - Optional: email digest settimanale (richiede backend minimo)

---

### Fase 4: Monitoring & Maintenance (ONGOING)

**Obiettivo**: Salute progetto

1. **Scraper health**
   - Monitor IG/GB DOM changes (monthly audit)
   - Fallback strategy se APIs cambiano
   - Log errors + retry logic

2. **Analytics**
   - Implementare Plausible Analytics (privacy-first, no cookies)
   - Track: game clicks, affiliate clicks, filters usati
   - Monthly report su revenue affiliate

3. **Content freshness**
   - Review giochi new/removed monthly (Steam API)
   - Validate affiliate URLs (200 HTTP check)
   - Check CCU trends (giochi dead removal candidate)

4. **Performance monitoring**
   - PageSpeed Insights (target >90 mobile, >95 desktop)
   - Lighthouse audit (monthly)
   - Asset size monitoring

---

## 💰 Revenue Projection (Estimate basato su dati storici)

| Canale | Stato | Commissione | Est. Games | Est. Click/mese | Est. Revenue/mese |
|--------|-------|-------------|-----------|-----------------|-------------------|
| Instant Gaming | ✅ Active | 3% | 250+ | ~300 | ~$50-80 |
| GameBillet | ✅ Active | 5% | 200+ | ~150 | $30-50 |
| Gameseal (CJ) | 🔄 Partial | varia | ~15 | ~30 | $5-15 |
| Epic (pending CC) | ⏳ Ready | varia | ~80 | ~40 | $20-40 |
| GOG (pending ID) | ⏳ Ready | varia | ~120 | ~60 | $30-60 |
| Fanatical + others | ⏳ CJ pending | varia | ~100 | ~50 | $20-40 |
| **TOTALE** | - | - | - | **~630** | **$155-285** |

**Note**: Stime conservative, reale dipende da click-through rate (CTR) e conversion

---

## 📝 Log Modifiche

### 2026-03-19 (Today)

- **Commit f880f0a**: `fix(ux): mobile toolbar compatta + scraper IG ottimizzato`
  - Mobile toolbar: genre/mode filters collassati dietro toggle
  - Ko-fi float nascosto su mobile
  - Scraper IG: navigazione a product page per `.discounted`
  - Scraper IG/GB: semaphore concurrency (IG=8, GB=5), 12x speedup
  - Cache bust version: `20260319-mob`
  - Test: Brotato -60%, Elden Ring -22%, Rust -92% ✅

### 2026-03-18

- **Commit a669512**: `fix(ui): move Gratis to special row, fix played toggle visibility, homogenize cards`
  - Filtro "Gratis" spostato in filterSpecial (accanto all/trending)
  - Bottone ✓ "Giochi Già Giocati": visibile (z-index 15, top-left, glass effect)
  - Note button ✎ su card giocate
  - Card layout omogeneo (rimosso margin-top: auto da .card-desc)
  - Filter alignment: full-width rows

- **Commit 051a329**: `fix(ui): remove admin button, fix filter alignment, improve played/note UX`
  - Admin button rimosso (HTML + CSS + JS)
  - Filter container: width 100% (full-width rows)
  - Played toggle: z-index 15, positioned top-left con cerchio 30px

---

## 🤝 Collaboration Notes

- **Andrea** (owner): decisioni, testing, deploy
- **Claude Code**: tech lead, code review, roadmap, fix prioritizzazione
- **Aider + Ollama**: task delegati (coding ripetitivo, scraper fixes, refactoring meccanico)

**Prossima sync**: Plan per Fase 1 (Gameseal + Epic + GOG affiliate coverage)
