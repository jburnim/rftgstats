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

DISCARDABLE_CARDS = ['Doomed World', 'Colony Ship', 'New Military Tactics']

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
<a href="http://mozilla.org">Firefox 3</a> or <a
href="http://www.google.com/chrome">Chrome</a>.  Contributions
welcome!</p>

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
<p>This graph shows data by analyzing end game tableaus. </p>
<p>Strong cards have high winning rates and tend to be played more often.  
You can click on a card's icon to see its name.</p>
<p>Cards played as homeworlds are excluded from the data, so that they don't
totally skew the play rate.  All the analyzed games are using the Gathering 
Storm expansion so the play rate distribution is fair.</p>
<p>The absolute play rate is divided by the number of instances of the card
in the deck, so investment credits is divided by 2, and contact specialist
is divided by 3.  By doing so, cheap developments do not dominate the play
frequency.</p>
<p>
"""

HOMEWORLD_WINNING_RATE_DESCRIPTION = """<p>Influence of goal on winning rate
of homeworld.</p>
<p>The baseline winning rate of each homeworld is the fat dot.
The winning rate with the goal is the end of the segment without
the dot.  Hence, you can tell the absolute rate of winning by the
end of the line, and the relative change by the magnitude of the line.</p>
"""


RATING_BLURB = """<h3>Rating Methodology</h3>
<p>Each column comes from running an Elo rating algorithm on a
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

def InitCardInfoDict():
    card_info = list(csv.DictReader(open('card_attributes.csv', 'r')))
    card_info_dict = dict((x["Name"], x) for x in card_info)
    return card_info_dict

class CardInfo:
    card_info_dict = InitCardInfoDict()

    @staticmethod
    def CardFrequencyInDeck(card_name):
        card = CardInfo.card_info_dict[card_name]
        if card['Name'] == 'Contact Specialist':
            return 3
        if card['Type'] == 'Development':
            return 2 - (card['Cost'] == '6')
        return 1


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

def Score(result):
    return result['points'] * 100 + result['goods'] + result['hand']

def WinningScore(game):
    return max(Score(result) for result in game['player_list'])

def ComputeWinningStatsByBucket(games, bucketter, rating_system = None):
    """ Returns a list of BucketInfo sorted by win_rate"""
    wins = AccumDict()
    norm_exp_wins = AccumDict()
    freq = AccumDict()
    for game in FilterOutTies(games):
        winners = GameWinners(game)
        assert len(winners) == 1

        won_game_prob = {}
        winner_name = winners[0]['name']

        game_no = game['game_no']
        n = float(len(game['player_list']))
        for player_result in game['player_list']:
            player_name = player_result['name']
            if rating_system:
                won_game_prob[player_name] = (
                    rating_system.ProbWonAtGameNo(game_no, player_name))
            else:
                won_game_prob[player_name] = 1.0 / n
 
        for player_result in game['player_list']:
            for key in bucketter(player_result, game):
                freq.Add(key, 1)
                norm_exp_wins.Add(
                    key, n * won_game_prob[player_result['name']])
                if player_result['name'] == winner_name:
                    wins.Add(key, n)


    win_rates = []
    for bucket in norm_exp_wins:
        win_rates.append(BucketInfo(
                bucket, wins[bucket], norm_exp_wins[bucket], freq[bucket]))

    win_rates.sort(key = lambda x: -x.win_rate)
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

def NormalizeProbs(prob_list):
    s = sum(prob_list)
    return [i / s for i in prob_list]

class MultiSkillModelProbProd(EloSkillModel):
    def __init__(self, base_rating, move_const):
        EloSkillModel.__init__(self, base_rating, move_const)

    def MultiplayerWinProb(self, player_list):
        ret = []
        for idx, player1 in enumerate(player_list):
            ret.append(1)
            for player2 in player_list:
                if player1 != player2:
                    ret[idx] = ret[idx] * self.Predict(player1, player2)
                    
        return NormalizeProbs(ret)

