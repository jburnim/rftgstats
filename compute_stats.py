#!/usr/bin/python

import collections
import csv
import math
import pprint
import random
import os
import simplejson as json
import shutil
import sys

BASE_SKILL = 1500
MOVEMENT_CONST = 15


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

TITLE = 'Masters of Space: Race for the Galaxy Statistics'
JS_INCLUDE = '<script type="text/javascript" src="genie_analysis.js"></script>'
CSS = '<link rel="stylesheet" type="text/css" href="style.css" />'

INTRO_BLURB = """<h2>Introduction</h2>
<p>Hi, welcome to Race for the Galaxy
statistics page by rrenaud, Danny, and Aragos.
All of the data here is collected from the wonderful
<a href="http://genie.game-host.org">Genie online Race for the Galaxy server
</a>.  The code that computes this information is open source and available
at <a href="http://code.google.com/p/rftgstats">the rftgstats google code
project</a>.  These stats look best when viewed with a recent version of 
<a href="http://mozilla.org">Firefox 3</a>.  In particular, some graphs may
not show up or be missing text without a new version Firefox. 
Contributions welcome!</p>

<h3>A brief discussion about <i>Winning Rates</i></h3>
<p>
An <i>n</i> player game is worth <i>n</i> points.  The wining rate is the
number of points accumulated divided by the number of games played.
Thus, if you win a 4 player game, lose a 3 player game, and lose a 2
player game, your winning rate would (4 + 0 + 0) / 3 = 1.33.
Thus, a totally average and optimally balanced homeworld will have a
winning rate of near 1 after many games.  Likewise, a player whose skill
is totally representative of the distribution of the player population will
have a winning rate of 1.
"""

WINNING_RATE_VS_PLAY_RATE_DESCRIPTION = """<p>
<h2>Card winning rate vs play rate</h2>
<p>
This graph shows data by analyzing end game tableaus.  
<p>
The x axis is the probability that the card will end up in the final tableau, 
per instance of the card in the deck.
<p>
The y axis on this graph is the conditional winning rate of the card.
The conditional winning rate is the winning rate of the card given that it 
was played.
<p>
Strong cards have high winning rates and tend to be played more often.  
<p>You can click on a card's icon to see its name.
Cards played as homeworlds are excluded from the data, so that they don't
totally skew the play rate.  All the analyzed games are using the Gathering 
Storm expansion so the play rate distribution is fair.</p>
"""

HOMEWORLD_WINNING_RATE_DESCRIPTION = """<p>Influence of goal on winning rate
of homeworld.
<p>The winning rate is a generalization of winning probability that scales
fairly to multiplayer games with different distribubtions of number of
players.  
<p>The baseline winning rate of each homeworld is the fat dot.
The winning rate with the goal is the end of the segment without
the dot.  Hence, you can tell the absolute rate of winning by the
end of the line, and the relative change by the magnitude of the line.</p>
"""


RATING_BLURB = """<h3>Rating Methodology</h3>
Each column comes from running an Elo rating algorithm on the appriopriately
filtered set of games.  The first number is the rating and the second number is
the percentile for that rating.  To display a rating, 10 2-player games,
7 3-player, or 5 4-player games are required.
These differ from the Genie rating in at
least the following ways.
<ul>
<li>The ratings are computed with an Elo system with K value 15.  I am
unsure about what the Genie server uses.
<font size=-1>Eventually, I'll play around with fitting some more sophisticated
models to the data.</font></li>
<li>Ties do not count.</li>
<li>In multiplayer games, a second place is scored the same as a last place
finish.  Win or bust!</li>
<li>The ratings are computed in game number order (which is ordered by game
start time),
rather than game end time, as Genie does.  Since there are some players who game
the Genie system, I suspect this method may be slightly more accurate simply
because players do not have much of an incentive to game it.</li>
<li>The ratings lag genie by some amount, often by days or so.
<font size=-1>Eventually, I'll also fix this, making it lag only a few minutes.
</font>
</li>
</ul>
"""

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
        self.base_card_info = ComputeWinningStatsByCardPlayed(games)
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
        for card_name, card_win_ratio, card_exp_wins in self.base_card_info:
            player_card_win_ratio, player_card_exp_wins = (
                self.player_card_info[(player_name, card_name)])
                
            win_ratio_diff = player_card_win_ratio - card_win_ratio

            overall_play_ratio = card_exp_wins / self.num_games # wrong
            player_play_ratio = player_card_exp_wins / (
                self.num_games_by_player[player_name]) # also wrong
                

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

