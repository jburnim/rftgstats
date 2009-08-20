#!/usr/bin/python

import pprint
import sys
import csv
import math
import random
import os
import collections

HOMEWORLDS = ["Alpha Centauri", "Epsilon Eridani", "Old Earth",
              "Ancient Race", "Damaged Alien Factory",
              "Earth's Lost Colony", "New Sparta",
              "Separatist Colony", "Doomed world"]

GOALS = [ 
    '4+ Production',
    '4+ Devs',
    '6+ Military',
    '3+ Blue/Brown',
    '5 VP',
    'First 6 Dev',
    'All Abilities',
    'First Discard',
    'All Colors',
    '3 Aliens',
    ]

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
        self._accum[key] += val

    def __getattr__(self, key):
        return getattr(self._accum, key)

    def __getitem__(self, key):
        if key not in self._accum:
            self._accum[key] = 0.0
        return self._accum[key]

def ComputeWinningStatsByHomeworld(games):
    def HomeworldYielder(player_result, game):
        yield Homeworld(player_result)
    return ComputeWinningStatsByBucket(games, HomeworldYielder)

def ComputeWinningStatsByCardPlayed(games):
    def CardYielder(player_result, game):
        for card in player_result['cards']:
            yield card
    return ComputeWinningStatsByBucket(games, CardYielder)

def ComputeWinningStatsByCardPlayedAndPlayer(games):
    def PlayerCardYielder(player_result, game):
        for card in player_result['cards']:
            yield player_result['name'], card
    return ComputeWinningStatsByBucket(games, PlayerCardYielder)

class PlayerCardAffinity:
    def __init__(self, games):
        self.baseline_card_info = ComputeWinningStatsByCardPlayed(games)
        player_card_info = ComputeWinningStatsByCardPlayedAndPlayer(games)
        rekeyed_player_card_info = collections.defaultdict(lambda: (0.0, 0.0))
        for player_card, card_win_ratio, card_exp_wins in player_card_info:
            rekeyed_player_card_info[player_card] = (card_win_ratio,
                                                     card_exp_wins)
        self.player_card_info = rekeyed_player_card_info
            
        self.num_games_by_player = collections.defaultdict(float)
        for game in games:
            for player_result in game['player_list']:
                self.num_games_by_player[player_result['name']] += 1

        self.num_games = float(len(games))
        
    def PlayerVsBaseCardInfo(self, player_name):
        card_diff_info = []
        for card_name, card_win_ratio, card_exp_wins in self.baseline_card_info:
            player_card_win_ratio, player_card_exp_wins = self.player_card_info[
                (player_name, card_name)]
            win_ratio_diff = player_card_win_ratio - card_win_ratio

            overall_play_ratio = card_exp_wins / self.num_games # wrong
            player_play_ratio = player_card_exp_wins / self.num_games_by_player[
                player_name] # also wrong

            play_ratio_diff = player_play_ratio - overall_play_ratio
            card_diff_info.append((card_name, win_ratio_diff, play_ratio_diff))
        card_diff_info.sort(key = lambda x: x[1])
        return card_diff_info
        

def ComputeWinningStatsByPlayer(games):
    def PlayerYielder(player_result, game):
        yield player_result['name']
    return ComputeWinningStatsByBucket(games, PlayerYielder)

def Score(result):
    return result['points'] * 100 + result['goods'] + result['hand'] 

def WinningScore(game):
    return max(Score(result) for result in game['player_list'])
        

def ComputeWinningStatsByBucket(games, bucketter):
    """ Returns a list of (bucket_key, win_ratio, exp_wins),
    sorted by win_ratio"""
    wins = AccumDict()
    exp_wins = AccumDict()
    for game in games:
        winners = []
        max_score = WinningScore(game)
        inv_num_players = 1.0 / len(game['player_list'])

        num_winning_players = 0
        for player_result in game['player_list']:
            if Score(player_result) == max_score:
                num_winning_players += 1
        inv_num_winners = 1.0 / num_winning_players

        for player_result in game['player_list']:
            for bucket in bucketter(player_result, game):
                exp_wins.Add(bucket, inv_num_players)
                if Score(player_result) == max_score:
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
    return [p for p in game['player_list'] if Score(p) == max_score]

def FilterOutTies(games):
    return [g for g in games if not GameTied(g)]

def GetPlayerResultForName(game, player_name):
    for player in game['player_list']:
	if player['name'] == player_name:
	    return player

class PlayerSkillInfo:
    def __init__(self, rating, wins, exp_wins):
        self.rating = rating
        self.wins = wins
        self.exp_wins = exp_wins

    def __repr__(self):
        return str(self.rating)

