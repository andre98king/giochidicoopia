# Stato Progetto & Roadmap SEO — 30/03/2026

## 📊 Situazione Attuale
- **Catalogo**: 582 giochi censiti (ID max 602).
- **Stato SEO**: 
    - **Titoli**: Aggiornati su tutte le 582 pagine gioco e 5 hub pages (IT/EN) per includere keyword "co-op PC".
    - **Meta Description**: Ottimizzate (max 160 char) con dati dinamici su player count e rating.
    - **Indicizzazione**: Sitemap (1182 URL) reinviata con successo via API GSC il 30/03. Stato: **In attesa di elaborazione**. ✅

## ✅ Task Completati (Sessione 30/03)
1. **Fix Titoli SEO**: Modificato `build_static_pages.py` e `build_hub_pages.py` per formati titoli più aggressivi (es. "gioco coop PC").
2. **Indexing API**: Creato script `scripts/local/resubmit_sitemap.py` per notifica immediata a Google tramite API Search Console.
3. **Analisi Traffico**: Estratti dati via API: 6 click/mese (GSC) e 13.6k PageViews (CF). Cache Hit Rate critico al **6.9%**.
4. **SEO Override System**: Implementato `data/seo_overrides.json` per meta description manuali.
5. **Hub Editorial Content**: Creato `data/hub_editorial.json` e aggiornato `build_hub_pages.py` per iniettare guide editoriali (500+ parole) nelle hub pages (IT/EN).
6. **Top CTR Optimization**: Ottimizzati snippet SEO per *Project Zomboid*, *PAYDAY 3* e *Moving Out 2*.

## 📋 Prossimi Obiettivi

### 1. Monitoraggio & Performance (Settimana 14)
- **Cache Hit Rate Fix**: Accedere alla dashboard Cloudflare e creare una Cache Rule per forzare il caching di tutto il sito (Edge TTL: 7 giorni).
- Espandere `data/hub_editorial.json` per le altre 4 hub pages (Locale, 2 Giocatori, Free, Indie).
- Monitorare se l'autorità semantica delle nuove Hub Pages spinge il sito in Top 10 per "giochi coop 2026".

### 2. Monetizzazione & Affiliazione
- **Gameseal Fix**: Risolvere il problema degli sconti (attualmente segnano 0% in molti casi).
- **Espansione Store**: Integrare dati da nuovi partner (MacGameStore, Fanatical).

### 3. Contenuti Editoriali
- Aggiungere intro editoriali più profonde (400-600 parole) nelle hub pages per aumentare il tempo di permanenza e l'autorità semantica.
- Aggiungere mini-recensioni manuali per i primi 20 giochi trending.

## 🛠 Comandi Utili
- **Build Totale**: `python3 scripts/build_hub_pages.py && python3 scripts/build_static_pages.py`
- **Re-indexing**: `python3 scripts/local/resubmit_sitemap.py`
