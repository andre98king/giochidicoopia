#!/usr/bin/env python3
# DEPRECATED (2026-04-02): superseded by auto_update.py pipeline.
# La discovery + quality gate + enrich è ora integrata direttamente nel workflow CI.
# Questo file rimane per ingest manuale one-shot da file JSON esterni.
"""
Catalog Ingest Pipeline — automated co-op game ingestion with quality gates.

Full pipeline:
  1. Reads candidate games (from JSON file or multi_cross_reference.json)
  2. Validates each candidate with quality_gate.py (Steam categories + RAWG tags)
  3. Enriches approved games with full Steam data (via catalog_enricher.py)
  4. Outputs approved/rejected reports to data/
  5. Optionally adds approved games to assets/games.js (--apply flag)

Usage:
    # Dry-run (default): validate and preview, no changes
    python3 scripts/catalog_ingest.py

    # Validate only a specific input file
    python3 scripts/catalog_ingest.py --input data/coop_games_to_add.json

    # Validate + apply to games.js
    python3 scripts/catalog_ingest.py --apply

    # Use custom input and apply
    python3 scripts/catalog_ingest.py --input data/coop_games_to_add.json --apply

    # Skip enrichment (just validate, faster)
    python3 scripts/catalog_ingest.py --no-enrich
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import quality_gate
import catalog_enricher

GAMES_JS = ROOT / "assets" / "games.js"
DATA_DIR = ROOT / "data"
APPROVED_PATH  = DATA_DIR / "approved_candidates.json"
REJECTED_PATH  = DATA_DIR / "rejected_candidates.json"
REVIEW_PATH    = DATA_DIR / "needs_review_candidates.json"
DEFAULT_INPUT  = DATA_DIR / "coop_games_to_add.json"
CROSS_REF_PATH = DATA_DIR / "multi_cross_reference.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_env() -> dict[str, str]:
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def get_max_id() -> int:
    content = GAMES_JS.read_text(encoding="utf-8")
    ids = [int(i) for i in re.findall(r"^\s{4}id:\s*(\d+),", content, re.MULTILINE)]
    return max(ids) if ids else 600


def extract_app_id(steam_url: str) -> str | None:
    m = re.search(r"/app/(\d+)", steam_url or "")
    return m.group(1) if m else None


def get_existing_app_ids() -> set[str]:
    """Return all Steam app IDs already in games.js."""
    content = GAMES_JS.read_text(encoding="utf-8")
    urls = re.findall(r'steamUrl:\s*"(https://store\.steampowered\.com/app/\d+[^"]*)"', content)
    result = set()
    for u in urls:
        aid = extract_app_id(u)
        if aid:
            result.add(aid)
    return result


def load_candidates(input_path: Path) -> list[dict]:
    """Load candidates from a JSON file.

    Accepts two formats:
    1. List of {title, steam_url, app_id, ...}  (from coop_games_to_add.json)
    2. multi_cross_reference.json format (has .potential_new_games[])
    """
    with open(input_path) as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    # multi_cross_reference.json format
    if isinstance(data, dict) and "potential_new_games" in data:
        raw = data["potential_new_games"]
        candidates = []
        for item in raw:
            d = item.get("data", {})
            steam_url = (
                d.get("steam_url") or
                d.get("url") or
                d.get("steamUrl") or
                (f"https://store.steampowered.com/app/{d['app_id']}" if d.get("app_id") else None)
            )
            candidates.append({
                "title": item.get("title", d.get("name", "")),
                "steam_url": steam_url,
                "source": item.get("source", "unknown"),
            })
        return candidates

    return []


def bool_js(v: bool) -> str:
    return "true" if v else "false"


def js_esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_game_js(g: dict) -> str:
    def n(v):
        return "null" if v is None else str(v)

    lines = [
        "  {",
        f'    id: {g["id"]},',
        f'    igdbId: {g.get("igdbId", 0)},',
        f'    title: "{js_esc(g["title"])}",',
        f'    categories: {json.dumps(g.get("categories", ["action"]))},',
        f'    genres: {json.dumps(g.get("genres", []))},',
        f'    coopMode: {json.dumps(g.get("coopMode", ["online"]))},',
        f'    maxPlayers: {g.get("maxPlayers", 2)},',
        f'    crossplay: {bool_js(g.get("crossplay", False))},',
        f'    players: "{g.get("players", "1-2")}",',
        f'    releaseYear: {g.get("releaseYear", 0)},',
        f'    image: "{js_esc(g.get("image", ""))}",',
        f'    description: "{js_esc(g.get("description", ""))}",',
        f'    description_en: "{js_esc(g.get("description_en", ""))}",',
        f'    personalNote: "{js_esc(g.get("personalNote", ""))}",',
        f'    played: {bool_js(g.get("played", False))},',
        f'    steamUrl: "{js_esc(g.get("steamUrl", ""))}",',
        f'    gogUrl: "{js_esc(g.get("gogUrl", ""))}",',
        f'    epicUrl: "{js_esc(g.get("epicUrl", ""))}",',
        f'    itchUrl: "{js_esc(g.get("itchUrl", ""))}",',
        f'    ccu: {g.get("ccu", 0)},',
        f'    trending: {bool_js(g.get("trending", False))},',
        f'    rating: {g.get("rating", 0)},',
        f'    igUrl: "{js_esc(g.get("igUrl", ""))}",',
        f'    igDiscount: {g.get("igDiscount", 0)},',
        f'    gbUrl: "{js_esc(g.get("gbUrl", ""))}",',
        f'    gbDiscount: {g.get("gbDiscount", 0)},',
        f'    gsUrl: "",',
        f'    gsDiscount: 0,',
        f'    kgUrl: "",',
        f'    kgDiscount: 0,',
        f'    k4gUrl: "",',
        f'    k4gDiscount: 0,',
        f'    gmvUrl: "",',
        f'    gmvDiscount: 0,',
        f'    gmgUrl: "",',
        f'    gmgDiscount: 0,',
        f'    coopScore: {n(g.get("coopScore"))},',
        f'    mini_review_it: "{js_esc(g.get("mini_review_it", ""))}",',
        f'    mini_review_en: "{js_esc(g.get("mini_review_en", ""))}"',
        "  }",
    ]
    return "\n".join(lines)


def apply_to_games_js(entries: list[dict]) -> int:
    """Append entries to games.js. Returns number of games added."""
    content = GAMES_JS.read_text(encoding="utf-8")
    insertion = ",\n".join(render_game_js(g) for g in entries)
    old_tail = "\n];"
    idx = content.rfind(old_tail)
    if idx == -1:
        print("ERROR: could not find closing ]; in games.js")
        return 0
    new_content = content[:idx] + f",\n{insertion}\n];"
    GAMES_JS.write_text(new_content, encoding="utf-8")
    return len(entries)


# ─── Main pipeline ────────────────────────────────────────────────────────────

def run(
    input_path: Path,
    apply: bool,
    enrich: bool,
    rawg_api_key: str | None,
    igdb_client_id: str | None = None,
    igdb_client_secret: str | None = None,
    verbose: bool = True,
) -> None:
    print("=" * 60)
    print("CATALOG INGEST PIPELINE")
    print("=" * 60)
    print(f"Input:   {input_path}")
    print(f"Mode:    {'APPLY to games.js' if apply else 'DRY RUN (preview only)'}")
    print(f"Enrich:  {'yes (Steam + RAWG)' if enrich else 'no (validate only)'}")
    print(f"RAWG:    {'key found' if rawg_api_key else 'no key — RAWG cross-check disabled'}")
    print(f"IGDB:    {'credentials found' if igdb_client_id else 'no credentials — IGDB check disabled'}")
    print(f"GOG:     always checked by title (no credentials needed)")
    print()

    candidates = load_candidates(input_path)
    print(f"Loaded {len(candidates)} candidates from {input_path.name}")

    existing_app_ids = get_existing_app_ids()
    print(f"Catalog has {len(existing_app_ids)} games with Steam URLs")
    print()

    # Filter already-in-catalog
    new_candidates = []
    skipped_dup = []
    for c in candidates:
        aid = extract_app_id(c.get("steam_url", ""))
        if aid and aid in existing_app_ids:
            skipped_dup.append(c.get("title", aid))
        else:
            new_candidates.append(c)

    if skipped_dup:
        print(f"⏭  Skipped {len(skipped_dup)} already in catalog: {', '.join(skipped_dup[:5])}")
        print()

    if not new_candidates:
        print("No new candidates to process.")
        return

    print(f"Processing {len(new_candidates)} new candidates...")
    print()

    approved = []
    rejected = []
    needs_review = []
    next_id = get_max_id() + 1

    for i, cand in enumerate(new_candidates, 1):
        title = cand.get("title", "?")
        steam_url = cand.get("steam_url", "")
        app_id = extract_app_id(steam_url)

        print(f"[{i:2}/{len(new_candidates)}] {title[:45]}", end="  ")

        if not app_id:
            print("✗ no Steam URL — skip")
            rejected.append({**cand, "verdict": "rejected", "reason": "No Steam URL"})
            continue

        # Step 1: Quality gate (Steam + IGDB + GOG + RAWG)
        verdict = quality_gate.validate(
            app_id,
            rawg_api_key=rawg_api_key,
            igdb_client_id=igdb_client_id,
            igdb_client_secret=igdb_client_secret,
        )
        status = verdict["status"]
        conf_icon = {"high": "★", "medium": "◆", "low": "○"}.get(verdict["confidence"], "?")

        if status == "rejected":
            print(f"✗ REJECT [{conf_icon}] {verdict['reason']}")
            rejected.append({**cand, "app_id": app_id, "verdict": verdict})
            continue

        if status == "needs_review":
            print(f"⚠ REVIEW [{conf_icon}] {verdict['reason']}")
            needs_review.append({**cand, "app_id": app_id, "verdict": verdict})
            continue

        # Step 2: Enrich with Steam data
        if enrich:
            entry = catalog_enricher.enrich(
                app_id=app_id,
                game_id=next_id,
                rawg_api_key=rawg_api_key,
                coop_modes=verdict["coop_modes"],
                coop_score_hint=verdict["coop_score_hint"],
                rate_limit_delay=1.2,
            )
        else:
            entry = {
                "id": next_id,
                "title": verdict["steam_name"] or title,
                "steamUrl": f"https://store.steampowered.com/app/{app_id}/",
                "coopMode": verdict["coop_modes"],
                "coopScore": verdict["coop_score_hint"],
                "categories": ["action"],
                "genres": [],
                "maxPlayers": 4,
                "crossplay": False,
                "players": "1-4",
                "releaseYear": 0,
                "image": "", "description": "", "description_en": "",
                "personalNote": "", "played": False,
                "gogUrl": "", "epicUrl": "", "itchUrl": "",
                "ccu": 0, "trending": False, "rating": 0,
                "igUrl": "", "igDiscount": 0, "gbUrl": "", "gbDiscount": 0,
                "gsUrl": "", "gsDiscount": 0, "kgUrl": "", "kgDiscount": 0,
                "k4gUrl": "", "k4gDiscount": 0, "gmvUrl": "", "gmvDiscount": 0,
                "gmgUrl": "", "gmgDiscount": 0,
                "mini_review_it": "", "mini_review_en": "",
            }

        if entry:
            print(f"✓ APPROVE [{conf_icon}] {verdict['reason']}")
            approved.append({**entry, "_verdict": verdict})
            next_id += 1
        else:
            print(f"⚠ ENRICH FAILED — Steam data unavailable, adding stub")
            # Still add with minimal data
            stub = {
                "id": next_id,
                "title": title,
                "steamUrl": f"https://store.steampowered.com/app/{app_id}/",
                "coopMode": verdict["coop_modes"],
                "coopScore": verdict["coop_score_hint"],
                "categories": ["action"], "genres": [],
                "maxPlayers": 4, "crossplay": False, "players": "1-4",
                "releaseYear": 0, "image": "", "description": "", "description_en": "",
                "personalNote": "enrichment failed — needs manual review",
                "played": False, "gogUrl": "", "epicUrl": "", "itchUrl": "",
                "ccu": 0, "trending": False, "rating": 0,
                "igUrl": "", "igDiscount": 0, "gbUrl": "", "gbDiscount": 0,
                "gsUrl": "", "gsDiscount": 0, "kgUrl": "", "kgDiscount": 0,
                "k4gUrl": "", "k4gDiscount": 0, "gmvUrl": "", "gmvDiscount": 0,
                "gmgUrl": "", "gmgDiscount": 0, "mini_review_it": "", "mini_review_en": "",
            }
            needs_review.append({**stub, "_verdict": verdict})
            next_id += 1

    # Save reports
    now = datetime.datetime.now().isoformat(timespec="seconds")
    meta = {"generated": now, "input": str(input_path), "total": len(new_candidates)}

    clean_approved = [{k: v for k, v in g.items() if k != "_verdict"} for g in approved]
    clean_review   = [{k: v for k, v in g.items() if k != "_verdict"} if isinstance(g, dict) else g for g in needs_review]

    APPROVED_PATH.write_text(
        json.dumps({"meta": meta, "count": len(approved), "games": clean_approved}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    REJECTED_PATH.write_text(
        json.dumps({"meta": meta, "count": len(rejected), "games": rejected}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    REVIEW_PATH.write_text(
        json.dumps({"meta": meta, "count": len(needs_review), "games": clean_review}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Summary
    print()
    print("=" * 60)
    print(f"RESULTS: {len(approved)} approved | {len(rejected)} rejected | {len(needs_review)} needs review")
    print(f"Reports:")
    print(f"  ✓ {APPROVED_PATH.name}  ({len(approved)} games)")
    print(f"  ✗ {REJECTED_PATH.name}  ({len(rejected)} games)")
    print(f"  ⚠ {REVIEW_PATH.name}  ({len(needs_review)} games)")

    if approved:
        print()
        print("APPROVED games:")
        for g in approved:
            v = g.get("_verdict", {})
            print(f"  ID {g['id']:4} | {g['title'][:40]:40} | coopScore={g.get('coopScore')} | rating={g.get('rating')} | {v.get('confidence','?')}")

    if rejected:
        print()
        print("REJECTED games:")
        for r in rejected:
            v = r.get("verdict", {})
            reason = v.get("reason", str(v)) if isinstance(v, dict) else str(v)
            print(f"  ✗ {r.get('title', '?')[:40]:40} | {reason}")

    if needs_review:
        print()
        print("NEEDS REVIEW (co-op + PvP mixed, or low confidence):")
        for r in needs_review:
            v = r.get("_verdict", r.get("verdict", {}))
            reason = v.get("reason", "?") if isinstance(v, dict) else "?"
            print(f"  ⚠ {r.get('title', '?')[:40]:40} | {reason}")

    # Apply
    if apply and approved:
        print()
        print(f"Applying {len(clean_approved)} games to games.js...")
        added = apply_to_games_js(clean_approved)
        print(f"Added {added} games. Run build_static_pages.py to rebuild.")
    elif apply and not approved:
        print("\nNothing to apply — no approved games.")
    else:
        print(f"\nDRY RUN complete. Re-run with --apply to add approved games.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Catalog Ingest Pipeline")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=None,
        help=f"Input JSON (default: {DEFAULT_INPUT.name} or {CROSS_REF_PATH.name})",
    )
    parser.add_argument(
        "--apply", "-a",
        action="store_true",
        help="Apply approved games to games.js (default: dry-run)",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip Steam data enrichment (only validate, faster)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    # Resolve input
    if args.input:
        input_path = args.input
    elif DEFAULT_INPUT.exists():
        input_path = DEFAULT_INPUT
    elif CROSS_REF_PATH.exists():
        input_path = CROSS_REF_PATH
    else:
        print(f"ERROR: No input file found. Pass --input or create {DEFAULT_INPUT.name}")
        sys.exit(1)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    env = load_env()
    rawg_api_key = env.get("RAWG_API_KEY")
    igdb_client_id = env.get("IGDB_CLIENT_ID")
    igdb_client_secret = env.get("IGDB_CLIENT_SECRET")

    run(
        input_path=input_path,
        apply=args.apply,
        enrich=not args.no_enrich,
        rawg_api_key=rawg_api_key,
        igdb_client_id=igdb_client_id,
        igdb_client_secret=igdb_client_secret,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