class PlayerInfo:
    def __init__(self):
	pass

    def SetRatingFlowByOpponent(rating_flow):
	self.rating_flow_by_opponent = rating_flow

    def SetRatingFlowByHomeworld(rating_flow):
	self._rating_flow_by_homeworld = rating_flow

def SortDictByKeys(d):
    return sorted(d.items(), key = lambda x: -x[1])

class SkillRatings:
    def __init__(self, games, prob_func, base_rating, move_const):
        self.ratings = {}
        self.base_rating = base_rating
	self.rating_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))
	self.rating_by_homeworld_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))

        for game in FilterOutTies(games):
            winner = GameWinners(game)[0]
            win_name = winner['name']
            delta = {win_name: 0.0}
            for player in game['player_list']:
                if player['name'] == win_name:
                    continue
                winner_rating = self.GetSkillInfo(win_name).rating
                loser_name = player['name']
                loser_rating = self.GetSkillInfo(loser_name).rating
                win_prob = prob_func(winner_rating, loser_rating)
                lose_prob = 1.0 - win_prob
                delta[win_name] = delta[win_name] + win_prob * move_const
                delta[loser_name] = -win_prob * move_const
            for player_name in delta:
                self.ratings[player_name].rating += delta[player_name]
                self.ratings[player_name].exp_wins += 1.0 / (
                    len(game['player_list']))

                homeworld = Homeworld(GetPlayerResultForName(game, win_name))

		self.rating_by_homeworld_flow[player_name][homeworld] += (
                    delta[player_name])

                if win_name == player_name:
                    continue
                self.rating_flow[win_name][player_name] -= delta[player_name]
                self.rating_flow[player_name][win_name] += delta[player_name]


            self.ratings[win_name].wins += 1.0

    def GetHomeworldSkillFlow(self, name):
	return SortDictByKeys(self.rating_by_homeworld_flow[name])

    def GetSkillInfo(self, name):
        if name not in self.ratings:
            self.ratings[name] = PlayerSkillInfo(self.base_rating, 0, 0)
        return self.ratings[name]

    def GetRatingFlow(self, name):
        return SortDictByKeys(self.rating_flow[name])

    def PlayersSortedBySkill(self):
        return sorted(self.ratings.items(), key = lambda x: -x[1].rating) 

    def ComputeRatingBuckets(self, games, num_buckets):
        skills_weighted_by_games = []
        for g in games:
            for p in g['player_list']:
                rating = self.GetSkillInfo(p['name']).rating
                skills_weighted_by_games.append(rating)
        skills_weighted_by_games.sort()
        num_player_game_results = float(len(skills_weighted_by_games))
        skill_sections = []
        for i in range(1, num_buckets):
            idx = int(num_player_game_results * i / num_buckets)
            skill_sections.append(skills_weighted_by_games[idx])
        skill_sections.append(1e10)
        return skill_sections

    def PlayerSkillBucket(self, player_name, skill_sections):
        player_rating = self.ratings[player_name].rating
        skill_level = 0
        for bucket in skill_sections:
            if player_rating > bucket:
                skill_level += 1
        return skill_level


def EloProbability(r1, r2):
    return 1 / (1 + 10 ** ((r1 - r2) / 400.0))

def ComputeWinningStatsByCardPlayedAndSkillLevel(games, skill_ratings):
    def CardSkillYielder(player_result, game):
        skill_info = skill_ratings.GetSkillInfo(player_result['name'])
        for card in player_result['cards']:
            yield card, skill_info.rating, skill_info.wins, skill_info.exp_wins
    bucketted_stats = ComputeWinningStatsByBucket(games, CardSkillYielder)
    
    grouped_by_card = {}

    for key, win_rate, exp_wins in bucketted_stats:
        card, rating, player_wins, player_exp_wins = key
        if not card in grouped_by_card:
            grouped_by_card[card] = {'weighted_rating': 0.0,
                                     'player_wins': 0.0,
                                     'player_exp_wins': 0.0,
                                     'wins': 0.0,
                                     'exp_wins': 0.0}
        card_stats = grouped_by_card[card]
        card_stats['weighted_rating'] += rating * exp_wins
        card_stats['player_wins'] += player_wins
        card_stats['player_exp_wins'] += player_exp_wins
        card_stats['wins'] += win_rate * exp_wins
        card_stats['exp_wins'] += exp_wins

    for card in grouped_by_card:
        card_stats = grouped_by_card[card]
        card_stats['avg_rating'] = (card_stats['weighted_rating'] / 
                                    card_stats['exp_wins'])
        del card_stats['weighted_rating']

        card_stats['player_win_rate'] = (card_stats['player_wins'] / 
                                         card_stats['player_exp_wins'])
        del card_stats['player_wins']
        del card_stats['player_exp_wins']

        card_stats['win_rate'] = card_stats['wins'] / card_stats['exp_wins']
        del card_stats['wins']

    return grouped_by_card