class BucketInfo:
    def __init__(self, key, win_ratio, expected_wins, frequency):
        self.key = key
        self.win_ratio = win_ratio
        self.expected_wins = expected_wins
        self.frequency = frequency

    def __getitem__(self, idx):
        if idx == 0: return self.key
        elif idx == 1: return self.win_ratio
        elif idx == 2: return self.expected_wins
        raise IndexError(idx)

    def __len__(self):
        return 3

def ComputeWinningStatsByBucket(games, bucketter):
    """ Returns a list of BucketInfo sorted by win_ratio"""
    wins = AccumDict()
    exp_wins = AccumDict()
    freq = AccumDict()
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
                freq.Add(bucket, 1)
                if Score(player_result) == max_score:
                    wins.Add(bucket, inv_num_winners)

    win_rates = []
    for bucket in exp_wins:
        frequency = freq[bucket]
        win_ratio = wins[bucket] / (exp_wins[bucket] or 1.0)
        win_rates.append(BucketInfo(bucket, win_ratio, exp_wins[bucket],
                                    frequency))

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
    def __init__(self, rating, wins, exp_wins, games_played):
        self.rating = rating
        self.wins = wins
        self.exp_wins = exp_wins
        self.games_played = games_played
        self.percentile = None

    def __repr__(self):
        return str(self.rating)


def SortDictByKeys(d):
    return sorted(d.items(), key = lambda x: -x[1])

class EloSkillModel:
    def __init__(self, base_rating, move_const):
        self.ratings = {}
        self.base_rating = base_rating
        self.move_const = move_const

    def Predict(self, winner_name, loser_name):
        winner_rating = self.GetSkillInfo(winner_name).rating
        loser_rating = self.GetSkillInfo(loser_name).rating
        return EloProbability(winner_rating, loser_rating)

    def AdjustRatings(self, winner, losers):
        """Adjust the winner and losers ratings; return the rating changes."""
        delta = {winner: 0.0}
        for loser in losers:
            winner_wins_prob = self.Predict(winner, loser)
            loser_wins_prob = 1.0 - winner_wins_prob
            # higher loser_wins_prob means a weaker opponent, which should
            # be penalized more.
            loser_rating_move = -loser_wins_prob * self.move_const
            delta[loser] = loser_rating_move
            self.ratings[loser].rating += loser_rating_move
            delta[winner] += -loser_rating_move
            self.ratings[winner].rating += -loser_rating_move
        return delta

    def GetSkillInfo(self, name):
        if name not in self.ratings:
            self.ratings[name] = PlayerSkillInfo(self.base_rating, 0, 0, 0)
        return self.ratings[name]

    def PlayersSortedBySkill(self):
        return sorted(self.ratings.items(),
                      key = lambda x: -x[1].rating)


class SkillRatings:
    def __init__(self, games, skill_model):
        self.skill_model = skill_model
	self.rating_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))
	self.rating_by_homeworld_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))
        self.model_log_loss = 0.0

        for game in FilterOutTies(games):
            winner = GameWinners(game)[0]
            win_name = winner['name']
            losers = []
            for player in game['player_list']:
                if player['name'] == win_name:
                    continue
                loser_name = player['name']
                win_prob = self.skill_model.Predict(win_name, loser_name)
                self.model_log_loss += math.log(win_prob) / math.log(2)
                losers.append(loser_name)

            delta = self.skill_model.AdjustRatings(win_name, losers)
            for player_name in delta:
                skill_info = self.GetSkillInfo(player_name)
                skill_info.games_played += 1
                skill_info.exp_wins += 1.0 / (len(game['player_list']))

                homeworld = Homeworld(GetPlayerResultForName(game,
                                                             player_name))

		self.rating_by_homeworld_flow[player_name][homeworld] += (
                    delta[player_name])

                if win_name == player_name:
                    continue
                self.rating_flow[win_name][player_name] -= delta[player_name]
                self.rating_flow[player_name][win_name] += delta[player_name]

            self.GetSkillInfo(win_name).wins += 1.0

        self.sorted_by_skill = self.skill_model.PlayersSortedBySkill()
        self.ranking_percentile = {}
        for idx, (name, skill_info) in enumerate(self.sorted_by_skill):
            self.ranking_percentile[name] = 100.0 * (1.0 - (
                float(idx) / len(self.sorted_by_skill)))

    def ModelPerformance(self):
        return self.model_log_loss

    def GetHomeworldSkillFlow(self, name):
	return SortDictByKeys(self.rating_by_homeworld_flow[name])

    def HasPlayer(self, name):
        return name in self.ranking_percentile

    def NumPlayers(self):
        return len(self.sorted_by_skill)

    def GetSkillInfo(self, name):
        return self.skill_model.GetSkillInfo(name)

    def GetPercentile(self, name):
        return self.ranking_percentile[name]

    def GetRatingFlow(self, name):
        return SortDictByKeys(self.rating_flow[name])

    def PlayersSortedBySkill(self):
        return self.sorted_by_skill

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
    """Probability that r1 beats r2"""
    return 1 / (1 + 10 ** ((r2 - r1) / 400.0))

