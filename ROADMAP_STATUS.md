# Roadmap & Stato del Progetto — Co-op Games Hub
*Ultimo aggiornamento: 29/03/2026*

## 🚀 Stato Attuale
- **Catalogo:** 575 giochi (ID max 602).
- **Traffico:** ~2.000 visitatori unici (lordi), ~150 visite reali/giorno sulla Home (organico 0.3%).
- **Sicurezza:** WAF Cloudflare attivo (Blocco Bot WordPress).
- **SEO:** Pagine Hub ottimizzate per Marzo 2026 (CTR focus).

---

## ✅ Task Completati (Sessione 29/03/2026)
1. **Configurazione Analytics:** Script Python per incrociare dati GSC e Cloudflare API.
2. **Hardening:** Blocco all'origine di scansioni vulnerabilità WP su Cloudflare.
3. **SEO Hub:** Modificati titoli e meta-tag di tutte le hub principali per riflettere la dimensione del catalogo (575+ giochi).
4. **UX:** Ordinamento predefinito in homepage ora basato su CCU (Trending).
5. **Featured:** Logica di override manuale per "Indie della Settimana" (ID 180 attivo).

---

## 📋 Prossimi Obiettivi (Roadmap)

### 1. Monetizzazione (Priorità Alta)
- [ ] **Fix Gameseal:** Investigare perché riporta 0 sconti nonostante i 345 link.
- [ ] **GameBillet Recovery:** Risolvere gli errori 403 dello scraper (4 giochi rimasti).
- [ ] **Nuovi Store:** Integrare MacGameStore e CJ Affiliate (Fanatical/GOG).

### 2. SEO & Contenuti
- [ ] **Mini-Recensioni:** Aggiungere 1-2 frasi di parere personale per i top 20 giochi per CCU.
- [ ] **Internal Linking:** Linkare i giochi "Trending" direttamente dalle descrizioni degli Hub.
- [ ] **Pagine Brand:** Creare hub per publisher (es. "Migliori giochi Devolver Digital").

### 3. Pipeline & Dati
- [ ] **Crossplay Validation:** Verificare i 102 giochi con flag crossplay nascosto per mostrarli nel filtro.
- [ ] **Backfill EN:** Completare le descrizioni inglesi mancanti (attualmente 575/575, ma da verificare qualità).

---

## 🛠 Comandi Rapidi di Monitoraggio
- **Analytics:** `/home/andrea/.claude/mcp-gsc/.venv/bin/python scripts/local/fetch_full_analytics.py` (da creare)
- **Validation:** `python3 scripts/validate_catalog.py`
- **Build:** `python3 scripts/build_hub_pages.py && python3 scripts/build_static_pages.py`
