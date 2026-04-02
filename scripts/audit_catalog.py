#!/usr/bin/env python3
"""
Audit & Quality Improvement for Game Catalog Database.

Validates schema, calculates quality metrics, flags issues, and optionally applies safe fixes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import catalog_data


REPORT_DIR = Path("reports")
DATA_DIR = Path("data")
BACKUP_SUFFIX = ".bak"

REQUIRED_FIELDS = ["id", "title", "categories", "coopMode", "players"]
OPTIONAL_FIELDS = [
    "description",
    "description_en",
    "image",
    "steamUrl",
    "releaseYear",
    "rating",
    "ccu",
    "trending",
    "crossplay",
    "maxPlayers",
    "igUrl",
    "igDiscount",
    "gbUrl",
    "gbDiscount",
    "gsUrl",
    "gsDiscount",
    "kgUrl",
    "kgDiscount",
    "k4gUrl",
    "k4gDiscount",
    "gmvUrl",
    "gmvDiscount",
    "gmgUrl",
    "gmgDiscount",
    "gogUrl",
    "epicUrl",
    "itchUrl",
    "personalNote",
    "played",
    "mini_review_it",
    "mini_review_en",
]


def load_catalog() -> list[dict]:
    """Load the public catalog."""
    catalog_path = DATA_DIR / "catalog.public.v1.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "games" in data:
        return data["games"]
    return data


def save_catalog(games: list[dict]) -> None:
    """Save the catalog with backup."""
    catalog_path = DATA_DIR / "catalog.public.v1.json"
    if catalog_path.exists():
        backup_path = catalog_path.with_suffix(f".json{BACKUP_SUFFIX}")
        shutil.copy2(catalog_path, backup_path)
        print(f"  Backup created: {backup_path}")
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {catalog_path}")


def validate_field_types(game: dict, idx: int) -> list[str]:
    """Validate field types match expected schema."""
    issues = []
    if not isinstance(game.get("id"), int):
        issues.append(f"id: expected int, got {type(game.get('id')).__name__}")
    if "title" in game and not isinstance(game["title"], str):
        issues.append(f"title: expected str, got {type(game['title']).__name__}")
    if "categories" in game and not isinstance(game["categories"], list):
        issues.append(
            f"categories: expected list, got {type(game['categories']).__name__}"
        )
    if "coopMode" in game and not isinstance(game["coopMode"], list):
        issues.append(f"coopMode: expected list, got {type(game['coopMode']).__name__}")
    return issues


def check_required_fields(game: dict) -> list[str]:
    """Check all required fields are present and non-empty."""
    issues = []
    for field in REQUIRED_FIELDS:
        if field not in game:
            issues.append(f"missing required field: {field}")
        elif not game[field]:
            issues.append(f"empty required field: {field}")
    return issues


def check_description_quality(game: dict) -> list[str]:
    """Check description length and quality."""
    issues = []
    for field in ["description", "description_en"]:
        if field in game and game[field]:
            length = len(game[field])
            if length < 30:
                issues.append(f"{field}: too short ({length} chars)")
            elif length > 500:
                issues.append(f"{field}: too long ({length} chars)")
    return issues


def check_url_validity(game: dict) -> list[str]:
    """Check URL fields are valid."""
    issues = []
    url_fields = ["steamUrl", "gogUrl", "epicUrl", "itchUrl", "igUrl", "gbUrl"]
    for field in url_fields:
        if field in game and game[field]:
            url = game[field]
            if not url.startswith(("http://", "https://")):
                issues.append(f"{field}: missing https:// prefix")
            if url.startswith("https://") and len(url) < 20:
                issues.append(f"{field}: suspiciously short URL")
    return issues


def check_tags_normalization(game: dict) -> list[str]:
    """Check tags are normalized (lowercase, no duplicates, sorted)."""
    issues = []
    list_fields = ["categories", "genres"]
    for field in list_fields:
        if field in game and isinstance(game[field], list):
            tags = game[field]
            normalized = [t.strip().lower() for t in tags if t]
            if len(normalized) != len(set(normalized)):
                issues.append(f"{field}: contains duplicates")
            if tags != sorted(tags, key=str.lower):
                issues.append(f"{field}: not sorted alphabetically")
            if any(t != t.strip() for t in tags):
                issues.append(f"{field}: contains leading/trailing whitespace")
    return issues


def check_title_quality(game: dict) -> list[str]:
    """Check title length and encoding."""
    issues = []
    if "title" in game and game["title"]:
        title = game["title"]
        if len(title) < 2:
            issues.append("title: too short")
        if len(title) > 150:
            issues.append(f"title: too long ({len(title)} chars)")
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", title):
            issues.append("title: contains non-printable characters")
    return issues


def check_language_gap(game: dict) -> list[str]:
    """Check for IT/EN field gaps."""
    issues = []
    it_fields = ["description", "mini_review_it"]
    en_fields = ["description_en", "mini_review_en"]

    for it_field, en_field in zip(it_fields, en_fields):
        has_it = it_field in game and game[it_field]
        has_en = en_field in game and game[en_field]
        if has_it and not has_en:
            issues.append(f"missing {en_field} (IT present)")
        elif has_en and not has_it:
            issues.append(f"missing {it_field} (EN present)")
    return issues


def check_duplicates(games: list[dict]) -> dict:
    """Find duplicate IDs and titles."""
    seen_ids = {}
    seen_titles = {}
    duplicates = {"id": [], "title": []}

    for game in games:
        gid = game.get("id")
        title = game.get("title", "").lower().strip()

        if gid in seen_ids:
            duplicates["id"].append(
                {"id": gid, "games": [seen_ids[gid], game.get("title")]}
            )
        else:
            seen_ids[gid] = game.get("title")

        if title in seen_titles:
            duplicates["title"].append(
                {"title": game.get("title"), "ids": [seen_titles[title], gid]}
            )
        else:
            seen_titles[title] = gid

    return duplicates


def audit_game(game: dict, idx: int) -> dict:
    """Run all audits on a single game."""
    issues = {
        "type_errors": validate_field_types(game, idx),
        "required_fields": check_required_fields(game),
        "description_quality": check_description_quality(game),
        "url_validity": check_url_validity(game),
        "tags_normalization": check_tags_normalization(game),
        "title_quality": check_title_quality(game),
        "language_gap": check_language_gap(game),
    }

    all_issues = []
    for category, items in issues.items():
        all_issues.extend(items)

    return {
        "game_id": game.get("id"),
        "title": game.get("title"),
        "issues": all_issues,
        "issue_count": len(all_issues),
        "by_category": issues,
    }


def calculate_metrics(audits: list[dict], total_games: int) -> dict:
    """Calculate aggregate quality metrics."""
    games_with_issues = sum(1 for a in audits if a["issue_count"] > 0)
    total_issues = sum(a["issue_count"] for a in audits)

    categories = {
        "type_errors": 0,
        "required_fields": 0,
        "description_quality": 0,
        "url_validity": 0,
        "tags_normalization": 0,
        "title_quality": 0,
        "language_gap": 0,
    }

    for audit in audits:
        for cat, issues in audit["by_category"].items():
            categories[cat] += len(issues)

    return {
        "total_games": total_games,
        "games_with_issues": games_with_issues,
        "games_clean": total_games - games_with_issues,
        "total_issues": total_issues,
        "issues_by_category": categories,
        "completion_rate": round(
            (total_games - games_with_issues) / total_games * 100, 1
        ),
    }


def apply_safe_fixes(game: dict) -> dict:
    """Apply low-risk fixes to a game record."""
    fixed = game.copy()
    changes = []

    if "title" in fixed and fixed["title"]:
        if fixed["title"] != fixed["title"].strip():
            fixed["title"] = fixed["title"].strip()
            changes.append("title: stripped whitespace")
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", fixed["title"])
        if cleaned != fixed["title"]:
            fixed["title"] = cleaned
            changes.append("title: removed non-printable chars")

    for field in ["description", "description_en"]:
        if field in fixed and fixed[field]:
            if fixed[field] != fixed[field].strip():
                fixed[field] = fixed[field].strip()
                changes.append(f"{field}: stripped whitespace")
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", fixed[field])
            if cleaned != fixed[field]:
                fixed[field] = cleaned
                changes.append(f"{field}: removed non-printable chars")

    for field in ["categories", "genres"]:
        if field in fixed and isinstance(fixed[field], list):
            normalized = [t.strip().lower() for t in fixed[field] if t]
            unique = list(dict.fromkeys(normalized))
            unique.sort(key=str.lower)
            if unique != fixed[field]:
                fixed[field] = unique
                changes.append(f"{field}: normalized, deduped, sorted")

    for url_field in ["steamUrl", "gogUrl", "epicUrl", "itchUrl"]:
        if url_field in fixed and fixed[url_field]:
            url = fixed[url_field].strip()
            if not url.startswith(("http://", "https://")):
                fixed[url_field] = "https://" + url
                changes.append(f"{url_field}: added https:// prefix")
            elif url.endswith("/"):
                fixed[url_field] = url.rstrip("/")
                changes.append(f"{url_field}: removed trailing slash")

    return fixed, changes


def generate_report(
    audits: list[dict], metrics: dict, duplicates: dict, output_path: Path
) -> None:
    """Generate JSON and CSV reports."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "generated": date.today().isoformat(),
        "metrics": metrics,
        "duplicates": duplicates,
        "games": audits,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  JSON report: {output_path}")

    csv_path = output_path.with_suffix(".csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["game_id", "title", "issue_count", "issues"])
        for audit in audits:
            writer.writerow(
                [
                    audit["game_id"],
                    audit["title"][:50] if audit["title"] else "",
                    audit["issue_count"],
                    "; ".join(audit["issues"])[:200],
                ]
            )
    print(f"  CSV report: {csv_path}")


def print_summary(metrics: dict, duplicates: dict) -> None:
    """Print audit summary to console."""
    print("\n" + "=" * 60)
    print("CATALOG QUALITY AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total games:     {metrics['total_games']}")
    print(f"Clean games:    {metrics['games_clean']} ({metrics['completion_rate']}%)")
    print(f"Games w/issues: {metrics['games_with_issues']}")
    print(f"Total issues:   {metrics['total_issues']}")
    print()
    print("Issues by category:")
    for cat, count in metrics["issues_by_category"].items():
        if count > 0:
            print(f"  {cat}: {count}")

    if duplicates["id"]:
        print(f"\nDuplicate IDs: {len(duplicates['id'])}")
    if duplicates["title"]:
        print(f"Duplicate titles: {len(duplicates['title'])}")


def main():
    parser = argparse.ArgumentParser(description="Audit game catalog quality")
    parser.add_argument(
        "--report-only", action="store_true", help="Only generate report, no fixes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without applying",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply safe fixes to catalog"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed issues per game"
    )
    args = parser.parse_args()

    if args.apply and not (args.dry_run or args.report_only):
        print(
            "⚠️  Running with --apply: fixes will be written to catalog.public.v1.json"
        )
        print("    A backup will be created first.")

    print("Loading catalog...")
    games = load_catalog()
    print(f"Loaded {len(games)} games")

    print("Running audits...")
    audits = [audit_game(game, idx) for idx, game in enumerate(games)]
    metrics = calculate_metrics(audits, len(games))
    duplicates = check_duplicates(games)

    print_summary(metrics, duplicates)

    today = date.today().strftime("%Y%m%d")
    report_path = REPORT_DIR / f"quality_audit_{today}.json"
    generate_report(audits, metrics, duplicates, report_path)

    if args.report_only:
        print("\nReport-only mode: no fixes applied")
        return

    if args.dry_run:
        print("\n--- DRY RUN: Safe fixes that would be applied ---")
        fixable = 0
        for audit in audits:
            if audit["issue_count"] > 0:
                game = games[audit["game_id"] - 1]
                fixed, changes = apply_safe_fixes(game.copy())
                if changes:
                    fixable += 1
                    print(f"  Game {audit['game_id']}: {audit['title'][:40]}")
                    for change in changes:
                        print(f"    + {change}")
        print(f"\nWould fix {fixable} games")
        return

    if args.apply:
        print("\n--- Applying safe fixes ---")
        fixed_games = []
        total_changes = 0
        for game in games:
            fixed, changes = apply_safe_fixes(game)
            fixed_games.append(fixed)
            if changes:
                total_changes += 1
                if args.verbose:
                    print(f"  Game {game['id']}: {game['title'][:40]}")
                    for change in changes:
                        print(f"    + {change}")

        save_catalog(fixed_games)
        print(f"\nFixed {total_changes} games")


if __name__ == "__main__":
    main()
