#!/usr/bin/env python3
"""
Catalog Audit — Verifica che i giochi siano ancora Co-op validi

Logica semplificata:
- --daily: Solo 50 trending games (veloce, ~2 min)
- --full: Tutti i giochi con fallback (completo, ~15 min)
- --resume: Continua da dove aveva lasciato

Rate limiting rispettato:
- Steam: 1s delay (60/min, 3600/giorno)
- IGDB/RAWG: 0.5s delay (120/min, 7200/giorno)
"""

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "scripts"))

import quality_gate

# ─── Paths ───────────────────────────────────────────────────────────────────

GAMES_JS = ROOT / "assets" / "bundles" / "games-data.js"
DATA_DIR = ROOT / "data"
STATE_PATH = DATA_DIR / "audit_state.json"


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


def parse_games() -> list[dict]:
    """Estrae lista giochi dal file bundle."""
    content = GAMES_JS.read_text(encoding="utf-8")
    games = []

    # Estrai ogni blocco { id:, title:, steamUrl: }
    block_pattern = re.compile(
        r'\{\s*id:\s*(\d+).*?title:\s*"([^"]+)".*?steamUrl:\s*"([^"]*)"', re.DOTALL
    )

    for match in block_pattern.finditer(content):
        games.append(
            {
                "id": int(match.group(1)),
                "title": match.group(2),
                "steamUrl": match.group(3) if match.group(3) else "",
            }
        )

    return games


def extract_app_id(url: str) -> str | None:
    m = re.search(r"/app/(\d+)", url or "")
    return m.group(1) if m else None


def load_state() -> dict[str, dict]:
    """Carica stato audit precedente."""
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict[str, dict]) -> None:
    """Salva stato audit."""
    STATE_PATH.write_text(json.dumps(state, indent=2))


def audit_game(
    game: dict,
    sources: frozenset[str],
    rawg_key: str | None,
    igdb_id: str | None,
    igdb_secret: str | None,
    delay: float = 1.0,
) -> tuple[dict, str | None, dict]:
    """Audit singolo gioco."""
    app_id = extract_app_id(game.get("steamUrl", ""))

    if not app_id:
        return (
            game,
            None,
            {
                "status": "needs_review",
                "reason": "No Steam URL",
                "confidence": "low",
            },
        )

    try:
        verdict = quality_gate.validate(
            app_id,
            rawg_api_key=rawg_key,
            igdb_client_id=igdb_id,
            igdb_client_secret=igdb_secret,
            sources=sources,
            rate_limit_delay=delay,
        )
        time.sleep(delay)  # Rate limiting
    except Exception as e:
        verdict = {
            "status": "needs_review",
            "reason": f"Error: {e}",
            "confidence": "low",
        }

    return game, app_id, verdict


def run_audit(
    games: list[dict],
    state: dict[str, dict],
    sources: frozenset[str],
    rawg_key: str | None,
    igdb_id: str | None,
    igdb_secret: str | None,
    delay: float = 1.0,
    max_workers: int = 2,
    skip_cached: bool = True,
) -> dict[str, dict]:
    """Esegue audit su lista giochi."""

    # Separa cached da pending
    pending = []
    cached_count = 0

    for game in games:
        app_id = extract_app_id(game.get("steamUrl", ""))
        if skip_cached and app_id and app_id in state:
            cached_count += 1
        else:
            pending.append((game, app_id))

    print(f"Games: {len(games)} total, {cached_count} cached, {len(pending)} to audit")

    # Processa pending
    results = state.copy()
    completed = 0

    if max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    audit_game, g, sources, rawg_key, igdb_id, igdb_secret, delay
                ): g
                for g, a in pending
                if a
            }
            for future in as_completed(futures):
                game, app_id, verdict = future.result()
                if app_id:
                    results[app_id] = verdict
                completed += 1
                progress = completed * 100 // len(pending) if pending else 100
                print(f"  Progress: {completed}/{len(pending)} ({progress}%)")
    else:
        for game, app_id in pending:
            if app_id:
                _, _, verdict = audit_game(
                    game, sources, rawg_key, igdb_id, igdb_secret, delay
                )
                results[app_id] = verdict
            completed += 1
            progress = completed * 100 // len(pending) if pending else 100
            print(f"  Progress: {completed}/{len(pending)} ({progress}%)")

    return results


