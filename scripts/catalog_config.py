import os

DELAY = 1.5  # secondi tra richieste API
MAX_NEW_GAMES = 30  # max nuovi giochi per run (SteamSpy)
MAX_EN_FETCH = 30  # max giochi esistenti a cui aggiungere desc EN per run
MIN_CCU_TRENDING = (
    10000  # CCU minimo per badge 🔥 Trending (~top 10% catalogo, ~54 giochi)
)
MAX_ITCH_GAMES = 20  # max giochi itch.io per run (RSS feed)
ITCH_IO_KEY = os.environ.get("ITCH_IO_KEY", "")
IGDB_CLIENT_ID = os.environ.get("IGDB_CLIENT_ID", "")
IGDB_CLIENT_SECRET = os.environ.get("IGDB_CLIENT_SECRET", "")
STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
RAWG_API_KEY = os.environ.get("RAWG_API_KEY", "") or None
MAX_IGDB_DISCOVERY = 30  # max nuovi giochi da IGDB discovery per run
MAX_GOG_GAMES = 10  # max nuovi giochi GOG-only per run
MAX_STEAM_NEW = 20  # max nuovi giochi da Steam new releases per run
MAX_RAWG_DISCOVERY = 20  # max nuovi giochi da RAWG discovery per run

# Tag Steam → categoria sito
TAG_MAP = {
    "Horror": "horror",
    "Psychological Horror": "horror",
    "Survival Horror": "horror",
    "Action": "action",
    "Shooter": "action",
    "FPS": "action",
    "Third-Person Shooter": "action",
    "Beat 'em up": "action",
    "Fighting": "action",
    "Puzzle": "puzzle",
    "Puzzle Platformer": "puzzle",
    "Logic": "puzzle",
    "Local Co-Op": "splitscreen",
    "Split Screen": "splitscreen",
    "Local Multiplayer": "splitscreen",
    "Couch Co-Op": "splitscreen",
    "Shared/Split Screen": "splitscreen",
    "Shared/Split Screen Co-op": "splitscreen",
    "RPG": "rpg",
    "Action RPG": "rpg",
    "JRPG": "rpg",
    "Dungeon Crawler": "rpg",
    "Loot": "rpg",
    "Survival": "survival",
    "Open World Survival Craft": "survival",
    "Building": "factory",
    "Automation": "factory",
    "Colony Sim": "factory",
    "Factory": "factory",
    "Resource Management": "factory",
    "Roguelike": "roguelike",
    "Roguelite": "roguelike",
    "Rogue-lite": "roguelike",
    "Sports": "sport",
    "Racing": "sport",
    "Soccer": "sport",
    "Football": "sport",
    "Strategy": "strategy",
    "Turn-Based Strategy": "strategy",
    "RTS": "strategy",
    "Tower Defense": "strategy",
    "Grand Strategy": "strategy",
    "Tactical": "strategy",
    "Indie": "indie",
}