def TotalNumTableaus(games):
    return sum(len(g['player_list']) for g in games)

def ComputeWinningStatsByCardPlayedAndSkillLevel(games, skill_ratings, 
                                                 num_cards_by_name):
    def CardSkillYielder(player_result, game):
        skill_info = skill_ratings.GetSkillInfo(player_result['name'])
        for idx, card in enumerate(player_result['cards']):
            if not (idx == 0 and card in HOMEWORLDS):
                yield (card, skill_info.rating, skill_info.wins, 
                       skill_info.exp_wins)
    bucketted_stats = ComputeWinningStatsByBucket(games, CardSkillYielder)

    grouped_by_card = {}

    for bucket_info in bucketted_stats:
        key, win_rate, exp_wins = bucket_info
        card, rating, player_wins, player_exp_wins = key
        if not card in grouped_by_card:
            grouped_by_card[card] = {'weighted_rating': 0.0,
                                     'player_wins': 0.0,
                                     'player_exp_wins': 0.0,
                                     'wins': 0.0,
                                     'exp_wins': 0.0,
                                     'frequency': 0}
        card_stats = grouped_by_card[card]
        card_stats['weighted_rating'] += rating * exp_wins
        card_stats['player_wins'] += player_wins
        card_stats['player_exp_wins'] += player_exp_wins
        card_stats['wins'] += win_rate * exp_wins
        card_stats['exp_wins'] += exp_wins
        card_stats['frequency'] += bucket_info.frequency

    total_tableaus = float(TotalNumTableaus(games))

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
        
        card_stats['prob_per_card'] = card_stats['frequency'] / (
            total_tableaus * num_cards_by_name[card])
        del card_stats['frequency']

    return grouped_by_card

def FilterOutNonGoals(games):
    return [g for g in games if 'goals' in g]

class HomeworldGoalAnalysis:
    def __init__(self, games):
        games = FilterOutNonGoals(games)
        def HomeworldGoalYielder(player_result, game):
            for goal in game['goals']:
                yield Homeworld(player_result), goal
        self.bucketted_by_homeworld_goal = ComputeWinningStatsByBucket(
            games, HomeworldGoalYielder)
        self.keyed_by_homeworld_goal = {}
        for (homeworld, goal), win_rate, exp_wins in (
            self.bucketted_by_homeworld_goal):
            self.keyed_by_homeworld_goal[(homeworld, goal)] = win_rate

        self.bucketted_by_homeworld = ComputeWinningStatsByHomeworld(games)

    def RenderStatsAsHtml(self):
        html = '<table border=1><tr><td>Homeworld</td><td>'
        html += 'Baseline Winning Rate</td>'
        for goal in GOALS:
            html += '<td>%s</td>' % goal
        html += '</tr>\n'

        for homeworld, win_rate, exp_wins in self.bucketted_by_homeworld:
            html += '<tr><td>%s</td><td>%.3f</td>' % (homeworld, win_rate)
            for goal in GOALS:
                diff = (
                    self.keyed_by_homeworld_goal[(homeworld, goal)] - win_rate)
                html += '<td>%.3f</td>' % diff
            html += '</tr>\n'
        return html

    def RenderToJson(self):
        ret = []
        for homeworld, win_rate, exp_wins in self.bucketted_by_homeworld:
            ret.append({'homeworld': homeworld, 'win_rate': win_rate,
                        'adjusted_rate': []})
            for goal in GOALS:
                ret[-1]['adjusted_rate'].append(
                    self.keyed_by_homeworld_goal[(homeworld, goal)])
        return json.dumps(ret)


