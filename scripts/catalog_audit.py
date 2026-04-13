#!/usr/bin/env python3
"""
Catalog Audit — quality gate sweep over all existing games in games.js.

Finds false co-op entries already in the catalog: games with no real co-op
signal on Steam, PvP-only titles that slipped through, or games whose Steam
data has changed since they were added.

Modes:
  --fast (default)  Steam-only. ~2-3 min for 599 games (4 parallel workers).
  --full            Steam + IGDB + GOG + RAWG. ~15 min with 2 workers.

Actions:
  Default           Dry-run — writes JSON reports only, no changes.
  --apply           Remove hard-rejected games from games.js (only high-confidence
                    rejections where Steam explicitly has zero co-op categories).
                    Games in needs_review are NEVER auto-removed.

Resume:
  --resume          Skip games already in data/audit_state.json.
                    Useful when the run is interrupted mid-way.

Output:
  data/audit_rejected.json       — confirmed false co-op
  data/audit_needs_review.json   — ambiguous (PvP+coop, IGDB disagrees, etc.)
  data/audit_state.json          — intermediate state for --resume

Usage:
    python3 scripts/catalog_audit.py
    python3 scripts/catalog_audit.py --full
    python3 scripts/catalog_audit.py --resume --apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import quality_gate

GAMES_JS = ROOT / "assets" / "bundles" / "games-data.js"
DATA_DIR = ROOT / "data"
STATE_PATH = DATA_DIR / "audit_state.json"
REJECTED_PATH = DATA_DIR / "audit_rejected.json"
REVIEW_PATH = DATA_DIR / "audit_needs_review.json"


# ─── Env ──────────────────────────────────────────────────────────────────────


def load_env() -> dict[str, str]:
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


# ─── games.js parsing ─────────────────────────────────────────────────────────

_FIELD_PATTERNS = {
    "id": re.compile(r"^\s+id:\s*(\d+),", re.MULTILINE),
    "title": re.compile(r'^\s+title:\s*"(.*?)"', re.MULTILINE),
    "steamUrl": re.compile(r'^\s+steamUrl:\s*"(.*?)"', re.MULTILINE),
    "coopScore": re.compile(r"^\s+coopScore:\s*(\d+|null)", re.MULTILINE),
    "mini_review_it": re.compile(r'^\s+mini_review_it:\s*"(.*?)"', re.MULTILINE),
    "mini_review_en": re.compile(r'^\s+mini_review_en:\s*"(.*?)"', re.MULTILINE),
}


def parse_games_js() -> list[dict]:
    """
    Extract lightweight game records from games.js.
    Returns list of {id, title, steamUrl, coopScore, mini_review_it, mini_review_en}.
    """
    content = GAMES_JS.read_text(encoding="utf-8")
    games = []
    for block in re.split(r"\n  \{", content)[1:]:
        id_m = _FIELD_PATTERNS["id"].search(block)
        if not id_m:
            continue
        score_m = _FIELD_PATTERNS["coopScore"].search(block)
        games.append(
            {
                "id": int(id_m.group(1)),
                "title": (
                    m.group(1) if (m := _FIELD_PATTERNS["title"].search(block)) else ""
                ),
                "steamUrl": (
                    m.group(1)
                    if (m := _FIELD_PATTERNS["steamUrl"].search(block))
                    else ""
                ),
                "coopScore": (
                    int(score_m.group(1))
                    if score_m and score_m.group(1) != "null"
                    else None
                ),
                "mini_review_it": (
                    m.group(1)
                    if (m := _FIELD_PATTERNS["mini_review_it"].search(block))
                    else ""
                ),
                "mini_review_en": (
                    m.group(1)
                    if (m := _FIELD_PATTERNS["mini_review_en"].search(block))
                    else ""
                ),
            }
        )
    return games


def extract_app_id(steam_url: str) -> str | None:
    m = re.search(r"/app/(\d+)", steam_url or "")
    return m.group(1) if m else None


# ─── games.js rewrite (remove by ID) ─────────────────────────────────────────


def remove_games_by_id(ids_to_remove: set[int]) -> int:
    """Remove game blocks from games.js by ID. Returns count removed."""
    content = GAMES_JS.read_text(encoding="utf-8")
    removed = 0
    for gid in ids_to_remove:
        pattern = rf",?\n  \{{\n    id: {gid},[\s\S]*?  \}}(?=,?\n)"
        content, n = re.subn(pattern, "", content)
        removed += n
    content = re.sub(r",\s*,", ",", content)
    content = re.sub(r",\s*\];", "\n];", content)
    GAMES_JS.write_text(content, encoding="utf-8")
    return removed


# ─── State / resume ───────────────────────────────────────────────────────────


def load_state() -> dict[str, dict]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ─── Per-game audit worker (runs in thread pool) ──────────────────────────────


def _audit_one(
    game: dict,
    sources: frozenset[str],
    rawg_api_key: str | None,
    igdb_client_id: str | None,
    igdb_client_secret: str | None,
    delay: float,
) -> tuple[dict, str | None, dict]:
    """
    Audit a single game. Thread-safe — no shared mutable state.
    Returns (game, app_id, verdict).
    """
    app_id = extract_app_id(game["steamUrl"])
    if not app_id:
        return (
            game,
            None,
            {
                "status": "needs_review",
                "reason": "No Steam URL — manual review needed",
                "confidence": "low",
            },
        )
    try:
        verdict = quality_gate.validate(
            app_id,
            rawg_api_key=rawg_api_key,
            igdb_client_id=igdb_client_id,
            igdb_client_secret=igdb_client_secret,
            sources=sources,
            rate_limit_delay=delay,
        )
    except Exception as exc:
        verdict = {
            "status": "needs_review",
            "reason": f"Audit error: {exc}",
            "confidence": "low",
        }
    return game, app_id, verdict


# ─── Main audit ───────────────────────────────────────────────────────────────


def run(
    full_mode: bool,
    apply: bool,
    resume: bool,
    rawg_api_key: str | None,
    igdb_client_id: str | None,
    igdb_client_secret: str | None,
) -> None:
    sources = quality_gate.SOURCES_FULL if full_mode else quality_gate.SOURCES_FAST
    workers = 1 if full_mode else 2
    delay = 2.0 if full_mode else 1.5

    print("=" * 60)
    print("CATALOG AUDIT")
    print("=" * 60)
    print(
        f"Mode:    {'FULL (Steam+IGDB+GOG+RAWG)' if full_mode else 'FAST (Steam only)'}"
    )
    print(
        f"Action:  {'APPLY — remove hard-rejected games' if apply else 'DRY RUN — reports only'}"
    )
    print(f"Workers: {workers} parallel")
    if full_mode:
        print(
            f"IGDB:    {'enabled' if igdb_client_id else 'disabled (no credentials)'}"
        )
        print(f"RAWG:    {'enabled' if rawg_api_key else 'disabled (no key)'}")
    print()

    all_games = parse_games_js()
    print(f"Loaded {len(all_games)} games from games.js")

    cached_state = load_state() if resume else {}
    if resume and cached_state:
        print(f"Resuming — {len(cached_state)} games already audited")

    # Separate cached from pending
    cached_results: list[tuple[dict, str | None, dict]] = []
    pending: list[dict] = []
    for game in all_games:
        app_id = extract_app_id(game["steamUrl"])
        if resume and app_id and app_id in cached_state:
            cached_results.append((game, app_id, cached_state[app_id]))
        else:
            pending.append(game)

    print(f"To audit: {len(pending)} games  (cached: {len(cached_results)})\n")

    # ── Run parallel audit ──
    fresh_results: list[tuple[dict, str | None, dict]] = []
    completed = 0
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _audit_one,
                game,
                sources,
                rawg_api_key,
                igdb_client_id,
                igdb_client_secret,
                delay,
            ): game
            for game in pending
        }
        for future in as_completed(futures):
            game, app_id, verdict = future.result()
            with lock:
                completed += 1
                fresh_results.append((game, app_id, verdict))
                pct = completed * 100 // len(pending) if pending else 100
                status = verdict["status"]
                icon = {"approved": "✓", "needs_review": "⚠", "rejected": "✗"}.get(
                    status, "?"
                )
                conf_i = {"high": "★", "medium": "◆", "low": "○"}.get(
                    verdict.get("confidence", ""), "?"
                )
                print(
                    f"[{completed:3}/{len(pending)} {pct:3}%] "
                    f"{game['title'][:40]:<40}  "
                    f"{icon}{conf_i} {verdict.get('reason', '')[:45]}"
                )

    # ── Merge cached + fresh, sort by game ID ──
    all_results = sorted(cached_results + fresh_results, key=lambda t: t[0]["id"])

    # Persist state for --resume
    new_state = {app_id: verdict for _, app_id, verdict in all_results if app_id}
    save_state(new_state)

    # ── Categorize ──
    passed, needs_review, rejected, no_steam = [], [], [], []
    for game, app_id, verdict in all_results:
        rec = {**game, "app_id": app_id, "verdict": verdict}
        if not app_id:
            no_steam.append(rec)
            needs_review.append(rec)
        elif verdict["status"] == "approved":
            passed.append(rec)
        elif verdict["status"] == "needs_review":
            needs_review.append(rec)
        else:
            rejected.append(rec)

    # ── Summary ──
    print()
    print("=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"  ✓ Passed:       {len(passed)}")
    print(
        f"  ⚠ Needs review: {len(needs_review)}  (incl. {len(no_steam)} without Steam URL)"
    )
    print(f"  ✗ Rejected:     {len(rejected)}")
    print()

    if rejected:
        print("REJECTED (false co-op):")
        for r in rejected:
            print(
                f"  [{r['id']:4}] {r['title'][:45]:<45}  {r['verdict'].get('reason', '')}"
            )
        print()

    if needs_review:
        print("NEEDS REVIEW:")
        for r in needs_review:
            v = r["verdict"]
            conf_i = {"high": "★", "medium": "◆", "low": "○"}.get(
                v.get("confidence", ""), "?"
            )
            print(
                f"  [{r['id']:4}] {r['title'][:45]:<45}  {conf_i} {v.get('reason', '')[:45]}"
            )
        print()

    # ── Write reports ──
    DATA_DIR.mkdir(exist_ok=True)
    REJECTED_PATH.write_text(json.dumps(rejected, indent=2, ensure_ascii=False))
    REVIEW_PATH.write_text(json.dumps(needs_review, indent=2, ensure_ascii=False))
    print(
        f"Reports: {REJECTED_PATH.name} ({len(rejected)}), {REVIEW_PATH.name} ({len(needs_review)})"
    )
    print()

    # ── Apply ──
    if apply and rejected:
        safe_to_remove = [
            r
            for r in rejected
            if r["verdict"].get("confidence") == "high"
            and r["verdict"].get("status") == "rejected"
        ]
        if not safe_to_remove:
            print("Nothing to remove (no high-confidence rejections).")
            return
        ids_to_remove = {r["id"] for r in safe_to_remove}
        print(f"Removing {len(ids_to_remove)} games from games.js:")
        for r in safe_to_remove:
            print(f"  [{r['id']:4}] {r['title']}")
        n = remove_games_by_id(ids_to_remove)
        print(f"\n✓ Removed {n} game(s) from games.js")
    elif apply:
        print("Nothing to remove — catalog is clean.")

    # Clean up state file after a non-resume full run
    if not resume and STATE_PATH.exists():
        STATE_PATH.unlink()


# ─── CLI ──────────────────────────────────────────────────────────────────────


def retry_steam_unavailable(
    rawg_api_key: str | None,
    igdb_client_id: str | None,
    igdb_client_secret: str | None,
) -> None:
    """
    Re-audit games that previously failed with 'Steam API unavailable'.
    Uses IGDB + RAWG + GOG as fallback. Updates audit_state.json in place.
    """
    state = load_state()
    to_retry = {
        app_id: v for app_id, v in state.items() if "Steam API" in v.get("reason", "")
    }
    if not to_retry:
        print("No games to retry — all already resolved.")
        return

    print(f"Retrying {len(to_retry)} games with IGDB+GOG+RAWG fallback...")
    sources = frozenset({"igdb", "gog", "rawg"})  # skip Steam (still blocked)
    updated = 0

    for app_id, old_verdict in to_retry.items():
        try:
            verdict = quality_gate.validate(
                app_id,
                rawg_api_key=rawg_api_key,
                igdb_client_id=igdb_client_id,
                igdb_client_secret=igdb_client_secret,
                sources=sources,
                rate_limit_delay=1.5,
            )
            state[app_id] = verdict
            updated += 1
            icon = {"approved": "✓", "needs_review": "⚠", "rejected": "✗"}.get(
                verdict["status"], "?"
            )
            print(f"  {icon} {app_id}: {verdict['reason'][:60]}")
        except Exception as exc:
            print(f"  ⚡ {app_id}: {exc}")

    save_state(state)
    print(
        f"\nUpdated {updated} games. Re-run `catalog_audit.py --resume --apply` to apply."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit existing catalog for false co-op entries"
    )
    parser.add_argument(
        "--full", action="store_true", help="All sources (Steam+IGDB+GOG+RAWG)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Remove hard-rejected games from games.js"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Skip games already in audit_state.json"
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Retry Steam-unavailable games using IGDB+GOG+RAWG",
    )
    args = parser.parse_args()

    env = load_env()
    kwargs = dict(
        rawg_api_key=env.get("RAWG_API_KEY"),
        igdb_client_id=env.get("IGDB_CLIENT_ID"),
        igdb_client_secret=env.get("IGDB_CLIENT_SECRET"),
    )

    if args.fallback:
        retry_steam_unavailable(**kwargs)
        return

    run(full_mode=args.full, apply=args.apply, resume=args.resume, **kwargs)


if __name__ == "__main__":
    main()