class SkillRatings:
    def __init__(self, games, skill_model):
        self.skill_model = skill_model
	self.rating_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))
	self.rating_by_homeworld_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))
        self.model_log_loss = 0.0
        self.winner_pred_log_loss = 0.0
        self.ratings_at_game_no = collections.defaultdict(dict)
        self.prob_beat_winner = collections.defaultdict(dict)

        for game in FilterOutTies(games):
            winner = GameWinners(game)[0]
            win_name = winner['name']
            losers = []
            for player in game['player_list']:
                player_name = player['name']
                rating = self.GetSkillInfo(player_name).rating
                game_no = game['game_no']
                self.ratings_at_game_no[game_no][player_name] = rating
                if player_name == win_name:
                    continue
                loser_name = player['name']
                win_prob = self.skill_model.Predict(win_name, loser_name)
                self.prob_beat_winner[game_no][loser_name] = win_prob
                self.model_log_loss += math.log(win_prob) / math.log(2)
                losers.append(loser_name)

            if hasattr(skill_model, 'MultiplayerWinProb'):
                player_names = [player['name'] for player in
                                game['player_list']]
                winner_idx = player_names.index(win_name)
                pred = skill_model.MultiplayerWinProb(player_names)[winner_idx]
                self.winner_pred_log_loss += math.log(pred) / math.log(2)

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
                # This symettry is wrong for rating systems which are more
                # general than Elo.
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

    def WinProportionAtGameNo(self, game_no, player):
        ret = 1.0
        for other_player in self.ratings_at_game_no[game_no]:
            if other_player == player:
                continue
            ret *= EloProbability(self.ratings_at_game_no[player],
                                  self.ratings_at_game_no[other_player])
        return ret

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

def FilterDiscardables(mapping):
    ret = dict(mapping)
    for card in DISCARDABLE_CARDS:
        if card in mapping:
            del ret[card]
    return ret

class BucketInfo:
    def __init__(self, key, win_points, norm_exp_win_points, frequency):
        self.key = key
        self.win_points = win_points
        self.win_rate = win_points / frequency
        self.frequency = frequency
        self.norm_exp_win_points = norm_exp_win_points
        self.norm_win_rate = win_points / norm_exp_win_points
        
# this has the overly non-general assumption that the card is the key, rather
# than simply a part of the key
def ComputeAdvancedByCardStats(games, card_yielder):
    bucketted_stats = ComputeWinningStatsByBucket(games, card_yielder)
    
    grouped_by_card = {}
    total_tableaus = float(TotalNumTableaus(games))
    for bucket_info in bucketted_stats:
        card = bucket_info.key
        grouped_by_card[card] = {
            'win_rate': bucket_info.win_rate,
            'norm_win_rate': bucket_info.norm_win_rate,
            'prob_per_card': (bucket_info.frequency * total_tableaus /
                              CardInfo.CardFrequencyInDeck(card))
                              }       
    return grouped_by_card
    

def ComputeWinningStatsByCardPlayedAndSkillLevel(games, skill_ratings):
    def NonHomeworldCardYielder(player_result, game):
        skill_info = skill_ratings.GetSkillInfo(player_result['name'])
        for idx, card in enumerate(player_result['cards']):
            if not (idx == 0 and card in HOMEWORLDS or
                    card == 'Gambling World'):
                yield card
    return FilterDiscardables(ComputeAdvancedByCardStats(
            games, NonHomeworldCardYielder))
            

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
        for bucket in self.bucketted_by_homeworld_goal:
            self.keyed_by_homeworld_goal[bucket.key] = bucket.win_rate

        self.bucketted_by_homeworld = ComputeWinningStatsByHomeworld(games)

    def RenderStatsAsHtml(self):
        html = '<table border=1><tr><td>Homeworld</td><td>'
        html += 'Baseline Winning Rate</td>'
        for goal in GOALS:
            html += '<td>%s</td>' % goal
        html += '</tr>\n'

        for bucket_info in self.bucketted_by_homeworld:
            homeworld = bucket_info.key
            win_rate = bucket_info.win_rate
            html += '<tr><td>%s</td><td>%.3f</td>' % (homeworld, win_rate)
            for goal in GOALS:
                diff = (
                    self.keyed_by_homeworld_goal[(homeworld, goal)] - win_rate)
                html += '<td>%.3f</td>' % diff
            html += '</tr>\n'
        html += '</table>\n'
        return html

    def RenderToJson(self):
        ret = []
        for bucket_info in self.bucketted_by_homeworld:
            homeworld = bucket_info.key
            ret.append({'homeworld': homeworld,
                        'win_rate': bucket_info.win_rate,
                        'adjusted_rate': []})
            for goal in GOALS:
                ret[-1]['adjusted_rate'].append(
                    self.keyed_by_homeworld_goal[(homeworld, goal)])
        return json.dumps(ret)


