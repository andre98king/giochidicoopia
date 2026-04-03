#!/usr/bin/env python3
"""
SEO Content Generator — thin content expander + JSON-LD builder.

  generate_game_description(game, lang) → <div class="game-section game-expanded">
  generate_json_ld(game, page_url_val, lang) → JSON payload string for {jsonld} placeholder
"""
from __future__ import annotations

import hashlib
import html
import json
import re


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


_COOP_LABELS_IT = {"online": "cooperativa online", "local": "cooperativa locale", "sofa": "split-screen"}
_COOP_LABELS_EN = {"online": "online co-op", "local": "local co-op", "sofa": "split-screen"}

_CAT_LABELS_IT = {
    "action": "azione", "rpg": "RPG", "survival": "sopravvivenza", "shooter": "sparatutto",
    "puzzle": "rompicapo", "strategy": "strategia", "platformer": "platform", "horror": "horror",
    "adventure": "avventura", "sports": "sport", "racing": "gare", "simulation": "simulazione",
    "fighting": "picchiaduro", "sandbox": "sandbox", "indie": "indie",
    "free": "free-to-play", "mmo": "MMO",
}
_CAT_LABELS_EN = {
    "action": "action", "rpg": "RPG", "survival": "survival", "shooter": "shooter",
    "puzzle": "puzzle", "strategy": "strategy", "platformer": "platformer", "horror": "horror",
    "adventure": "adventure", "sports": "sports", "racing": "racing", "simulation": "simulation",
    "fighting": "fighting", "sandbox": "sandbox", "indie": "indie",
    "free": "free-to-play", "mmo": "MMO",
}

_CTA_IT = [
    "Se ami i giochi cooperativi, questo titolo merita una prova con i tuoi compagni di avventura.",
    "Un'ottima scelta per chi cerca un gioco da condividere con amici, sia online che in locale.",
    "Perfetto per sessioni in compagnia: la cooperazione è il cuore di questa esperienza.",
]
_CTA_EN = [
    "If you enjoy co-op games, this title is definitely worth trying with your gaming companions.",
    "A great choice for those looking for a game to share with friends, online or locally.",
    "Perfect for group gaming sessions: cooperation is at the heart of this experience.",
]


