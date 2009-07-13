#!/usr/bin/python

import pprint
import sys
import csv

HOMEWORLDS = ["Alpha Centauri", "Epsilon Eridani", "Old Earth",
              "Ancient Race", "Damaged Alien Factory",
              "Earth's Lost Colony", "New Sparta",
              "Separatist Colony", "Doomed world"]

def Homeworld(player_info):
    # This misclassifes initial doomed world settles that are other homeworlds.
    # I doubt that happens all that often though.
    if player_info['cards'][0] not in HOMEWORLDS:
        return 'Doomed world'
    return player_info['cards'][0]


class AccumDict:
    def __init__(self):
        self._accum = {}

    def Add(self, key, val):
        if key not in self._accum:
            self._accum[key] = 0.0
        self._accum[key] = self._accum[key] + val

    def __getattr__(self, key):
        return getattr(self._accum, key)

    def __getitem__(self, key):
        if key not in self._accum:
            self._accum[key] = 0.0
        return self._accum[key]

def ComputeWinningStatsByHomeworld(games):
    def HomeworldYielder(player_result):
        yield Homeworld(player_result)
    return ComputeWinningStatsByBucket(games, HomeworldYielder)

def ComputeWinningStatsByCardPlayed(games):
    def CardYielder(player_result):
        for card in player_result['cards']:
            yield card
    return ComputeWinningStatsByBucket(games, CardYielder)

def ComputeWinningStatsByBucket(games, bucketter):
    wins = AccumDict()
    exp_wins = AccumDict()
    for game in games:
        winners = []
        max_score = max(result['points'] for result in game['player_list'])
        inv_num_players = 1.0 / len(game['player_list'])

        num_winning_players = 0
        for player_result in game['player_list']:
            if player_result['points'] == max_score:
                num_winning_players += 1
        inv_num_winners = 1.0 / num_winning_players

        for player_result in game['player_list']:
            for bucket in bucketter(player_result):
                exp_wins.Add(bucket, inv_num_players)
                if player_result['points'] == max_score:
                    wins.Add(bucket, inv_num_winners)

    win_rates = []
    for bucket in exp_wins:
        win_ratio = wins[bucket] / (exp_wins[bucket] or 1.0)
        win_rates.append((bucket, win_ratio, exp_wins[bucket]))

    win_rates.sort(key = lambda x: -x[1])
    return win_rates


if __name__ == '__main__':
    games = eval(open('condensed_games.json').read())
    games = [g for g in games if len(g['player_list']) == 2]
             

    print 'analyzing', len(games), 'games'
    pprint.pprint(ComputeWinningStatsByHomeworld(games))
    print
    print

    card_info = list(csv.DictReader(open('card_attributes.csv', 'r')))
    dev_6_names = [card['Name'] for card in card_info if card['Cost'] == '6' and
                   card['Type'] == 'Development']

    winning_stats_by_cards = ComputeWinningStatsByCardPlayed(games)
    pprint.pprint(winning_stats_by_cards)
    dev_6_stats = []
    for by_card_stats in winning_stats_by_cards:
        if by_card_stats[0] in dev_6_names:
            dev_6_stats.append(by_card_stats)

    def Utility(card_stat):
        # Just some approximate way to measure how good a card performed.
        # The first term is how much your winning rate increases from the 
        # baseline, given that it was played.  It's given a bit more weight
        # than the second term, which is basically how often the card is played.
        return -(card_stat[1] - 1.0) * card_stat[2] ** .5
    dev_6_stats.sort(key=Utility)
    pprint.pprint(dev_6_stats)
    
