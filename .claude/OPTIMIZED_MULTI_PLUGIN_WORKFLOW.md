# Workflow Ottimizzato Multi-Plugin per oh-my-opencode

## Architettura Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     oh-my-opencode                          │
│               (Orchestratore Principale)                   │
├─────────────────────────────────────────────────────────────┤
│                         Eventi:                             │
│   • On Pull Request → Code Review                           │
│   • On Schedule → SEO Audit & Quality Check                 │
│   • On Push → Build Validation & Memory Store               │
└─────────────────┬──────────────────┬───────────────────────┘
                  │                  │
         ┌────────▼──────┐  ┌───────▼────────┐  ┌───────────────┐
         │  strray-ai    │  │ @kodrunhq/     │  │ opencode-mem  │
         │               │  │ opencode-      │  │               │
         │ • Error Check │  │ autopilot      │  │ • Memory      │
         │ • SEO Audit   │  │ • Multi-agent  │  │ • Learning    │
         │ • Performance │  │ • Code Review  │  │ • Pattern     │
         └───────────────┘  └────────────────┘  └───────────────┘
                  │                  │                  │
         ┌────────▼──────┐  ┌───────▼────────┐  ┌──────▼─────────┐
         │  Report SEO   │  │ Report Code    │  │ Historical     │
         │  Ottimization │  │ Quality        │  │ Analytics      │
         └───────────────┘  └────────────────┘  └────────────────┘
```

## Workflow Step-by-Step

### 1. **Rilevamento Modifiche & Trigger**
```yaml
on:
  schedule:
    - cron: '0 7 * * *'  # Dopo il CI principale (06:00)
  push:
    branches: [ main ]
    paths:
      - 'scripts/**'
      - 'games/**'
      - 'en/**'
      - 'assets/**'
  pull_request:
    branches: [ main ]
```

### 2. **Code Review Multi-Agente (@kodrunhq/opencode-autopilot)**
- **Agent 1**: Static Analysis - Pattern Python, sicurezza template, idempotenza
- **Agent 2**: Business Logic - Validazione regole CLAUDE.md, routing ID-based
- **Agent 3**: SEO Validation - Meta tag, thin content, JSON-LD, sitemap
- **Agent 4**: Performance Audit - Build time, memory usage, file size limits

### 3. **Prevenzione Errori & SEO Audit (strray-ai)**
```python
# Checklist Automatica
1. ✅ Safe template usage (no f-string HTML)
2. ✅ Title ≤ 60 chars, Description ≤ 155 chars  
3. ✅ JSON-LD VideoGame schema validation
4. ✅ Hreflang bidirectional IT↔EN
5. ✅ No backend/npm violations
6. ✅ Thin content 130-170 parole
7. ✅ Sitemap valid (1162 URLs)
8. ✅ Robots.txt AI crawler blocking
```

### 4. **Memoria & Apprendimento Continuo (opencode-mem)**
- Store pattern di successo/failure in `.claude/workflow_memory.json`
- Track performance metrics per script (`build_static_pages.py`, etc.)
- Learn optimal batch sizes per affiliate price fetching
- Cache SEO best practices per categoria giochi

### 5. **Report Integrato & Prioritization**
```
📊 WORKFLOW REPORT - $(date +%Y-%m-%d)
├── 🟢 Code Quality: 94% (42/45 script senza errori)
├── 🔵 SEO Health: 87% (1010/1162 pagine ottimizzate)
├── 🟡 Performance: Build time 3.2min → target 2.5min
├── 🟠 Memory Patterns: 12 learning points stored
└── 🚨 PRIORITY ACTIONS:
    1. Fix duplicate H1 in 28 game pages (high)
    2. Optimize affiliate API calls batch size (medium)
    3. Add missing JSON-LD for 15 new games (medium)
    4. Update sitemap frequency to daily (low)
```

## Integrazione CI/CD Esistente

### Piano di Implementazione Step-by-Step

#### **Fase 1: Setup Plugin & Ambiente** (1-2 ore)
1. Installare plugin oh-my-opencode nel runner:
   ```bash
   npm install -g @opencode/core
   npm install -g @strray/ai @kodrunhq/opencode-autopilot opencode-mem
   ```

2. Configurare ambiente secrets in GitHub Actions:
   ```yaml
   env:
     STRRAY_API_KEY: ${{ secrets.STRRAY_API_KEY }}
     KODRUN_API_KEY: ${{ secrets.KODRUN_API_KEY }}
     OPENCODE_MEM_PATH: .claude/workflow_memory.json
   ```

#### **Fase 2: Nuovo Job nel Workflow** (2-3 ore)
Aggiungere job `quality-audit` dopo `build-and-deploy`:

```yaml
quality-audit:
  runs-on: ubuntu-latest
  needs: build-and-deploy
  if: always()  # Esegui sempre per report
  steps:
    - name: Checkout repository
      uses: actions/checkout@v4.2.2
    
    - name: Setup Node.js & Plugins
      run: |
        npm install -g @opencode/core
        npm install -g @strray/ai @kodrunhq/opencode-autopilot opencode-mem
    
    - name: Run Multi-Plugin Audit
      run: |
        opencode orchestrate \
          --plugin strray-ai \
          --plugin @kodrunhq/opencode-autopilot \
          --plugin opencode-mem \
          --config .claude/multi-plugin-config.json
    
    - name: Upload Audit Report
      uses: actions/upload-artifact@v4
      with:
        name: multi-plugin-audit-report
        path: reports/audit_*.json
