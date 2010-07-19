#!/usr/bin/python

import collections

from deck_info import DeckInfo, RVI_HOMEWORLDS, GOOD_TYPES, PROD_TYPES, EXPANSIONS, BaseDeckInfo, GSDeckInfo, DISCARDABLE_CARDS
import tableau_scorer
import math
import pprint
import random
import re
import os
import simplejson as json
import shutil
import sys
import time

EXP_ABBREV = ['base', 'tgs', 'rvi']

BASE_SKILL = 1500
MOVEMENT_CONST = 15

GS_GOALS = [
    'Most Prod worlds',
    'Most Developments',
    'Most Military',
    'Most Rares or Novelties',
    'First 5 vps',
    'First 6 pt dev',
    'First all phase powers',
    'First discard',
    'First all worlds',
    'First 3 aliens',
    ]

RVI_GOALS = GS_GOALS + [
    'Most Explore Powers',
    'Most Rebel Military Worlds',
    'First 4 Prod goods',
    'First 3 Uplift',
    'First 8 Tableau'
]

MATCH_TRAILING_DIGITS = re.compile('(\d+)$')

# move to deck info

TITLE = 'RFTGStats.com: Race for the Galaxy Statistics'
JS_INCLUDE = (
    '<script type="text/javascript" src="card_attrs.js"></script>'
    '<script type="text/javascript" src="genie_analysis.js"></script>'
    )
CSS = '<link rel="stylesheet" type="text/css" href="style.css" />'

INTRO_BLURB = """<h2>Introduction</h2>
<p>Hi, welcome to Race for the Galaxy
statistics page by <a href="player_rrenaud.html">rrenaud</a>, 
<a href="player_Danny.html">Danny</a>, and 
<a href="player_Aragos.html">Aragos</a>.
All of the data here is collected from the wonderful
<a href="http://genie.game-host.org">Genie online Race for the Galaxy server
</a> or the <a href="http://flexboardgames.com/Rftg.html">Flexboardgames Race
for the Galaxy server</a>.  The code that computes this information is 
open source and available
at <a href="http://code.google.com/p/rftgstats">the rftgstats google code
project</a>.  These stats look best when viewed with a recent version of 
<a href="http://mozilla.org">Firefox 3</a> or <a
href="http://www.google.com/chrome">Chrome</a>.  The raw data from genie is
available <a href="condensed_games.json.gz">here</a>. The raw data from flex is
available <a href="condensed_flex.json.gz">here</a>. Contributions
welcome!</p>"""

SIX_DEV_BLURB = """<h3>Sub-analysis</h3>
<p>Here is a graph of the number of points each <a href="six_dev_analysis.html">
six cost development scores</a> when it both when a 6 dev is played and when 
not played."""

CARDS_GAME_SIZE = """<p>Here is an animated graph of the winning 
rate/play rate as a function of <a href="game_size.html">the number of 
players</a>."""

CARDS_GOALS = """<p>Here is an animated graph on the win rate play/rate as 
a function of the <a href="goals_vs_nongoals.html">inclusion of goals</a>."""

WINNING_RATES_BLURB = """<h3>A brief discussion about <i>Winning Rates</i></h3>
<p>
An <i>n</i> player game is worth <i>n</i> points.  The wining rate is the
number of points accumulated divided by the number of games played.
Thus, if you win a 4 player game, lose a 3 player game, and lose a 2
player game, your winning rate would (4 + 0 + 0) / 3 = 1.33.
Thus, a totally average and optimally balanced homeworld will have a
winning rate of near 1 after many games.  Likewise, a player whose skill
is totally representative of the distribution of the player population will
have a winning rate of 1.

<h3><i>Skill Normalized</i> win rates</h3>
<p>One problem with win rates is that they do not scale well with player skill.
Therefore, I compute a prior probability to win the game for each player based
on the player ratings before the start of a game.  Consider a hypothetical game
between players rrenaud, fairgr, and kingcong.  Assume that rating system
predicts that the players will win with .3, .5, and .2 respectively.  Then if
fairgr wins, he (or specifically in the winning rate graph, the cards he played)
will be awarded 3 points, and will be expected to win 1.5 points.  If rrenaud
wins, the cards he played will be awarded 3 points, and expected to win 
.9 points.  If kingcong wins, her cards wil be awarded 3 points, and are 
expected to win .6 points.  I call the the total awarded poins divided by 
the expected number of points the <i>Skill normalized</i> win rate, and it
is what is plotted in the card graph below."""

WINNING_RATE_VS_PLAY_RATE_DESCRIPTION = """<p>
<h2>Skill normalized card winning rate vs play rate</h2>
<p>This graph shows data by analyzing end game tableaus. </p>
<p>Strong cards have high skill normalized winning rates and 
tend to be played more often.  
You can click on a card's icon to see its name.</p>
<p>Cards played as homeworlds are excluded from the data, so that they don't
totally skew the play rate.
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
<li>This includes games from flex, which are currently all assumed to occur
after the last game on genie.</li>
</ul>
"""

def GoalVector(goals):
    ret = [0] * len(GS_GOALS)
    for goal in goals:
        ret[GS_GOALS.index(goal)] = 1
    return ret

def GetAndRemove(dict, key):
    ret = dict[key]
    del dict[key]
    return ret

class FixedExpansionGameSet:
    def __init__(self, games, exp_ver):
        self.games = [g for g in games if g.Expansion() == exp_ver]
        self.exp_ver = exp_ver
        self.exp_name = EXPANSIONS[exp_ver]

        self.goals = []
        self.deck = BaseDeckInfo
        if exp_ver == 1:
            self.goals = GS_GOALS
            self.deck = GSDeckInfo
        elif exp_ver == 2:
            self.goals = RVI_GOALS
            self.deck = DeckInfo

    def Goals(self):
        return self.goals

    def Deck(self):
        return self.deck


