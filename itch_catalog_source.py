"""
itch_catalog_source.py
======================
Adapter per aggiungere giochi co-op da itch.io al catalogo.
Richiede ITCH_IO_KEY (env var).
"""

from steam_catalog_source import derive_genres


class ItchCatalogSource:
    def __init__(self, api_key: str, fetch_fn, max_games: int = 10):
        self.api_key = api_key
        self.fetch_fn = fetch_fn
        self.max_games = max_games

    def fetch_games(self, existing_itch_urls: set, next_id: int) -> list[dict]:
        queries = [
            'co-op', 'cooperative multiplayer', 'local co-op',
            'online co-op', 'multiplayer indie',
        ]
        all_games = {}
        for q in queries:
            url = f"https://itch.io/api/1/{self.api_key}/search/games?query={q.replace(' ', '+')}"
            data = self.fetch_fn(url) or {}
            for g in data.get('games', []):
                gid = g.get('id')
                if gid and gid not in all_games:
                    all_games[gid] = g

        # Ordina per priorità: giochi con più info disponibili
        candidates = sorted(
            all_games.values(),
            key=lambda g: (len(g.get('short_text') or ''), g.get('id', 0)),
            reverse=True,
        )

        added = []
        for ig in candidates:
            if len(added) >= self.max_games:
                break
            game_url = ig.get('url', '')
            if not game_url or game_url in existing_itch_urls:
                continue
            short_text = ig.get('short_text', '') or ''
            if len(short_text) < 20:
                continue
            title = ig.get('title', '')
            if not title:
                continue

            is_free = (ig.get('min_price', 1) == 0)
            cats = ['indie']
            if is_free:
                cats.append('free')

            added.append({
                'id':             next_id,
                'title':          title,
                'categories':     cats,
                'genres':         derive_genres(cats),
                'coopMode':       ['online'],
                'maxPlayers':     4,
                'crossplay':      False,
                'players':        '2-4',
                'image':          ig.get('cover_url') or ig.get('cover') or '',
                'description':    short_text,
                'description_en': short_text,
                'personalNote':   '',
                'played':         False,
                'steamUrl':       '',
                'epicUrl':        '',
                'itchUrl':        game_url,
                'ccu':            0,
                'trending':       False,
                'rating':         0,
            })
            next_id += 1

        return added