BLACKLIST_APPIDS = {
    "730",  # CS2 (PvP)
    "1172470",  # Apex Legends (PvP)
    "1938090",  # Call of Duty: Warzone (PvP)
    "431960",  # Wallpaper Engine
    "1091500",  # Cyberpunk 2077 (single player)
    "1245620",  # Elden Ring (NIGHTREIGN è già nel DB)
    "1817070",  # Marvel's Spider-Man
    "2358720",  # Black Myth: Wukong
    # Giochi senza co-op che SteamSpy tagga erroneamente come co-op
    "578080",  # PUBG (battle royale PvP)
    "289070",  # Civilization VI (multiplayer competitivo)
    "8930",  # Civilization V
    "629520",  # Soundpad (tool)
    "1325860",  # VTube Studio (tool)
    "761890",  # Albion Online (MMO PvP)
    "949230",  # Cities: Skylines II (single)
    "1407200",  # World of Tanks (PvP)
    "570940",  # Dark Souls Remastered
    "305620",  # The Long Dark (single)
    "703080",  # Planet Zoo (single)
    "363970",  # Clicker Heroes (idle)
    "1677740",  # Stumble Guys (PvP)
    "386360",  # SMITE (PvP/MOBA)
    "1013320",  # Firestone Idle RPG
    "3070070",  # TCG Card Shop Simulator
    "977950",  # A Dance of Fire and Ice (rhythm)
    "601510",  # Yu-Gi-Oh! Duel Links (card PvP)
    "582160",  # AC Origins (single)
    "1850570",  # Death Stranding (single)
    "805550",  # Assetto Corsa Competizione (racing sim)
    "1244460",  # Jurassic World Evolution 2 (single)
    "203770",  # Crusader Kings II (grand strategy)
    "2651280",  # Spider-Man 2 (single)
    "613100",  # House Flipper 1 (single)
    "1971870",  # Mortal Kombat 1 (fighting PvP)
    "1888160",  # Armored Core VI (single mostly)
    "1066780",  # Transport Fever 2 (single)
    "766570",  # Russian Fishing 4
    "367520",  # Hollow Knight (single player)
    "221380",  # Age of Empires II Retired
    "1128810",  # RISK: Global Domination
    "1645820",  # SurrounDead
    "3400930",  # Guilty as Sock
    "719890",  # Beasts of Bermuda
    "433850",  # Z1 Battle Royale
    "1046930",  # Dota Underlords
    "444090",  # Paladins
    "286690",  # Metro 2033 Redux
    "1237970",  # Titanfall 2
    "311690",  # Enter the Gungeon (no co-op on Steam)
    "883710",  # Resident Evil 2 (single)
    "1196590",  # Resident Evil Village (single mostly)
    "335240",  # Transformice
    "767560",  # War Robots
    "297000",  # Heroes of M&M III HD
    "2688950",  # Planet Coaster 2
    "1238860",  # Battlefield 4
    # Tool / emulatori
    "1118310",  # RetroArch (emulatore, non un gioco)
    # MMO prevalentemente PvP
    "109600",  # Neverwinter (MMO PvP)
    "24200",  # DC Universe Online (MMO)
    # Simulatori con co-op marginale
    "223750",  # DCS World Steam Edition (simulatore militare)
    # Giochi prevalentemente PvP con modalità co-op secondaria
    "1985810",  # Call of Duty: Black Ops Cold War (PvP principale)
    # Rimossi da cross-validation 2026-03-21
    "268500",  # XCOM 2 (multiplayer PvP, no co-op campaign)
    "32470",  # STAR WARS Empire at War (RTS PvP)
    "392160",  # X4: Foundations (single player)
    "12210",  # Grand Theft Auto IV (rimosso da Steam)
    "880940",  # Pummel Party (party PvP)
    "532270",  # Nidhogg 2 (1v1 PvP fighting)
    "1318440",  # Worms Rumble (PvP battle royale)
    # Rimossi per low reviews (< 20 recensioni Steam)
    "1634130",  # Color Escape: VR Coop (10 recensioni)
    "3887470",  # Maid Cafe Coop (44 recensioni, VR niche)
}

# Filtro qualità minima per nuovi giochi — pipeline SteamSpy (trending)
MIN_RATING_NEW = 75  # rating minimo (%) per giochi SteamSpy (aumentato da 65)
MIN_CCU_NEW = 2000  # CCU minimo per candidati SteamSpy (aumentato da 500)

# Filtro qualità per pipeline IGDB/GOG (giochi non necessariamente trending)
# Qui non usiamo CCU perché penalizza: co-op locale, indie di nicchia, giochi vecchi.
# Usiamo invece: recensioni totali Steam come prova di interesse + rating %
MIN_RATING_QUALITY = 70  # rating % minimo (più alto perché non filtra CCU)
MIN_REVIEWS_QUALITY = 100  # recensioni totali Steam minime (pos+neg) (aumentato da 50)
MIN_IGDB_RATING = 65  # IGDB rating (0-100) minimo per giochi senza dati Steam