class Game:
    def __init__(self, game_dict):
        n = float(len(game_dict['player_list']))

        self.player_list = map(PlayerResult, game_dict['player_list'])
        del game_dict['player_list']

        for player_result in self.PlayerList():
            player_result.SetWinPoints(0.0)
            player_result.SetGame(self)
        winners = self.GameWinners()
        for player_result in winners:
            player_result.SetWinPoints(n / len(winners))
        self.player_list.sort(key = PlayerResult.WinPoints, reverse=True)

        self.goals = []
        if 'goals' in game_dict:
            self.goals = GetAndRemove(game_dict, 'goals')

        self.game_id = GetAndRemove(game_dict, 'game_id')
        self.expansion = GetAndRemove(game_dict, 'expansion')
        self.advanced = GetAndRemove(game_dict, 'advanced')

        if '_id' in game_dict:
            del game_dict['_id']

    def __str__(self):
        player_info_string = '\t' + '\n\t'.join(
            str(p) for p in self.PlayerList())
        return '%s %s\n' % (self.GameId(), player_info_string)

    def WinningScore(self):
        return max(result.Score() for result in self.PlayerList())

    def GameWinners(self):
        max_score = self.WinningScore()
        return [p for p in self.PlayerList() if p.Score() == max_score]

    def Tied(self):
        return len(self.GameWinners()) > 1

    def PlayerList(self):
        return self.player_list

    def GameId(self):
        return self.game_id

    def GameNo(self):
        return int(MATCH_TRAILING_DIGITS.search(self.game_id).group(1))

    def Goals(self):
        return self.goals

    def GoalVector(self):
        return GoalVector(self.Goals())

    def GoalGame(self):
        return len(self.goals) > 0

    def Expansion(self):
        return self.expansion

    def Advanced(self):
        return self.advanced

    def PlayerResultForName(self, player_name):
        for player in self.PlayerList():
            if player.Name() == player_name:
                return player
        raise ValueError


class PlayerResult:
    def __init__(self, player_info_dict):
        self.cards = GetAndRemove(player_info_dict, 'cards')

        self.homeworld = ''
        # This misclassifes initial doomed world settles that are
        # other homeworlds.  I doubt that happens all that often
        # though.
        if self.cards[0] in RVI_HOMEWORLDS:
            self.homeworld = self.cards[0]
        else:
            self.homeworld = 'Doomed World'

        self.name = GetAndRemove(player_info_dict, 'name')
        self.points = GetAndRemove(player_info_dict, 'points')
        self.hand = GetAndRemove(player_info_dict, 'hand')
        self.goods = GetAndRemove(player_info_dict, 'goods')

        self.goals = []
        if 'goals' in player_info_dict:
            self.goals = GetAndRemove(player_info_dict, 'goals')
        self.chips = GetAndRemove(player_info_dict, 'chips')

        assert len(player_info_dict) == 0, player_info_dict.keys()

    def Homeworld(self):
        return self.homeworld

    def SetGame(self, game):
        self.game = game

    def Game(self):
        return self.game

    def SetWinPoints(self, win_points):
        self.win_points = win_points

    def WinPoints(self):
        return self.win_points

    def Points(self):
        return self.points

    def Score(self):
        return self.points * 100 + self.goods + self.hand

    def Chips(self):
        return self.chips

    def Cards(self):
        return self.cards

    def Goals(self):
        return self.goals

    def GoalVector(self, weight = 1):
        ret = [0] * len(GS_GOALS)
        for goal in self.goals:
            ret[GS_GOALS.index(goal)] = weight
        return ret

    def __str__(self):
        card_str = ','.join(self.cards)
        goal_str = ','.join(self.goals)
        return '%s %d %d %s <%s>' % (
            self.Name(), self.points, self.chips, card_str, goal_str)

    def __repr__(self):
        return self.__str__()

    def WonGoalVector(self):
        return GoalVector(self.goals)

    def CardVector(self, record_places = True):
        card_vec = [0] * DeckInfo.NumCards()
        dw_comp = 0
        if (self.Homeworld() == 'Doomed World' and 
            self.Cards()[0] != 'Doomed World'):
            dw_comp += 1
            
        card_vec[DeckInfo.CardIndexByName(self.Homeworld())] = 1
        for idx, card in enumerate(self.Cards()):
            card_ind = DeckInfo.CardIndexByName(card)
            if record_places:
                card_vec[card_ind] = dw_comp + idx + 1
            else:
                card_vec[card_ind] = 1
        return card_vec

    def Name(self):
        return self.name


class RandomVariableObserver:
    def __init__(self):
        self.freq = 0
        self.sum = 0.0
        self.sum_sq = 0.0

    def AddOutcome(self, val):
        self.freq += 1
        self.sum += val
        self.sum_sq += val * val

    def Frequency(self):
        return self.freq

    def Mean(self):
        return self.sum / (self.freq or 1)

    def Variance(self):
        if self.freq <= 1:
            return 1e10
        return (self.sum_sq - (self.sum ** 2) / self.freq) / (self.freq - 1)

    def StdDev(self):
        return self.Variance() ** .5

    def SampleStdDev(self):
        return (self.Variance() / (self.freq or 1)) ** .5
        
def ComputeWinningStatsByHomeworld(games, rating_system):
    def HomeworldYielder(player_result, game):
        yield player_result.Homeworld()
    return ComputeStatsByBucketFromGames(games, HomeworldYielder,
                                         rating_system)

def ComputeStatsByBucketFromPlayerResults(player_results, 
                                          bucketter, rating_system):
    wins = collections.defaultdict(RandomVariableObserver)
    norm_wins = collections.defaultdict(RandomVariableObserver)

    for player_result in player_results:
        game = player_result.Game()
        game_id = game.GameId()
        n = float(len(game.PlayerList()))
        player_name = player_result.Name()
        if rating_system:
            won_prob = rating_system.ProbWonAtGameId(game_id, player_name)
        else:
            won_prob = 1.0 / n

        normalized_outcome = player_result.WinPoints() / (n * won_prob)
        standard_outcome = player_result.WinPoints()

        for key in bucketter(player_result, game):
            norm_wins[key].AddOutcome(normalized_outcome)
            wins[key].AddOutcome(standard_outcome)

    bucket_infos = []
    for bucket in norm_wins:
        bucket_infos.append(BucketInfo(
                bucket, wins[bucket].Mean(), wins[bucket].SampleStdDev(), 
                norm_wins[bucket].Mean(), norm_wins[bucket].SampleStdDev(), 
                wins[bucket].Frequency()))

    bucket_infos.sort(key = lambda x: -x.win_points)
    return bucket_infos

