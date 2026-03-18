# AI Collaboration Notes

Punto di handoff e log decisionale del progetto.
Leggi questo file prima di intervenire. Aggiornalo dopo modifiche rilevanti.

---

## Team

| Agente | Ruolo |
|--------|-------|
| **Claude Code** | Leader tecnico — decisioni architetturali, QA, review, fix mirati |
| **Aider + Ollama** (qwen2.5-coder:14b, GPU Vulkan AMD RX 9070 XT) | Task delegati via `ai-delegate` o aider CLI |
| Gemini CLI | Fallback — quota API limitata |

Setup Ollama: v0.18.0, backend Vulkan, ~5s generazione codice, ~26s analisi file complesso.

---

## Regole operative

- Leggere questo file prima di toccare qualsiasi cosa.
- Aggiornare il log dopo modifiche non banali.
- Non sovrascrivere lavoro altrui senza leggere prima lo stato corrente.
- Non lasciare decisioni importanti solo in chat — salvarle qui o nei file del progetto.
- Segnalare sempre se una conclusione è confermata o solo un'ipotesi.
- Non fare commit o push senza conferma esplicita dell'utente.

---

## Stato corrente del progetto

- **Sito**: online su https://coophubs.net (GitHub Pages + Cloudflare)
- **Catalogo**: 520 giochi, pipeline modulare multi-source
- **Pagine statiche**: 520 pagine in `games/` + sitemap aggiornata
- **i18n**: completo su tutte le pagine principali (IT/EN)
- **Giochi gratuiti**: workflow giornaliero funzionante con dati reali
- **PageSpeed Mobile**: Performance 93, Accessibility 92, Best Practices 100, SEO 100
- **Architettura pipeline**: `auto_update.py` → `catalog_config.py` + `steam_catalog_source.py` + `itch_catalog_source.py` + `gog_catalog_source.py` + `igdb_catalog_source.py` + `steam_new_releases_source.py` + `catalog_data.py`
- **Monetizzazione**: Ko-fi footer attivo, UTM tracking su link store, CJ Affiliate attivo (Fanatical in review), GOG affiliate in attesa risposta
- **Crossplay**: 86 giochi marcati `true`, filtro UI attivato, hreflang aggiunto

### Decisioni architetturali confermate

- **Multi-source pipeline**: IGDB e GOG adapter aggiunti — rivalutare orchestratore se si aggiunge un quinto source.
- **game.html**: fallback legacy con `noindex` + canonical → pagina statica. Non rimuovere.
- **crossplay**: 86 giochi marcati — dati provengono da IGDB/SteamSpy, non ancora verificati manualmente al 100%.
- **PWA**: `manifest.json` presente ma nessun service worker — non prioritario.
- **Font**: self-hosted (no dipendenza Google Fonts).
- **Affiliate**: UTM tracking via `app.js`, parametri affiliato Epic/GOG pronti ma Creator Code/partner ID non ancora ottenuti.

---

## Log

### 2026-03-13 (Codex)
Prima implementazione: `contact.html`, `about.html`, footer, SEO metadati, `build_static_pages.py`, 311 pagine statiche, sitemap, `validate_catalog.py`, privacy policy riscritta.

### 2026-03-14 (Codex)
Anno footer 2025→2026, sezione giochi gratuiti (`free.html`, `fetch_free_games.py`, `free_games.js`), i18n espanso, decomposizione `auto_update.py` in adapter modulari (`catalog_config.py`, `steam_catalog_source.py`, `itch_catalog_source.py`, `catalog_data.py`).

### 2026-03-15 (Claude Code)
- Fix game 156 "We Were Here Forever": steamUrl corretto (appid 1703880→1341290), image e description_en aggiornati
- PageSpeed fix: font non-bloccanti, ARIA roles (`role="listitem"`), contrasto 4.5:1+ (accent #7c6aff→#6b5ce0), rimossi meta `no-cache` da 317 pagine
- Risultato PageSpeed Mobile: 82→93 (+11), LCP 3.4s→2.6s, TBT 180ms→0ms
- Creato `ai-continuity` + systemd per handoff automatico Claude↔Ollama quando i token si esauriscono

### 2026-03-17 (Claude Code)
- Rimosso commit spazzatura di aider (`path/to/filename.js` con system prompt interno)
- Rimosso backend Node.js introdotto senza permesso (Express + package.json + node_modules)
- Ripristinato repo locale a origin/main (`c241c03`), poi pull allineato a `69ca2e3`
- Riorganizzazione file MD: `CLAUDE.md` unificato (era duplicato tra CLAUDE.md e AIDER_INSTRUCTIONS.md), `AI_COLLABORATION.md` trimmed, `SETUP_DOMAIN_CLOUDFLARE.md` rimosso (setup già completato), `.gitignore` migliorato, `.aider.conf.yml` creato

### 2026-03-18 (Claude Code)
- Analisi completa stato progetto: catalogo a 520 giochi, nuovi adapter IGDB/GOG/steam_new_releases
- **CJ Affiliate**: completato onboarding (9/9 step), W-8BEN firmato, account attivo
- **CJ Pending applications (7)**: Fanatical, G2A, Gameseal, GAMIVO, GOG.COM INT, K4G, Kinguin
- **GOG Affiliate**: email application inviata a affiliate@gog.com (+ GOG.COM INT su CJ in pending)
- **Green Man Gaming (Impact.com)**: account creato (username: coophubs), applicazione inviata, In Review
  - impact.com general marketplace: Declined (VPN + timing verifica) — non influenza GMG
  - Meta tag verifica aggiunto a index.html, sito verificato
- **WinGameStore affiliate**: account creato (andrea900924@gmail.com), email confermata, in attesa approvazione (entro 5 giorni lavorativi)
- **Instant Gaming affiliate**: già attivo — link `https://www.instant-gaming.com/?igr=gamer-ddc4a8` (3% commissione per vendita)
- **GameBillet affiliate**: attivo — link `http://www.gamebillet.com/?affiliate=fb308ca0-647e-4ce7-9e80-74c2c591eac1` (5% commissione, pagamento il 15 del mese)
- **Ko-fi support strip**: sezione sopra footer con pulsante grande visibile
- **Crossplay**: filtro UI attivato, 86 giochi marcati, hreflang aggiunto alle pagine statiche
- Fix SEO critico: sitemap re-inviata a Google (era ferma a 314 URL del 14/03, ora 524 URL)
- Workflow `update.yml`: cron cambiato da settimanale a **giornaliero** (ogni giorno 6:00 UTC)

---

## Prossimi step consigliati

- Attendere approvazione CJ (Fanatical, GOG, Kinguin, GAMIVO, K4G, Gameseal, G2A)
- Attendere risposta GOG direct affiliate (affiliate@gog.com)
- Attendere approvazione Green Man Gaming (Impact.com, 2 giorni lavorativi)
- Attendere approvazione **WinGameStore** affiliate (email confermata, entro 5 giorni lavorativi)
- **Instant Gaming affiliate**: attivo — link `https://www.instant-gaming.com/?igr=gamer-ddc4a8` (3% commissione)
- **GameBillet affiliate**: attivo — link `http://www.gamebillet.com/?affiliate=fb308ca0-647e-4ce7-9e80-74c2c591eac1` (5% commissione, pagamento il 15 del mese)
- Analytics: attivare Cloudflare Web Analytics (zero cookie, gratuito)
- Paginazione/lazy loading: 520 giochi tutti in RAM è pesante su mobile
- Verificare campi `isFree` e `isIndie` (risultano sempre false)