SKIP_WORDS = [
    "demo",
    " dlc",
    "soundtrack",
    "artbook",
    "playtest",
    "beta",
    "prologue",
    "upgrade pack",
    "season pass",
    "content pack",
    "expansion",
    "bundle",
    "test server",
    "dedicated server",
    "editor",
    "modding",
    "toolkit",
]

# Selezione manuale gioco indie della settimana (Featured)
# Imposta a 0 per usare l\x27algoritmo automatico basato su rating/CCU
FEATURED_OVERRIDE_ID = 180

# Pattern per edizioni vecchie (FIFA 23 quando c\x27è FC 25, NBA 2K23 quando c\x27è 2K25, ecc.)
OLD_EDITION_PATTERNS = [
    (r"FIFA \d+", r"FC \d+"),  # vecchia FIFA → nuova FC
    (r"NBA 2K(\d+)", lambda m: int(m.group(1)) < 25),  # NBA 2K con anno < 25
    (r"F1 (\d+)", lambda m: int(m.group(1)) < 24),  # F1 con anno < 24
    (r"Football Manager (\d+)", lambda m: int(m.group(1)) < 25),
]

# Giochi che Steam/SteamSpy tagga come "Indie" ma NON sono indie
# (studi AA/AAA, publisher grossi, IP di grandi aziende)
NOT_INDIE_APPIDS = {
    "251570",  # 7 Days to Die
    "436150",  # A Way Out
    "346110",  # ARK: Survival Evolved
    "945360",  # Among Us
    "361420",  # Astroneer
    "960090",  # Bloons TD 6
    "291550",  # Brawlhalla
    "221100",  # DayZ
    "435150",  # Divinity: Original Sin 2
    "373420",  # Divinity: Original Sin Enhanced Edition
    "1203620",  # Enshrouded
    "505460",  # Foxhole
    "467710",  # Gang Beasts
    "4000",  # Garry's Mod
    "815370",  # Green Hell
    "219990",  # Grim Dawn
    "581320",  # Insurgency: Sandstorm
    "232090",  # Killing Floor 2
    "899770",  # Last Epoch
    "1129580",  # Medieval Dynasty
    "275850",  # No Man's Sky
    "1623730",  # Palworld
    "1260320",  # Party Animals
    "238960",  # Path of Exile
    "1042710",  # Predecessor
    "252950",  # Rocket League
    "252490",  # Rust
    "526870",  # Satisfactory
    "244850",  # Space Engineers
    "393380",  # Squad
    "985890",  # Streets of Rage 4
    "286160",  # Tabletop Simulator
    "1361510",  # TMNT: Shredder's Revenge
    "690640",  # Trine 4
    "1225560",  # Unravel Two
    "235540",  # Warhammer: End Times - Vermintide
    "552500",  # Warhammer: Vermintide 2
}

# Publisher/developer noti come NON indie (match parziale, lowercase)
NOT_INDIE_PUBLISHERS = {
    "electronic arts",
    "ea ",
    "ubisoft",
    "activision",
    "blizzard",
    "bethesda",
    "square enix",
    "capcom",
    "bandai namco",
    "sega",
    "warner bros",
    "take-two",
    "2k games",
    "2k ",
    "rockstar",
    "epic games",
    "riot games",
    "valve",
    "microsoft",
    "xbox game studios",
    "sony",
    "playstation",
    "tencent",
    "netease",
    "nexon",
    "level infinite",
    "amazon games",
    "focus entertainment",
    "deep silver",
    "thq nordic",
    "embracer",
    "gearbox",
    "curve games",
    "curve digital",
    "paradox interactive",
    "hi-rez",
    "hi rez",
    "grinding gear",
    "digital extremes",
    "psyonix",
    "respawn",
    "innersloth",
    "facepunch",
    "funcom",
    "techland",
    "keen software",
    "new world interactive",
    "offworld industries",
    "stunlock",
    "fatshark",
    "iron gate",
    "hopoo",
    "behaviour interactive",
    "daybreak",
    "jagex",
    "ncsoft",
    "smilegate",
    "pearl abyss",
    "krafton",
    "pubg",
    "supercell",
    "mihoyo",
    "hoyoverse",
    "gaijin",
    "wargaming",
    "coffee stain",
}

