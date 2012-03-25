import compute_stats
import simplejson

def ReadGameNos(fn):
    raw_games = simplejson.load(open(fn, 'r'))
    games = map(compute_stats.Game, raw_games)
    return [g.GameId() for g in games]

def ReadGameNosSet(fn):
    ret = set()
    raw_games = simplejson.load(open(fn, 'r'))
    for g in raw_games:
        ret.add(compute_stats.Game(g).GameId())
    return ret
