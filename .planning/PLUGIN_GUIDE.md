# Guida Plugin AI — Co-op Games Hub

I tre plugin installati per migliorare il workflow di sviluppo.

---

## GSD (Get Shit Done)

**Quando usarlo**: Per pianificare e gestire task complessi con context engineering.

### Comandi Principali

```bash
/gsd:new-project          # Inizializza nuovo progetto/feature
/gsd:map-codebase         # Analizza codebase esistente
/gsd:quick <task>         # Task veloce senza planning completo
/gsd:discuss-phase <n>   # Chiarisci dettagli implementativi
/gsd:plan-phase <n>      # Crea piani esecutivi
/gsd:execute-phase <n>  # Esegui i piani
/gsd:verify-work <n>     # Verifica manually il lavoro
/gsd:progress            # Mostra stato attuale
/gsd:next                # Auto-avanza al prossimo step
/gsd:help                # Mostra tutti i comandi
```

### Per Questo Progetto

Il sito ha già la documentazione in `.planning/`:
- `.planning/PROJECT.md` — Visione e obiettivi
- `.planning/REQUIREMENTS.md` — Requisiti v1-v3
- `.planning/ROADMAP.md` — 3 fasi, 8 milestone
- `.planning/codebase/` — Analisi completa

---

## Ralph

**Quando usarlo**: Per task autonomi ripetitivi che devono essere completati iterativamente.

### Installazione (già fatta)

```bash
# Copia gli script nella directory del progetto
mkdir -p scripts/ralph
cp /tmp/ralph/ralph.sh scripts/ralph/
chmod +x scripts/ralph/ralph.sh
```

### Utilizzo

```bash
# Creare prd.json con le task da fare
./scripts/ralph/ralph.sh 10    # Max 10 iterazioni
```

### Come Funziona

1. Ogni iterazione = nuova istanza AI con contesto pulito
2. Implementa una story alla volta
3. Aggiorna prd.json con `passes: true`
4. Quando tutte le story passano → `<promise>COMPLETE</promise>`

---

## BMAD (Breakthrough Method for Agile AI-Driven Development)

**Quando usarlo**: Per review del codice, analisi architetturale, brainstorming.

### Skill Disponibili

| Skill | Uso |
|-------|-----|
| `bmad-help` | Chiedi "cosa devo fare adesso?" |
| `bmad-party-mode` | Bring multiple agent personas in session |
| `bmad-brainstorming` | Sessione brainstorming strutturata |
| `bmad-review-adversarial-general` | Code review critica |
| `bmad-review-edge-case-hunter` | Trova edge case mancanti |
| `bmad-editorial-review-prose` | Review contenuti testuali |

### Come Usare

```bash
# Chiedi al bot
bmad-help          # Dice cosa fare dopo
bmad-party-mode   # Attiva modalità party con più agenti
```

---

## Workflow Consigliato

### Per Task Semplici (fix veloci)
```
1. Usa /gsd:quick "fix gameseal discounts"
```

### Per Task Complessi (nuove feature)
```
1. /gsd:new-project  (già fatto)
2. /gsd:discuss-phase 1
3. /gsd:plan-phase 1  
4. /gsd:execute-phase 1
5. /gsd:verify-work 1
```

### Per Task Ripetitivi ( Ralph)
```
1. Crea prd.json con le story
2. ./scripts/ralph/ralph.sh
```

### Per Review
```
1. bmad-review-adversarial-general
2. bmad-help (chiedi suggerimenti)
```

---

## File Creati

I plugin hanno creato:
- `.planning/` — Documentazione GSD
- `.planning/codebase/` — Analisi 7 documenti

Questi file sono tracciati in gitignore e non vengono committati.