def generate_game_description(game: dict, lang: str = "it") -> str:
    """
    Generate a semantic HTML expanded description block (~130-170 words).
    Output is fully deterministic from game fields; seed = hashlib.md5(game_id).
    """
    gid = str(game.get("id", "0"))
    seed = int(hashlib.md5(gid.encode()).hexdigest(), 16)

    title = game.get("title", "")
    base_desc = game.get("description_en" if lang == "en" else "description") or game.get("description", "")

    coop_modes = game.get("coopMode") or []
    categories = game.get("categories") or []
    players = game.get("players") or "1-4"
    rating = game.get("rating") or 0
    release_year = game.get("releaseYear") or 0

    coop_labels = _COOP_LABELS_EN if lang == "en" else _COOP_LABELS_IT
    cat_labels   = _CAT_LABELS_EN  if lang == "en" else _CAT_LABELS_IT

    coop_str = ", ".join(coop_labels.get(m, m) for m in coop_modes) or ("co-op" if lang == "en" else "cooperativa")
    cat_str  = ", ".join(cat_labels.get(c, c) for c in categories[:3])

    parts = []

    # 1. Base description
    if base_desc:
        parts.append('<p class="game-expanded-desc">' + _esc(base_desc) + "</p>")

    # 2. Co-op features
    if lang == "en":
        p = _esc(title) + " supports " + _esc(coop_str) + " for " + _esc(players) + " players. "
        if "online" in coop_modes and ("local" in coop_modes or "sofa" in coop_modes):
            p += "Play online with friends or gather locally on the same screen. "
        elif "online" in coop_modes:
            p += "Team up online for a shared adventure. "
        elif "local" in coop_modes or "sofa" in coop_modes:
            p += "Gather friends for local or split-screen cooperative play. "
        p += "Cooperative mechanics are central to the experience, making each session unique."
    else:
        p = _esc(title) + " supporta la modalità " + _esc(coop_str) + " per " + _esc(players) + " giocatori. "
        if "online" in coop_modes and ("local" in coop_modes or "sofa" in coop_modes):
            p += "Puoi giocare sia online con gli amici che in locale sullo stesso schermo. "
        elif "online" in coop_modes:
            p += "Unisciti agli amici online per un'avventura condivisa. "
        elif "local" in coop_modes or "sofa" in coop_modes:
            p += "Raduna gli amici per una sessione cooperativa in locale o in split-screen. "
        p += "Le meccaniche cooperative sono centrali nell'esperienza, rendendo ogni sessione unica."
    parts.append("<p>" + p + "</p>")

    # 3. Genre + rating + release year
    if cat_str:
        if lang == "en":
            g = "Categorized as " + _esc(cat_str) + ", " + _esc(title) + " offers a blend of gameplay styles for co-op enthusiasts. "
            g += ("Released in " + str(release_year) + ", it " if release_year > 0 else "It ")
            if rating >= 85:
                g += "has been very well received by players and critics alike."
            elif rating >= 70:
                g += "has received positive reviews from the community."
            else:
                g += "continues to attract co-op players looking for new experiences."
        else:
            g = "Catalogato come " + _esc(cat_str) + ", " + _esc(title) + " offre un mix di generi adatto agli appassionati di giochi cooperativi. "
            g += ("Rilasciato nel " + str(release_year) + ", " if release_year > 0 else "")
            if rating >= 85:
                g += "ha ricevuto ottime recensioni da giocatori e critica."
            elif rating >= 70:
                g += "ha ottenuto recensioni positive dalla community."
            else:
                g += "continua ad attrarre giocatori co-op in cerca di nuove esperienze."
        parts.append("<p>" + g + "</p>")

    # 4. CTA (variant chosen by game_id seed)
    cta_pool = _CTA_EN if lang == "en" else _CTA_IT
    parts.append("<p>" + cta_pool[seed % len(cta_pool)] + "</p>")

    return (
        '<div class="game-section game-expanded" style="margin-top:20px">'
        + "".join(parts)
        + "</div>"
    )


def generate_json_ld(game: dict, page_url_val: str, lang: str = "it") -> str:
    """
    Build the VideoGame JSON-LD payload (string, no surrounding <script> tags).
    Drop-in replacement for the inline video_game_json block in build_static_pages.py.
    Feed the return value directly into the {jsonld} placeholder via safe_template().
    """
    coop_modes = game.get("coopMode") or []
    play_modes: list[str] = ["SinglePlayer"]
    if "online" in coop_modes:
        play_modes += ["CoOp", "MultiPlayer"]
    if "local" in coop_modes or "sofa" in coop_modes:
        if "CoOp" not in play_modes:
            play_modes.append("CoOp")

    players_str = game.get("players") or "1-4"
    players_parts = players_str.replace(" ", "").split("-")
    try:
        players_min = int(players_parts[0])
        players_max = int(players_parts[-1])
    except (ValueError, IndexError):
        players_min, players_max = 1, 4

    image = game.get("image") or ""
    desc = (
        game.get("description_en" if lang == "en" else "description")
        or game.get("description", "")
    )

    schema: dict = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": game["title"],
        "url": page_url_val,
        "description": desc,
        "image": image,
        "genre": game.get("categories") or [],
        "gamePlatform": "PC",
        "operatingSystem": "Windows",
        "applicationCategory": "Game",
        "numberOfPlayers": {
            "@type": "QuantitativeValue",
            "minValue": players_min,
            "maxValue": players_max,
        },
        "playMode": play_modes,
    }

    if game.get("releaseYear") and game["releaseYear"] > 0:
        schema["datePublished"] = str(game["releaseYear"])

    if game.get("rating") and game["rating"] > 0:
        agg: dict = {
            "@type": "AggregateRating",
            "ratingValue": game["rating"],
            "bestRating": 100,
            "worstRating": 0,
        }
        if game.get("totalReviews") and game["totalReviews"] > 0:
            agg["ratingCount"] = game["totalReviews"]
        schema["aggregateRating"] = agg

    if game.get("steamUrl"):
        schema["offers"] = {
            "@type": "Offer",
            "url": game["steamUrl"],
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
        }

    return json.dumps(schema, ensure_ascii=False)