def NiceFormatWinningStatsByCardPlayedAndSkillLevel(games, skill_ratings):
    win_stats_by_card_skill = ComputeWinningStatsByCardPlayedAndSkillLevel(
        games, skill_ratings)
    win_stats_by_card_skill = win_stats_by_card_skill.items()
    keys = ['win_rate']
    for key_name in keys:
        win_stats_by_card_skill.sort(key = lambda x: -x[1][key_name])
        print '\nsorted by', key_name
        print '%s%s%s%s%s' % ('card_name'.ljust(30), 'avgrat'.ljust(10),
                              'E[win]'.ljust(10), 'p_win_r'.ljust(10),
                              'w_rate'.ljust(10))
        for card, info in win_stats_by_card_skill:
            print '%s%s%s%s%s' % (
                card.ljust(30), 
                ('%.0f' % info['avg_rating']).ljust(10), 
                ('%.2f' % info['exp_wins']).ljust(10), 
                ('%.2f' % info['player_win_rate']).ljust(10), 
                ('%.2f' % info['win_rate']).ljust(10))

def FilterOutNonGoals(games):
    return [g for g in games if 'goals' in g]

def ComputeWinningStatsByHomeworldGoal(games):
    games = FilterOutNonGoals(games)
    print 'total games with goals analyzed', len(games)
    def HomeworldGoalYielder(player_result, game):
        for goal in game['goals']:
            yield Homeworld(player_result), goal
    bucketted_by_homeworld_goal = ComputeWinningStatsByBucket(
        games, HomeworldGoalYielder)
    keyed_by_homeworld_goal = {}
    for (homeworld, goal), win_rate, exp_wins in bucketted_by_homeworld_goal:
        keyed_by_homeworld_goal[(homeworld, goal)] = win_rate
        
    HOMEWORLD_SPACE = 25
    PER_NUM_SPACE = 8
    print ''.ljust(HOMEWORLD_SPACE + PER_NUM_SPACE),
    for goal in GOALS[::2]:
        print goal.ljust(PER_NUM_SPACE * 2 + 1),
    print

    print ''.ljust(HOMEWORLD_SPACE + PER_NUM_SPACE * 2),
    for goal in GOALS[1::2]:
        print goal.ljust(PER_NUM_SPACE * 2 + 1),
    print
    
    bucketted_by_homeworld = ComputeWinningStatsByHomeworld(games)
    for homeworld, win_rate, exp_wins in bucketted_by_homeworld:
        print homeworld.ljust(HOMEWORLD_SPACE), ('%.3f' % win_rate).ljust(PER_NUM_SPACE),
        
        for goal in GOALS:
            diff_as_str = '%.3f' % (
                (keyed_by_homeworld_goal[(homeworld, goal)] - win_rate))
            print diff_as_str.ljust(PER_NUM_SPACE),
        print
        

def ComputeWinStatsByHomeworldSkillLevel(games, skill_ratings):
    untied_games = FilterOutTies(games)
    NUM_SKILL_BUCKETS = 3
    skill_buckets = skill_ratings.ComputeRatingBuckets(untied_games, 
                                                       NUM_SKILL_BUCKETS)
    print skill_buckets

    def HomeworldSkillYielder(player_result):
        name = player_result['name']
        skill_bucket = skill_ratings.PlayerSkillBucket(name, skill_buckets)
        yield (Homeworld(player_result), skill_bucket)

    bucketted_stats = ComputeWinningStatsByBucket(untied_games, 
                                                  HomeworldSkillYielder)
    keyed_by_bucket = {}
    for (homeworld, skill), win_rate, exp_wins in bucketted_stats:
        keyed_by_bucket[(homeworld, skill)] = (win_rate, exp_wins)
    print keyed_by_bucket
    ret = {}
    for homeworld in HOMEWORLDS:
        ret[homeworld] = []
        for i in range(NUM_SKILL_BUCKETS):
            ret[homeworld].append(keyed_by_bucket[(homeworld, i)])
    return ret

def SixDevRankings(games):
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

