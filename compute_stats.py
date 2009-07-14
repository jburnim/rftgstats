#!/usr/bin/python

import pprint
import sys
import csv
import math

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

def ComputeWinningStatsByPlayer(games):
    def PlayerYielder(player_result):
        yield player_result['name']
    return ComputeWinningStatsByBucket(games, PlayerYielder)

def WinningScore(game):
    return max(result['points'] for result in game['player_list'])

def ComputeWinningStatsByBucket(games, bucketter):
    wins = AccumDict()
    exp_wins = AccumDict()
    for game in games:
        winners = []
        max_score = WinningScore(game)
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

def GameTied(game):
    return len(GameWinners(game)) > 1

def GameWinners(game):
    max_score = WinningScore(game)
    return [p for p in game['player_list'] if p['points'] == max_score]

def FilterOutTies(games):
    return [g for g in games if not GameTied(g)]

def ProbabilityBasedRanker(games, prob_func, base_rating, move_const):
    ratings = {}
    for game in FilterOutTies(games):
        winner = GameWinners(game)[0]
        win_name = winner['name']
        delta = {win_name: 0.0}
        for player in game['player_list']:
            if player['name'] == win_name:
                continue
            winner_rating = ratings.get(win_name, base_rating)
            loser_rating = ratings.get(player['name'], base_rating)
            win_prob = prob_func(winner_rating, loser_rating)
            lose_prob = 1.0 - win_prob
            delta[win_name] = delta[win_name] + lose_prob * move_const
            delta[player['name']] = -win_prob * move_const
        for player_name in delta:
            ratings[player_name] = (ratings.get(player_name, base_rating) + 
                                    delta[player_name])
    return sorted(ratings.items(), key=lambda x: -x[1])

def EloProbability(r1, r2):
    return 1 / (1 + 10 ** ((r1 - r2) / 400.0))

def ComputeWinStatsByHomeworldSkillLevel(games, skill_ratings):
    untied_games = FilterOutTies(games)
    skill_ratings_by_name = dict(skill_ratings)
    skills_weighted_by_games = []
    for g in untied_games:
        for p in g['player_list']:
            skills_weighted_by_games.append(skill_ratings_by_name[p['name']])
    skills_weighted_by_games.sort()

    num_player_game_results = len(skills_weighted_by_games)
    NUM_SKILL_BUCKETS = 3
    skill_sections = []
    for i in range(1, NUM_SKILL_BUCKETS):
        idx = int(float(num_player_game_results) * i / NUM_SKILL_BUCKETS)
        skill_sections.append(skills_weighted_by_games[idx])
    skill_sections.append(1e10)


    def HomeworldSkillYielder(player_result):
        player_rating = skill_ratings_by_name[player_result['name']]
        skill_level = 0
        for bucket in skill_sections:
            if player_rating > bucket:
                skill_level += 1
        yield (Homeworld(player_result), skill_level)
    bucketted_stats = ComputeWinningStatsByBucket(untied_games, 
                                                  HomeworldSkillYielder)
    keyed_by_bucket = {}
    for (homeworld, skill), win_rate, exp_wins in bucketted_stats:
        keyed_by_bucket[(homeworld, skill)] = (win_rate, exp_wins)
    ret = {}
    for homeworld in HOMEWORLDS:
        ret[homeworld] = []
        for i in range(NUM_SKILL_BUCKETS):
            ret[homeworld].append(keyed_by_bucket[(homeworld, i)])
    return ret
    
if __name__ == '__main__':
    games = eval(open('condensed_games.json').read())
    games = [g for g in games if len(g['player_list']) == 2]

    print 'analyzing', len(games), 'games'
    #pprint.pprint(ComputeWinningStatsByHomeworld(games))

    card_info = list(csv.DictReader(open('card_attributes.csv', 'r')))
    dev_6_names = [card['Name'] for card in card_info if card['Cost'] == '6' and
                   card['Type'] == 'Development']

    winning_stats_by_cards = ComputeWinningStatsByCardPlayed(games)
    #pprint.pprint(winning_stats_by_cards)

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
    #pprint.pprint(dev_6_stats)

    skill_ratings = ProbabilityBasedRanker(games, EloProbability, 1500, 10)
    win_stats_by_homeworld_skill_level = ComputeWinStatsByHomeworldSkillLevel(games, skill_ratings)
    pprint.pprint(win_stats_by_homeworld_skill_level)

    
