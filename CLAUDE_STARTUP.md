# Prompt per Claude Code — Co-op Games Hub

## Ciao! Sono Andrea, il titolare del progetto.

Sito: **coophubs.net** — catalogo di 589 giochi cooperativi per PC.
Stack: HTML/CSS/JS statico, Python pipeline, GitHub Pages + Cloudflare.
Titolare: Metalink Application S.r.l.s (P.IVA: 04739980615)

---

## 📋 Panoramica Progetto

- **Dominio**: coophubs.net ( Cloudflare proxy HTTPS )
- **Hosting**: GitHub Pages + Cloudflare
- **Giochi catalogati**: 589
- **SEO Score**: 91/100
- **PageViews**: ~15,000/mese
- **Cache Hit Rate**: 15.3%

---

## 🤖 Plugin AI che usiamo

### GSD (Get Shit Done)
Workflow management con context engineering.
```
/gsd:new-project    # Inizializza progetto/feature
/gsd:map-codebase   # Analizza codebase
/gsd:quick <task>   # Task veloce
/gsd:progress       # Mostra stato
```

### Ralph
Agente autonomo per task ripetitivi.
- Script: `scripts/ralph/ralph.sh`

### BMAD
Agile AI development con 34+ workflow.
- Skill: `bmad-help`, `bmad-party_mode`, `bmad-review-*`

---

## ✅ Cosa abbiamo fatto oggi (2026-03-31)

### Completato e deployato (commit 5a1ddf68):
1. **SEO Title/Meta** — Aggiornati con keyword "coop online games", "game pc coop"
2. **Hub Pages** — 5 pagine con contenuto editoriale completo (it + en)
3. **Mini-Recensioni** — 17 giochi trending con `mini_review_it` e `mini_review_en`
4. **UI** — Mini-reviews in card, featured e modal
5. **Backlink** — Creato checklist directory italiane

### File modificati:
- `index.html` — Title/meta 589, keywords
- `assets/games.js` — 589 giochi + 17 mini_reviews
- `assets/app.js` — Rendering mini_reviews
- `assets/style.css` — Stili mini_reviews
- `data/hub_editorial.json` — Contenuti hub completi
- `.planning/backlink_checklist.md` — Directory italiane

---

## 🔍 Contesto SEO (2026-03-31)

### Sitemap
- Split in 4 file per superare limite 50K URL
- `sitemap.xml` → index
- `sitemap-main.xml` → homepage + statiche (9 URL)
- `sitemap-hubs.xml` → hub EN (5 URL)
- `sitemap-games-1.xml` → games 1-450 (900 URL)
- `sitemap-games-2.xml` → games 451-589 (278 URL)

### Google Search Console (2026-03)
| Metrica | Valore |
|---------|--------|
| Clicks | 7 |
| Impressions | 383 |
| CTR | 1.83% |
| Pos Media | 20.6 |

### Query pos 6-10 (da migliorare)
- "coop online game" (pos 8.0)
- "coop online games" (pos 7.0)
- "game pc coop" (pos 6.0)
- "giochi cooperativi pc" (pos 9.0)

### robots.txt
- Blocca: GPTBot, ClaudeBot, Google-Extended, Bytespider, PerplexityBot, CCBot
- Mantiene indexing: Googlebot, Bingbot

---

## 💰 Programmi Affiliate Attivi

| Store | Commissione | Status | Note |
|-------|-------------|--------|------|
| Instant Gaming | 3% | ✅ Attivo | `?igr=gamer-ddc4a8` |
| GameBillet | 5% | ✅ Attivo | `?affiliate=fb308ca0-...` |
| Green Man Gaming | 5%/2% | ✅ Approvato | Impact.com, username: coophubs |
| GAMIVO | vari | ✅ Attivo | 346 link |
| K4G | vari | ✅ Attivo | 402 link |
| Gameseal | vari | ✅ CJ | Non ancora integrato |
| Adtraction | - | ⏳ In approvazione |

---

## ⚙️ Workflow GitHub Actions

| Workflow | Schedule | Funzione |
|----------|----------|----------|
| `update.yml` | Lunedì 6:00 | Aggiorna catalogo giochi |
| `fetch-prices.yml` | Giornaliero | Prezzi affiliati |
| `fetch-free.yml` | Giornaliero | Giochi gratuiti |

---

## 📜 Script Utili

### Analytics (GSC + Cloudflare)
```bash
python3 scripts/fetch_analytics.py --days 30
```
- Scarica dati da Google Search Console
- Estrae statistiche Cloudflare (cache hit rate, bandwidth, requests)
- Output: clicks, impressions, posizioni, cache stats
- **Richiede**:
  - `.env` con `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ZONE_ID`
  - Token GSC in `/home/andrea/.claude/mcp-gsc/token.json`
  - MCP Google Search Console configurato

### Build Scripts
- `scripts/build_hub_pages.py` — Genera 5 hub pages + versioni EN
- `scripts/build_static_pages.py` — Genera 589 pagine game + sitemap
- `scripts/validate_catalog.py` — Valida catalogo

---

## 📁 File Importanti

| File | Descrizione |
|------|-------------|
| `index.html` | Homepage con catalogo e filtri |
| `assets/games.js` | DB 589 giochi ⚠️ 94K token - NON passare ad Aider |
| `assets/app.js` | Logica JS (filtri, rendering, modal) |
| `assets/style.css` | Stili CSS |
| `assets/i18n.js` | Traduzioni IT/EN |
| `data/hub_editorial.json` | Contenuti editoriali hub pages |
| `data/game_reviews.json` | Mini-recensioni trending |
| `stitch_design/` | Design files per futuro redesign |

---

## 📖 Leggi Prima di Intervenire

1. **`.planning/STATE.md`** — Stato attuale del progetto (sempre)
2. **`.planning/ROADMAP.md`** — Roadmap e todo
3. **`.planning/backlink_checklist.md`** — Directory italiane

---

## 🚀 Prossimi Passi

1. **Verificare indexing** — Aspetta 24-48h, poi controlla GSC
2. **Backlink building** — Contattare directory italiane
3. **Espansione catalogo** — Aggiungere nuovi giochi

---

## ⚠️ Regole Fondamentali

- **NON fare commit/push** senza chiedere prima
- **NON creare backend** — solo statico
- **NON creare package.json**
- **NON modificare `.github/workflows/`** senza approvazione
- `assets/games.js` è troppo grande per Aider (allucina numeri)
- Leggi sempre `.planning/STATE.md` prima di lavorare

---

## 🔧 Quick Reference

| Info | Dettaglio |
|------|-----------|
| GCP Project | coophubs-gsc |
| MCP GSC | `/home/andrea/.claude/mcp-gsc/` |
| Env File | `.env` (gitignored) |
| Cloudflare | Token in `.env`, accesso full analytics |

---

## 📊 Statistiche Attuali

- Giochi: 589
- Affiliate links: 2,137
- Hub pages: 5 (IT) + 5 (EN)
- Mini-reviews: 17
- SEO Score: 91/100
- GEO Score: 82/100