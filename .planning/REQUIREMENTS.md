# REQUIREMENTS.md — Co-op Games Hub

## Requisiti v1 (Q1 2026)

### 1. Fix Cache Cloudflare

**Problema**: Cache hit rate 6.9% invece di 90%+

**Soluzione**: 
- Configurare Cloudflare Cache Rule con Edge TTL 7 giorni
- Verificare `_headers` esistente
- Testare dopo 24-48h

**Criteri di successo**: Cache hit rate > 90%

---

### 2. Fix Gameseal Sconti

**Problema**: Sconti Gameseal mostrano 0% in molti casi

**Soluzione**:
- Investigare API/endpoint Gameseal
- Fixare logica calcolo sconto
- Testare su sample di giochi

**Criteri di successo**: Sconti corretti per >90% dei giochi con offerta Gameseal

---

### 3. SEO - Ottimizzazione Snippet

**Problema**: Query con pos 6-8 ma 0 clic

**Soluzione**:
- Analizzare query senza clic in GSC
- Migliorare title/meta description
- Aggiungere structured data dove mancante

**Criteri di successo**: Almeno 50 click GSC/mese

---

## Requisiti v2 (Q2 2026)

### 4. Monetizzazione - Nuovi Partner

**Problema**: MacGameStore e Fanatical non integrati

**Soluzione**:
- Ottenere link affiliati da MacGameStore
- Richiedere accesso Fanatical
- Integrare in `app.js` e `build_static_pages.py`

**Criteri di successo**: 5+ store disponibili per comparazione prezzi

---

### 5. Contenuti Editoriali

**Problema**: Solo 1/5 hub pages con contenuto editoriale completo

**Soluzione**:
- Espandere `data/hub_editorial.json` per tutte le 5 hub pages
- Aggiungere intro SEO-friendly
- Aggiungere call-to-action affiliate

**Criteri di successo**: Tutte le 5 hub pages con contenuto completo

---

### 6. Backlink Building

**Problema**: 0 backlink, domain authority bassa

**Soluzione**:
- Submit a directory italiane (gamingtalk.it, multiplayer.it)
- Guest post su siti gaming italiani
- Creare contenuti linkable ("migliori giochi coop 2026")

**Criteri di successo**: 10+ backlink da domini pertinenti

---

## Requisiti v3 (Q3 2026)

### 7. Mini-Recensioni

**Problema**: Nessuna recensione per i giochi

**Soluzione**:
- Aggiungere campo `review` ai dati gioco
- Creare mini-recensioni per i 20 giochi trending
- Mostrare nella pagina gioco e nel modal

**Criteri di successo**: 20+ giochi con recensione

---

### 8. Nuove Categorie

**Problema**: Catalogo limitato a categorie esistenti

**Soluzione**:
- Aggiungere categorie: "Party Games", "RPG Coop", "Survival Coop"
- Espandere catalogo con nuovi giochi
- Aggiornare filtri

**Criteri di successo**: 5+ nuove categorie, 100+ nuovi giochi

---

## Out of Scope

- Backend/sistema utenti
- Sistema commenti
- Newsletter
- App mobile
- Analytics avanzati
