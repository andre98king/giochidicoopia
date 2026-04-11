#!/usr/bin/env python3
"""
Fetch and cross-reference analytics from Google Search Console and Cloudflare.
Usage: python3 scripts/fetch_analytics.py [--days 30]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

GSC_TOKEN_FILE = "/home/andrea/.claude/mcp-gsc/token.json"
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
SITE_URL = "sc-domain:coophubs.net"


def get_gsc_service():
    """Initialize GSC service using existing token."""
    import google.oauth2.credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(GSC_TOKEN_FILE):
        raise FileNotFoundError(f"Token GSC non trovato in {GSC_TOKEN_FILE}")

    with open(GSC_TOKEN_FILE, "r") as f:
        creds_data = json.load(f)

    creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_data)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def fetch_gsc_analytics(
    service, start_date: str, end_date: str, dimensions: list = None
):
    """Fetch search analytics from GSC."""
    if dimensions is None:
        dimensions = ["date"]

    request = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": 500,
        "dataState": "all",
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    return response


def fetch_gsc_overview(service, start_date: str, end_date: str):
    """Fetch aggregated performance overview."""
    request = {
        "startDate": start_date,
        "endDate": end_date,
        "dataState": "all",
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    return response


def fetch_cloudflare_analytics(start_date: str, end_date: str):
    """Fetch analytics from Cloudflare GraphQL API."""
    import urllib.request
    import json

    query = """
{
  viewer {
    zones(filter: {zoneTag: "%s"}) {
      httpRequests1dGroups(
        limit: 31
        filter: {date_geq: "%s", date_leq: "%s"}
        orderBy: [date_ASC]
      ) {
        dimensions { date }
        sum { requests pageViews bytes cachedRequests }
        uniq { uniques }
      }
    }
  }
}
""" % (CLOUDFLARE_ZONE_ID, start_date, end_date)

    data = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=data,
        headers={
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception as e:
        return {"success": False, "errors": [{"message": str(e)}]}

    if resp.get("errors"):
        return {"success": False, "errors": resp["errors"]}

    groups = (
        resp.get("data", {})
        .get("viewer", {})
        .get("zones", [{}])[0]
        .get("httpRequests1dGroups", [])
    )

    if not groups:
        return {
            "success": True,
            "result": {
                "totals": {
                    "requests": {"all": 0, "cached": 0},
                    "bandwidth": {"all": 0, "cached": 0},
                },
                "rows": [],
            },
        }

    totals_requests = sum(g["sum"]["requests"] for g in groups)
    totals_cached = sum(g["sum"]["cachedRequests"] for g in groups)
    totals_bytes = sum(g["sum"]["bytes"] for g in groups)
    totals_pageviews = sum(g["sum"]["pageViews"] for g in groups)
    totals_uniques = sum(g["uniq"]["uniques"] for g in groups)

    return {
        "success": True,
        "result": {
            "totals": {
                "requests": {"all": totals_requests, "cached": totals_cached},
                "bandwidth": {"all": totals_bytes, "cached": 0},
                "pageViews": totals_pageviews,
                "uniques": totals_uniques,
            },
            "rows": groups,
        },
    }


def fetch_cloudflare_cache_stats(start_date: str, end_date: str):
    """Fetch detailed cache statistics."""
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/analytics/cache"

    params = {
        "since": start_date,
        "until": end_date,
    }

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def format_number(n: float) -> str:
    """Format number with thousand separators."""
    if n is None:
        return "N/A"
    return f"{int(n):,}".replace(",", ".")


def print_gsc_overview(data: dict):
    """Print GSC overview data."""
    print("\n" + "=" * 60)
    print("📊 GOOGLE SEARCH CONSOLE - PANORAMICA")
    print("=" * 60)

    if "rows" not in data or not data["rows"]:
        print("Nessun dato disponibile")
        return

    rows = data["rows"]

    total_clicks = sum(r.get("clicks", 0) for r in rows)
    total_impressions = sum(r.get("impressions", 0) for r in rows)
    avg_ctr = sum(r.get("ctr", 0) for r in rows) / len(rows) if rows else 0
    avg_position = sum(r.get("position", 0) for r in rows) / len(rows) if rows else 0

    print(f"\n📈 clicks totali: {format_number(total_clicks)}")
    print(f"👁️  Impressioni: {format_number(total_impressions)}")
    print(f"📍 CTR medio: {avg_ctr * 100:.2f}%")
    print(f"🎯 Posizione media: {avg_position:.1f}")

    if total_impressions > 0:
        print(f"📊 Tasso di clic: {(total_clicks / total_impressions) * 100:.2f}%")

    top_queries = fetch_gsc_queries()
    if top_queries:
        print(f"\n🔝 Top 10 query per clic:")
        for i, q in enumerate(top_queries[:10], 1):
            print(
                f"  {i:2}. {q['query']} ({q['clicks']} clic, pos {q['position']:.1f})"
            )


def fetch_gsc_queries():
    """Fetch top queries."""
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    service = get_gsc_service()

    request = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "dimensions": ["query"],
        "rowLimit": 20,
        "dataState": "all",
    }

    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()

    if "rows" not in response:
        return []

    return [
        {
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0),
            "position": row.get("position", 0),
        }
        for row in response["rows"]
    ]


def print_cloudflare_overview(data: dict):
    """Print Cloudflare overview data."""
    print("\n" + "=" * 60)
    print("🌩️ CLOUDFLARE - PANORAMICA")
    print("=" * 60)

    if not data.get("result"):
        print("Nessun dato disponibile")
        return

    result = data["result"]

    totals = result.get("totals", {})
    requests_data = totals.get("requests", {})
    bandwidth_data = totals.get("bandwidth", {})

    requests_total = (
        requests_data.get("all", 0) if isinstance(requests_data, dict) else 0
    )
    bandwidth_total = (
        bandwidth_data.get("all", 0) if isinstance(bandwidth_data, dict) else 0
    )
    cache_hits = (
        requests_data.get("cached", 0) if isinstance(requests_data, dict) else 0
    )
    cache_all = requests_total

    cache_rate = (cache_hits / cache_all * 100) if cache_all > 0 else 0

    page_views = totals.get("pageViews", 0)
    uniques = totals.get("uniques", 0)

    print(f"\n🌐 Richieste totali: {format_number(requests_total)}")
    print(f"👁️  PageViews: {format_number(page_views)}")
    print(f"👤 Visitatori unici: {format_number(uniques)}")
    print(f"📶 Bandwidth: {bandwidth_total / (1024**3):.2f} GB")
    print(f"💾 Cache hit: {format_number(cache_hits)}")
    print(f"📦 Cache total: {format_number(cache_all)}")
    print(f"⚡ Cache Hit Rate: {cache_rate:.1f}%")

    if cache_rate < 50:
        print("⚠️  WARNING: Cache Hit Rate basso! Considera di creare una Cache Rule.")
    elif cache_rate < 70:
        print("⚡ Cache Hit Rate moderato. Potrebbe essere migliorato.")


def print_combined_analysis(gsc_data: dict, cf_data: dict):
    """Print combined analysis comparing GSC and Cloudflare data."""
    print("\n" + "=" * 60)
    print("📈 ANALISI COMBINATA GSC + CLOUDFLARE")
    print("=" * 60)

    if "rows" not in gsc_data or not gsc_data["rows"]:
        print("Dati GSC insufficienti per l'analisi")
        return

    gsc_total_clicks = sum(r.get("clicks", 0) for r in gsc_data["rows"])

    if cf_data.get("result"):
        cf_requests_data = cf_data["result"]["totals"].get("requests", {})
        cf_requests = (
            cf_requests_data.get("all", 0) if isinstance(cf_requests_data, dict) else 0
        )
    else:
        cf_requests = 0

    if cf_requests > 0:
        gsc_to_cf_ratio = gsc_total_clicks / cf_requests * 100 if cf_requests > 0 else 0
        print(f"\n🔗 GSC Clic / CF Richieste: {gsc_to_cf_ratio:.2f}%")
        print(
            f"   → Significato: {gsc_to_cf_ratio:.1f}% delle visite arrivano da Google"
        )

        if gsc_to_cf_ratio < 5:
            print("   📌 Insight: Il traffico organico è basso. Focus su SEO.")
        elif gsc_to_cf_ratio < 20:
            print("   📌 Insight: Traffico organico moderato, c'è spazio di crescita.")
        else:
            print("   📌 Insight: Buon traffico organico!")

    if cf_data.get("result"):
        cf_totals = cf_data["result"]["totals"]
        cf_requests = cf_totals.get("requests", {})
        if isinstance(cf_requests, dict):
            cached = cf_requests.get("cached", 0)
            all_req = cf_requests.get("all", 1)
            cache_rate = (cached / all_req * 100) if all_req > 0 else 0
        else:
            cache_rate = 0
        print(f"\n💾 Performance Cache: {cache_rate:.1f}%")

        if cache_rate < 50:
            print("   ⚠️  CRITICO: Creare Cache Rule su Cloudflare")
            print("   → Vai su Cloudflare → Caching → Cache Rules")
            print("   → Crea regola: If: all incoming requests")
            print("   → Then: Cache Level: Cache Everything, Edge TTL: 7 days")
        elif cache_rate < 70:
            print("   ⚡ Potenziale miglioramento con Cache Rule")


def main():
    parser = argparse.ArgumentParser(description="Fetch GSC and Cloudflare analytics")
    parser.add_argument("--days", type=int, default=30, help="Number of days to fetch")
    parser.add_argument("--gsc-only", action="store_true", help="Fetch only GSC data")
    parser.add_argument(
        "--cf-only", action="store_true", help="Fetch only Cloudflare data"
    )
    args = parser.parse_args()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"\n📅 Periodo: {start_str} → {end_str} (ultimi {args.days} giorni)")

    gsc_data = None
    cf_data = None

    if not args.cf_only:
        print("\n⏳ Fetching GSC data...")
        try:
            service = get_gsc_service()
            gsc_data = fetch_gsc_overview(service, start_str, end_str)
            print("✅ GSC data fetched")
        except Exception as e:
            print(f"❌ Errore GSC: {e}")

    if not args.gsc_only:
        print("⏳ Fetching Cloudflare data (GraphQL API)...")
        try:
            cf_data = fetch_cloudflare_analytics(start_str, end_str)
            if cf_data.get("success"):
                print("✅ Cloudflare data fetched")
            else:
                err_msg = cf_data.get("errors", [{"message": "Unknown error"}])[0][
                    "message"
                ]
                print(f"⚠️  Cloudflare GraphQL non disponibile: {err_msg}")
                print("   (Richiede token con permessi Account Level)")
                cf_data = None
        except Exception as e:
            print(f"⚠️  Cloudflare non disponibile: {e}")
            cf_data = None
        except Exception as e:
            print(f"⚠️  Cloudflare non disponibile: {e}")
            cf_data = None

    if gsc_data:
        print_gsc_overview(gsc_data)

    if cf_data:
        print_cloudflare_overview(cf_data)

    if gsc_data and cf_data:
        print_combined_analysis(gsc_data, cf_data)

    print("\n" + "=" * 60)
    print("✅ Analisi completata!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
