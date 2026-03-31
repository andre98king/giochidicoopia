# Co-op Games Hub — PROJECT.md

## Visione

Il posto dove i gamer vanno quando vogliono dire "giochiamo insieme stasera" — catalogo co-op PC con qualità certificata, per chi vuole staccare da MMORPG e PvP competitivo e riscoprire i veri titoli cooperativi, nuovi e classici.

## Current Milestone: v1.1 — Database Quality & Co-op Purity

**Goal:** Trasformare il catalogo nella fonte più affidabile di giochi veramente co-op — qualità sui dati, zero compromessi sulla definizione di "gioco co-op".

**Target features:**
- Audit completo tag coopMode su tutti i 589 giochi (correggere/rimuovere giochi non veramente co-op)
- Nuovo campo `coopScore` 1-3 (1=co-op marginale, 2=co-op solido, 3=pensato per co-op)
- Fix dati mancanti: maxPlayers, coopMode, crossplay su giochi incompleti
- Script candidati classici/sottovalutati (tutte le epoche) + revisione manuale per approvazione

---

## Obiettivi Strategici

1. **Crescita organica**: Aumentare traffico da Google, costruire backlink
2. **Monetizzazione sostenibile**: Revenue affiliate senza compromettere UX
3. **Qualità tecnica**: Performance veloci, SEO solido, UX mobile-first

---

## Vincoli

- **Stack**: HTML + CSS + JavaScript puro, Python pipeline, GitHub Pages + Cloudflare
- **Nessun backend**: Tutto statico
- **Nessun analytics**: Scelta GDPR
- **Budget**: Dominio e hosting già configurati

---

## Stack Tecnologico

- Frontend: HTML5, CSS3, JavaScript ES6+
- Pipeline: Python 3.11 (httpx, requests, beautifulsoup4)
- Hosting: GitHub Pages + Cloudflare (DNS, proxy, cache, HTTPS)
- CI/CD: GitHub Actions

---

## Budget e Risorse

- Tempo: Sviluppo part-time, ~5h/settimana
- Budget: Costo dominio (~€15/anno) + Cloudflare (piano free)
- Team: 1 persona + AI assistant (Claude, Aider)

---

## Timeline

- Fase 1 (Q1 2026): Stabilizzazione pipeline, fix cache, SEO base
- Fase 2 (Q2 2026): Monetizzazione, backlink building, contenuti editoriali
- Fase 3 (Q3 2026): Scale - nuove feature, espansione categorie

---

## Metriche di Successo

| Metrica | Target Q1 | Target Q2 |
|---------|-----------|-----------|
| PageViews/mese | 20k | 50k |
| Click GSC/mese | 50 | 200 |
| Cache Hit Rate | 90%+ | 90%+ |
| SEO Score | 95+ | 95+ |
| Revenue affiliate | €0 | €50/mese |

---

## Stakeholder

- **Utenti**: Giocatori coop PC, cercano giochi con amici
- **Partner**: Instant Gaming, GameBillet, Green Man Gaming, Gameseal
- **Proprietario**: Andrea (sviluppatore)

---

## Riferimenti

- `.planning/codebase/` — Analisi codebase
- `project_roadmap_state.md` — Stato attuale

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

*Last updated: 2026-04-01 — Milestone v1.1 started*
