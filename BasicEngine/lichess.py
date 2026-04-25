import requests

EXPLORER_URL = "https://explorer.lichess.ovh/lichess"
MASTERS_URL = "https://explorer.lichess.ovh/masters"
TIMEOUT = 5

_explorer_cache: dict = {}
_masters_cache: dict = {}


def query_explorer(fen, ratings=(2000, 2200), speeds=("blitz", "rapid")):
    key = (fen, ratings, speeds)
    if key in _explorer_cache:
        return _explorer_cache[key]
    params = {
        "fen": fen,
        "ratings": ",".join(str(r) for r in ratings),
        "speeds": ",".join(speeds),
        "moves": 30,
    }
    try:
        r = requests.get(EXPLORER_URL, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        data = None
    _explorer_cache[key] = data
    return data


def query_masters(fen):
    if fen in _masters_cache:
        return _masters_cache[fen]
    try:
        r = requests.get(MASTERS_URL, params={"fen": fen, "moves": 30}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        data = None
    _masters_cache[fen] = data
    return data


def total_games(response):
    if not response:
        return 0
    return response.get("white", 0) + response.get("draws", 0) + response.get("black", 0)
