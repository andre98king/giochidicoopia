#!/usr/bin/env python3
"""
Apply bulk fixes to games.js with backup and validation.

This script reads data/pending_fixes.json and applies corrections to games.js:
- DRY-RUN by default (no --apply flag = no changes)
- Creates automatic backup before any write
- Validates old_value matches current catalog before applying

Usage:
    python3 apply_fixes.py              # Dry-run mode
    python3 apply_fixes.py --apply      # Apply fixes
    python3 apply_fixes.py --apply --input custom_fixes.json  # Custom input
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

import catalog_data


ROOT = Path(__file__).resolve().parent.parent
GAMES_JS = ROOT / "assets" / "games.js"
DATA_DIR = ROOT / "data"
DEFAULT_INPUT = DATA_DIR / "pending_fixes.json"


def backup_games_js(games_js_path: Path) -> Path:
    """Create timestamped backup of games.js."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = games_js_path.with_suffix(f".js.backup.{ts}")
    shutil.copy2(games_js_path, backup_path)
    return backup_path


def validate_fix(game: dict, fix: dict) -> tuple[bool, str]:
    """Validate that old_value matches current catalog value."""
    field = fix["field"]
    old_value = fix.get("old_value")
    current_value = game.get(field)

    if old_value is None and current_value is None:
        return True, "ok"
    if old_value is None or current_value is None:
        return False, f"old_value is {old_value}, current is {current_value}"

    if current_value == old_value:
        return True, "ok"

    return False, f"old_value={old_value} != current={current_value}"


def apply_fixes(
    games: list[dict],
    fixes: list[dict],
    dry_run: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Apply fixes to games list. Returns (applied, skipped)."""
    applied = []
    skipped = []

    for fix in fixes:
        game_id = fix["game_id"]
        field = fix["field"]
        new_value = fix["new_value"]

        game = next((g for g in games if g.get("id") == game_id), None)
        if not game:
            skipped.append(
                {
                    "fix": fix,
                    "reason": "game not found in catalog",
                }
            )
            continue

        valid, reason = validate_fix(game, fix)
        if not valid:
            skipped.append(
                {
                    "fix": fix,
                    "reason": f"old_value mismatch: {reason}",
                    "current_value": game.get(field),
                }
            )
            continue

        if dry_run:
            applied.append(
                {
                    "fix": fix,
                    "action": "would apply",
                }
            )
        else:
            game[field] = new_value
            applied.append(
                {
                    "fix": fix,
                    "action": "applied",
                }
            )

    return applied, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply bulk fixes to games.js with backup and validation"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes to games.js (default: dry-run mode)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input fixes file (default: {DEFAULT_INPUT})",
    )
    args = parser.parse_args()

    input_path = args.input
    if not input_path.is_file():
        print(f"ERROR: Input file not found: {input_path}")
        print(f"Create {input_path} with the following structure:")
        print("""
{
  "fixes": [
    {
      "game_id": 24,
      "field": "maxPlayers",
      "old_value": 65535,
      "new_value": 32,
      "reason": "Factorio wiki: max 32 players"
    }
  ]
}
""")
        return 1

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    fixes = data.get("fixes", [])
    if not fixes:
        print("ERROR: No fixes found in input file")
        return 1

    print(f"Loaded {len(fixes)} fixes from {input_path}")

    if args.apply:
        print("APPLY MODE: Changes will be written to games.js")
    else:
        print("DRY-RUN MODE: No changes will be made. Use --apply to apply.")

    print("\nLoading catalog...")
    featured_id, games = catalog_data.load_legacy_catalog_bundle()
    print(f"  Loaded {len(games)} games")

    applied, skipped = apply_fixes(games, fixes, dry_run=not args.apply)

    print(f"\nResults:")
    print(f"  Applied: {len(applied)}")
    print(f"  Skipped: {len(skipped)}")

    if skipped:
        print("\nSkipped fixes:")
        for s in skipped:
            fix = s["fix"]
            print(f"  - Game {fix['game_id']}, field {fix['field']}: {s['reason']}")

    if not args.apply:
        print("\n=== Dry-Run Summary ===")
        print("Would apply:")
        for a in applied:
            fix = a["fix"]
            print(
                f"  - Game {fix['game_id']}: {fix['field']} = {fix['new_value']} ({fix.get('reason', '')})"
            )
        return 0

    backup_path = backup_games_js(GAMES_JS)
    print(f"\nBackup created: {backup_path}")

    output_path = catalog_data.write_legacy_games_js(games, featured_id)
    print(f"Written to: {output_path}")

    print("\n=== Apply Complete ===")
    print(f"  Applied: {len(applied)} fixes")
    print(f"  Backup: {backup_path.name}")
    print(f"  To restore: mv {backup_path} {GAMES_JS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
