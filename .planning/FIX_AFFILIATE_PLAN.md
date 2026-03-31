# Piano Miglioramenti — Co-op Games Hub

## Contesto
Il sito ha 589 giochi cooperativi. L'audit ha rivisto problemi nella pipeline e negli affiliate.

## Situazione Attuale

### Affiliate Links
| Partner | Link Attivi | Problema |
|---------|-------------|----------|
| Instant Gaming | 270/589 | ✅ Funziona |
| GameBillet | 4/589 | ❌ Pipeline rotta |
| Gameseal | 345/589 | ✅ Funziona (sconto 15%) |
| Kinguin | 368/589 | ✅ Funziona |
| GAMIVO | 0/589 | ❌ Mai implementato |
| Green Man Gaming | 26 (no affiliate) | ⚠️ Link GOG senza affiliazione |

### Qualità Dati
- Nessun campo YouTube (per validare giochi nuovi)
- GameBillet pipeline broken
- GAMIVO non implementato

---

## Priorità

### P0 - URGENTE (Revenue)
1. **Fix GameBillet** — Solo 4 link su 589 = perdita revenue immediata
2. **Implementa GAMIVO** — 0 link = potenziale revenue non sfruttato

### P1 - Importante (Qualità)
3. **Aggiungi YouTube data** — Per validare giochi nuovi/appena usciti
4. **Verifica Green Man Gaming** — 26 link ma senza affiliazione

### P2 - Miglioramento Continuo
5. **Migliora categorizzazione** — Usa IGDB per dati più accurati
6. **Aggiungi release year ai giochi** — Per filtrare nuovi vs vecchi

---

## Azioni

### P0: GameBillet + GAMIVO
- [ ] Investigare perché fetch_affiliate_prices.py non aggiorna GB
- [ ] Fixare logica GAMIVO (CJ link wrap)
- [ ] Testare su sample di giochi

### P1: YouTube
- [ ] Ottenere YouTube API Key
- [ ] Testare fetch_youtube_videos.py
- [ ] Integrare nel workflow

### P1: Green Man Gaming
- [ ] Verificare se link GMG hanno affiliazione
- [ ] Se no, richiedere link affiliate

---

## Piano di Implementazione

1. **Prima**: Fix GameBillet (1-2 ore)
2. **Secondo**: Implementa GAMIVO (1-2 ore)
3. **Terzo**: YouTube API setup (dipende da API key)
4. **Quarto**: Verifica GMG affiliate

---

## Output Atteso

- GameBillet: 200+ link funzionanti
- GAMIVO: 200+ link funzionanti
- YouTube: campo youtubeVideos per ogni gioco
- GMG: link affiliate funzionanti