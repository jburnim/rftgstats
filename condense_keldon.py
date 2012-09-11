import re
import copy
import gzip
import os
import simplejson as json

import compute_stats
from deck_info import DeckInfo
import tableau_scorer

import string
from name_handler import name_handler

EXP_DICT = {
    'Base' : 0,
    'TGS' : 1,
    'RvI' : 2,
    'BoW' : 3,
    }

GOAL_DICT = {
    'Propaganda Edge' : 'Most Rebel Military Worlds',
    'Research Leader' : 'Most Explore Powers',
    'Greatest Military' : 'Most Military',
    'Galactic Prestige' : 'Most Prestige',
    'Production Leader' : 'Most Prod worlds',
    'Largest Industry' : 'Most Rares or Novelties',
    'Greatest Infrastructure' : 'Most Developments',
    'Prosperity Lead' : 'Most Consume Powers',
    'Overlord Discoveries' : 'First 3 aliens',
    'Peace/War Leader' : 'First peace / war',
    'Galactic Standing' : 'First 2 Prestige + 3 vps',
    'Expansion Leader' : 'First 8 Tableau',
    'Galactic Status' : 'First 6 pt dev',
    'Military Influence' : 'First military influence',
    'Innovation Leader' : 'First all phase powers',
    'Galactic Standard of Living' : 'First 5 vps',
    'Galactic Riches' : 'First 4 Prod goods',
    'Uplift Knowledge' : 'First 3 Uplift',
    'Budget Surplus' : 'First discard',
    'System Diversity' : 'First all worlds',
    
    }

# convert the naming convention on keldon to the one already defined in card_attributes3.csv
def RenameCard(card): 
    if card == 'Galactic Survey: SETI':
        return 'Galactic Survey SETI'
    if card == 'The Last of the Uplift Gnarssh':
        return 'Last Uplift Gnarssh'
    if card == 'R&D Crash Program':
        return 'R and D Crash Program'
    if card == 'Pan-Galactic League':
        return 'Pan Galactic League'
    if card == 'Earth\'s Lost Colony':
        return 'Earths Lost Colony'
    if card == 'Bio-Hazard Mining World':
        return 'Bio-hazard Mining World'
    return card

chSearch = re.compile("(\d+) VP in chips")
prSearch = re.compile("(\d+) prestige")
poSearch = re.compile("(\d+) total VP")
gSearch = re.compile("claims (.+) goal\.")

def ParsePlayerNode(player_node, expansion):
    ret = {}
    # the hand is not stored
    ret['hand'] = 0
    # goods not stored
    ret['goods'] = 0
    # could perhaps get the goals, but that would be more work
    #ret['chips'] = int(re.search( r"(\d+) VP in chips", player_node ).group(1))
    ret['chips'] = int(chSearch.search( player_node ).group(1))
    if expansion >= EXP_DICT['BoW']:
        #ret['prestige'] = int(re.search( r"(\d+) prestige", player_node ).group(1))
        ret['prestige'] = int(prSearch.search( player_node ).group(1))

    ret['cards'] = []

    for card_dat in player_node.split('alt="')[1:]:
        ret['cards'].append( RenameCard(card_dat.split('"')[0]) )

    #ret['points'] = int(re.search( r"(\d+) total VP", player_node ).group(1))
    ret['points'] = int(poSearch.search( player_node ).group(1))
    if ret['points'] < 4:
        print 'very few points in tableau'
        return None
    ret['name'] = player_node.split('</h3>')[0]
    if len(ret['name']) > 120:
        print "Suspiciously long name:", name
        return None
    return ret

def ParsePlayerRow(row, expansion):
    ret = {}
    # will only get minimal data, but enough to use in rankings
    ret['hand'] = 0
    ret['goods'] = 0
    ret['cards'] = []
    if expansion >= EXP_DICT['BoW']:
        ret['prestige'] = 0
    
    entries = row.split('<td>')
    ret['name'] = entries[1].split('</td>')[0][1:-1]
    ret['points'] = int(entries[2].split('</td>')[0][1:-1])
    ret['chips'] = ret['points'] # should we do this for consistency, or set it to 0 so it doesn't mess up any stats about number of chips?
    return ret

def ParseGame(game_node, game_id):
    game_dict = {'player_list': []}

    parts = game_node.split('<h3>')

    header = parts[0]
    exp_short = header.split('Expansion</th><td> ')[1].split()[0]
    game_dict['expansion'] = EXP_DICT[exp_short]


    table = header.split('<tbody>\n')[1].split('\n</tbody>')[0].split('<tr')[1:]
    winners = []
    for row in table:
        if row.split('<td>')[3].split('</td>')[0] == 'Yes':
            winners.append(row.split('<td>')[1].split('</td>')[0][1:-1])
    game_dict['winners'] = winners
    game_dict['game_id'] = 'http://www.keldon.net/rftg/showgame.cgi?gid='+str(game_id)
    game_dict['advanced'] = ( header.find('(advanced)') != -1 ) and len(table) == 2

    if len(parts) == 1:
        for row in table:
            game_dict['player_list'].append(ParsePlayerRow(row, game_dict['expansion']))
        return game_dict
    
    for player_part in parts[1:]:
        player_dict = ParsePlayerNode(player_part, game_dict['expansion'])
        if not player_dict:
            print 'Could not parse player', player_part[:10], 'at game', game_id
            return None
        #player_result = compute_stats.PlayerResult(copy.deepcopy(player_dict))
        game_dict['player_list'].append(player_dict)

    if len(game_dict['player_list']) <= 1:
        print 'only one player?'
        return None

    # this is only an approximate extraction of the goals
    game_log = game_node.split('<pre>')[1]
    goals = []
    for line in game_log.split('\n'):
        #g = re.search( r"claims (.+) goal\.", line )
        g = gSearch.search( line )
        if g:
            goal = GOAL_DICT[g.group(1)]
            if goal not in goals:
                goals.append(goal)
    if goals:
        game_dict['goals'] = goals
                         
    #g = compute_stats.Game(copy.deepcopy(dict(game_dict)))
    return game_dict

if __name__ == '__main__':
    games = []
    for fn in os.listdir('keldon'):
        #try:
            full_fn = 'keldon/' + fn
            contents = open(full_fn, 'r').read()

            g = ParseGame(contents, int(fn))
            if g:
                #print 'success'
                games.append(g)
        #except Exception, e:
        #    print full_fn, e

    def ExtractId(game):
        return int(''.join(filter(lambda c: c in string.digits,
                                  game['game_id'])))
        
    games.sort(key = ExtractId)
    try:
        oldGames = json.load(open('condensed_keldon.json', 'r'))
    except:
        print "Warning, old condensed data not found or corrupt"
        oldGames = []
    newGames = []
    gIndex = 0
    for g in oldGames:
        gid = ExtractId(g)
        while gIndex < len(games) and ExtractId(games[gIndex]) < gid:
            newGames.append(games[gIndex])
            gIndex += 1
        if gid == ExtractId(games[gIndex]):
            newGames.append(games[gIndex])
            gIndex += 1
            continue
        newGames.append(g)
    while gIndex < len(games):
        newGames.append(games[gIndex])
        gIndex += 1
    print len(games), len(oldGames), len(newGames)

    json.dump(newGames, open('condensed_keldon.json', 'w'), indent=True)
    gzip.GzipFile('condensed_keldon.json.gz', 'w').write(
        open('condensed_keldon.json', 'r').read())
    
        
