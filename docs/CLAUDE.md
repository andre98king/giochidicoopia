# Co-op Games Hub — Istruzioni per AI

Questo file è letto automaticamente da Claude Code.
Contiene vincoli architetturali, convenzioni SEO e regole di sicurezza. **L'AI DEVE rispettarli tassativamente.**

---

## 🚨 REGOLE CRITICHE (Leggi PRIMA di ogni task)

1. 🚫 **Nessun backend**: Zero Express, Flask, FastAPI, Node, `package.json`. Sito 100% statico.
2. 🚫 **Nessun refactoring non richiesto**: Tocca SOLO i file necessari al task specifico.
3. 🚫 **Zero commit/push autonomi**: Proponi il `diff`, attendi conferma esplicita (`APPLICA`).
4. 🔒 **Routing ID-based**: `games/{id}.html` (IT) | `games/en/{id}.html` (EN). **VIETATO** passare a slug testuali.
5. 🔒 **Idempotenza obbligatoria**: `if out.exists() and out.read_text(encoding="utf-8") == new_content: continue`. **MAI rimuovere o bypassare**.
6. 🔒 **Templating sicuro**: Usa SOLO `safe_template()` o `.replace()`. **VIETATO** usare f-string dirette dentro blocchi HTML.
7. 🔒 **Soglie anti-shovelware intoccabili**: `reviews == 0` → `pending data`, non fail.
8. 🌐 **Build statica pura**: Zero JS client-side per contenuti generati. Tutto in `build_static_pages.py`.
9. ✅ **CI bypass intelligente**: `blocked_keyword:` (demo/test/prototype) → `exit 0`. Errori strutturali → `exit 1`.

---

## 🏗️ Architettura Pipeline & Dati

