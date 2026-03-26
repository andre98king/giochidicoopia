# Handoff: Setup GPU locale RX 9070 XT per LLM inference

**Data**: 2026-03-26 | **Stato**: funzionante, ottimizzazione opzionale disponibile

---

## Stato attuale — FUNZIONANTE

### Setup in produzione
- **Binary**: `/usr/local/bin/llama-server` (llama.cpp build 8537, Vulkan backend)
- **Modello principale**: `/home/andrea/models/mistralai_Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf` (14.3GB, bartowski/HF)
- **Modello alternativo**: `/usr/share/ollama/.ollama/models/blobs/sha256-ac9b...` (qwen2.5-coder:14b, compatibile)
- **API endpoint**: `http://127.0.0.1:8080/v1/chat/completions` (OpenAI-compatible)
- **Systemd service**: `/etc/systemd/system/llama-server.service` (template in `/tmp/llama-server.service`)

### Avvio manuale
```bash
GGML_VK_VISIBLE_DEVICES=0 llama-server \
  -m /home/andrea/models/mistralai_Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf \
  -ngl 99 --host 127.0.0.1 --port 8080 \
  --ctx-size 4096 --n-predict 200 --threads 8 --parallel 2
```

### Benchmark misurati (2026-03-26)
| Modello | Tok/s | VRAM | Note |
|---------|-------|------|------|
| mistral-small 24B Q4_K_M | ~32 tok/s | 14.6GB/16GB | qualità ottima per testo IT/EN |
| qwen2.5-coder 14B | ~53 tok/s | 9.5GB/16GB | più veloce, peggiore per prosa |

---

## Perché Vulkan e non ROCm

**Problema ROCm 6.4.0 su gfx1201 (RDNA 4)**:
- Bug #5706: GPU resta a 0% utilizzo, tutto gira su CPU (~10-15 tok/s)
- Bug #4868: ROCm 6.4 è 10x più lento di ROCm 6.3
- Instabilità WiFi MT7922 dopo stress GPU con ROCm

**Soluzione applicata**: llama.cpp compilato con Vulkan backend (Mesa RADV, già supporta gfx1201)

**Fix WiFi permanente applicato**:
- GRUB: `pcie_port_pm=off pcie_aspm=off` in `/etc/default/grub`
- Systemd: `/etc/systemd/system/wifi-mt7922-fix.service`

---

## 🧪 Ricercafork Ottimizzati (2026-03-26)

### Analisi Comparativa

| Fork | tok/s | Backend | Problema |
|------|-------|---------|----------|
| [tlee933/llama.cpp-rdna4-gfx1201](https://github.com/tlee933/llama.cpp-rdna4-gfx1201) | ~99 | ROCm 7.11 HIP | Bug #5706 GPU idle 100% |
| [lemonade-sdk/llamacpp-rocm](https://github.com/lemonade-sdk/llamacpp-rocm) | ~99+ | ROCm 7.10 HIP | Stesso bug #5706 |

### Nostro Setup Attuale

| Feature | Valore |
|---------|--------|
| Backend | Vulkan (Mesa RADV) |
| tok/s | ~32 |
| Stabilità | ✅ Nessun bug |
| Facilità | ✅ Facile |

### Perché i Fork NON funzionano per noi

1. **Usano ROCm/HIP** — noi usiamo Vulkan
2. **Bug #5706** — GPU resta al 100% dopo idle, non usabile
3. **ROCm 7.11 instabile** — non disponibile come pacchetto Ubuntu

### Verdetto Finale

> Per il nostro caso d'uso (generare descrizioni con mistral-small), **Vulkan + llama-server è la soluzione migliore**.
> 
> I fork ottimizzati sono per chi ha bisogno di >60 tok/s e può permettersi di configurare ROCm 7.2+ stabile (non ancora disponibile).

---

## PROSSIMO TASK OPZIONALE: provare fork ottimizzato per gfx1201

### Opzione A: lemonade-sdk/llamacpp-rocm (CONSIGLIATA, ~45 min)
Repository con binary precompilati per gfx1201, ROCm 7.10, nightly builds.
```bash
# Verificare se hanno binary per Ubuntu 24.04 (Noble)
# https://github.com/lemonade-sdk/llamacpp-rocm
```
- Pro: facile, mantenuto attivamente
- Con: richiede ROCm 7.10 installato

### Opzione B: tlee933/llama.cpp-rdna4-gfx1201 (~2-3 ore)
Fork con ottimizzazioni HIP specifiche per gfx1201. Riporta ~99 tok/s.
```bash
git clone https://github.com/tlee933/llama.cpp-rdna4-gfx1201
# Richiede ROCm 7.11 installato (non disponibile come pacchetto Ubuntu Noble 24.04)
```
- Pro: ~99 tok/s (3x miglioramento)
- Con: richiede ROCm 7.11 da source, più complesso

### Benchmarking dopo il cambio
Usare questo comando per confronto apples-to-apples:
```bash
start=$(date +%s%3N)
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"test","messages":[{"role":"user","content":"Scrivi 2-3 frasi su Overcooked 2, co-op per 1-4 giocatori. Rispondi SOLO con la descrizione."}],"max_tokens":150,"temperature":0.7,"stream":false}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); u=d.get('usage',{}); toks=u.get('completion_tokens',0); print(f'gen={toks} tok/s={toks/($(date +%s%3N)-$start)*1000:.1f}')"
```

---

## Script generazione descrizioni

**Path**: `scripts/generate_descriptions_ollama.py`
**Uso**: `python3 scripts/generate_descriptions_ollama.py`
**Configurazione**:
- `MIN_DESC_LEN = 300` — soglia per considerare una descrizione "thin"
- `OLLAMA_URL = "http://localhost:8080/v1/chat/completions"`
- `OLLAMA_MODEL = "mistral-small-3.1-24b"`

**Stato descrizioni**:
- Giochi totali: 551
- Non-Steam thin (<300c): 147 → 86 aggiornati nell'ultima run (59%)
- 61 "non migliorava" = avevano già desc più lunga del generato

---

## Hardware
- GPU: AMD RX 9070 XT (RDNA 4, gfx1201, 16GB GDDR6)
- RAM: 16GB
- OS: Ubuntu 24.04 (Noble)
- llama.cpp build: 8537 (dc8d14c58), Vulkan
- Driver GPU: Mesa RADV (open-source, già supporta gfx1201)

---

## 📋 Note per Prossima AI

> **NON tentare di fixare il bug #5706** — è un problema di basso livello nel runtime ROCm. La soluzione pragmatica è:
> 1. Usare Vulkan + llama-server (funziona)
> 2. Attendere ROCm 7.2+ stabile
> 3. Testare allora i fork ottimizzati
>
> La configurazione attuale con ~32 tok/s è **più che sufficiente** per generare descrizioni (147 giochi in ~5 minuti).

---

## 🔮 Quando ROCm 7.2+ sarà stabile

1. **Monitorare**: [ROCm Release Notes](https://rocm.docs.amd.com/), [GitHub ROCm Issues #5706](https://github.com/ROCm/ROCm/issues/5706), [llama.cpp RDNA4](https://github.com/ggerganov/llama.cpp/discussions/10879)
2. **Testare**: Benchmarkare con mistral-small e confrontare
3. **Migrare**: Da Vulkan a ROCm solo se:
   - Bug #5706 risolto
   - tok/s > 60
   - Stabilità verificata