class OverviewStats:
    def __init__(self, games):
        self.max_game_no = 0
        self.games_played = len(games)
        player_size = collections.defaultdict(int)
        race_type = collections.defaultdict(int)

        for game in games:
            self.max_game_no = max(self.max_game_no, game['game_no'])
            adv = ''
            if game['advanced'] == 1:
                adv = ' adv'
            
            players_size_str = '%dp%s' % ( len(game['player_list']), adv )
            player_size[players_size_str] += 1

            race_type_str = 'Base'
            if game['expansion'] == 1:
                race_type_str = 'Gathering Storm'
            if 'goals' in game['player_list'][0]:
                race_type_str += ' with Goals'

            race_type[race_type_str] += 1

        self.player_size = player_size.items()
        self.player_size.sort()
        self.race_type = race_type.items()
        self.race_type.sort()

    def RenderAsHTMLTable(self):
        header_fmt = '<table border=1><tr><td>%s</td><td>Num Games' + (
            '</td><td>Percentage</td></tr>')
        html = '<a name="overview">Last seen game %d<br>' % self.max_game_no
        html += header_fmt % 'Player Size'
        for size in self.player_size:
            html += '<tr><td>%s</td><td>%d</td><td>%d%%</td></tr>' % (
                ( size[0], size[1], int( 100. * size[1] / self.games_played )))
        html += '</table border=1><table>'
        html += header_fmt % 'Game Type'
        for d in self.race_type:
            html += '<tr><td>%s</td><td>%d</td><td>%d%%</td></tr>' % (
                ( d[0], d[1], int( 100. * d[1] / self.games_played )))
        html += '</table>'
        return html

def PlayerFile(player_name):
    return 'player_' + player_name + '.html'

def PlayerLink(player_name):
    return '<a href="' + PlayerFile(player_name) + '">' + player_name + '</a>'

def RenderTopPage(games, skill_ratings):
    overview = OverviewStats(games)
    top_out = open('output/index.html', 'w')
    
    top_out.write('<html><head><title>Genie Overview Stats</title><head>\n')
    top_out.write('<body>' + overview.RenderAsHTMLTable())

    top_out.write('<table border=1>')

    player_by_skill = skill_ratings.PlayersSortedBySkill()
    top_out.write('Total players %d\n' % len(player_by_skill))
    top_out.write('<tr><td>Rank</td><td>Player Name</td><td>Rating</td></tr>\n')
    for ind, (player_name, skill_info) in enumerate(player_by_skill):
        top_out.write('<tr><td>%d</td><td>%s</td><td>%.0f</td></tr>\n' %
                      (ind + 1, PlayerLink(player_name), skill_info.rating))
    top_out.write('</table')

    top_out.write('</body></html>')

def PlayerToGameList(games):
    players_to_games = collections.defaultdict(list)
    for game in games:
        for player in game['player_list']:
            players_to_games[player['name']].append(game)
    return players_to_games

def WritePlayerFloatPairsAsTableRows(output_file, pairs):
    for s, f in pairs:
        output_file.write('<tr><td>%s</td><td>%.1f</td></tr>\n' % (s, f))

def RenderPlayerPage(player, player_games, skill_ratings):
    overview = OverviewStats(player_games)
    player_out = open('output/' + PlayerFile(player), 'w')
    player_out.write('<html><head><title>Genie Statistics for player %s'
                     '<title></head><body>\n' % player)

    player_out.write('<a href="#overview">Overview</a>\n' 
                     '<a href="#homeworld_flow">Homeworld Rating Flow</a>'
                     '<a href="#player_flow">Player Rating Flow</a>\n' 
                     '<br>\n')
    player_out.write(overview.RenderAsHTMLTable())

    player_out.write('<a name="homeworld_flow"> '
                     '<table border=1><tr><td>Homeworld</td>'
                     '<td>Net rating change when playing<td></tr>')
    WritePlayerFloatPairsAsTableRows(
        player_out, skill_ratings.GetHomeworldSkillFlow(player))
    player_out.write('</table>')

    player_out.write('<a name="player_flow"> '
                     '<table border=1><tr><td>Opponent</td>'
                     '<td>Net rating flow</td></tr>\n')
    linked_out = [(PlayerLink(o), s) for o, s in
                  skill_ratings.GetRatingFlow(player)]
    WritePlayerFloatPairsAsTableRows(player_out, linked_out)
    player_out.write('</table>')



    player_out.write('</html>')

def main():
    games = eval(open('condensed_games.json').read())
    #games = eval(open('terse_games.json').read())
    #open('terse_games.json', 'w').write(str(random.sample(games, 100)))
        
    skill_ratings = SkillRatings(games, EloProbability, 1500, 15)
    # #     print skill_ratings.GetSkillInfo( 'rrenaud' ).rating
    #NiceFormatWinningStatsByCardPlayedAndSkillLevel(games, skill_ratings)

    #     player_card_info = PlayerCardAffinity(games)
    #     pprint.pprint(player_card_info.PlayerVsBaseCardInfo('Danny'))
    if not os.access('output', os.O_RDONLY):
        os.mkdir('output')
    RenderTopPage(games, skill_ratings)

    for player, player_games in PlayerToGameList(games).iteritems():
        RenderPlayerPage(player, player_games, skill_ratings)

if __name__ == '__main__':
    main()

