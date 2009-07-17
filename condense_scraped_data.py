#!/usr/bin/python

import csv
import pprint
import os.path
import re

ALL_DIGITS = re.compile('\d+')
POINTS_RE = re.compile('points = (-?\d+)p')
CHIPS_RE = re.compile('(\d+) chips')
GAME_NUM_RE = re.compile('Game #(\d+)')
GOAL_NUM_RE = re.compile('g(\d+)')

GOAL_NUM_TO_NAME = {
    1: '5 VP',
    2: 'First 6 Dev',
    3: 'All Abilities',
    4: 'First Discard',
    5: 'All Colors',
    6: '3 Aliens',
    10: '4+ Production',
    11: '4+ Devs',
    12: '6+ Military',
    13: '3+ Blue/Brown',
}

def ParseGoals(snip_with_goals):
    avail_goal_chunks = snip_with_goals.split('rftg/')[1:]
    ret = []
    for goal_chunk in avail_goal_chunks:
        goal_num = int(GOAL_NUM_RE.search(goal_chunk).group(1))
        ret.append(GOAL_NUM_TO_NAME[goal_num])
    return ret


def ParseGame(page_contents, card_info):
    version_loc = page_contents.index(': Game #')
    version_with_context = page_contents[version_loc-50:version_loc + 50]
    is_exp = 'Gathering Storm' in version_with_context
    using_goals = False
    goals = set()
    if 'Available goals' in version_with_context:
        end_goal_loc = page_contents.find('Chosen Actions')
        snip_with_goals = page_contents[version_loc - 50:end_goal_loc]
        goals.update(ParseGoals(snip_with_goals))
        using_goals = True
    
    #print 'using goals?', using_goals
    ret = {'player_list': [], 
           'game_no': int(GAME_NUM_RE.search(version_with_context).group(1)),
           'expansion': int(is_exp)}

    if 'Status:' not in page_contents:
        #print 'could not find status'
        return None

    status_list = page_contents.split('Status:')[1:]

    for status in status_list:
        player_result = {}
        status_lines = status.split('<br/>')
        is_game_end = status_lines[0]
        if 'Game End' not in is_game_end:
            #print "Don't think game is over"
            return None
        
        name_points = status_lines[1]
        player_result['name'] = name_points[:name_points.find("'")]
        player_result['points'] = int(POINTS_RE.search(name_points).group(1))
        player_result['chips'] = int(CHIPS_RE.search(name_points).group(1))
        if player_result['points'] <= 5:
            #print "Don't think this game is legit..", player_result['name'], player_result['points']
            return None
                    
        card_goal_list_line = status_lines[2]
        card_goal_list_imgs = card_goal_list_line.split('src=')
        cards = []
        won_goals = []
        for card_or_goal in card_goal_list_imgs[1:]:
            img = card_or_goal.replace('/', ' ').replace('.', ' ').split()[1]
            if img[0] == 'g':
                won_goals.append(GOAL_NUM_TO_NAME[int(img[1:])])
            else:
                card_data = card_info[img]
                cards.append(card_data['name'])
            
        player_result['cards'] = cards
        if using_goals:
            goals.update(won_goals)
            player_result['goals'] = won_goals
        ret['player_list'].append(player_result)
    if using_goals:
        ret['goals'] = list(goals)
    return ret

if __name__ == '__main__':
    card_info = csv.DictReader(open('card_names.csv', 'r'))
    cards_by_id = {}
    for row in card_info:
        id_line = row['BGG img number ID']
        card_id = ALL_DIGITS.search(id_line).group()
        cards_by_id[card_id] = row

    games = []
    for game_data_fn in os.listdir('data'):
        # ['game.htm?gid=1681']
        try:
            print game_data_fn
            if game_data_fn.endswith('dead'): 
                continue
            game = ParseGame(open('data/' + game_data_fn, 'r').read(), 
                             cards_by_id)
            if game and len(game['player_list']):
                games.append(game)
        except Exception, e:
            print 'error', e, game_data_fn

    #print games
    pprint.pprint(games, open('condensed_games.json', 'w'))
