# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-01)

**Core value:** Il posto dove i gamer vanno quando vogliono dire "giochiamo insieme stasera" — catalogo co-op PC con qualita certificata
**Current focus:** Phase 1 — Schema Foundation & CI Hardening

## Current Position

Phase: 1 of 4 (Schema Foundation & CI Hardening)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-04-01 — Roadmap v1.1 creata, Phase 1 pronta per planning

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0h

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:** No data yet

*Updated after each plan completion*

## Accumulated Context

### Decisions

- [Pre-v1.1]: coopScore semantics definiti: 3=Co-op Core, 2=Co-op Solid, 1=Co-op Marginale, null=non ancora scorato
- [Pre-v1.1]: Tutti gli script output JSON per revisione manuale — nessuna auto-scrittura al catalogo senza approvazione utente
- [Pre-v1.1]: `audit_coop_tags.py` NON va aggiunto a GitHub Actions — solo CLI manuale
- [Pre-v1.1]: Phase 3 (Classic Discovery) e Phase 2 (Audit) sono eseguibili in parallelo dopo Phase 1

### Pending Todos

- [UTENTE] Abilitare Google Indexing API in GCP
- [UTENTE] Backlink building manuale (Reddit, Discord, directory italiane)
- Creare Cloudflare Cache Rule (hit rate attuale: 15.3%, target: 60%+)

### Blockers/Concerns

- CI gira giornalmente (non settimanalmente come scritto in CLAUDE.md) — Phase 1 deve risolvere questo prima di qualsiasi lavoro di scoring

## Session Continuity

Last session: 2026-04-01
Stopped at: Roadmap v1.1 creata con 4 fasi e 15 requirements mappati
Resume file: None
