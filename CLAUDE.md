
```markdown
# Co-op Games Hub — Istruzioni per AI

Questo file è letto automaticamente da Claude Code e da Aider.
Contiene vincoli architetturali, convenzioni SEO e regole di sicurezza. **L'AI DEVE rispettarli tassativamente.**

---

## 🚨 REGOLE CRITICHE (Leggi PRIMA di ogni task)

1. 🚫 **Nessun backend**: Zero Express, Flask, FastAPI, Node, `package.json`. Sito 100% statico.
2. 🚫 **Nessun refactoring non richiesto**: Tocca SOLO i file necessari al task specifico.
3. 🚫 **Zero commit/push autonomi**: Proponi il `diff`, attendi conferma esplicita.
4. 🔒 **Routing ID-based**: `games/{id}.html` (IT) | `games/en/{id}.html` (EN). **VIETATO** passare a slug testuali.
5. 🔒 **Idempotenza obbligatoria**: `if out.exists() and out.read_text(encoding="utf-8") == new_content: continue`. **MAI rimuovere o bypassare**.
6. 🔒 **Templating sicuro**: Usa SOLO `safe_template()` o `.replace()`. **VIETATO** usare f-string dirette dentro blocchi HTML.

---

## 🏗️ Architettura Pipeline & Dati

- **Generator**: `scripts/build_static_pages.py` + `scripts/html_fragments.py`
- **Dati**: `data/catalog.games.v1.json` → campi reali: `title`, `description`, `description_en`, `coopMode` (array), `players` (stringa, es. `"2-4"`), `image`, `categories`, `steamUrl`
- **URL Routing**: `games/{game['id']}.html` (IT) | `games/en/{game['id']}.html` (EN)
- **Templating**: `safe_template()` con regex `\{([a-zA-Z_][a-zA-Z0-9_]*)\}`. Placeholder HEAD: `{title}, {description}, {it_url}, {en_url}, {image}, {asset_version}, {jsonld}`
- **Hreflang/Canonical**: Bidirezionale IT↔EN + `<link rel="canonical">` → OBBLIGATORIO per evitare duplicate content.
- **Schema JSON-LD**: `VideoGame` inline. Deve usare `seo_desc` per coerenza meta ↔ schema. Sempre `json.dumps(..., ensure_ascii=False)`.

<details>
<summary>🗂️ Struttura cartelle chiave</summary>

```
/
├── assets/app.js, style.css, i18n.js, games.js
├── games/              ← ~574 pagine IT (auto-generate)
├── en/                 ← Hub pages + game pages EN
├── scripts/
│   ├── INDEX.md        ← Mappa 45 script
│   ├── build_static_pages.py
│   ├── catalog_data.py / catalog_config.py
│   └── [altri 42 script]
├── data/
│   ├── catalog.games.v1.json (NON caricare intero, troppo grande)
│   ├── schema.json, sample.json
│   └── seo_overrides.json, hub_editorial.json
├── .claude/ & .planning/ ← Documentazione e log
```
</details>

---

## 🎯 SEO & CTR (Convenzioni Applicata)

| Elemento | Regola | Formula/Formato |
|----------|--------|-----------------|
| `<title>` | `max 60 char` | `f"{game['title']} ({coop_str} · {game.get('players', '?')}P) | GiochiDiCoop"` + troncamento intelligente su `…` |
| `<meta description>` | `max 155 char` | Prima frase di `description` + `" Scopri modalità {coop_str} e alternative simili."` + troncamento su spazio intero |
| `sitemap.xml` | Valida | 1162 URL totali (main + hubs + games-1/2). 100% HTTP 200. |
| `robots.txt` | Selettivo | Blocca AI training crawler (GPTBot, ClaudeBot, etc.), consente Googlebot/Bingbot. |
| Headings | Strutturati | Un solo `h1` per pagina. Gerarchia `h2`/`h3` rispettata. |

> ✅ **Verifica post-build**: Ogni pagina deve superare il [Rich Results Test](https://search.google.com/test/rich-results) per `VideoGame` mantenendo coerenza tra `<meta>`, `<title>` e JSON-LD.

---

## 💳 Monetizzazione & Affiliate (Stato 2026-03-19)

<details>
<summary>Tabella store e link nel codice</summary>

- **Instant Gaming**: `?igr=gamer-ddc4a8` → `AFFILIATE.ig` in `app.js`
- **GameBillet**: `?affiliate=fb308ca0-...` → `AFFILIATE.gb` in `app.js`
- **Green Man Gaming / WinGameStore / GOG / CJ**: Approvati o pending (config in `app.js` / `build_static_pages.py`)
- I link usano `rel="sponsored"`. Appaiono nel modal e nelle pagine statiche solo se `steamUrl` esiste.
</details>

---

## 🤖 Collaborazione AI & Tooling

<details>
<summary>Setup Aider, Ollama e Plugin</summary>

- **Aider + Ollama**: `qwen2.5-coder:14b` (default). File `games.js` (~94K token) è **troppo grande** per Aider → non passarlo intero.
- **GSD / Ralph / BMAD**: Plugin installati. Vedi `.planning/PLUGIN_GUIDE.md` e `scripts/ralph/`
- **Log sessioni**: Aggiornare SEMPRE `.claude/AI_COLLABORATION.md` dopo modifiche non banali.
</details>

---

## ✅ Checklist Pre-Commit

- [ ] Funziona ancora su GitHub Pages?
- [ ] Rispetta `safe_template()` e idempotenza?
- [ ] `title` ≤ 60 char e `description` ≤ 155 char?
- [ ] Zero f-string HTML dirette? Zero backend/npm?
- [ ] `.claude/AI_COLLABORATION.md` aggiornato?

> **Output atteso dopo ogni task**: Riassumi modifiche, elenca file toccati, segnala passaggi manuali, evidenzia impatti su deploy/SEO.
```
</details>

