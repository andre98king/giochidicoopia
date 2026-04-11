#!/usr/bin/env python3
import os
import json
import httpx
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Carica variabili ambiente da .env
load_dotenv()

# Configurazione GSC
GSC_DIR = "/home/andrea/.claude/mcp-gsc/"
TOKEN_FILE = os.path.join(GSC_DIR, "token.json")
SITE_URL = "sc-domain:coophubs.net"

# Configurazione Cloudflare
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CF_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")

def get_gsc_service():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Token non trovato in {TOKEN_FILE}")
    with open(TOKEN_FILE, 'r') as token:
        creds_data = json.load(token)
    creds = Credentials.from_authorized_user_info(creds_data)
    return build("searchconsole", "v1", credentials=creds)

def fetch_gsc_data(days=30):
    service = get_gsc_service()
    end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+2)).strftime('%Y-%m-%d')
    
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date'],
        'rowLimit': 1000
    }
    
    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    rows = response.get('rows', [])
    
    total_clicks = sum(row['clicks'] for row in rows)
    total_impressions = sum(row['impressions'] for row in rows)
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_position = sum(row['position'] for row in rows) / len(rows) if rows else 0
    
    return {
        'clicks': total_clicks,
        'impressions': total_impressions,
        'ctr': avg_ctr,
        'position': avg_position,
        'rows': rows
    }

def fetch_cf_data(days=30):
    if not CF_API_TOKEN or not CF_ZONE_ID:
        return {"error": "Cloudflare credentials missing"}
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    query = """
    query {
      viewer {
        zones(filter: {zoneTag: "%s"}) {
          httpRequests1dGroups(
            filter: {date_geq: "%s", date_leq: "%s"}
            limit: 100
          ) {
            dimensions { date }
            sum {
              requests
              pageViews
              cachedRequests
            }
          }
        }
      }
    }
    """ % (CF_ZONE_ID, start_date, end_date)
    
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(
                "https://api.cloudflare.com/client/v4/graphql",
                json={"query": query},
                headers=headers,
                timeout=30
            )
            data = response.json()
            
            if 'errors' in data and data['errors']:
                return {"error": data['errors'][0]['message']}
            
            groups = data['data']['viewer']['zones'][0]['httpRequests1dGroups']
            
            total_requests = sum(g['sum']['requests'] for g in groups)
            total_pageviews = sum(g['sum']['pageViews'] for g in groups)
            total_cached = sum(g['sum']['cachedRequests'] for g in groups)
            cache_hit_rate = (total_cached / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'requests': total_requests,
                'pageViews': total_pageviews,
                'cacheHitRate': cache_hit_rate,
                'days': len(groups)
            }
    except Exception as e:
        return {"error": str(e)}

def fetch_gsc_details(days=30):
    service = get_gsc_service()
    end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+2)).strftime('%Y-%m-%d')
    
    # Query per Pagine
    req_pages = {
        'startDate': start_date, 'endDate': end_date,
        'dimensions': ['page'], 'rowLimit': 10
    }
    res_pages = service.searchanalytics().query(siteUrl=SITE_URL, body=req_pages).execute()
    
    # Query per Query
    req_queries = {
        'startDate': start_date, 'endDate': end_date,
        'dimensions': ['query'], 'rowLimit': 10
    }
    res_queries = service.searchanalytics().query(siteUrl=SITE_URL, body=req_queries).execute()
    
    return res_pages.get('rows', []), res_queries.get('rows', [])

def main():
    print("--- Analisi Traffico & SEO (Ultimi 30 giorni) ---")
    
    try:
        gsc = fetch_gsc_data()
        print(f"\n[Google Search Console - Overview]")
        print(f"Click: {gsc['clicks']} | Impressioni: {gsc['impressions']} | CTR: {gsc['ctr']:.2f}% | Pos: {gsc['position']:.1f}")
        
        pages, queries = fetch_gsc_details()
        
        print("\n[Top 10 Pagine per Impressioni]")
        for p in pages:
            url = p['keys'][0].replace("https://coophubs.net", "")
            print(f"{url:40} | Impr: {p['impressions']:3} | Click: {p['clicks']} | Pos: {p['position']:.1f}")
            
        print("\n[Top 10 Query per Impressioni]")
        for q in queries:
            print(f"{q['keys'][0]:40} | Impr: {q['impressions']:3} | Click: {q['clicks']} | Pos: {q['position']:.1f}")

    except Exception as e:
        print(f"Errore GSC: {e}")
        
    print("\n[Cloudflare Analytics]")
    cf = fetch_cf_data()
    if "error" in cf:
        print(f"Errore Cloudflare: {cf['error']}")
    else:
        print(f"PageViews totali: {cf['pageViews']}")
        print(f"Richieste totali: {cf['requests']}")
        print(f"Cache Hit Rate: {cf['cacheHitRate']:.1f}%")
        print(f"Giorni monitorati: {cf['days']}")

if __name__ == "__main__":
    main()