# not called, might be broken by refactor of bucketinfo
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
    keyed_by_hw_rough_skill = {}
    for bucket in bucketted_stats:
        keyed_by_hw_rough_skill[bucket.key] = (bucket.win_rate,
                                               bucket.expected_wins)
    print keyed_by_hw_rough_skill
    ret = {}
    for homeworld in HOMEWORLDS:
        ret[homeworld] = []
        for i in range(NUM_SKILL_BUCKETS):
            ret[homeworld].append(keyed_by_hw_rough_skill[(homeworld, i)])
    return ret

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
        html += '</a>'
        html += '<div class="h3">'
        html += 'Total games analyzed: %d<br>\n' % self.games_played
        html += 'Last seen game number: %d<br>\n' % self.max_game_no
        html += header_fmt % 'Player Size'
        for size in self.player_size:
            html += '<tr><td>%s</td><td>%d</td><td>%d%%</td></tr>' % (
                ( size[0], size[1], int( 100. * size[1] / self.games_played )))
        html += '</table border=1>'
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

def RenderTopPage(games, rankings_by_game_type):
    overview = OverviewStats(games)
    top_out = open('output/index.html', 'w')

    top_out.write('<html><head><title>' + TITLE + '</title>' + JS_INCLUDE + 
                  CSS + '</head>\n')

    top_out.write('<body>')
    top_out.write(INTRO_BLURB)
    top_out.write(overview.RenderAsHTMLTable())

    gathering_storm_games = [g for g in games if g['advanced']]
    top_out.write(WINNING_RATE_VS_PLAY_RATE_DESCRIPTION)
    top_out.write('<p>From %d Gathering Storm games.</p><br>\n' %
                  len(gathering_storm_games))    
    card_win_info = ComputeWinningStatsByCardPlayedAndSkillLevel(
        gathering_storm_games, rankings_by_game_type.AllGamesRatings())

    top_out.write("""
<script type="text/javascript">
var cardInfo = %s;
</script>
""" % json.dumps(CardInfo.card_info_dict, indent=2))

    top_out.write("""
<p>
<table><tr><td>Winning Rate</td>
   <td><canvas id="cardWinInfoCanvas" height="600" width="800"></canvas></td>
</tr>
<tr>
<td></td><td><center>
Probability instance of card appears on tableau</center></td>
</tr>
</table>
<script type="text/javascript">
  var cardWinInfo = %s;
  RenderCardWinInfo(cardWinInfo,document.getElementById("cardWinInfoCanvas"));
</script>
</p>
""" % json.dumps(card_win_info, indent=2))

    homeworld_goal_analysis = HomeworldGoalAnalysis(games)    
    top_out.write("""
<h2>Goal Influence</h2>
  <h3>Goal Influence Graph</h3>
      %s
<p><canvas id="homeworld_goal_canvas" height=500 width=800>
</canvas></p>""" % HOMEWORLD_WINNING_RATE_DESCRIPTION)
            
    top_out.write('<script type="text/javascript">\n' +
                  'var homeworld_goal_data = ' +
                  homeworld_goal_analysis.RenderToJson() + ';\n' +
                  'RenderHomeworldGoalData("homeworld_goal_canvas", '
                  'homeworld_goal_data);\n' +
                  '</script>');

    top_out.write('<h3>Goal Influence Table</h3><p>')
    top_out.write(homeworld_goal_analysis.RenderStatsAsHtml());
    
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

        self.rating_systems = [
            SkillRatings(games, EloSkillModel(BASE_SKILL, MOVEMENT_CONST))
            for games in self.filt_game_lists]

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


def KeyGamesByOpponent(target_player, games):
    ret = collections.defaultdict(list)
    for game in games:
        for player in game['player_list']:
            if player['name'] != target_player:
                ret[player['name']].append(game)
    return ret

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

    paired_games = KeyGamesByOpponent(player, player_games)

    player_out.write('<a name="player_flow"> '
                     '<table border=1><tr><td>Opponent</td>'
                     '<td>Net rating flow</td></tr>\n')
    for opponent, skill_flow in all_games_ratings.GetRatingFlow(player):
        player_out.write('<tr><td>%s</td><td>%.1f</td>' % (
                PlayerLink(opponent), skill_flow))

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