def summarize(results: dict[str, dict]) -> None:
    """Mostra riepilogo risultati."""
    passed = sum(1 for v in results.values() if v.get("status") == "approved")
    needs_review = sum(1 for v in results.values() if v.get("status") == "needs_review")
    rejected = sum(1 for v in results.values() if v.get("status") == "rejected")

    print("\n=== AUDIT SUMMARY ===")
    print(f"  ✓ Passed:       {passed}")
    print(f"  ⚠ Needs review: {needs_review}")
    print(f"  ✗ Rejected:     {rejected}")

    # Lista rejected
    rejected_games = [
        (app_id, v.get("reason", ""))
        for app_id, v in results.items()
        if v.get("status") == "rejected"
    ]
    if rejected_games:
        print("\nRejected games (remove from catalog):")
        for app_id, reason in rejected_games:
            print(f"  {app_id}: {reason[:60]}")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit catalog for false co-op entries"
    )
    parser.add_argument(
        "--daily", action="store_true", help="Daily quick check (50 trending)"
    )
    parser.add_argument("--full", action="store_true", help="Full audit with fallback")
    parser.add_argument(
        "--resume", action="store_true", help="Resume from previous state"
    )
    parser.add_argument("--apply", action="store_true", help="Remove rejected games")
    args = parser.parse_args()

    env = load_env()
    rawg_key = env.get("RAWG_API_KEY")
    igdb_id = env.get("IGDB_CLIENT_ID")
    igdb_secret = env.get("IGDB_CLIENT_SECRET")

    print("=" * 60)
    print("CATALOG AUDIT")
    print("=" * 60)

    # Carica giochi
    games = parse_games()
    print(f"Loaded {len(games)} games")

    # Carica stato precedente
    state = load_state() if args.resume else {}

    # Determina modalità
    if args.daily:
        # Daily: solo 50 trending (veloce)
        print("\nMode: DAILY (50 trending games)")

        # Prendi solo i trending (o primi 50)
        trending = [g for g in games if g.get("trending")] or games[:50]

        # Steam solo (più veloce, rate limit 1s)
        sources = frozenset({"steam"})
        results = run_audit(
            trending,
            state,
            sources,
            rawg_key,
            igdb_id,
            igdb_secret,
            delay=1.0,
            max_workers=1,
            skip_cached=False,  # Riaudit i trending
        )

    elif args.full:
        # Full: tutti con fallback
        print("\nMode: FULL (all games with IGDB/RAWG fallback)")

        # Usa tutte le fonti (rate limit 0.5s per non superare limiti)
        sources = frozenset({"steam", "igdb", "gog", "rawg"})
        results = run_audit(
            games,
            state,
            sources,
            rawg_key,
            igdb_id,
            igdb_secret,
            delay=0.5,
            max_workers=2,
            skip_cached=args.resume,
        )

    elif args.resume:
        # Resume: continua da stato esistente
        print("\nMode: RESUME (continue from state)")

        sources = frozenset({"steam", "igdb", "gog", "rawg"})
        results = run_audit(
            games,
            state,
            sources,
            rawg_key,
            igdb_id,
            igdb_secret,
            delay=0.5,
            max_workers=2,
            skip_cached=True,
        )

    else:
        print("Use --daily, --full, or --resume")
        return

    # Salva stato
    save_state(results)

    # Riepilogo
    summarize(results)

    # Applica rimozioni se richiesto
    if args.apply:
        rejected = [k for k, v in results.items() if v.get("status") == "rejected"]
        if rejected:
            print(f"\nRemoving {len(rejected)} rejected games...")
            # Implementare rimozione da games.js
        else:
            print("\nNo games to remove")


if __name__ == "__main__":
    main()
