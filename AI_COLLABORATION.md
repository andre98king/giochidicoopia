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
- **Catalogo**: 334 giochi, pipeline modulare Steam + itch.io
- **Pagine statiche**: 334 pagine in `games/` + sitemap aggiornata
- **i18n**: completo su tutte le pagine principali (IT/EN)
- **Giochi gratuiti**: workflow giornaliero funzionante con dati reali
- **PageSpeed Mobile**: Performance 93, Accessibility 92, Best Practices 100, SEO 100
- **Architettura pipeline**: `auto_update.py` → `catalog_config.py` + `steam_catalog_source.py` + `itch_catalog_source.py` + `catalog_data.py`

### Decisioni architetturali confermate

- **No orchestratore multi-source**: con solo 2 adapter (Steam + itch.io) sarebbe over-engineering. Rivalutare se arriva un terzo source.
- **game.html**: fallback legacy con `noindex` + canonical → pagina statica. Non rimuovere.
- **crossplay**: campo presente ma quasi nessun gioco marcato `true` — dati non ancora verificati sistematicamente.
- **PWA**: `manifest.json` presente ma nessun service worker — non prioritario.

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

---

## Prossimi step consigliati

- Verificare dati `crossplay: true` — attualmente pochi giochi marcati, campo quasi inutilizzato
- Valutare analytics leggeri (es. Cloudflare Web Analytics, zero cookie) se si vuole capire il traffico
- Test visuale periodico su mobile (home, pagina gioco, pagina free)