def ComputeWinStatsByHomeworldSkillLevel(games, skill_ratings, card_info):
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
        header_fmt = ('<table border=1><tr><td>%s</td><td>Num Games'
                      '</td><td>Percentage</td></tr>' )
        html = '<a name="overview">'
        html += '<h2>Overview</h2>'
        html += '<div class="h3">'
        html += 'Total games analyzed: %d<br>\n' % self.games_played
        html += 'Last seen game number: %d<br>\n' % self.max_game_no
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
        html += '</div>'
        return html

def PlayerFile(player_name):
    return 'player_' + player_name + '.html'

def PlayerLink(player_name):
    return '<a href="' + PlayerFile(player_name) + '">' + player_name + '</a>'

def CardsPerName(card_info):
    ret = {}
    for card in card_info:
        if card['Type'] == 'Development':
            ret[card['Name']] = 2 - (card['Cost'] == '6')
            if card['Name'] == 'Contact Specialist':
                ret[card['Name']] = 3
        else:
            ret[card['Name']] = 1
    return ret

def RenderTopPage(games, rankings_by_game_type):
    overview = OverviewStats(games)
    top_out = open('output/index.html', 'w')

    top_out.write('<html><head><title>' + TITLE + '</title>' + JS_INCLUDE + 
                  CSS + '<head>\n')

    top_out.write('<body>')
    top_out.write(INTRO_BLURB)
    top_out.write(overview.RenderAsHTMLTable())

    gathering_storm_games = [g for g in games if g['advanced']]
    top_out.write(WINNING_RATE_VS_PLAY_RATE_DESCRIPTION)
    top_out.write('From %d Gathering Storm games.<br>\n' %
                  len(gathering_storm_games))
    card_info = list(csv.DictReader(open('card_attributes.csv', 'r')))
    num_cards_per_name = CardsPerName(card_info)
    card_info_dict = dict((x["Name"], x) for x in card_info)
    card_win_info = ComputeWinningStatsByCardPlayedAndSkillLevel(
        gathering_storm_games, rankings_by_game_type.AllGamesRatings(),
        num_cards_per_name)


    top_out.write("""
<script type="text/javascript">
var cardInfo = %s;
</script>
""" % json.dumps(card_info_dict, indent=2))

    top_out.write("""
<canvas id="cardWinInfoCanvas" height="500" width="800"></canvas>
<script type="text/javascript">
  var cardWinInfo = %s
  RenderCardWinInfo(cardWinInfo,document.getElementById("cardWinInfoCanvas"));
</script>)
""" % json.dumps(card_win_info, indent=2))

    homeworld_goal_analysis = HomeworldGoalAnalysis(games)
    top_out.write(homeworld_goal_analysis.RenderStatsAsHtml());
    top_out.write('<h2>Goal Influence</h2>' +
                  '<h3>Goal Influence Graph</h3>' +
                  HOMEWORLD_WINNING_RATE_DESCRIPTION +
                  '<canvas id="homeworld_goal_canvas" height=500 width=800>' +
                  '</canvas>'
                  )
    top_out.write('<script type="text/javascript">\n' +
                  'var homeworld_goal_data = ' +
                  homeworld_goal_analysis.RenderToJson() + ';\n' +
                  'RenderHomeworldGoalData("homeworld_goal_canvas", '
                  'homeworld_goal_data);\n' +
                  '</script>');

    top_out.write('<h3>Goal Influence Table</h3><table border=1>')
    rankings_by_game_type.RenderAllRankingsAsHTML(top_out)
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

def GoalGame(game):
    return 'goals' in game and game['goals']

def TwoPlayerAdvanced(game):
    return len(game['player_list']) == 2 and game['advanced']

def TwoPlayerNotAdvanced(game):
    return  len(game['player_list']) == 2 and not game['advanced']