def PlayerResultsFromGames(games):
    ret = []
    for game in games:
        ret.extend(game.PlayerList())
    return ret

def ComputeStatsByBucketFromGames(games, bucketter, rating_system = None):
    return ComputeStatsByBucketFromPlayerResults(PlayerResultsFromGames(games),
                                                 bucketter, rating_system)

def FilterOutTies(games):
    return [g for g in games if not g.Tied()]

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

class PoweredSkillModelProbProd(EloSkillModel):
    def __init__(self, base_rating, move_const, pow3, pow4):
        EloSkillModel.__init__(self, base_rating, move_const)
        self.pows = [1, 1, 1, pow3, pow4]

    def MultiplayerWinProb(self, player_list):
        ret = []
        for idx, player1 in enumerate(player_list):
            ret.append(1)
            for player2 in player_list:
                if player1 != player2:
                    p = self.Predict(player1, player2) ** self.pows[
                        len(player_list)]
                    ret[idx] = ret[idx] * p
                    
        return NormalizeProbs(ret)
    

class UberNaiveMultiSkillModel(EloSkillModel):
    def __init__(self, base_rating, move_const):
        EloSkillModel.__init__(self, base_rating, move_const)

    def MultiplayerWinProb(self, player_list):
        return [1. / len(player_list)] * len(player_list)

class SkillRatings:
    def __init__(self, games, skill_model):
        self.skill_model = skill_model
	self.rating_flow = collections.defaultdict(
            lambda: collections.defaultdict(float))
	self.rating_by_homeworld_flow = collections.defaultdict(
            lambda: collections.defaultdict(float))
	self.rating_by_opp_homeworld_flow = collections.defaultdict(
            lambda: collections.defaultdict(float))
        self.model_log_loss = 0.0
        self.winner_pred_log_loss = 0.0
        self.ratings_at_game_id = collections.defaultdict(dict)
        self.prob_won_at_game_id = collections.defaultdict(dict)

        for game in FilterOutTies(games):
            winner = game.GameWinners()[0]
            win_name = winner.Name()
            losers = []
            game_id = game.GameId()
            for player in game.PlayerList():
                player_name = player.Name()
                rating = self.GetSkillInfo(player_name).rating
                self.ratings_at_game_id[game_id][player_name] = rating
                if player_name == win_name:
                    continue
                loser_name = player.Name()
                win_prob = self.skill_model.Predict(win_name, loser_name)
                self.model_log_loss += math.log(win_prob) / math.log(2)
                losers.append(loser_name)

            player_names = [player.Name() for player in
                            game.PlayerList()]
            winner_idx = player_names.index(win_name)
            winner_hw = game.PlayerList()[winner_idx].Homeworld()
            multiplayer_win_probs = skill_model.MultiplayerWinProb(
                player_names)
            name_prob_pairs = [(player_name, win_prob) for player_name, win_prob
                               in zip(player_names, multiplayer_win_probs)]
            self.prob_won_at_game_id[game_id] = name_prob_pairs
            pred = multiplayer_win_probs[winner_idx]
            self.winner_pred_log_loss += math.log(pred) / math.log(2)

            delta = self.skill_model.AdjustRatings(win_name, losers)
            for player_name in delta:
                skill_info = self.GetSkillInfo(player_name)
                skill_info.games_played += 1
                skill_info.exp_wins += 1.0 / (len(game.PlayerList()))

                homeworld = game.PlayerResultForName(player_name).Homeworld()

		self.rating_by_homeworld_flow[player_name][homeworld] += (
                    delta[player_name])


                if win_name == player_name:
                    continue

                ohf = self.rating_by_opp_homeworld_flow
                ohf[win_name][homeworld] -= delta[player_name]
                ohf[player_name][winner_hw] += delta[player_name]
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

    def RatingAtGameId(self, game_id, player_name):
        return self.ratings_at_game_id[game_id][player_name]

    def ProbWonAtGameId(self, game_id, player_name):
        name_probs = self.prob_won_at_game_id[game_id]
        for name, prob in name_probs:
            if player_name == name:
                return prob
        raise ValueError()
            

    def ModelPerformance(self):
        return self.model_log_loss

    def GetHomeworldSkillFlow(self, name):
	return SortDictByKeys(self.rating_by_homeworld_flow[name])

    def GetOpponentHomeworldSkillFlow(self, name):
        return SortDictByKeys(self.rating_by_opp_homeworld_flow[name])

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
            for p in g.PlayerList():
                rating = self.GetSkillInfo(p.Name()).rating
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
        player_rating = self.skill_model.GetSkillInfo(player_name).rating
        skill_level = 0
        for bucket in skill_sections:
            if player_rating > bucket:
                skill_level += 1
        return skill_level


def EloProbability(r1, r2):
    """Probability that r1 beats r2"""
    return 1 / (1 + 10 ** ((r2 - r1) / 400.0))

def FilterDiscardables(mapping):
    ret = dict(mapping)
    for card in DISCARDABLE_CARDS:
        if card in mapping:
            del ret[card]
    return ret

class BucketInfo:
    def __init__(self, key, 
                 win_points, win_points_ssd, 
                 norm_win_points, norm_win_points_ssd, frequency):
        self.key = key
        self.win_points = win_points
        self.win_points_ssd = max(win_points_ssd, 0)
        self.frequency = frequency
        self.norm_win_points = norm_win_points
        self.norm_win_points_ssd = norm_win_points_ssd

    def __str__(self):
        return '%s,win points:%f,freq: %f,ssd: %f' % (
            str(self.key), self.win_points, self.frequency, self.win_points_ssd)
        
# this has the overly non-general assumption that the card is the key, rather
# than simply a part of the key
def ComputeByCardStats(player_results, card_yielder, skill_ratings, gameset):
    bucketted_stats = ComputeStatsByBucketFromPlayerResults(
        player_results, card_yielder, skill_ratings)
    
    grouped_by_card = {}
    total_tableaus = float(len(player_results))
    for bucket_info in bucketted_stats:
        card = bucket_info.key
        prob_per_card_name = bucket_info.frequency / total_tableaus
        prob_per_card_name_var = prob_per_card_name * (1 - prob_per_card_name)
        scaled_var = prob_per_card_name_var / total_tableaus
        prob_per_card_name_ssd = scaled_var ** .5
        freq_in_deck = DeckInfo.CardFrequencyInDeck(card, gameset.exp_ver)
        prob_per_card = prob_per_card_name / freq_in_deck
        prob_per_card_ssd = prob_per_card_name_ssd / freq_in_deck
        grouped_by_card[card] = {
            'win_points': bucket_info.win_points,
            'norm_win_points': bucket_info.norm_win_points,
            'norm_win_points_ssd': bucket_info.norm_win_points_ssd,
            'prob_per_card': prob_per_card,
            'prob_per_card_ssd': prob_per_card_ssd
            }
    return grouped_by_card
    

