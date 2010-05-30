#!/usr/bin/python

import csv
import pprint
import os.path
import re
import simplejson as json
import gzip

ALL_DIGITS = re.compile('\d+')
POINTS_RE = re.compile('points = (-?\d+)p')
CHIPS_RE = re.compile('(\d+) chips')
GAME_NUM_RE = re.compile('Game #(\d+)')
GOAL_NUM_RE = re.compile('g(\d+)')
CARD_NUM_RE = re.compile('has (\d+) card on hand')

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

class BogusGoalNum(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class CompleteButRejectedGame(Exception):
    pass

def ParseGoals(snip_with_goals):
    avail_goal_chunks = snip_with_goals.split('rftg/')[1:]
    ret = []
    for goal_chunk in avail_goal_chunks:
        goal_num_match = GOAL_NUM_RE.search(goal_chunk)
        if not goal_num_match:
            continue
        goal_num = int(goal_num_match.group(1))
        if goal_num not in GOAL_NUM_TO_NAME:
            print 'bogus goal num?', goal_num
            raise BogusGoalNum("Bogus goal number " + str(goal_num))
        ret.append(GOAL_NUM_TO_NAME[goal_num])
    return ret


def ParseGame(page_contents, card_id_to_name, card_name_to_version):
    page_contents = page_contents.replace('<br/>', '<br>')
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

    ret = {'player_list': [], 
           'game_no': int(GAME_NUM_RE.search(version_with_context).group(1))}

    if 'Status:' not in page_contents:
        print 'could not find status'
        raise CompleteButRejectedGame()

    page_contents = page_contents[:page_contents.find('Comments'):]
    status_list = page_contents.split('Status:')[1:]

    for status in status_list:
        player_result = {}
        status_lines = status.split('<br>')
        if len(status_lines) < 3:
            print 'confused, could not under status lines', status_lines
        game_end_line = status_lines[0]
        if 'Game End' not in game_end_line:
            if 'Frozen' in game_end_line:
                raise CompleteButRejectedGame()
            print "Don't think game", ret['game_no'] ,"is over"
            return None
        
        name_points = status_lines[1]
        player_result['name'] = name_points[:name_points.find("'")]
        player_result['points'] = int(POINTS_RE.search(name_points).group(1))
        player_result['chips'] = int(CHIPS_RE.search(name_points).group(1))
        if player_result['points'] <= 5:
            raise CompleteButRejectedGame()
                    
        card_goal_list_line = status_lines[2]
        card_goal_list_imgs = card_goal_list_line.split('src=')
        cards = []
        won_goals = []
        goods = 0
        for card_or_goal in card_goal_list_imgs:
            if 'border-width:5px' in card_or_goal:
                goods += 1
        for card_or_goal in card_goal_list_imgs[1:]:
            img = card_or_goal.replace('/', ' ').replace('.', ' ').split()[1]
            if img[0] == 'g':
                won_goals.append(GOAL_NUM_TO_NAME[int(img[1:])])
            else:
                card_data = card_id_to_name[img]
                card_name = card_data['name']
                cards.append(card_name)
                if 'Gathering' in card_name_to_version[card_name]:
                    is_exp = True
            
        player_result['cards'] = cards
        if using_goals:
            goals.update(won_goals)
            player_result['goals'] = won_goals
        player_result['goods'] = goods
        ret['player_list'].append(player_result)

    if len(ret['player_list']) <= 1:
        print 'insufficient players'
        raise CompleteButRejectedGame()

    if using_goals:
        ret['goals'] = list(goals)

    hand_sizes = [int(x) for x in CARD_NUM_RE.findall(page_contents)]
    for player_result, hand_size in zip(ret['player_list'], hand_sizes):
        player_result['hand'] = hand_size

    ret['advanced'] = int('Action1:' in page_contents and
                          'Action2:' in page_contents)
    ret['expansion'] = int(is_exp)
    return ret

def main():
    card_id_to_name = csv.DictReader(open('card_names.csv', 'r'))
    cards_by_id = {}

    for row in card_id_to_name:
        id_line = row['BGG img number ID']
        card_id = ALL_DIGITS.search(id_line).group()
        cards_by_id[card_id] = row

    card_attrs = csv.DictReader(open('card_attributes.csv', 'r'))
    card_name_to_version = {}
    for row in card_attrs:
        card_name_to_version[row['Name']] = row['Release']

    games = []
    error_sources = []
    known_errors = []
    data_sources = [x for x in os.listdir('data') if not 'xml' in x]
    for game_data_fn in data_sources:
        write_dead = False
        try:
            print game_data_fn
            if game_data_fn.endswith('dead'):
                continue

            full_game_fn = 'data/' + game_data_fn
            game = ParseGame(open(full_game_fn, 'r').read(), 
                             cards_by_id, card_name_to_version)
            if game and len(game['player_list']):
                games.append(game)
        except BogusGoalNum, e:
            known_errors.append(game_data_fn)
            write_dead = True
        except CompleteButRejectedGame:
            print 'Rejecting', game_data_fn
            write_dead = True
        except Exception, e:
            error_sources.append(game_data_fn)
            print 'error', e, game_data_fn
        if write_dead:
            open(full_game_fn + '.dead', 'w')


    print 'games with errors', error_sources
    print 'games with known errors', known_errors
    json.dump(games, open('condensed_games.json', 'w'), indent=True)
    gzip.GzipFile('condensed_games.json.gz', 'w').write(
        open('condensed_games.json', 'r').read())
    

if __name__ == '__main__':
    main()
