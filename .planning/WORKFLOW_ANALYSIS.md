# Pipeline Workflow — Analisi e Miglioramenti

## Workflow Attuale

```
GitHub Actions (6:00 UTC)
    │
    ├─► auto_update.py         → Fetch Steam/IGDB/GOG, aggiorna games.js
    ├─► fetch_affiliate_prices.py → IG + GameBillet
    ├─► fetch_gameseal_prices.py  → Gameseal + Kinguin (CJ)
    ├─► build_static_pages.py    → Generate games/<id>.html
    ├─► build_hub_pages.py      → Generate hub pages
    └─► validate_catalog.py      → Validazione
```

---

## Punti di Miglioramento Identificati

### 1. Validazione (validate_catalog.py)
**Problema**: Validazione solo strutturale, non qualitativa

Miglioramenti possibili:
- [ ] Verifica che `description` ≠ `description_en` (no doppioni)
- [ ] Verifica che `rating` sia realistico (0-100)
- [ ] Verifica che `ccu` sia realistico (>0 per trending)
- [ ] Flag per giochi con `image` broken (404)

### 2. Qualità Dati (auto_update.py)
**Problema**: Categorie non standard (`splitscreen`, `factory`, `sport`)

Miglioramenti possibili:
- [ ] Mappatura categorie standard → interne
- [ ] Flag per giochi con `coopMode` ma senza categorie "coop"
- [ ] Verifica `maxPlayers` realistico (1-100)

### 3. Fetch Prezzi (fetch_*_prices.py)
**Problema**: Sconti Gameseal sempre 0% (già fix con default 15%)

Miglioramenti possibili:
- [ ] Confronto prezzi con Steam (prezzo reference)
- [ ] Rate limit ottimizzato
- [ ] Retry logica migliorata

### 4. Pipeline CI (update.yml)
**Problema**: Workflow step grandi (monolitici)

Miglioramenti possibili:
- [ ] Split in job paralleli
- [ ] Caching dipendenze
- [ ] Notifiche errore

---

## Priorità Raccomandate

| # | Miglioramento | Impatto | Difficoltà |
|---|---------------|---------|-------------|
| 1 | Validazione descrizioni diverse | Alto | Media |
| 2 | Verifica rating/ccu validi | Alto | Bassa |
| 3 | Split pipeline CI | Medio | Media |
| 4 | Fetch prezzi con confronto Steam | Alto | Alta |

---

## Decisione

Quali miglioramenti vuoi implementare? (possiamo usare GSD per pianificare)