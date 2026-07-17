# AI Collaboration Log

Registro delle modifiche non banali apportate da agenti AI al progetto.

---

## 2026-04-02

### Co-op Classifier AI - Training & Development (Claude Code + Ollama)

**Obiettivo**: Classificare giochi come YES (co-op friendly), NO (PvP), MIXED (both)

**Pipeline creata**:
- `training/coop-classifier/modelfile` - Prompt engineering per llama3.1:8b con 40+ few-shot examples
- `training/coop-classifier/dataset_quality.json` - 147 entries con classificazioni accurate
- `training/coop-classifier/dataset_embeddings.npy` - Embeddings precomputati (all-MiniLM-L6-v2)
- `training/coop-classifier/semantic_rag_classifier.py` - Classificatore con retrieval semantico

**Risultati test**:
- Accuratezza problemi difficili: 100% (20/20 giochi problematici testati)
- Batch test 60 giochi: 78% YES, 20% NO, 2% MIXED
- Categorie gestite: sandbox (Minecraft, Terraria), survival (ARK, Rust), farming sim (Factorio), MMO (Genshin), party games

**Note**: Classifier locale in `training/coop-classifier/` - non committato, solo per uso interno/testing.

---

## 2026-04-01

### Phase 1: Schema Foundation & CI Hardening (Claude Code)
- `catalog_data.py`: esteso `ef()` per gestire `null` JS; `load_games()` legge `coopScore`, `mini_review_it/en`; `write_legacy_games_js()` li scrive
- `assets/games.js`: aggiunto `coopScore: null` a tutti i 589 giochi; preservate 17 mini-recensioni esistenti
- `data/catalog.games.v1.json`, `data/catalog.public.v1.json`: rigenerati con `coopScore`
- `.github/workflows/update.yml`: rimosso `continue-on-error: true` dai build step

### Phase 1-02: coopMode Vocabulary Canonicalization (Claude Code)
- `split` → `sofa` rinominato in tutti gli 8 script Python + `app.js` + 210 giochi in `games.js`
- `validate_catalog.py`: aggiunto `CANONICAL_COOP_MODES = {"online", "local", "sofa"}` con hard-error

### Quality Gate: aggiunta validazione IGDB + GOG (Claude Code)
- `quality_gate.py`: aggiunto `fetch_igdb_coop()` (Steam app ID → IGDB game_modes=3 via Twitch OAuth2)
- `quality_gate.py`: aggiunto `fetch_gog_coop()` (ricerca per titolo su `catalog.gog.com/v1/catalog`, controlla `features[]` per "co-op")
- `validate()` ora accetta `igdb_client_id` e `igdb_client_secret`; restituisce `igdb_confirmed` e `gog_confirmed`
- Logica confidence aggiornata: IGDB=False → `needs_review`; più conferme esterne → `high`
- `catalog_ingest.py`: legge `IGDB_CLIENT_ID`/`IGDB_CLIENT_SECRET` da `.env` e li passa a `validate()`
- Sorgenti attive: Steam (primario) + IGDB (secondario) + GOG (terziario) + RAWG (quaternario)

### Aggiunta 9 nuovi giochi (Claude Code)
- Aggiunti ID 618-628 (esclusi CS2 e Wuthering Waves — non adatti al catalogo co-op)
- Giochi aggiunti: Drunkslop, Maid Cafe Coop, Color Escape VR, Fifth Sun, Get Together, Cat Parents, NAKWON, Subnautica 2, Wurst Defender
- Pagine statiche e JSON export rigenerati (599 giochi totali)
- Nota: descrizioni e immagini saranno popolate dal CI settimanale (auto_update.py)