class RankingByGameTypeAnalysis:
    def __init__(self, games):
        self.filters = [
            ('all games', 10, lambda game: True),
            ('goal games', 10, lambda game: GoalGame(game)),
            ('non goal games', 10, lambda game: not GoalGame(game)),
            ('2 player adv', 10, TwoPlayerAdvanced),
            ('2 player not adv', 10, TwoPlayerNotAdvanced),
            ('3 player', 7, lambda game: len(game['player_list']) == 3),
            ('4 player', 5, lambda game: len(game['player_list']) == 4)
            ]
        self.filt_game_lists = [[] for filt in self.filters]
        for game in games:
            for (_, _, filter_func), filt_list in zip(
                self.filters, self.filt_game_lists):
                if filter_func(game):
                    filt_list.append(game)
        self.rating_systems = [SkillRatings(games, EloSkillModel(BASE_SKILL,
                                            MOVEMENT_CONST)) for games in
                               self.filt_game_lists]
        #for i in [5, 7, 10, 15]:
        #    print i, SkillRatings(games, EloSkillModel(BASE_SKILL, i)).ModelPerformance()

    def AllGamesRatings(self):
        return self.rating_systems[0]

    def RenderAllRankingsAsHTML(self, top_out):
        top_out.write('<h2>Player rankings by game type</h2>')
        top_out.write(RATING_BLURB)
        top_out.write('Total players %d<br>\n' %
                      self.rating_systems[0].NumPlayers())
        top_out.write('<table border=1>')

        top_out.write('<tr><td>Player Name</td>')
        for filt_name, _, filt_func in self.filters:
            top_out.write('<td>' + filt_name + '</td>')
        top_out.write('<tr>\n')

        for player_name, skill in self.rating_systems[0].PlayersSortedBySkill():
            top_out.write('<tr><td>' + PlayerLink(player_name) + '</td>')
            for rating_system, (_, games_req, _), in zip(self.rating_systems,
                                                         self.filters):
                if (rating_system.HasPlayer(player_name) and
                    rating_system.GetSkillInfo(player_name).games_played
                    >= games_req):
                    contents = '%d (%.1f%%)' % (
                        rating_system.GetSkillInfo(player_name).rating,
                        rating_system.GetPercentile(player_name))
                else:
                    contents = ''
                top_out.write('<td>' + contents + '</td>')
            top_out.write('</tr>')
        top_out.write('</table>')



def RenderPlayerPage(player, player_games, by_game_type_analysis):
    overview = OverviewStats(player_games)
    player_out = open('output/' + PlayerFile(player), 'w')
    player_out.write('<html><head><title> %s %s'
                     '</title></head><body>\n' % (TITLE, player))

    player_out.write('<a href="#overview">Overview</a>\n'
                     '<a href="#homeworld_flow">Homeworld Rating Flow</a>'
                     '<a href="#player_flow">Player Rating Flow</a>\n'
                     '<br>\n')
    player_out.write(overview.RenderAsHTMLTable())

    player_out.write('<a name="homeworld_flow"> '
                     '<table border=1><tr><td>Homeworld</td>'
                     '<td>Net rating change when playing<td></tr>')
    all_games_ratings = by_game_type_analysis.AllGamesRatings()
    WritePlayerFloatPairsAsTableRows(
        player_out, all_games_ratings.GetHomeworldSkillFlow(player))

    player_out.write('</table>')

    player_out.write('<a name="player_flow"> '
                     '<table border=1><tr><td>Opponent</td>'
                     '<td>Net rating flow</td></tr>\n')
    linked_out = [(PlayerLink(o), s) for o, s in
                  all_games_ratings.GetRatingFlow(player)]
    WritePlayerFloatPairsAsTableRows(player_out, linked_out)
    player_out.write('</table>')

    player_out.write('</html>')

def CopyOrLink(fn, debugging_on):
    if os.access('output/' + fn, os.O_RDONLY):
        os.remove('output/' + fn)
    if not debugging_on:
        shutil.copy(fn, 'output')
    else:
        os.system('ln -s ./../%s output/%s' % (fn, fn))
    

def CopySupportFilesToOutput(debugging_on):
    CopyOrLink('genie_analysis.js', debugging_on)
    CopyOrLink('style.css', debugging_on)
    
    if not os.access('output/flot', os.O_RDONLY):
        shutil.copytree('flot', 'output/flot')
    if not os.access('output/images', os.O_RDONLY):
        shutil.copytree('images', 'output/images')

def main():
    debugging_on = False
    if len(sys.argv) > 1:
        debugging_on = True

    if debugging_on:
        games = eval(open('terse_games.json').read())
    else:
        games = eval(open('condensed_games.json').read())
        open('terse_games.json', 'w').write(str(random.sample(games, 1000)))

    by_game_type_analysis = RankingByGameTypeAnalysis(games)
    if not os.access('output', os.O_RDONLY):
        os.mkdir('output')
    RenderTopPage(games, by_game_type_analysis)

    for player, player_games in PlayerToGameList(games).iteritems():
        RenderPlayerPage(player, player_games, by_game_type_analysis)
    CopySupportFilesToOutput(debugging_on)

if __name__ == '__main__':
    main()