def ComputeWinningStatsByCardPlayed(player_results, skill_ratings, gameset):
    def NonHomeworldCardYielder(player_result, game):
        for idx, card in enumerate(player_result.Cards()):
            if not (idx == 0 and card in RVI_HOMEWORLDS or
                    card == 'Gambling World'):
                yield card
    return FilterDiscardables(ComputeByCardStats(
            player_results, NonHomeworldCardYielder, skill_ratings, gameset))

def VersionInfluenceOnCardStats(games, skill_ratings):
    stats_by_ver = []
    for version_idx, version_abbrev in enumerate(EXP_ABBREV):
        gameset = FixedExpansionGameSet(games, version_idx)
        cur_stats = ComputeWinningStatsByCardPlayed(
            PlayerResultsFromGames(gameset.games), skill_ratings, gameset)
        stats_by_ver.append({'title': version_abbrev,
                             'data': cur_stats})
    return stats_by_ver

def GoalInfluenceOnCardStats(player_results, skill_ratings, gameset):
    with_goals, without_goals = [], []
    for player_result in player_results:
        if player_result.Game().GoalGame():
            with_goals.append(player_result)
        else:
            without_goals.append(player_result)
    return [
        {'title': 'Without goals',
         'data': ComputeWinningStatsByCardPlayed(without_goals, 
                                                 skill_ratings, gameset)},
        {'title': 'With goals',
         'data': ComputeWinningStatsByCardPlayed(with_goals, 
                                                 skill_ratings, gameset)}
        ]

def GameSizeInfluenceOnCardStats(player_results, ratings, gameset):
    games_by_size = collections.defaultdict(list)
    for player_result in player_results:
        game_size = len(player_result.Game().PlayerList())
        games_by_size[game_size].append(player_result)
    return [
        {'title': 'Game Size %d' % size,
         'data': ComputeWinningStatsByCardPlayed(games_by_size[size], 
                                                 ratings, gameset)}
        for size in sorted(games_by_size.keys())
        ]

def FilterOutNonGoals(games):
    return [g for g in games if g.GoalGame()]

class HomeworldGoalAnalysis:
    def __init__(self, games, gameset, player_ratings):
        self.gameset = gameset
        games = FilterOutNonGoals(games)
        def HomeworldGoalYielder(player_result, game):
            for goal in game.Goals():
                yield player_result.Homeworld(), goal
        self.bucketted_by_homeworld_goal = ComputeStatsByBucketFromGames(
            games, HomeworldGoalYielder, player_ratings)
        self.keyed_by_homeworld_goal = {}
        for bucket in self.bucketted_by_homeworld_goal:
            self.keyed_by_homeworld_goal[bucket.key] = bucket.norm_win_points

        self.bucketted_by_homeworld = ComputeWinningStatsByHomeworld(
            games, player_ratings)
            

    def RenderStatsAsHtml(self):
        html = '<table border=1><tr><td>Homeworld</td>'
        html += '<td>Baseline Winning Rate</td>'
        html += '<td>Frequency</td>'
        for goal in self.gameset.Goals():
            html += '<td>%s</td>' % goal
        html += '</tr>\n'

        for bucket_info in self.bucketted_by_homeworld:
            homeworld = bucket_info.key
            win_points = bucket_info.norm_win_points
            freq = bucket_info.frequency
            html += '<tr><td>%s</td><td>%.3f</td><td>%d</td>' % (
                homeworld, win_points, freq)
            for goal in self.gameset.Goals():
                diff = (
                    self.keyed_by_homeworld_goal[(homeworld, goal)] -
                    win_points)
                html += '<td>%.3f</td>' % diff
            html += '</tr>\n'
        html += '</table>\n'
        return html

    def _Serialize(self):
        ret = []
        for bucket_info in self.bucketted_by_homeworld:
            homeworld = bucket_info.key
            ret.append({'homeworld': homeworld,
                        'win_points': bucket_info.norm_win_points,
                        'adjusted_rate': []})
            for goal in self.gameset.Goals():
                ret[-1]['adjusted_rate'].append(
                    self.keyed_by_homeworld_goal[(homeworld, goal)])
        return ret

    def RenderToJson(self):
        return json.dumps(self._Serialize())

class OverviewStats:
    def __init__(self, games):
        self.max_genie_id = 0
        self.max_flex_id = 0
        self.games_played = len(games)
        self.exps = [0] * len(EXPANSIONS)
        player_size = collections.defaultdict(int)
        race_type = collections.defaultdict(int)

        for game in games:
            if 'flex' in game.GameId():
                self.max_flex_id = max(self.max_flex_id, game.GameNo())
            else:
                self.max_genie_id = max(self.max_genie_id, game.GameNo())
                
            adv = ''
            if game.Advanced() == 1:
                adv = ' adv'

            players_size_str = '%dp%s' % ( len(game.PlayerList()), adv )
            player_size[players_size_str] += 1

            race_type_str = 'Base'
            if game.Expansion() == 1:
                race_type_str = 'Gathering Storm'
            elif game.Expansion() == 2:
                race_type_str = 'Rebel vs Imperium'
            if game.GoalGame():
                if game.Expansion() == 0:
                    print game
                race_type_str += ' with Goals'

            race_type[race_type_str] += 1
            self.exps[game.Expansion()] += 1

        self.player_size = player_size.items()
        self.player_size.sort()
        self.race_type = race_type.items()
        self.race_type.sort()

    def NumExpansionGames(self, exp_no):
        return self.exps[exp_no]

    def RenderAsHTMLTable(self):
        header_fmt = ('<table border=1><tr><td>%s</td><td>Num Games'
                      '</td><td>Percentage</td></tr>' )
        html = '<a name="overview">'
        html += '<h2>Overview</h2>'
        html += '</a>'
        html += '<div class="h3">'
        html += 'Total games analyzed: %d<br>\n' % self.games_played
        if self.max_genie_id:
            html += 'Last seen genie game number: %d<br>\n' % self.max_genie_id
        if self.max_flex_id:
            html += 'Last seen flex game number: %d<br>\n' % self.max_flex_id
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

