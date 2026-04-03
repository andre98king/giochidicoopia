#!/usr/bin/env python3
"""
Curation Gate Runner — estratto dalla CI per esecuzione locale e CI.

Esegue il quality gate sul catalogo giochi, filtra entries a bassa qualità,
esporta report e genera il catalogo pubblico.
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from catalog_data import load_games
from quality_gate import run_curation_gate


def main():
    catalog = load_games()
    valid, hidden, stats = run_curation_gate(catalog, strict=False, apply=False)

    Path("reports").mkdir(parents=True, exist_ok=True)
    report_file = (
        f"reports/curation_gate_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    )

    criticals = [h for h in hidden if h.get("severity") == "critical"]
    expected_blocked = all(
        h.get("reason", "").startswith("blocked_keyword:") for h in criticals
    )
    unexpected_criticals = [
        h for h in criticals if not h.get("reason", "").startswith("blocked_keyword:")
    ]

    report_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "stats": stats,
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
        "games": valid,
    }
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(
        f"✅ Catalogo filtrato: {stats['valid']} validi, {stats['hidden']} nascosti, {stats['critical_fails']} bloccati"
    )


if __name__ == "__main__":
    main()
