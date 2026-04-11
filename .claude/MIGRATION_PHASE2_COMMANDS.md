# Comandi migrazione — Fase 2 e 3

Esegui questi comandi SOLO dopo aver letto il piano e capito cosa fa ciascun blocco.
Ogni blocco è indipendente e reversibile via git.

---

## FASE 2 — Root cleanup

### 2a. Crea cartella .dev/ per file non-codice

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
mkdir -p .dev/screenshots
mkdir -p .dev/design
```

### 2b. Sposta screenshots PNG dalla root

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
mv screenshot-fixed.png  .dev/screenshots/
mv screenshot-home.png   .dev/screenshots/
mv screenshot-modal.png  .dev/screenshots/
mv screenshot-static.png .dev/screenshots/
# se esiste screenshot-mobile.png:
[ -f screenshot-mobile.png ] && mv screenshot-mobile.png .dev/screenshots/
```

### 2c. Sposta file design / zip

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
[ -d stitch_design ] && mv stitch_design .dev/design/
[ -f stitch_co_op_hubs_homepage_modernizzata.zip ] && mv stitch_co_op_hubs_homepage_modernizzata.zip .dev/design/
```

### 2d. Rimuovi backup .js dalla cartella assets/

> Prima verifica che siano già in git (lo sono — sono stati creati il 01/04):

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
ls -la assets/games.js.backup.*
# Se ti fidi del git history, rimuovi:
rm assets/games.js.backup.20260401_154414
rm assets/games.js.backup.20260401_154427
rm assets/games.js.backup.20260401_161618
```

### 2e. Sposta file di stato duplicati in .planning/

Questi file esistono sia nella root che in `.planning/`:

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
# Confronta prima di rimuovere dalla root:
diff project_roadmap_state.md .planning/STATE.md
diff ROADMAP_STATUS.md .planning/ROADMAP.md

# Se i contenuti .planning/ sono più aggiornati, rimuovi dalla root:
rm project_roadmap_state.md
rm ROADMAP_STATUS.md
```

> ⚠️ ATTENZIONE: confronta il diff prima di rimuovere. Se la root ha info più recenti,
> copia il contenuto in .planning/ e poi rimuovi.

### 2f. Aggiungi .dev/ a .gitignore

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
echo "" >> .gitignore
echo "# Dev artifacts (screenshots, design files)" >> .gitignore
echo ".dev/" >> .gitignore
```

---

## FASE 3 — data/ — SOLO documentazione, NO file move

### Decisione finale: NON spostare i file JSON in sottocartelle

Dopo analisi delle dipendenze, spostare i file in `data/sources/`, `data/pipeline/`, ecc.
richiederebbe aggiornare path in questi file:

| File | Righe da aggiornare |
|------|-------------------|
| `scripts/catalog_data.py` | `DATA_DIR` (riga 23) |
| `scripts/catalog_ingest.py` | `APPROVED_PATH`, `REJECTED_PATH`, `REVIEW_PATH` (righe 51-53) |
| `scripts/build_static_pages.py` | `ROOT / "data" / "seo_overrides.json"` (riga 33) |
| `scripts/build_hub_pages.py` | `ROOT / "data" / "hub_editorial.json"` (riga 34) |
| `scripts/igdb_scraper.py` | `"data/igdb_coop_games.json"` (riga 88) |
| `scripts/rawg_scraper.py` | `"data/rawg_coop_games.json"` (riga 98) |
| `scripts/gog_scraper.py` | `"data/gog_coop_games.json"` (riga 128) |
| `scripts/cross_reference.py` | `"data/steam_coop_games.json"` e altri (righe 49-195) |
| `scripts/multi_cross_reference.py` | 5+ path hardcoded (righe 29-180) |
| `.github/workflows/update.yml` | `git add data/catalog.games.v1.json data/catalog.public.v1.json` (riga 74) |

**Beneficio**: struttura più pulita visivamente.
**Costo**: 10+ file da aggiornare, rischio CI, nessun miglioramento funzionale.

**Conclusione**: il file `data/README.md` già creato dà lo stesso beneficio (navigabilità AI)
senza toccare niente. Fase 3 chiusa con documentazione.

---

## Verifica post-cleanup

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"

# Controlla che nessun file di codice sia stato spostato
git status

# Verifica che la pipeline Python giri ancora (dry-run)
cd scripts && python3 -c "import catalog_data; import catalog_config; import quality_gate; print('OK')"

# Verifica sitemap e pagine ancora presenti
ls games/*.html | wc -l     # deve essere 589+
ls sitemap*.xml              # deve listare 4-5 file

# Torna alla root
cd ..
```

---

## Rollback completo

```bash
cd "/home/andrea/Progetto sito/giochidicoopia"
git checkout -- .              # ripristina tutti i file tracciati
git clean -fd .dev/            # rimuove .dev/ se non tracciato
```