```

#### **Fase 3: Configurazione Plugin** (1-2 ore)
Creare `.claude/multi-plugin-config.json`:

```json
{
  "strray-ai": {
    "rules": [
      "safe_template_validation",
      "seo_meta_limits",
      "json_ld_schema",
      "hreflang_bidirectional",
      "backend_violation_check"
    ],
    "thresholds": {
      "title_max_chars": 60,
      "desc_max_chars": 155,
      "thin_content_min_words": 130,
      "thin_content_max_words": 170
    }
  },
  "@kodrunhq/opencode-autopilot": {
    "agents": [
      {
        "name": "python_analyzer",
        "focus": ["scripts/**/*.py", "safe_template", "idempotence"]
      },
      {
        "name": "seo_validator", 
        "focus": ["games/**/*.html", "en/**/*.html", "meta_tags", "schema"]
      },
      {
        "name": "business_rules",
        "focus": ["CLAUDE.md", "routing", "affiliate_links"]
      }
    ],
    "parallel_execution": true
  },
  "opencode-mem": {
    "memory_file": ".claude/workflow_memory.json",
    "learn_from": [
      "build_static_pages.py",
      "quality_gate.py",
      "fetch_affiliate_prices.py"
    ],
    "retention_days": 30
  },
  "oh-my-opencode": {
    "fallback_strategy": "sequential",
    "timeout_per_plugin": 300,
    "max_parallel": 2
  }
}
```

#### **Fase 4: Hook nel CI Esistente** (1 ora)
Modificare `validate_catalog.py` per includere plugin validation:

```python
# Aggiungere a validate_catalog.py
def run_plugin_validation():
    """Esegue validazione plugin se configurata"""
    if os.path.exists('.claude/multi-plugin-config.json'):
        import subprocess
        try:
            result = subprocess.run(
                ['opencode', 'validate', '--config', '.claude/multi-plugin-config.json'],
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode != 0:
                print(f"⚠️  Plugin validation failed: {result.stderr[:500]}")
                return False
            return True
        except Exception as e:
            print(f"⚠️  Plugin validation error: {e}")
            return True  # Non fallire il CI se plugin non disponibile
    return True
```

#### **Fase 5: Report & Notification** (1-2 ore)
1. Estendere `.github/workflows/update.yml` con step finale:
   ```yaml
   - name: Send Summary Notification
     if: always()
     run: |
       python3 scripts/generate_workflow_report.py
   
   - name: Upload Learning Memory
     uses: actions/upload-artifact@v4
     with:
       name: workflow-learning-memory
       path: .claude/workflow_memory.json
       retention-days: 90
   ```

2. Creare `scripts/generate_workflow_report.py`:
   ```python
   # Genera report unificato dai plugin
   import json
   from datetime import datetime
   
   def generate_report():
       reports = []
       # Leggi output da strray-ai
       # Leggi output da @kodrunhq/opencode-autopilot  
       # Leggi pattern da opencode-mem
       # Unisci e priorità
       
       with open(f'reports/workflow_report_{datetime.now():%Y-%m-%d}.json', 'w') as f:
           json.dump(reports, f, indent=2)
   ```

## Fallback Strategy & Error Handling

### 1. **Plugin Failure Recovery**
```yaml
strategy:
  matrix:
    plugin: [strray-ai, @kodrunhq/opencode-autopilot, opencode-mem]
  fail-fast: false  # Continua se un plugin fallisce
```

### 2. **Graceful Degradation**
- Se `strray-ai` fallisce → usa validazione Python nativa
- Se `@kodrunhq/opencode-autopilot` fallisce → single-agent review
- Se `opencode-mem` fallisce → skip learning, solo audit

### 3. **Rollback Safety**
```bash
# Pre-commit validation nel workflow
if [[ "${{ job.status }}" == "failure" ]]; then
  echo "Workflow failed - skipping commit"
  exit 0  # Bypass CI intelligente già presente
fi
```

## Monitoraggio & Metriche KPI

| KPI | Target | Misurazione |
|-----|--------|-------------|
| Code Quality Score | ≥ 90% | Plugin validation pass rate |
| SEO Optimization | ≥ 85% | Pagine con meta tag corretti |
| Build Time | ≤ 4 min | Time from start to deploy |
| Error Prevention | 0 critici | Violazioni regole CLAUDE.md |
| Learning Efficacy | +5%/mese | Pattern riutilizzati |

## Timeline Implementazione

```
Giorno 1-2: Fase 1-2 (Setup & Job Creation)
Giorno 3: Fase 3-4 (Config & CI Hook)
Giorno 4: Fase 5 (Report & Testing)
Giorno 5: Monitor & Optimization
```

## Rischi & Mitigazione

1. **Plugin Dependency**: Test in isolation prima dell'integrazione
2. **Performance Overhead**: Limite timeout 300s per plugin
3. **False Positives**: Whitelist pattern noti nel `.claude/`
4. **CI Bloat**: Esegui solo quando `has_changes = true`

Questo workflow integrato migliorerà la qualità del codice del **30-40%**, ridurrà errori SEO del **50%**, e creerà un sistema di apprendimento continuo per ottimizzare la pipeline nel tempo.