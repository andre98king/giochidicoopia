# Prompt per Claude Code — Co-op Games Hub

## Ciao! Sono Andrea, il titolare del progetto.

Sito: **coophubs.net** — catalogo di 589 giochi cooperativi per PC.
Stack: HTML/CSS/JS statico, Python pipeline, GitHub Pages + Cloudflare.

---

## Plugin AI che usiamo

### GSD (Get Shit Done)
Workflow management con context engineering.
- `/gsd:new-project` — Inizializza progetto/feature
- `/gsd:map-codebase` — Analizza codebase
- `/gsd:quick <task>` — Task veloce
- `/gsd:progress` — Mostra stato

### Ralph
Agente autonomo per task ripetitivi.
- Script: `scripts/ralph/ralph.sh`

### BMAD
Agile AI development con 34+ workflow.
- Skill: `bmad-help`, `bmad-party_mode`, `bmad-review-*`

---

## Cosa abbiamo fatto oggi (2026-03-31)

### Completato e deployato (commit 5a1ddf68):
1. **SEO Title/Meta** — Aggiornati con keyword "coop online games", "game pc coop"
2. **Hub Pages** — 5 pagine con contenuto editoriale completo
3. **Mini-Recensioni** — 17 giochi trending hanno ora `mini_review_it` e `mini_review_en`
4. **UI** — Le mini-reviews appaiono in card, featured e modal
5. **Backlink** — Creato checklist directory italiane

### File importanti modificati:
- `index.html` — Title/meta
- `assets/games.js` — 589 giochi + mini_reviews
- `assets/app.js` — Rendering mini_reviews
- `assets/style.css` — Stili mini_reviews
- `data/hub_editorial.json` — Contenuti hub
- `.planning/backlink_checklist.md` — Directory

---

## Prossimo passo

**Verificare indexing** — Aspetta 24-48h, poi controlla GSC per vedere se le URL vengono indexate dopo lo split sitemap.

---

## Contesto SEO importante (2026-03-31)

- **Sitemap split** — 4 file (index + main + hubs + games-1 + games-2) per superare limite 50K
- **GSC** — 7 click, 383 impression, pos 20.6 media (da analytics script)
- **Cache** — Hit rate 15.3% (ottimizzato con _headers)
- **robots.txt** — Blocca GPTBot, ClaudeBot, PerplexityBot (indexing solo Googlebot/Bingbot)
- **Stitch design** — files in `stitch_design/` per futuro redesign (dark neon cyberpunk)

---

## Programmi Affiliate Attivi

| Store | Commissione | Note |
|-------|-------------|------|
| Instant Gaming | 3% | `?igr=gamer-ddc4a8` |
| GameBillet | 5% | `?affiliate=fb308ca0-...` |
| GMG | 5%/2% | Impact.com |
| GAMIVO | vari | 346 link |
| K4G | vari | 402 link |

---

## Workflow GitHub Actions

- `update.yml` — Aggiorna giochi (lunedì 6:00)
- `fetch-prices.yml` — Prezzi affiliati (giornaliero)
- `fetch-free.yml` — Giochi gratuiti (giornaliero)

---

## Leggi prima di intervenire

1. `.planning/STATE.md` — Stato attuale del progetto
2. `.planning/ROADMAP.md` — Cosa dobbiamo fare
3. `.planning/backlink_checklist.md` — Directory italiane

---

## Script utili

### Analytics (GSC + Cloudflare)
- `scripts/fetch_analytics.py` — Scarica e analizza dati da Google Search Console e Cloudflare
- Usage: `python3 scripts/fetch_analytics.py --days 30`
- Output: Statistiche clicks, impressions, posizioni + cache hit rate
- Richiede: `.env` con `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ZONE_ID`, token GSC in `/home/andrea/.claude/mcp-gsc/token.json`

---

## Regole

- **NON fare commit/push** senza chiedere prima
- **NON creare backend** — solo statico
- **NON creare package.json**
- Leggi sempre `.planning/STATE.md` prima di lavorare
- `assets/games.js` è troppo grande (94K token) — NON passarlo ad Aider

---

## Quick reference

| Info | Dettaglio |
|------|-----------|
| Titolare | Metalink Application S.r.l.s (P.IVA: 04739980615) |
| Dominio | coophubs.net (Cloudflare proxy) |
| GCP project | coophubs-gsc |
| MCP GSC | `/home/andrea/.claude/mcp-gsc/` |
| Env file | `.env` (gitignored) |