import compute_stats
import simplejson

def ReadGameNos(fn):
    raw_games = compute_stats.simplejson.load(open(fn, 'r'))
    games = map(compute_stats.Game, raw_games)
    return [g.GameId() for in games]
