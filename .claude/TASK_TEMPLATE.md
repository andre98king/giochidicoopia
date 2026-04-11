# Task Template — CoopHubs.net

Copia e compila questo template prima di iniziare qualsiasi task con un AI.
Obbliga a definire confini chiari e riduce il rischio di modifiche indesiderate.

---

## Template

```
## TASK: [titolo breve]

### Target
[Descrizione precisa di cosa deve cambiare e perché]

### File da toccare
- [ ] assets/app.js
- [ ] assets/style.css
- [ ] assets/i18n.js
- [ ] assets/games.js           ← ATTENZIONE: 94K token, non passare intero ad aider
- [ ] scripts/[nome].py
- [ ] index.html
- [ ] [altro]

### NON TOCCARE
- [ ] .github/workflows/        ← richiedono approvazione esplicita
- [ ] assets/games.js           ← se non strettamente necessario
- [ ] games/*.html              ← sono auto-generate da build_static_pages.py
- [ ] sitemap*.xml              ← auto-generati, non editare manualmente
- [ ] [altro]

### Dipendenze da leggere prima
- [ ] CLAUDE.md                 ← regole progetto
- [ ] scripts/INDEX.md          ← se tocchi script Python
- [ ] data/README.md            ← se tocchi file in data/
- [ ] AI_COLLABORATION.md       ← log modifiche precedenti

### Output atteso
[Descrizione del comportamento dopo la modifica]

### Verifica pre-commit
- [ ] Apri http://localhost:8080 (python3 -m http.server 8080) e testa manualmente
- [ ] Se modifichi scripts: python3 scripts/validate_catalog.py
- [ ] Se modifichi HTML/CSS: screenshot desktop 1440px + mobile 390px
- [ ] Se modifichi build_static_pages.py: python3 scripts/build_static_pages.py + controlla games/1.html

### Rischi identificati
[Cosa potrebbe rompersi? SEO? Affiliate links? CI pipeline?]
```

---

## Esempi d'uso

### Task: Fix bug filtro anno

```
## TASK: Fix filtro anno non resetta quando si cambia categoria

### Target
In app.js, quando l'utente seleziona una nuova categoria dal menu,
il filtro anno rimane attivo. Deve tornare a "Tutti gli anni".

### File da toccare
- [x] assets/app.js

### NON TOCCARE
- [x] assets/games.js (non serve)
- [x] assets/style.css (non serve)
- [x] scripts/ (nessuno script)

### Dipendenze da leggere prima
- [x] CLAUDE.md

### Output atteso
Selezione categoria → filtro anno si resetta visivamente e funzionalmente.

### Verifica pre-commit
- [x] Test manuale su http://localhost:8080
- [x] Screenshot mobile (filtri visibili)

### Rischi identificati
- Possibile effetto collaterale su filtro maxPlayers (stessa logica reset)
```

---

## Regole per AI che usano questo template

1. **Leggi sempre** le dipendenze elencate prima di generare codice
2. **Non modificare** i file in "NON TOCCARE" senza domandare
3. **Non creare** file nuovi non listati in "File da toccare" senza proposta esplicita
4. **Non fare commit o push** — proponi le modifiche, aspetta conferma
5. Se `assets/games.js` è necessario, **usa solo la parte rilevante** (cerca per ID o campo specifico)
6. Dopo ogni modifica, **aggiorna `AI_COLLABORATION.md`** con data e descrizione
