#!/usr/bin/env python3
"""
Cleanup catalog.games.v1.json — rimuove campi duplicati e inutilizzati.
Campi rimossi:
  - descriptions: duplicato di description + description_en
  - taxonomy: duplicato di categories + genres
  - capabilities: duplicato di coopMode, players, maxPlayers, crossplay
  - signals: duplicato di ccu, trending, rating
  - genres: inutilizzato (usiamo categories)
  - slug: inutilizzato
  - isFeaturedIndie: inutilizzato
  - editorial: inutilizzato
  - externalIds: inutilizzato
  - sourceMeta: inutilizzato
  - storefronts: inutilizzato
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
MASTER_PATH = ROOT / "data" / "catalog.games.v1.json"
BACKUP_PATH = ROOT / "data" / "catalog.games.v1.json.bak.v1.2"

FIELDS_TO_REMOVE = {
    "descriptions",
    "taxonomy",
    "capabilities",
    "signals",
    "genres",
    "slug",
    "isFeaturedIndie",
    "editorial",
    "externalIds",
    "sourceMeta",
    "storefronts",
}


def main():
    if not MASTER_PATH.exists():
        print(f"❌ Master non trovato: {MASTER_PATH}")
        sys.exit(1)

    with open(MASTER_PATH) as f:
        data = json.load(f)

    games = data.get("games", data) if isinstance(data, dict) else data
    original_count = len(games)
    original_size = MASTER_PATH.stat().st_size

    removed_counts = {f: 0 for f in FIELDS_TO_REMOVE}
    for game in games:
        for field in FIELDS_TO_REMOVE:
            if field in game:
                del game[field]
                removed_counts[field] += 1

    # Write back
    if isinstance(data, dict):
        data["games"] = games
    with open(MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    new_size = MASTER_PATH.stat().st_size

    print(f"✅ Pulito {original_count} giochi")
    print(f"   Dimensione: {original_size/1024:.0f}KB → {new_size/1024:.0f}KB (-{(original_size-new_size)/1024:.0f}KB)")
    print(f"\n   Campi rimossi:")
    for field, count in sorted(removed_counts.items()):
        if count > 0:
            print(f"     - {field}: {count}/{original_count} giochi")

    # Update backup too for consistency
    import shutil
    shutil.copy2(MASTER_PATH, BACKUP_PATH)
    print(f"\n✅ Backup aggiornato: {BACKUP_PATH.name}")


if __name__ == "__main__":
    main()
