#!/usr/bin/python

import csv
import pprint
import os.path
import re

ALL_DIGITS = re.compile('\d+')
POINTS_RE = re.compile('points = (\d+)p')
CHIPS_RE = re.compile('(\d+) chips')

def ParseGame(page_contents, card_info, game_no):
    ret = {'player_list': [], 'game_no': game_no}
    if 'Status:' not in page_contents:
        return None
    status_list = page_contents.split('Status:')[1:]
    is_exp = False
    for status in status_list:
        player_result = {}
        status_lines = status.split('<br/>')
        is_game_end = status_lines[0]
        if 'Game End' not in is_game_end:
            return None
        
        name_points = status_lines[1]
        player_result['name'] = name_points[:name_points.find("'")]
        player_result['points'] = int(POINTS_RE.search(name_points).group(1))
        player_result['chips'] = int(CHIPS_RE.search(name_points).group(1))
                    
        card_list_line = status_lines[2]
        card_list_imgs = card_list_line.split('src=')
        cards = []
        for card in card_list_imgs[1:]:
            card_no = card.replace('/', ' ').replace('.', ' ').split()[1]
            card_data = card_info[card_no]
            is_exp = is_exp or (card_data['exp. 1'] == 'x')
            cards.append(card_data['name'])
            
        player_result['cards'] = cards
        ret['player_list'].append(player_result)
    ret['expansion'] = int(is_exp)
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
        if game_data_fn.endswith('dead'): 
            continue
        game_no = ALL_DIGITS.search(game_data_fn).group()
        game = ParseGame(open('data/' + game_data_fn, 'r').read(), 
                         cards_by_id, game_no)
        if game and len(game['player_list']):
            games.append(game)

    pprint.pprint(games, open('condensed_games.json', 'w'))
