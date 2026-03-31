# PLAN.md — Fix Affiliate GameBillet

## Problema
GameBillet ha solo 4 link su 589 giochi. La pipeline fetch_affiliate_prices.py non riesce a recuperare i link (403 Forbidden).

## Analisi
1. GameBillet NON è su CJ Affiliate
2. Ha un programma affiliazione diretto (earn-with-us)
3. Il sito blocca le richieste HTTP (403)
4. Servirebbe un account diretto con link personalizzato

## Opzioni

### Opzione A: Usa parametro ref fisso
In ogni link GameBillet aggiungere `?affiliate=fb308ca0-...` - ma i 4 link attuali già ce l'hanno e non funzionano

### Opzione B: Verifica account GameBillet
Controllare se hai un account GameBillet attivo con link ref funzionanti

### Opzione C: Rimuovi GB dalla pipeline
Tolgo GB dalla pipeline e lascio solo i link manuali esistenti

## Decisione
[Da definire con l'utente]

## Azioni
- [ ] Verificare se i 4 link GB esistenti funzionano
- [ ] Decidere se tenere GB o rimuoverlo dalla pipeline