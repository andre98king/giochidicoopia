#!/usr/bin/env python3
"""
Curation Gate Runner — estratto dalla CI per esecuzione locale e CI.

Esegue il quality gate sul catalogo giochi con gate dinamico 3-livelli:
  APPROVED  → incluso in catalog.public.v1.json
  PROBATION → incluso con curatedStatus="probation" (giochi nuovi, poche reviews)
  REJECTED  → escluso + ID salvato in data/excluded_games.json
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from catalog_data import load_games
from quality_gate import run_curation_gate

EXCLUDED_GAMES_PATH = Path("data/excluded_games.json")


def _load_excluded() -> set:
    if EXCLUDED_GAMES_PATH.exists():
        try:
            return set(json.loads(EXCLUDED_GAMES_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def _save_excluded(excluded: set) -> None:
    EXCLUDED_GAMES_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXCLUDED_GAMES_PATH.write_text(
        json.dumps(sorted(excluded), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def classify_game(game: dict) -> str:
    """
    Gate dinamico 3-livelli.
    Returns: 'APPROVED' | 'PROBATION' | 'REJECTED'
    """
    rating = game.get("rating") or 0
    # Normalizza rating 0-5 → 0-100
    if 0 < rating <= 5:
        rating = rating * 20

    # totalReviews è None/assente per giochi storici — trattali come "non misurabile"
    total_reviews_raw = game.get("totalReviews")
    total_reviews = total_reviews_raw if isinstance(total_reviews_raw, int) else None

    # Calcola age in giorni
    days_old = 365  # fallback
    release_date = game.get("releaseDate") or game.get("releaseYear")
    if release_date:
        try:
            if isinstance(release_date, int):
                release_dt = datetime(release_date, 1, 1, tzinfo=timezone.utc)
            else:
                for fmt in ("%Y-%m-%d", "%d %b, %Y", "%b %d, %Y", "%Y"):
                    try:
                        release_dt = datetime.strptime(str(release_date)[:10], fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
                else:
                    release_dt = None
            if release_dt:
                days_old = max(0, (datetime.now(timezone.utc) - release_dt).days)
        except Exception:
            pass

    # REJECTED: solo se totalReviews è noto (gioco nuovo ingestato con quel campo)
    # I giochi storici (totalReviews=None) sono già filtrati da quality_gate.py
    if total_reviews is not None:
        if total_reviews < 3:
            return "REJECTED"
        if rating < 70:
            return "REJECTED"

    # PROBATION: gioco nuovo con poche recensioni
    if total_reviews is not None and days_old < 120 and total_reviews < 25:
        return "PROBATION"

    return "APPROVED"


def main():
    catalog = load_games()
    valid, hidden, stats = run_curation_gate(catalog, strict=False, apply=False)

    Path("reports").mkdir(parents=True, exist_ok=True)
    report_file = (
        f"reports/curation_gate_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    )

    # Applica gate dinamico sui giochi passati dal quality gate base
    existing_excluded = _load_excluded()
    newly_rejected: set = set()
    approved_games = []
    probation_count = 0
    approved_count = 0
    rejected_count = 0

    for g in valid:
        verdict = classify_game(g)
        if verdict == "REJECTED":
            rejected_count += 1
            steam_appid = ""
            steam_url = g.get("steamUrl", "")
            if steam_url:
                import re
                m = re.search(r"/app/(\d+)", steam_url)
                if m:
                    steam_appid = m.group(1)
            if steam_appid:
                newly_rejected.add(steam_appid)
            print(f"  🚫 [REJECTED] [{g['id']}] {g['title']} (rating={g.get('rating')}, reviews={g.get('totalReviews',0)})")
        elif verdict == "PROBATION":
            probation_count += 1
            g_out = dict(g)
            g_out["curatedStatus"] = "probation"
            approved_games.append(g_out)
        else:
            approved_count += 1
            approved_games.append(g)

    # Aggiorna excluded_games.json con unione
    all_excluded = existing_excluded | newly_rejected
    _save_excluded(all_excluded)

    # Report
    criticals = [h for h in hidden if h.get("severity") == "critical"]
    expected_blocked = all(
        h.get("reason", "").startswith("blocked_keyword:") for h in criticals
    )
    unexpected_criticals = [
        h for h in criticals if not h.get("reason", "").startswith("blocked_keyword:")
    ]

    report_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "stats": {
            **stats,
            "approved": approved_count,
            "probation": probation_count,
            "dynamic_rejected": rejected_count,
        },
        "hidden_games": hidden,
        "expected_blocked": len(criticals) if expected_blocked else 0,
        "unexpected_criticals": unexpected_criticals,
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    if unexpected_criticals:
        print(f"🚨 CI BLOCKED: {len(unexpected_criticals)} unexpected critical fails:")
        for c in unexpected_criticals:
            print(f"   - {c['id']}: {c['reason']}")
        print(f"   See {report_file}")
        sys.exit(1)

    if stats.get("critical_fails", 0) > 0 and expected_blocked:
        print(
            f"ℹ️  Expected blocks bypassed: {stats['critical_fails']} demo/prototype/test entries filtered (safe to publish)"
        )

    catalog_path = Path("data/catalog.public.v1.json")
    if catalog_path.exists():
        shutil.copy2(catalog_path, catalog_path.with_suffix(".json.bak"))

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "schemaVersion": 1,
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "games": approved_games,
    }
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(
        f"✅ Curation → Approved: {approved_count} | ⏳ Probation: {probation_count} | 🚫 Rejected: {rejected_count}"
    )


if __name__ == "__main__":
    main()