- **Generator**: `scripts/build_static_pages.py` + `scripts/html_fragments.py` + `scripts/seo_content_generator.py`
- **Dati**: `data/catalog.games.v1.json` → campi reali: `title`, `description`, `description_en`, `coopMode` (array), `players` (stringa, es. `"2-4"`), `image`, `categories`, `steamUrl`
- **URL Routing**: `games/{game['id']}.html` (IT) | `games/en/{game['id']}.html` (EN)
- **Templating**: `safe_template()` con regex `\{([a-zA-Z_][a-zA-Z0-9_]*)\}`. Placeholder HEAD: `{title}, {description}, {it_url}, {en_url}, {image}, {asset_version}, {jsonld}`
- **Hreflang/Canonical**: Bidirezionale IT↔EN + `<link rel="canonical">` → OBBLIGATORIO per evitare duplicate content.
- **Schema JSON-LD**: `VideoGame` via `generate_json_ld()` in `seo_content_generator.py`. Sempre `json.dumps(..., ensure_ascii=False)`.
- **Thin Content**: `generate_game_description()` in `seo_content_generator.py` — blocco HTML deterministico 130-170 parole, seed `hashlib.md5(game_id)`.

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
│   ├── seo_content_generator.py  ← thin content + JSON-LD
│   ├── catalog_data.py / catalog_config.py
│   └── [altri 42 script]
├── data/
│   ├── catalog.games.v1.json (NON caricare intero, troppo grande)
│   ├── catalog.public.v1.json (filtrato da quality_gate)
│   ├── schema.json, sample.json
│   └── seo_overrides.json, hub_editorial.json
├── reports/            ← daily_audit_YYYY-MM-DD.json
├── .claude/ & .planning/ ← Documentazione e log
```
</details>

---

## 📍 FILE MAP & ENTRYPOINTS

| Percorso | Ruolo | Note Criticali |
|----------|-------|----------------|
| `scripts/catalog_data.py` | Loader JSON & sanitizzazione | Fonte unica di verità |
| `scripts/quality_gate.py` | Filtro curazione | `reviews == 0` → pending. Export audit in `reports/` |
| `scripts/build_static_pages.py` | Generatore HTML | Punto di iniezione SEO, JSON-LD, template |
| `scripts/seo_content_generator.py` | Thin content + JSON-LD | `generate_game_description()`, `generate_json_ld()` |
| `.github/workflows/update.yml` | Pipeline CI/CD | Smart bypass, trigger cron 6:00 UTC |
| `reports/daily_audit_*.json` | Tracciabilità | Delta giornaliero automatico |

---

## 📅 DECISION LOG

- `2026-04-03` — fix(qgate): `low_reviews:0` falso positivo (+198 giochi) → `53305fa7`
- `2026-04-03` — feat(CI): bypass `blocked_keyword` + audit export → `b8e54ef6`
- `2026-04-03` — docs: context sync CLAUDE.md → `c36163c0`
- `2026-04-03` — feat(seo): `seo_content_generator.py` — thin content 130-170w + JSON-LD centrale → `129311ac`

---

## 🎯 SEO & CTR (Convenzioni Applicate)

| Elemento | Regola | Formula/Formato |
|----------|--------|-----------------|
| `<title>` | `max 60 char` | `f"{game['title']} ({coop_str} · {game.get('players', '?')}P) | GiochiDiCoop"` + troncamento su `…` |
| `<meta description>` | `max 155 char` | Prima frase di `description` + `" Scopri modalità {coop_str} e alternative simili."` + troncamento su spazio |
| Thin content | 130-170 parole/pagina | `generate_game_description(game, lang)` — deterministico, seed md5 |
| `sitemap.xml` | Valida | 1162 URL totali (main + hubs + games-1/2). 100% HTTP 200. |
| `robots.txt` | Selettivo | Blocca AI training crawler (GPTBot, ClaudeBot, etc.), consente Googlebot/Bingbot. |
| Headings | Strutturati | Un solo `h1` per pagina. Gerarchia `h2`/`h3` rispettata. |

> ✅ **Verifica post-build**: Ogni pagina deve superare il [Rich Results Test](https://search.google.com/test/rich-results) per `VideoGame` mantenendo coerenza tra `<meta>`, `<title>` e JSON-LD.

---

## 💳 Monetizzazione & Affiliate

<details>
<summary>Tabella store e link nel codice</summary>

- **Instant Gaming**: `?igr=gamer-ddc4a8` → `AFFILIATE_IG` in `build_static_pages.py`
- **GameBillet**: `?affiliate=fb308ca0-...` → `AFFILIATE_GB`
- **Green Man Gaming / Gameseal / Kinguin / GAMIVO**: Config in `build_static_pages.py`
- I link usano `rel="sponsored"`. Appaiono solo se `steamUrl` esiste e il gioco non è free-to-play.
</details>

---

## 🤖 Collaborazione AI & Tooling

<details>
<summary>Setup AI e Plugin</summary>

- **GSD / Ralph / BMAD**: Plugin installati. Vedi `.planning/PLUGIN_GUIDE.md` e `scripts/ralph/`
- **Log sessioni**: Aggiornare SEMPRE `.claude/AI_COLLABORATION.md` dopo modifiche non banali.
</details>

---

## 🔮 Next Steps

- Cache Headers & Brotli precompression per performance
- Internal Linking Dinamico tra pagine correlate
- Audit GSC avanzato (CTR per query, pagine thin vs indicizzate)

---

## ✅ Checklist Pre-Commit

- [ ] Funziona ancora su GitHub Pages?
- [ ] Rispetta `safe_template()` e idempotenza?
- [ ] `title` ≤ 60 char e `description` ≤ 155 char?
- [ ] Zero f-string HTML dirette? Zero backend/npm?
- [ ] `.claude/AI_COLLABORATION.md` aggiornato?

> **Output atteso dopo ogni task**: Riassumi modifiche, elenca file toccati, segnala passaggi manuali, evidenzia impatti su deploy/SEO.
