# STATE.md — Co-op Games Hub

## Ultimo Aggiornamento
2026-04-01 — Milestone v1.1 avviata

---

## Posizione Corrente

**Milestone**: v1.1 — Database Quality & Co-op Purity
**Fase**: Non ancora iniziata (definizione requirements)
**Plan**: —
**Status**: Defining requirements
**Last activity**: 2026-04-01 — Milestone v1.1 started

---

## Milestone v1.0 — Completata ✅

**Fase**: 6c (Backlink/distribuzione) + attesa indexing Google
**Stato**:
- ✅ SEO base: title/meta migliorati per query pos 7-8
- ✅ Hub pages: **8 pagine IT + 8 EN** (5 originali + 3 nuove: horror/survival/offline)
- ✅ Mini-recensioni: 17 giochi trending
- ✅ Backlink building: checklist directory italiane
- ✅ Sitemap split in 5 file (index + main + hubs + games-1 + games-2), tutti sottomessi a GSC
- ✅ Sitemap-hubs.xml aggiornata con 3 nuove hub pages (6 URL: IT+EN)
- ✅ Fix descrizioni IT giochi itch.io 603-608 (traduzione via deep-translator da pagine reali)
- ✅ Fix releaseYear EverSiege (ID 609) → 2026
- ✅ GSC OAuth re-autenticato con scope webmasters + indexing (Desktop app type)
- ✅ Catalogo: 589 giochi, max ID 609
- ⏳ Google Indexing API: da abilitare in GCP (azione manuale richiesta)
- ⏳ Cache Cloudflare hit rate: 7.6% — Cache Rule da creare
- ❌ Backlink building: da fare manualmente

---

## Decisioni Prese

- [x] Visone confermata: Catalogo giochi coop PC, monetizzazione leggera, focus organico
- [x] Stack confermato: HTML/CSS/JS statico, Python pipeline, GitHub Pages + Cloudflare
- [x] GSD installato come sistema di project management
- [x] Ralph installato per task autonomi
- [x] BMAD installato per review e analisi

---

## Blocker

Nessun blocker attivo.

---

## Quick Tasks Completati

| Task | Data | Risultato |
|------|------|-----------|
| Fix Gameseal discounts | 2026-03-31 | ✅ Sconto default 15% invece di 0% |

---

## Cose da Fare Prossimamente

1. **[UTENTE]** Abilitare Google Indexing API in GCP: `console.cloud.google.com/apis/library/indexing.googleapis.com?project=832146891661` → poi Claude può richiedere crawl delle 14 pagine prioritarie
2. **[UTENTE]** Backlink building manuale: Reddit (r/CoOpGaming, r/patientgamers), Discord gaming IT, directory italiane (checklist in `.planning/backlink_checklist.md`)
3. [ ] Creare Cloudflare Cache Rule per migliorare hit rate (7.6% → target 60%+)
4. [ ] Verificare indexing 48-72h dopo sitemap resubmit
5. [ ] Espansione catalogo (T3.2 ROADMAP)

## GSC Analytics (2026-03)

| Metrica | Valore |
|---------|--------|
| Clicks | 7 |
| Impressions | 383 |
| CTR | 1.83% |
| Pos Media | 20.6 |

### Query pos 6-10 con 0 clic (da migliorare)
- "coop online game" (pos 8.0)
- "coop online games" (pos 7.0)
- "game pc coop" (pos 6.0)
- "giochi cooperativi pc" (pos 9.0)

---

## Learnings

- Il sito ha 589 giochi catalogati (max ID 609)
- SEO Score: 91/100 | GEO Score: 82/100
- **8 hub pages IT + 8 EN** con contenuto editoriale completo
- 17 mini-recensioni su giochi trending
- 2.137 affiliate links (IG, GB, GMG, GAMIVO, K4G, Gameseal)
- Cloudflare: ~15.082 pageviews/mese, cache hit 7.6% (basso)
- GSC: 7 click, 408 impressioni, 1.72% CTR, pos 20.7 (traffico organico quasi zero)
- Problema principale: dominio giovane (3 settimane), 0 backlink, pochissime pagine indicizzate
- Analytics: `python3 scripts/fetch_analytics.py --days 30`
- Workflow CI: `update.yml` (lunedì) include build_hub_pages.py; `free_games.yml` (giornaliero)

## Strumenti AI

| Strumento | Uso |
|-----------|-----|
| GSD | `.planning/` — project management, task veloci |
| Ralph | `scripts/ralph/ralph.sh` — task meccanici/ripetitivi |
| BMAD | `/bmad-*` skills — review, brainstorming, analisi |

---

## Archivio Sessioni

- 2026-03-31: Setup GSD, mappatura codebase, creazione roadmap
- 2026-03-31: Fase 1 completata - cache, Gameseal fix (15% default), GSC analisi
- 2026-03-31: GSD quick task - Fix Gameseal discounts
- 2026-03-31 18:30: SEO miglioramenti - title/meta, hub editoriali, mini-reviews, backlink checklist

---

## Workflow GSD Usato

1. **map-codebase**: Mappato codebase con 7 agent paralleli
2. **new-project**: Creati PROJECT.md, REQUIREMENTS.md, ROADMAP.md
3. **quick task**: Fix Gameseal con piano in `.planning/quick/`
