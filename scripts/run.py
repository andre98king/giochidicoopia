#!/usr/bin/env python3
"""
run.py — Dispatcher thin per la pipeline statica di CoopHubs.net.

Esegue in sequenza i 4 step della pipeline di build statica:
  1. validate-source  Controlla integrità di data/catalog.games.v1.json
  2. build-pages      Genera games/*.html + sitemap*.xml
  3. build-hubs       Genera hub pages IT (giochi-coop-*.html)
  4. verify           Valida output post-build (ID, campi, sitemap)

Uso:
    python scripts/run.py                        # esegui tutti gli step
    python scripts/run.py --dry-run              # mostra comandi senza eseguirli
    python scripts/run.py --step build-pages     # esegui solo uno step
    python scripts/run.py --verbose              # aggiungi timestamp ai log
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

# Root del progetto = parent della cartella scripts/
ROOT = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = ROOT / "scripts"
CATALOG_SOURCE = ROOT / "data" / "catalog.games.v1.json"


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def setup_logging(verbose: bool = False) -> None:
    fmt = "[%(asctime)s] %(message)s" if verbose else "%(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format=fmt, datefmt=datefmt, stream=sys.stdout)


def log_ok(msg: str) -> None:
    logging.info("[OK]   %s", msg)


def log_fail(msg: str) -> None:
    logging.error("[FAIL] %s", msg)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_script(script_name: str, dry_run: bool) -> None:
    """Lancia scripts/<script_name> come sottoprocesso con cwd=ROOT.

    Python aggiunge automaticamente scripts/ a sys.path perché è la directory
    del file — questo preserva i bare import esistenti (import catalog_data, ecc.).
    """
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)]
    cmd_str = " ".join(str(c) for c in cmd)

    if dry_run:
        logging.info("[DRY]  %s", cmd_str)
        return

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        log_fail(f"{script_name} → exit code {result.returncode}")
        sys.exit(1)
    log_ok(script_name)


# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------

def step_validate_source(dry_run: bool) -> None:
    """Step 1 — verifica JSON e non-vuoto di data/catalog.games.v1.json."""
    rel = CATALOG_SOURCE.relative_to(ROOT)

    if dry_run:
        logging.info("[DRY]  [validate-source] json.load(%s)", rel)
        return

    if not CATALOG_SOURCE.exists():
        log_fail(f"validate-source → file non trovato: {rel}")
        sys.exit(1)

    try:
        with open(CATALOG_SOURCE, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        log_fail(f"validate-source → JSON non valido: {exc}")
        sys.exit(1)

    # Supporta sia lista piatta che dict con chiave "games"
    records = data if isinstance(data, list) else data.get("games", [])
    if not records:
        log_fail(f"validate-source → {rel} è vuoto o privo di records")
        sys.exit(1)

    log_ok(f"validate-source → {rel} ({len(records)} records)")


def step_build_pages(dry_run: bool) -> None:
    """Step 2 — genera games/*.html + sitemap*.xml via build_static_pages.py."""
    run_script("build_static_pages.py", dry_run)


def step_build_hubs(dry_run: bool) -> None:
    """Step 3 — genera hub pages IT via build_hub_pages.py."""
    run_script("build_hub_pages.py", dry_run)


def step_verify(dry_run: bool) -> None:
    """Step 4 — verifica post-build via validate_catalog.py."""
    run_script("validate_catalog.py", dry_run)


# ---------------------------------------------------------------------------
# Step registry — ordine = ordine di esecuzione
# ---------------------------------------------------------------------------

STEPS: dict[str, tuple[str, object]] = {
    "validate-source": ("Validazione sorgente JSON",            step_validate_source),
    "build-pages":     ("Generazione games/*.html + sitemap",   step_build_pages),
    "build-hubs":      ("Generazione hub pages IT",             step_build_hubs),
    "verify":          ("Verifica post-build",                  step_verify),
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    epilog_lines = ["Step disponibili:"] + [
        f"  {name:<20s} {desc}" for name, (desc, _) in STEPS.items()
    ]
    parser = argparse.ArgumentParser(
        description="Pipeline statica CoopHubs — dispatcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(epilog_lines),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Stampa i comandi che verrebbero eseguiti senza lanciarli",
    )
    parser.add_argument(
        "--step",
        choices=list(STEPS),
        metavar="NOME",
        help=f"Esegui solo questo step ({', '.join(STEPS)})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Aggiunge timestamp ai messaggi di log",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    if args.dry_run:
        logging.info("=== DRY RUN — nessun comando verrà eseguito ===\n")

    steps_to_run = (
        {args.step: STEPS[args.step]} if args.step else STEPS
    )

    for name, (description, fn) in steps_to_run.items():
        logging.info("--- [%s] %s", name, description)
        fn(args.dry_run)  # type: ignore[call-arg]

    if not args.dry_run:
        log_ok("Pipeline completata.")


if __name__ == "__main__":
    main()
