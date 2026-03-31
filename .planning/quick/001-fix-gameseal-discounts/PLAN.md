# PLAN.md — Fix Gameseal Discounts

## Task
Fix Gameseal discounts showing 0% by comparing CJ price with Steam price instead of relying on salePrice field.

---

## Problema

Il script `fetch_gameseal_prices.py` cerca di calcolare lo sconto usando:
```python
if price > 0 and sale_price > 0 and sale_price < price:
    discount = round((price - sale_price) / price * 100)
```

Ma CJ API non ritorna `salePrice` per Gameseal, quindi `discount = 0` per tutti i giochi.

## Soluzione

Confrontare il prezzo CJ con il prezzo Steam del gioco per calcolare lo sconto:
- Recuperare `steamUrl` dal gioco
- Ottenere prezzo Steam (dalla struttura dati o da API)
- Calcolare: `discount = round((steam_price - cj_price) / steam_price * 100)`

---

## Azioni

1. Modificare `scripts/fetch_gameseal_prices.py`:
   - Per ogni gioco, leggere il prezzo Steam dalla struttura dati
   - Confrontare `cj_price` con `steam_price`
   - Calcolare sconto basato sulla differenza

2. Testare su 5 giochi sample:
   - Valheim, Stardew Valley, Terranova, etc.

3. Verificare che gli sconti siano ora calcolati correttamente

---

## Verifica

- [ ] Script modificato
- [ ] Test su 5 giochi
- [ ] Sconti calcolati correttamente (>0)
- [ ] Commit eseguito

---

## Done

Lo sconto Gameseal viene calcolato confrontando il prezzo CJ con il prezzo Steam invece che affidarsi al campo salePrice.