def PlayerLink(player_name, exp=None, anchor_text=None):
    exp_text = ''
    if exp is not None:
        exp_text = exp + '/'
    if anchor_text is None:
        anchor_text = player_name
    return ('<a href="' + exp_text + PlayerFile(player_name) + '">' + 
            anchor_text + '</a>')

def RenderCardWinGraph(out_file, card_win_info):
    out_file.write("""
<p>
<table><tr><td>Skill Normalized<br>Winning Rate</td>
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

def RenderCardAnimationGraph(out_file, animated_win_info):
    out_file.write("""
<p><div id="cardDataAnimHolder">
<script type="text/javascript">
window.onload = function() {
  var cardWinAnimationInfo = %s;
  var animation = CardDataAnimation("cardDataAnimHolder");
  animation.Render(cardWinAnimationInfo);
}
</script>
</p>
""" % json.dumps(animated_win_info, indent=2))
    

def AdjustedWinPoints(cardWinInfo):
    observed_norm_win_points = []

    for card in cardWinInfo:
        c = cardWinInfo[card]
        norm_win_points_per_game = c['prob_per_card'] * c['norm_win_points']
        c['norm_win_points_per_game'] = norm_win_points_per_game
        if (DeckInfo.card_info_dict[card]['Production'] == 'Production' and
            not card in HOMEWORLDS):
            observed_norm_win_points.append((card, c))
        if card == 'Plague World':
            plague_world_info  = c
    observed_norm_win_points.sort(key = lambda x: 
                                  x[1]['norm_win_points_per_game'])
    mean = sum(c[1]['norm_win_points_per_game'] for c in 
               observed_norm_win_points) / len(observed_norm_win_points)

    print 'mean = %f' % mean
    print 'name'.ljust(25), 'norm_ppg'.ljust(10)
    for per_card_info in observed_norm_win_points:
        print per_card_info[0].ljust(25), ('%.3f' % per_card_info[1]['norm_win_points_per_game']).ljust(20), per_card_info[1]['norm_win_points']

def RenderCardWinVsGameVersionPage(games, rankings_by_game_type, subtitle):
    out = open('version_' + subtitle.replace(' ', '_') + '.html', 'w')
    out.write('<html><head><title>' + TITLE + ' Card win/play rate '
              'by version ' + subtitle + '</title>' + 
              JS_INCLUDE + CSS + '</head>')
    untied_games = FilterOutTies(games)
    version_influence_data = VersionInfluenceOnCardStats(
        untied_games, rankings_by_game_type.AllGamesRatings())
    RenderCardAnimationGraph(out, version_influence_data)
    
    out.write('</html>')
    
def RenderGoalVsNonGoalPage(games, rankings_by_game_type, gameset):
    out = open('goals_vs_nongoals.html', 'w')
    out.write('<html><head><title>' + TITLE + ' ' + gameset.exp_name +
              ' goal vs non-goal influence' +
              '</title>' + JS_INCLUDE + CSS + '</head>')
    games_from_good_exp = FilterOutTies(games)
    goal_influence_data = GoalInfluenceOnCardStats(
        PlayerResultsFromGames(games_from_good_exp), 
        rankings_by_game_type.AllGamesRatings(), gameset)
    RenderCardAnimationGraph(out, goal_influence_data)
    open('goals_vs_nongoals.json', 'w').write(json.dumps(
        goal_influence_data))
    out.write('</html>')

def RenderGameSizePage(games, rankings_by_game_type, gameset):
    out = open('game_size.html', 'w')
    out.write('<html><head><title>' + TITLE + ' ' + gameset.exp_name + 
              ' Game size influence on cards' +
              '</title>' + JS_INCLUDE + CSS + '</head>')
    nontied_games = FilterOutTies(games)
    game_size_data = GameSizeInfluenceOnCardStats(
        PlayerResultsFromGames(nontied_games), 
        rankings_by_game_type.AllGamesRatings(), gameset)
    RenderCardAnimationGraph(out, game_size_data)
    open('game_size.json', 'w').write(json.dumps(
            game_size_data))
    out.write('</html>')

def RenderTopGamesetPage(games, rankings_by_game_type, gameset):
    overview = OverviewStats(games)
    top_out = open('index.html', 'w')

    top_out.write('<html><head><title>' + TITLE + ' ' + gameset.exp_name + 
                  '</title>' + JS_INCLUDE + CSS + '</head>\n')

    top_out.write('<body>')
    top_out.write(overview.RenderAsHTMLTable())

    nontied_games = FilterOutTies(games)
    top_out.write(WINNING_RATE_VS_PLAY_RATE_DESCRIPTION)
    top_out.write('<p>From %d %s games.</p><br>\n' % (
            len(nontied_games), gameset.exp_name))    
    card_win_info = ComputeWinningStatsByCardPlayed(
        PlayerResultsFromGames(nontied_games), 
        rankings_by_game_type.AllGamesRatings(), gameset)
    RenderCardWinGraph(top_out, card_win_info)
    
    top_out.write(SIX_DEV_BLURB)
    top_out.write(CARDS_GAME_SIZE)
    if gameset.Goals(): 
        top_out.write(CARDS_GOALS)

    if gameset.Goals():
        homeworld_goal_analysis = HomeworldGoalAnalysis(
            nontied_games, gameset, rankings_by_game_type.AllGamesRatings())
            
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
        for player in game.PlayerList():
            players_to_games[player.Name()].append(game)
    return players_to_games

def TwoPlayerAdvanced(game):
    return len(game.PlayerList()) == 2 and game.Advanced()

def TwoPlayerNotAdvanced(game):
    return  len(game.PlayerList()) == 2 and not game.Advanced()

class RankingByGameTypeAnalysis:
    def __init__(self, games):
        self.filters = [
            ('all games', 10, lambda game: True),
            ('rvi', 10, lambda game: game.Expansion() == 2),
            ('tgs', 10, lambda game: game.Expansion() == 1),
            ('base', 10, lambda game: game.Expansion() == 0),
            ('goal games', 10, lambda game: game.GoalGame()),
            ('non goal games', 10, lambda game: not game.GoalGame()),
            ('2 player adv', 10, TwoPlayerAdvanced),
            ('2 player not adv', 10, TwoPlayerNotAdvanced),
            ('3 player', 7, lambda game: len(game.PlayerList()) == 3),
            ('4 player', 5, lambda game: len(game.PlayerList()) == 4)
            ]
        self.filt_game_lists = [[] for filt in self.filters]
        for game in games:
            for (_, _, filter_func), filt_list in zip(
                self.filters, self.filt_game_lists):
                if filter_func(game):
                    filt_list.append(game)

        non_empty_filters = []
        non_empty_game_lists = []
        for filter, game_list in zip(self.filters, self.filt_game_lists):
            if len(game_list) > 0:
                non_empty_filters.append(filter)
                non_empty_game_lists.append(game_list)

        self.filters = non_empty_filters
        self.filt_game_lists = non_empty_game_lists
        
        # MultiSkillModelProbProd -35874.1528902
        # Powered .9 1.0 -35859.9701768
        # Powered .8 .7 -35801.2954015
        # Powered .7 .5 -35796.1161636
        # Powered .75 .5 -35796.070636
        # Powered .75 .6 -35794.5141947
        # Powered .72 .6 -35794.3374005
        # Powered .75 .62 -35795.0251957
        # Powered .75 .7 -35799.6666797
        # UberNaive -38744.6919391
        self.rating_systems = [
            SkillRatings(games, PoweredSkillModelProbProd(
                    BASE_SKILL, MOVEMENT_CONST, .72, .6))
            for games in self.filt_game_lists]
        print self.rating_systems[0].winner_pred_log_loss

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
    for game in games[::-1]:
        for player in game.PlayerList():
            if player.Name() != target_player:
                ret[player.Name()].append(game)
    return ret

def AbbrevHomeworld(homeworld_name):
    return ''.join(x[0] for x in homeworld_name.split())

def RenderTableauShort(player_result):
    abbrev_homeworld = AbbrevHomeworld(player_result.Homeworld())
    return '%s-%d' % (abbrev_homeworld, int(player_result.Points()))

def GetResultsForNames(game, source, target):
    source_result, target_result = None, None
    for player_result in game.PlayerList():
        if player_result.Name() == source:
            source_result = player_result
        elif player_result.Name() == target:
            target_result = player_result
    assert source_result != None, 'could not find %s in %s' % (
        source, str(game))
    assert target_result != None, 'could not find %s in %s' % (
        target, str(game))
    return source_result, target_result

WIN, LOSE, TIE = range(3)
OUTCOME_TO_COLOR = ['green', 'red', '#444444']

def OutcomeWithPerspective(game, source_result, target_result):
    if source_result.WinPoints() == len(game.PlayerList()):
        return WIN
    elif source_result.WinPoints() == 0 and target_result.WinPoints() > 0:
        return LOSE
    return TIE

def CountWinLossTieByPlayer(games, source, target):
    ret = [0, 0, 0]
    for game in games:
        source_result, target_result = GetResultsForNames(game, source, target)
        outcome = OutcomeWithPerspective(game, source_result, target_result)
        ret[outcome] += 1
    return ret

def RenderGameWithPerspective(game, source, target):
    source_result, target_result = GetResultsForNames(game, source, target)
    color = OUTCOME_TO_COLOR[OutcomeWithPerspective(game, source_result, 
                                                    target_result)]
    return '<a href="%s"><font color="%s">%s %s</font></a>' % (
        game.GameId(), color,
        RenderTableauShort(source_result),
        RenderTableauShort(target_result))

def GetTableausForPlayer(player, player_games):
    player_tableaus = []
    for game in FilterOutTies(player_games):
        for player_result in game.PlayerList():
            if player_result.Name() == player:
                player_tableaus.append(player_result)
    return player_tableaus

def Compute2PRecordByHomeworld(player_tableaus):
    player_tableaus = filter(lambda t: len(t.Game().PlayerList()) == 2, 
                             player_tableaus)
    my_rec_by_hw = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    rec_against_opp_by_hw = collections.defaultdict(lambda: [0.0, 0.0, 0.0])

    for my_tableau in player_tableaus:
        tableaus = my_tableau.Game().PlayerList()
        opp_tableau = tableaus[0] if tableaus[1] == my_tableau else tableaus[1]
        outcome = OutcomeWithPerspective(my_tableau.Game(), my_tableau, 
                                         opp_tableau)
        my_rec_by_hw[my_tableau.Homeworld()][outcome] += 1
        rec_against_opp_by_hw[opp_tableau.Homeworld()][outcome] += 1
    return my_rec_by_hw, rec_against_opp_by_hw

def RenderRecord(record):
    return ('<font color="%s">%d</font>-'
            '<font color="%s">%d</font>-'
            '<font color="%s">%d</font>' % (
            OUTCOME_TO_COLOR[WIN], record[WIN], 
            OUTCOME_TO_COLOR[LOSE], record[LOSE],
            OUTCOME_TO_COLOR[TIE], record[TIE]))

def RenderPlayerPage(player, player_games, by_game_type_analysis, gameset=None):
    overview = OverviewStats(player_games)
    player_out = open(PlayerFile(player), 'w')
    game_ver = ''
    if gameset:
        game_ver = gameset.exp_name
    player_out.write('<html><head><title> %s %s %s'
                     '</title>%s</head><body>\n' % (TITLE, game_ver, 
                                                    player, JS_INCLUDE))
    player_out.write('<a href="#overview">Overview</a> \n'
                     '<a href="#homeworld_flow">Homeworld Rating Flow</a> \n'
                     '<a href="#player_flow">Player Rating Flow</a> \n'
                     '<br>\n')
    player_out.write(overview.RenderAsHTMLTable())
    player_tableaus = GetTableausForPlayer(player, player_games)

    if gameset:
        card_win_info = ComputeWinningStatsByCardPlayed(
            player_tableaus, by_game_type_analysis.AllGamesRatings(), gameset)
        RenderCardWinGraph(player_out, card_win_info)
    else:
        player_out.write('<h2>Game version specific player pages</h2>')
        for exp_no, (exp_abbrev, exp_full) in enumerate(
            zip(EXP_ABBREV, EXPANSIONS)):
            exp_games = overview.NumExpansionGames(exp_no)
            if exp_games:
                player_out.write(
                    PlayerLink(player, exp=exp_abbrev, 
                               anchor_text='\n%d %s games<br>\n' % (
                            exp_games, EXPANSIONS[exp_no])))

    player_out.write('<table id="homeworld_flow_tables"><tr><td>')
    player_out.write('<br><a name="homeworld_flow"> '
                     '<table border=1><tr><td>Homeworld</td>'
                     '<td>Net rating change</td>'
                     '<td>2 Player record</td></tr>')
    all_games_ratings = by_game_type_analysis.AllGamesRatings()
    my_rec_by_hw, my_rec_against_hw = Compute2PRecordByHomeworld(
        player_tableaus)
    skill_flows = all_games_ratings.GetHomeworldSkillFlow(player)
    for homeworld, net_rating_flow in skill_flows:
        player_out.write('<tr><td>%s</td><td>%.1f</td><td>%s</td></tr>\n' % (
                homeworld, net_rating_flow, 
                RenderRecord(my_rec_by_hw[homeworld])))
    player_out.write('</table>')

    player_out.write('</td><td>')

    player_out.write('<br><table border=1><tr><td>Opponent Homeworld</td>'
                     '<td>Net flow against</td><td>2P rec against</td></tr>')
    opp_skill_flows = all_games_ratings.GetOpponentHomeworldSkillFlow(player)
    for homeworld, net_rating_flow in opp_skill_flows:
        player_out.write('<tr><td>%s</td><td>%.1f</td><td>%s</td></tr>\n' % (
                homeworld, net_rating_flow, 
                RenderRecord(my_rec_against_hw[homeworld])))
    player_out.write('</table>') # opponent flow table
    player_out.write('</table>') # homeworld_flow_tables


    paired_games = KeyGamesByOpponent(player, player_games)

    player_out.write('<a name="player_flow"> '
                     '<table border=1><tr><td>Opponent</td>'
                     '<td>Net rating flow</td><td>Record</td></tr>\n')
    for opponent, skill_flow in all_games_ratings.GetRatingFlow(player):
        record = CountWinLossTieByPlayer(
            paired_games[opponent], player, opponent)
        rowspan = (len(paired_games[opponent]) - 1) / 10 + 1
        rendered_rec = RenderRecord(record)
        player_link = PlayerLink(opponent)
        player_out.write(('<tr>'
                           '<td rowspan=%(rowspan)d>%(player_link)s</td>'
                           '<td rowspan=%(rowspan)d>%(skill_flow).1f</td>'
                           '<td rowspan=%(rowspan)d>%(rendered_rec)s</td>') % 
                         locals())
        
        ct = 0
        for game in paired_games[opponent]:
            if ct == 10:
                player_out.write('</tr><tr>')
                ct = 0
            player_out.write('<td>')
            player_out.write(RenderGameWithPerspective(game, player, opponent))
            player_out.write('</td>')
            ct += 1
    
        player_out.write('</tr>\n')
            

    player_out.write('</table>')
    player_out.write('</html>')

def CopyOrLink(fn, debugging_on, output_dir):
    if os.access(output_dir + '/' + fn, os.O_RDONLY):
        os.remove(output_dir + '/' + fn)
    if not debugging_on:
        shutil.copy(fn, output_dir)
    else:
        os.system('ln -s ./../%s %s/%s' % (fn, output_dir, fn))
    

def CopySupportFilesToOutput(debugging_on, output_dir):
    open('card_attrs.js', 'w').write('var cardInfo = %s;' % 
                                     json.dumps(DeckInfo.card_info_dict, 
                                                indent=2))
    CopyOrLink('card_attrs.js', debugging_on, output_dir)
    CopyOrLink('genie_analysis.js', debugging_on, output_dir)
    CopyOrLink('style.css', debugging_on, output_dir)
    CopyOrLink('condensed_games.json.gz', debugging_on, output_dir)
    CopyOrLink('condensed_flex.json.gz', debugging_on, output_dir)
    
    if not os.access(output_dir + '/images', os.O_RDONLY):
        shutil.copytree('images', output_dir + '/images')

def VivaFringeFormat(games, ratings, output_file):
    gs_2_player_games = [g for g in NonTiedGatheringStormGames(games) if
                         len(g.PlayerList()) == 2]
    #game_won, rating_1,rating_2,card_played_1,card_played_2,...

    for game in gs_2_player_games:
        cur_rating = []
        for player_result in game.PlayerList():
            cur_rating.append(
                ratings.RatingAtGameId(game.GameId(), player_result.Name()))
        winner = game.GameWinners()[0]
        for idx, player_result in enumerate(game.PlayerList()):
            won = 0
            if winner.Name() == player_result.Name():
                won = 1
            output_file.write('%d,%d,%d,' % (
                won, cur_rating[idx], cur_rating[1 - idx]))
            full_vector = player_result.FullFeatureVector()
            output_file.write(','.join(str(idx) for idx in full_vector))
            output_file.write('\n')

def DumpSampleGamesForDebugging(games):
    open('terse_games.json', 'w').write(
        json.dumps(random.sample(games, 5000)))


SAMPLE_INDS = [.05, .25, .5, .75, .95]
JITTER = [-.03, -.015, 0, .015, .03]

class PointDistribution:
    def __init__(self):
        self.point_dist = []
        self.observer = RandomVariableObserver()

    def AddOutcome(self, val):
        self.point_dist.append(val)
        self.observer.AddOutcome(val)

    def BoxPlotData(self, tableau_ct):
        summary_stats = []
        self.point_dist.sort()
        for ind in SAMPLE_INDS:
            avg = 0
            for jitter in JITTER:
                scaled_ind = int((ind + jitter) * len(self.point_dist))
                avg += self.point_dist[scaled_ind]
            summary_stats.append(avg / float(len(JITTER)))
        return {'prob': float(len(self.point_dist)) / tableau_ct, 
                'summary': summary_stats,
                'mean': self.observer.Mean(),
                'stdDev': self.observer.StdDev()}


def Analyze6Devs(gameset):
    dists_with = collections.defaultdict(PointDistribution)
    dists_without = collections.defaultdict(PointDistribution)
    tableau_ct = 0
    for g in gameset.games:
        for p in g.PlayerList():
            tableau_ct += 1
            tab_scorer = tableau_scorer.TableauScorer(p.Cards(), p.Chips())
            for card in gameset.Deck().SixDevList():  
                hypo_score = tab_scorer.Hypothetical6DevScore(card)
                if card in p.Cards():
                    dists_with[card].AddOutcome(hypo_score)
                else:
                    dists_without[card].AddOutcome(hypo_score)

    six_dev_summary = {}
    for card in gameset.Deck().SixDevList():
        six_dev_summary[card] = {
            'played': dists_with[card].BoxPlotData(tableau_ct),
            'unplayed': dists_without[card].BoxPlotData(tableau_ct)
            }    

    output_file = file('six_dev_analysis.html', 'w')
    output_file.write("""<html><head><title> %s %s: 6 Dev Point Distribution
    </title>%s %s
</head><body>
<div id="point_plot" style="width:1000px;height:600px"></div>
<script type="text/javascript">

var p = PointDistribution("point_plot");
var six_dev_summary = %s;
p.Render(six_dev_summary);
</script>
</body>
</html>""" % (TITLE, gameset.exp_ver,
              JS_INCLUDE, CSS, json.dumps(six_dev_summary, indent=2)))

def ConvertToMongoDBFormat(games, gamelist_name):
    out = open(gamelist_name + '.mongo.json', 'w')
    for g in games:
        raise 123         # g['_id'] = 'genie' + str(g['game_no']) 
        out.write(json.dumps(g) + '\n')

def LoadGames(debugging, gamelist_name):
    try:
        #import pymongo
        con = pymongo.Connection('localhost', 27017)
        db = con['games']
        if debugging:
            num_games = db.games.count()
            sample_id = random.randint(0, num_games)
            games = list(db.games.find(skip = sample_id).limit(5000))
        else:
            games = db.games.find()
    except Exception, e:
        print 'mongo failed!', e
        print 'failing back to reading from json file'
        games = json.loads(open(gamelist_name + '.json').read())

    if not debugging:
        DumpSampleGamesForDebugging(games)
    # ConvertToMongoDBFormat(games, gamelist_name)
    return map(Game, games)

def ChangeToMaybeNewDir(dir_name, debugging_on):
    orig = os.getcwd()
    if not os.access(dir_name, os.O_RDONLY):
        os.mkdir(dir_name)
    CopySupportFilesToOutput(debugging_on, dir_name)
    os.chdir(dir_name)
    return orig

def RenderGameset(gameset, output_dir, debugging_on):
    orig_dir = ChangeToMaybeNewDir(output_dir, debugging_on)

    by_game_type_analysis = RankingByGameTypeAnalysis(gameset.games)
    RenderTopGamesetPage(gameset.games, by_game_type_analysis, gameset)
    if len(gameset.Goals()):
        RenderGoalVsNonGoalPage(gameset.games, by_game_type_analysis, gameset)
    RenderGameSizePage(gameset.games, by_game_type_analysis, gameset)

    for player, player_games in PlayerToGameList(gameset.games).iteritems():
        if debugging_on and player != 'rrenaud' and player != 'Kesterer':
            continue
        RenderPlayerPage(player, player_games, by_game_type_analysis, gameset)

    Analyze6Devs(gameset)
    os.chdir(orig_dir)

def RenderTopPage(games, debugging_on):
    orig_dir = ChangeToMaybeNewDir('output', debugging_on)
    out = open('index.html', 'w')
    out.write('<html><head><title>' + TITLE + '</title>' + JS_INCLUDE + 
                  CSS + '</head>\n<body>')
    out.write(INTRO_BLURB)
    overview = OverviewStats(games)
    out.write(overview.RenderAsHTMLTable())

    out.write('<h2>Game version specific analysis</h2>')
    out.write('<p>')
    for idx, (exp_abbrev, exp_name) in enumerate(zip(EXP_ABBREV,EXPANSIONS)):
        out.write('<a href=%s/index.html>%d %s games</a><br>' % (
                exp_abbrev, overview.NumExpansionGames(idx), exp_name))

    out.write('<h3>Card play/win graphs as a function of game version</h3>')
    out.write('<ul><li><a href="version_with_goals.html">With goals.</a>'
              '    <li><a href="version_without_goals.html">Without goals</a>.'
              '</ul>')

    rankings = RankingByGameTypeAnalysis(games)
    games_without_goals = []
    games_with_goals = []
    for g in games:
        if g.Expansion() == 0 or g.Goals():
            games_with_goals.append(g)
        if g.Expansion() == 0 or not g.Goals():
            games_without_goals.append(g)

    RenderCardWinVsGameVersionPage(games_without_goals, rankings, 
                                   'without goals')
    RenderCardWinVsGameVersionPage(games_with_goals, rankings, 
                                   'with goals')

    rankings.RenderAllRankingsAsHTML(out)
    out.write('</body>')

    for player, player_games in PlayerToGameList(games).iteritems():
        RenderPlayerPage(player, player_games, rankings)

    os.chdir(orig_dir)
                
def main(argv):
    debugging, just_flex = False, False
    t0 = time.time()
    gamelists = ['condensed_games', 'condensed_flex']
    if len(argv) > 1:
        if argv[1] == '-d':
            debugging = True
            gamelists = ['terse_games']
        elif argv[1] == '-f':
            debugging, just_flex = True, True
            gamelists = ['condensed_flex']

    games = []
    for gamelist in gamelists:
        games.extend(LoadGames(debugging, gamelist))

    t1 = time.time()
    print 'games loaded time', t1 - t0

    RenderTopPage(games, debugging)

    exp_versions = enumerate(EXP_ABBREV)
    if just_flex:
        exp_versions = [(2, "rvi")]
    for idx, exp_abbrev in exp_versions:
        RenderGameset(FixedExpansionGameSet(games, idx), 
                      'output/' + exp_abbrev, debugging)

if __name__ == '__main__':
    main(sys.argv)
    #import profile
    #profile.run('main(sys.argv)')
