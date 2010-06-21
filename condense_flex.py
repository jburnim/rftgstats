import xml.etree.ElementTree as ET

import copy
import gzip
import os
import simplejson as json

import compute_stats
from deck_info import DeckInfo
import tableau_scorer

def ParsePlayerNode(player_node):
    ret = {}
    ret['hand'] = len(player_node.findall('hand/deck_card'))
    ret['chips'] = int(player_node.find('vp_chits').text)

    ret['cards'] = []
    ret['goods'] = 0
    for tableau_card_node in player_node.findall('tableau/tableau_card'):
        card_name = tableau_card_node.attrib['title']
        if card_name in ret['cards']: 
            return None
        if tableau_card_node.attrib['is_prod_good'] == 'false':
            ret['cards'].append(card_name)
            ret['goods'] += tableau_card_node.attrib['has_good'] == 'true'

    ret['goals'] = []
    points_from_goals = 0
    for goal_node in player_node.findall('goals/goal'):
        ret['goals'].append(goal_node.attrib['title'])
        if (goal_node.attrib['most_goal'] == 'true' and
            goal_node.attrib['tied'] == 'false'):
            points_from_goals += 5
        else:
            points_from_goals += 3
            
    ret['points'] = (tableau_scorer.TableauScorer(ret['cards'], ret['chips']
                                                  ).TotalPoints() + 
                     points_from_goals)
    if ret['points'] < 10:
        return None
    #s = player_node.find('name').text.encode('utf-8')
    name = player_node.find('name').text
    ret['name'] = ''.join(c for c in name if ord(c) < 128)
    return ret

GAME_FINISHED_STATUS_ID = 3

def ParseGame(game_node):
    game_dict = {'player_list': []}
    status_id = int(game_node.find('status_id').text)
    if status_id != GAME_FINISHED_STATUS_ID:
        return None
    for player_node in game_node.findall('players/player'):
        player_dict = ParsePlayerNode(player_node)
        if not player_dict:
            return None
        #player_result = compute_stats.PlayerResult(copy.deepcopy(player_dict))
        game_dict['player_list'].append(player_dict)
    game_dict['game_id'] = ('http://flexboardgames.com/games/' + 
                            game_node.find('id').text)
    game_dict['goals'] = []
    for goal_node in game_node.findall('goals/goal'):
        game_dict['goals'].append(goal_node.attrib['title'])
    
    def MaxCardVersion(player_dict):
        return max(DeckInfo.Version(card) for card in player_dict['cards'])
                   
    game_dict['expansion'] = max(
        MaxCardVersion(p) for p in game_dict['player_list'])
    game_dict['expansion'] = max(game_dict['expansion'], 
                                 int(len(game_dict['goals']) > 1))
    
    phases = game_node.find('current_turn/phase_choices/phase_choice')
    if phases is None:
        return None

    game_dict['advanced'] = bool(phases.attrib['phase_choice_id_2'])
    if game_dict['advanced'] and len(game_dict['player_list']) > 2:
        return None
                         
    #g = compute_stats.Game(copy.deepcopy(dict(game_dict)))
    return game_dict

if __name__ == '__main__':
    games = []
    for fn in os.listdir('flex2'):
        try:
            full_fn = 'flex2/' + fn
            contents = open(full_fn, 'r').read()
            if contents == 'error':
                continue
            t = ET.parse(full_fn)
            g = ParseGame(t.getroot())
            if g:
                games.append(g)
        except Exception, e:
            print full_fn, e
            raise e

    json.dump(games, open('condensed_flex.json', 'w'), indent=True)
    gzip.GzipFile('condensed_flex.json.gz', 'w').write(
        open('condensed_flex.json', 'r').read())
    
        