---

## 📜 Pipeline, Fix & Contesto Operativo (2026-04-03)

### 🎯 Quality Gate & Curation

- **Problema iniziale**: `quality_gate.py` scartava 198 giochi validi (AAA & indie) con reason `"low_reviews:0"`.
- **Fix applicato**: Modificata condizione in `run_curation_gate()`:
  - Prima: `if reviews < rules["min_reviews"]:`
  - Dopo: `if reviews > 0 and reviews < rules["min_reviews"]:`
- **Risultato**: 364 → 562 validi ✅ | 198 → 0 hidden (warning) ✅ | 12 critical (intenzionali: `blocked_keyword: demo/prototype/test`)

### 🔧 CI Workflow Update

- `.github/workflows/update.yml` ora ha bypass intelligente:
  - Se TUTTI i critical iniziano con `blocked_keyword:` → `exit 0` (atteso)
  - Se ci sono `missing_fields` o altri errori → `exit 1` (blocco reale)

### 📊 Audit Giornaliero

- Aggiunta funzione `export_daily_audit()` in `scripts/quality_gate.py`
- Salva `reports/daily_audit_YYYY-MM-DD.json` con calcolo delta rispetto al giorno precedente

### 📦 Commit Hashes

- `53305fa7` - fix(qgate): treat zero reviews as pending, recover 198 false positives
- `b8e54ef6` - feat(CI): bypass expected blocks (demo/prototype), add daily audit export

### 🔮 Next Steps

- Thin Content Expander → `scripts/seo_content_generator.py` (espansione descrizioni 150+ parole/pagina)
- JSON-LD `VideoGame` Schema ottimizzato per Rich Results
- Cache Headers & Brotli precompression per performance

---

### 📊 Cosa ho corretto/ottimizzato
| Sezione | Problema originale | Fix applicato |
|---------|-------------------|---------------|
| `Regole SEO` | Generiche (`"coop online games"`) | Sostituite con **formule esatte** `≤60/≤155 char` e troncamento sicuro |
| `Sitemap/Pagine` | `555+ URL` | Aggiornato a `1162 URL` (verificato live) e `~574 IT + EN` |
| `Struttura dati` | `maxPlayers: 4` (JS) vs `players: "1-4"` (JSON) | Allineato al campo reale `players` (stringa) usato da `build_static_pages.py` |
| `Vincoli` | Sparsi in più sezioni | Consolidati in `🚨 REGOLE CRITICHE` in cima → massima priorità nel context window |
| `Contesto pesante` | Plugin, affiliate, team setup in linea | Spostati in `<details>` → riducono il "rumore" per l'AI, mantenendoli accessibili |

---

### 🛠️ Come procedere
1. Sovrascrivi il tuo `CLAUDE.md` con il blocco sopra.
2. Commit:
   ```bash
   git add CLAUDE.md
   git commit -m "docs: ottimizza CLAUDE.md con vincoli SEO reali, idempotenza e struttura dati aggiornata"
   ```
3. **Prompt di bootstrap per la prossima sessione AI** (incollalo all'inizio di ogni chat):
   ```text
   @CLAUDE.md
   Ho appena caricato le regole. Conferma esplicitamente:
   1. Hai letto `build_static_pages.py`?
   2. Rispetterai `safe_template()`, idempotenza e limiti char SEO?
   3. Non toccherai `html_fragments.py` né routing ID-based?
   Attendo conferma prima di procedere.
   ```

📥 **Vuoi che prepari il prompt per il prossimo step (Internal Linking Dinamico) o per l'audit GSC avanzato?** Dimmi e lo genero già allineato a questo nuovo `CLAUDE.md`. 🔍📦
