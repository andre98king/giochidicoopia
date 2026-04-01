---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Database Quality & Co-op Purity
status: executing
stopped_at: Completed 01-01-PLAN.md (schema foundation + CI hardening)
last_updated: "2026-04-01T10:50:20.138Z"
last_activity: 2026-04-01
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 2
  completed_plans: 1
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-01)

**Core value:** Il posto dove i gamer vanno quando vogliono dire "giochiamo insieme stasera" — catalogo co-op PC con qualita certificata
**Current focus:** Phase 01 — schema-foundation-ci-hardening

## Current Position

Phase: 01 (schema-foundation-ci-hardening) — EXECUTING
Plan: 2 of 2
Status: Ready to execute
Last activity: 2026-04-01

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
| Phase 01-schema-foundation-ci-hardening P01 | 8 | 2 tasks | 5 files |

## Accumulated Context

### Decisions

- [Pre-v1.1]: coopScore semantics definiti: 3=Co-op Core, 2=Co-op Solid, 1=Co-op Marginale, null=non ancora scorato
- [Pre-v1.1]: Tutti gli script output JSON per revisione manuale — nessuna auto-scrittura al catalogo senza approvazione utente
- [Pre-v1.1]: `audit_coop_tags.py` NON va aggiunto a GitHub Actions — solo CLI manuale
- [Pre-v1.1]: Phase 3 (Classic Discovery) e Phase 2 (Audit) sono eseguibili in parallelo dopo Phase 1
- [Phase 01-schema-foundation-ci-hardening]: coopScore uses None/null (not 0) to distinguish unscored games from scored games — preserves Phase 2 scoring semantics
- [Phase 01-schema-foundation-ci-hardening]: gmgUrl and gmgDiscount added to public catalog export (were missing) alongside coopScore

### Pending Todos

- [UTENTE] Abilitare Google Indexing API in GCP
- [UTENTE] Backlink building manuale (Reddit, Discord, directory italiane)
- Creare Cloudflare Cache Rule (hit rate attuale: 15.3%, target: 60%+)

### Blockers/Concerns

- CI gira giornalmente (non settimanalmente come scritto in CLAUDE.md) — Phase 1 deve risolvere questo prima di qualsiasi lavoro di scoring

## Session Continuity

Last session: 2026-04-01T10:50:20.134Z
Stopped at: Completed 01-01-PLAN.md (schema foundation + CI hardening)
Resume file: None
