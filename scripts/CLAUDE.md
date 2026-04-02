# scripts/ — Contesto AI

Sei nella cartella degli script Python della pipeline dati di coophubs.net.

## Leggi prima di tutto

→ **[INDEX.md](INDEX.md)** — mappa completa dei 45 script: dominio, input, output, dipendenze, ordine CI

## Regole critiche per questa cartella

- Gli script usano **bare imports** (`import catalog_data`, `from quality_gate import ...`).
  Non spostare mai file in sottocartelle — romperebbe tutti gli import.
- `assets/games.js` (~94K token) è il database principale. Non passarlo intero ad Aider.
  Usa `catalog_data.py` per leggerlo/scriverlo programmaticamente.
- Ogni modifica alla pipeline va testata con:
  ```bash
  python3 scripts/validate_catalog.py
  ```
- Non modificare `.github/workflows/` senza approvazione esplicita.

## Entry point per tipo di task

| Task | File da leggere |
|------|----------------|
| Capire la pipeline CI | `INDEX.md` sezione Livello 1 |
| Aggiungere nuovi giochi | `catalog_ingest.py`, `quality_gate.py`, `catalog_config.py` |
| Modificare build pagine statiche | `build_static_pages.py`, `build_hub_pages.py` |
| Modificare fonti dati | `steam_catalog_source.py` / `igdb_catalog_source.py` / ecc. |
| Capire la struttura dati | `catalog_data.py` (I/O), `catalog_config.py` (costanti) |
| Prezzi affiliate | `fetch_affiliate_prices.py`, `fetch_gameseal_prices.py` |
