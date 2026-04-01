---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Database Quality & Co-op Purity
status: phase_complete
stopped_at: Phase 1 verified — ready to start Phase 2 or Phase 3 (parallel)
last_updated: "2026-04-01T11:45:00Z"
last_activity: 2026-04-01
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 2
  completed_plans: 2
  percent: 25
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-01)

**Core value:** Il posto dove i gamer vanno quando vogliono dire "giochiamo insieme stasera" — catalogo co-op PC con qualita certificata
**Current focus:** Phase 01 COMPLETE — ready for Phase 02 (Tag Audit & coopScore) or Phase 03 (Classic Discovery) in parallel

## Current Position

Phase: 01 (schema-foundation-ci-hardening) — COMPLETE AND VERIFIED
Plan: 2 of 2
Status: Verification passed (4/4 success criteria met) — ready to start Phase 2 and/or Phase 3
Last activity: 2026-04-01

Progress: [##########] 25% (1/4 phases complete)

## Performance Metrics

**Velocity:**

- Total plans completed: 2
- Average duration: 9 min/plan
- Total execution time: ~18min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 01 | 2 plans | 18min | 9min |

**Recent Trend:** Phase 1 executed at planned speed, 0 gaps found in verification

*Updated after each plan completion*
| Phase 01-schema-foundation-ci-hardening P01 | 8 | 2 tasks | 5 files |
| Phase 01-schema-foundation-ci-hardening P02 | 10 | 2 tasks | 11 files |

## Accumulated Context

### Decisions

- [Pre-v1.1]: coopScore semantics definiti: 3=Co-op Core, 2=Co-op Solid, 1=Co-op Marginale, null=non ancora scorato
- [Pre-v1.1]: Tutti gli script output JSON per revisione manuale — nessuna auto-scrittura al catalogo senza approvazione utente
- [Pre-v1.1]: `audit_coop_tags.py` NON va aggiunto a GitHub Actions — solo CLI manuale
- [Pre-v1.1]: Phase 3 (Classic Discovery) e Phase 2 (Audit) sono eseguibili in parallelo dopo Phase 1
- [Phase 01-schema-foundation-ci-hardening]: coopScore uses None/null (not 0) to distinguish unscored games from scored games — preserves Phase 2 scoring semantics
- [Phase 01-schema-foundation-ci-hardening]: gmgUrl and gmgDiscount added to public catalog export (were missing) alongside coopScore
- [Phase 01-schema-foundation-ci-hardening]: coopMode vocabulary canonical: {online, local, sofa} — 'split' permanently retired, CANONICAL_COOP_MODES enforced in validator

### Pending Todos

- [UTENTE] Abilitare Google Indexing API in GCP
- [UTENTE] Backlink building manuale (Reddit, Discord, directory italiane)
- Creare Cloudflare Cache Rule (hit rate attuale: 15.3%, target: 60%+)

### Blockers/Concerns

- CI gira giornalmente — Phase 1 ha risolto il problema di sovrascrittura dati curati

## Phase 1 Verification Summary

- SCH-01: SATISFIED — coopScore in all 589 games and both JSON exports
- SCH-02: SATISFIED — coopScore preserved through CI round-trip (auto_update.py reads and writes it unchanged)
- SCH-03: SATISFIED — continue-on-error removed from 2 build steps; 5 remain on affiliate fetch steps only
- SCH-04: SATISFIED — CANONICAL_COOP_MODES={"online","local","sofa"} enforced as hard error; 210 "split" renamed to "sofa"; 0 violations
- Verification report: .planning/phases/01-schema-foundation-ci-hardening/01-VERIFICATION.md

## Session Continuity

Last session: 2026-04-01T11:45:00Z
Stopped at: Phase 1 verified — all 4 success criteria passed
Resume file: None
Next action: Start Phase 2 (Tag Audit & coopScore Generation) and/or Phase 3 (Classic Game Discovery) — both depend only on Phase 1 which is now complete
