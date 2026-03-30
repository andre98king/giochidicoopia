# Guida Autenticazione Google Search Console (GSC)

Questo documento spiega come utilizzare le API di Google Search Console per Coophubs senza dover rieseguire l'autenticazione manuale nel browser.

## 🛠 Snippet Python per Accesso Diretto

Usa questo codice per inizializzare il servizio GSC utilizzando il token esistente (che include il `refresh_token`).

```python
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Percorsi standard sul sistema
GSC_DIR = "/home/andrea/.claude/mcp-gsc/"
TOKEN_FILE = os.path.join(GSC_DIR, "token.json")

def get_gsc_service():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Token non trovato in {TOKEN_FILE}")
    
    with open(TOKEN_FILE, 'r') as token:
        creds_data = json.load(token)
    
    creds = Credentials.from_authorized_user_info(creds_data)
    
    # Gestione automatica della scadenza del token
    if creds.expired and creds.refresh_token:
        print("Token scaduto, tentativo di refresh in corso...")
        creds.refresh(Request())
        # Opzionale: salva il nuovo token aggiornato
        with open(TOKEN_FILE, 'w') as token_file:
            token_file.write(creds.to_json())
            
    return build("searchconsole", "v1", credentials=creds)

# Esempio uso:
# service = get_gsc_service()
# sites = service.sites().list().execute()
```

## 🔑 Dettagli Tecnici Credenziali

- **Percorso Token**: `/home/andrea/.claude/mcp-gsc/token.json`
- **Percorso Client Secrets**: `/home/andrea/.claude/mcp-gsc/client_secrets.json`
- **Tipo Client**: `installed` (Desktop). 
  - **Perché non Web?** Le applicazioni Web richiedono un URL di redirect pubblico e la gestione di sessioni server. Il client "Desktop/Installed" è ideale per script locali e tool CLI (come questo) perché permette il redirect su `http://localhost` durante la prima autenticazione e supporta il `refresh_token` a lungo termine senza configurazioni server complesse.
- **Refresh Token**: Il token attuale è configurato con accesso offline (`access_type='offline'`), il che garantisce un `refresh_token` permanente. Finché l'utente non revoca l'accesso nelle impostazioni dell'account Google, lo script potrà rigenerare nuovi `access_token` autonomamente.

## ⚠️ Cosa fare se il token fallisce
Se ricevi un errore di tipo `401 Unauthorized` persistente o `Token expired`, lo script `get_gsc_service()` sopra proverà a fare il refresh. Se anche quello fallisce (raro), è necessario eseguire nuovamente il flow di autenticazione tramite il server MCP o un tool interattivo che possa aprire il browser.