# Giochi che SteamSpy tagga come "Free to Play" ma NON sono gratis
NOT_FREE_APPIDS = {
    "346110",  # ARK: Survival Evolved
    "906850",  # Age of Empires III: Definitive Edition
    "945360",  # Among Us
    "361420",  # Astroneer
    "960090",  # Bloons TD 6
    "1240440",  # EA SPORTS FC 25
    "39210",  # FINAL FANTASY XIV Online
    "654310",  # Fishing Planet
    "1293830",  # Forza Horizon 4 — NOTA: è nella lista free perché diventato F2P
    "505460",  # Foxhole
    "467710",  # Gang Beasts
    "815370",  # Green Hell
    "962130",  # Grounded
    "394360",  # Hearts of Iron IV
    "477160",  # Human: Fall Flat
    "594650",  # Hunt: Showdown 1896
    "232090",  # Killing Floor 2
    "238210",  # Magicka 2
    "274190",  # Move or Die
    "1290000",  # PowerWash Simulator
    "648800",  # Raft
    "1174180",  # Red Dead Online
    "393380",  # Squad
    "674940",  # Stick Fight: The Game
    "573090",  # Stormworks: Build and Rescue
    "376210",  # The Isle
    "386940",  # Ultimate Chicken Horse
    "865360",  # We Were Here Together
    "253710",  # theHunter: Call of the Wild
}

# Verifica integrità
MAX_VERIFY = 80  # max giochi da verificare via API per run (rate limit)
MAX_CROSSVAL = 80  # max giochi da cross-validare co-op per run

# Giochi verificati manualmente come co-op (override cross-validation)
# Questi giochi hanno tag Steam/IGDB mancanti ma sono co-op confermati
VERIFIED_COOP_APPIDS = {
    "700330",  # SCP: Secret Laboratory (co-op horror)
    "285900",  # Gang Beasts (co-op + party)
    "1057090",  # Trine 4: The Nightmare Prince (co-op puzzle platformer)
    "416200",  # Full Metal Furies (co-op action RPG)
    "1073980",  # Boomerang Fu (co-op + party)
    "2527950",  # Moving Out 2 (co-op moving sim)
    "1272790",  # Devour (co-op horror)
    "440",  # Team Fortress 2 (MvM co-op mode)
    "505460",  # Foxhole (team-based co-op warfare)
}

# Publisher che pubblicano SOLO giochi PvP/MOBA (non co-op)
PvP_ONLY_PUBLISHERS = {
    "riot games",
    "tencent games", 
    "nexon",
    "smilegate",
    "krafton",
    "valve",
    "supercell",
}

# Giochi specifici che sono PvP-only nonostante i tag
PvP_ONLY_GAMES = {
    "574421",  # VALORANT
    "570",     # Dota 2
    "730",     # Counter-Strike 2
    "578080",  # PUBG
    "1162720", # Lost Ark
    "440900",  # Legends of Runeterra
}

# Funzione helper per verificare se un gioco è genuinamente co-op basato sulle categorie Steam
def is_true_coop(cat_ids: set[int]) -> bool:
    """
    Un gioco è co-op solo se HA categorie co-op E NON è solo PvP.
    Questo previene falsi positivi da giochi PvP-only che hanno tag co-op generici.
    """
    # Categorie Steam che indicano co-op autentico
    COOP_ONLY_CATS = {9, 38, 39, 24, 48, 44}  # Co-op, RPG, etc. con co-op
    # Categorie Steam che indicano solo PvP/MOBA
    SOLO_PVP_CATS = {49, 36, 37, 47}  # PvP categories
    
    has_coop = bool(cat_ids & COOP_ONLY_CATS)
    has_only_pvp = bool(cat_ids & SOLO_PVP_CATS) and not has_coop
    return has_coop and not has_only_pvp
