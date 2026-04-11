#!/usr/bin/env python3
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Percorsi ai file di credenziali (usando quelli di Claude MCP)
GSC_DIR = "/home/andrea/.claude/mcp-gsc/"
TOKEN_FILE = os.path.join(GSC_DIR, "token.json")
SITE_URL = "sc-domain:coophubs.net"
SITEMAP_URL = "https://coophubs.net/sitemap.xml"

def get_gsc_service():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Token non trovato in {TOKEN_FILE}")
    
    with open(TOKEN_FILE, 'r') as token:
        creds_data = json.load(token)
    
    creds = Credentials.from_authorized_user_info(creds_data)
    return build("searchconsole", "v1", credentials=creds)

def resubmit_sitemap():
    service = get_gsc_service()
    try:
        service.sitemaps().submit(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        print(f"✅ Sitemap inviata con successo: {SITEMAP_URL}")
        
        # Verifica stato
        details = service.sitemaps().get(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        print(f"Stato: {details.get('isPending', True) and 'In attesa' or 'Elaborata'}")
        if 'contents' in details:
            for content in details['contents']:
                print(f"- {content.get('type')}: {content.get('submitted')} inviati, {content.get('indexed')} indicizzati")
                
    except HttpError as e:
        print(f"❌ Errore nell'invio della sitemap: {e.content.decode()}")

if __name__ == "__main__":
    resubmit_sitemap()
