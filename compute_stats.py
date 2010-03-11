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

GOOD_TYPES = [ "Novelty", "Rare", "Genes", "Alien"]
PROD_TYPES = [ "Windfall", "Production"]

HOMEWORLDS = ["Alpha Centauri", "Epsilon Eridani", "Old Earth",
              "Ancient Race", "Damaged Alien Factory",
              "Earth's Lost Colony", "New Sparta",
              "Separatist Colony", "Doomed World"]

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

TITLE = 'RFTGStats.com: Race for the Galaxy Statistics'
JS_INCLUDE = (
    '<script type="text/javascript" src="card_attrs.js"></script>'
    '<script type="text/javascript" src="genie_analysis.js"></script>'
    )
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
href="http://www.google.com/chrome">Chrome</a>.  The raw data from genie is
available <a href="condensed_games.json">here</a>. Contributions
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
</ul>
"""

def GoalVector(goals):
    ret = [0] * len(GOALS)
    for goal in goals:
        ret[GOALS.index(goal)] = 1
    return ret

def GetAndRemove(dict, key):
    ret = dict[key]
    del dict[key]
    return ret

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

        self.game_no = GetAndRemove(game_dict, 'game_no')
        self.expansion = GetAndRemove(game_dict, 'expansion')
        self.advanced = GetAndRemove(game_dict, 'advanced')
        
        assert len(game_dict) == 0

    def __str__(self):
        player_info_string = '\t' + '\n\t'.join(
            str(p) for p in self.PlayerList())
        return '%d %s\n' % (self.GameNo(), player_info_string)

    def WinningScore(self):
        return max(result.Score() for result in self.PlayerList())

    def GameWinners(self):
        max_score = self.WinningScore()
        return [p for p in self.PlayerList() if p.Score() == max_score]

    def PlayerList(self):
        return self.player_list

    def GameNo(self):
        return self.game_no

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
        if self.cards[0] in HOMEWORLDS:
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

    def Cards(self):
        return self.cards

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
        # handle doomed world

        return card_vec

    def _TableauSizeRelativeToMax(self):
        other_max = max(len(player_result.Cards()) for player_result in 
                        self.Game().PlayerList() if 
                        player_result.Name() != self.Name())
        return len(self.Cards()) - other_max

    def FeatureSummary(self):
        good_counts = [0] * len(GOOD_TYPES)
        prod_counts = [0] * len(PROD_TYPES)
        dev_count = 0
        dev_count_6_cost = 0
        world_count = 0
        mil_world_count = 0
        mil_strength = 0
        
        for card in self.Cards():
            if DeckInfo.CardIsDev(card):
                dev_count += 1
                if DeckInfo.Cost(card) == 6:
                    dev_count_6_cost += 1
            else:
                world_count += 1

                good_type = DeckInfo.GoodType(card)
                if good_type:
                    good_counts[GOOD_TYPES.index(good_type)] += 1

                prod_type = DeckInfo.ProductionPower(card)
                if prod_type:
                    prod_counts[PROD_TYPES.index(prod_type)] += 1

                mil_world_count += DeckInfo.IsMilWorld(card)
                mil_strength += DeckInfo.MilitaryStrength(card)

        return prod_counts + good_counts + [
            self.points / 30.0, self.chips / 12.0, dev_count, dev_count_6_cost, 
            world_count, mil_world_count, mil_strength / 2.0, 
            self._TableauSizeRelativeToMax()] + self.WonGoalVector()
            
    def FullFeatureVector(self):
        return self.CardVector(record_places=True) + \
            self.Game().GoalVector() + self.FeatureSummary() + [
            self.Name(), self.Game().GameNo()]
            

    def Name(self):
        return self.name

        
def InitDeckInfoDict():
    card_info = list(csv.DictReader(open('card_attributes.csv', 'r')))
    card_info_dict = dict((x["Name"], x) for x in card_info)
    card_names = (x["Name"] for x in card_info)
    card_names = list(set(card_names)) # remove dup gambling world
    card_names.sort()
    card_name_order_dict = dict((name, idx) for idx, name in
                                enumerate(card_names))
    #pprint.pprint(card_name_order_dict)
    return card_info_dict, card_name_order_dict

class DeckInfo:
    card_info_dict, card_name_order = InitDeckInfoDict()

    @staticmethod
    def CardFrequencyInDeck(card_name):
        card = DeckInfo.card_info_dict[card_name]
        if card['Name'] == 'Contact Specialist':
            return 3
        if card['Type'] == 'Development':
            return 2 - (card['Cost'] == '6')
        return 1

    @staticmethod
    def CardIndexByName(card_name):
        return DeckInfo.card_name_order[card_name]

    @staticmethod
    def NumCards():
        return len(DeckInfo.card_name_order)

    @staticmethod
    def CardIsDev(card_name):
        return DeckInfo.card_info_dict[card_name]['Type'].strip()== 'Development'

    @staticmethod
    def GoodType(card_name):
        return DeckInfo.card_info_dict[card_name]['Goods'].strip()

    @staticmethod
    def ProductionPower(card_name):
        return DeckInfo.card_info_dict[card_name]['Production'].strip()

    @staticmethod
    def IsMilWorld(card_name):
        return bool(DeckInfo.card_info_dict[card_name]['Military'].strip())

    @staticmethod
    def MilitaryStrength(card_name):
        return int(DeckInfo.card_info_dict[card_name]['Strength'])

    @staticmethod
    def Cost(card_name):
        return int(DeckInfo.card_info_dict[card_name]['Cost'])

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

    def SampleStdDev(self):
        return (self.Variance() / (self.freq or 1)) ** .5
        
def ComputeWinningStatsByHomeworld(games):
    def HomeworldYielder(player_result, game):
        yield player_result.Homeworld()
    return ComputeStatsByBucketFromGames(games, HomeworldYielder)

def ComputeStatsByBucketFromPlayerResults(player_results, 
                                          bucketter, rating_system):
    wins = collections.defaultdict(RandomVariableObserver)
    norm_wins = collections.defaultdict(RandomVariableObserver)

    for player_result in player_results:
        game = player_result.Game()
        game_no = game.GameNo()
        n = float(len(game.PlayerList()))
        player_name = player_result.Name()
        if rating_system:
            won_prob = rating_system.ProbWonAtGameNo(game_no, player_name)
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
                                                 
def GameTied(game):
    return len(game.GameWinners()) > 1

def FilterOutTies(games):
    return [g for g in games if not GameTied(g)]

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
            lambda: collections.defaultdict(int))
	self.rating_by_homeworld_flow = collections.defaultdict(
            lambda: collections.defaultdict(int))
        self.model_log_loss = 0.0
        self.winner_pred_log_loss = 0.0
        self.ratings_at_game_no = collections.defaultdict(dict)
        self.prob_won_at_game_no = collections.defaultdict(dict)

        for game in FilterOutTies(games):
            winner = game.GameWinners()[0]
            win_name = winner.Name()
            losers = []
            game_no = game.GameNo()
            for player in game.PlayerList():
                player_name = player.Name()
                rating = self.GetSkillInfo(player_name).rating
                self.ratings_at_game_no[game_no][player_name] = rating
                if player_name == win_name:
                    continue
                loser_name = player.Name()
                win_prob = self.skill_model.Predict(win_name, loser_name)
                self.model_log_loss += math.log(win_prob) / math.log(2)
                losers.append(loser_name)

            player_names = [player.Name() for player in
                            game.PlayerList()]
            winner_idx = player_names.index(win_name)
            multiplayer_win_probs = skill_model.MultiplayerWinProb(
                player_names)
            name_prob_pairs = [(player_name, win_prob) for player_name, win_prob
                               in zip(player_names, multiplayer_win_probs)]
            self.prob_won_at_game_no[game_no] = name_prob_pairs
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

    def RatingAtGameNo(self, game_no, player_name):
        return self.ratings_at_game_no[game_no][player_name]

    def ProbWonAtGameNo(self, game_no, player_name):
        name_probs = self.prob_won_at_game_no[game_no]
        for name, prob in name_probs:
            if player_name == name:
                return prob
        raise ValueError()
            

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
        self.win_points_ssd = win_points_ssd
        self.frequency = frequency
        self.norm_win_points = norm_win_points
        self.norm_win_points_ssd = norm_win_points_ssd
        
# this has the overly non-general assumption that the card is the key, rather
# than simply a part of the key
def ComputeByCardStats(player_results, card_yielder, skill_ratings):
    bucketted_stats = ComputeStatsByBucketFromPlayerResults(
        player_results, card_yielder, skill_ratings)
    
    grouped_by_card = {}
    total_tableaus = float(len(player_results))
    for bucket_info in bucketted_stats:
        card = bucket_info.key
        prob_per_card_name = bucket_info.frequency / total_tableaus
        prob_per_card_name_var = prob_per_card_name * (1 - prob_per_card_name)
        prob_per_card_name_ssd = (prob_per_card_name_var / total_tableaus) ** .5
        freq_in_deck = DeckInfo.CardFrequencyInDeck(card)
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
    

def ComputeWinningStatsByCardPlayed(player_results, skill_ratings):
    def NonHomeworldCardYielder(player_result, game):
        for idx, card in enumerate(player_result.Cards()):
            if not (idx == 0 and card in HOMEWORLDS or
                    card == 'Gambling World'):
                yield card
    return FilterDiscardables(ComputeByCardStats(
            player_results, NonHomeworldCardYielder, skill_ratings))

def GoalInfluenceOnCardStats(player_results, skill_ratings):
    with_goals, without_goals = [], []
    for player_result in player_results:
        if player_result.Game().GoalGame():
            with_goals.append(player_result)
        else:
            without_goals.append(player_result)
    return [
        {'title': 'Without goals',
         'data': ComputeWinningStatsByCardPlayed(without_goals, skill_ratings)},
        {'title': 'With goals',
         'data': ComputeWinningStatsByCardPlayed(with_goals, skill_ratings)}
        ]

def GameSizeInfluenceOnCardStats(player_results, ratings):
    games_by_size = collections.defaultdict(list)
    for player_result in player_results:
        game_size = len(player_result.Game().PlayerList())
        games_by_size[game_size].append(player_result)
    return [
        {'title': 'Game Size %d' % size,
         'data': ComputeWinningStatsByCardPlayed(games_by_size[size], ratings)}
        for size in sorted(games_by_size.keys())
        ]

def FilterOutNonGoals(games):
    return [g for g in games if g.GoalGame()]

class HomeworldGoalAnalysis:
    def __init__(self, games):
        games = FilterOutNonGoals(games)
        def HomeworldGoalYielder(player_result, game):
            for goal in game.Goals():
                yield player_result.Homeworld(), goal
        self.bucketted_by_homeworld_goal = ComputeStatsByBucketFromGames(
            games, HomeworldGoalYielder)
        self.keyed_by_homeworld_goal = {}
        for bucket in self.bucketted_by_homeworld_goal:
            self.keyed_by_homeworld_goal[bucket.key] = bucket.win_points

        self.bucketted_by_homeworld = ComputeWinningStatsByHomeworld(games)

    def RenderStatsAsHtml(self):
        html = '<table border=1><tr><td>Homeworld</td><td>'
        html += 'Baseline Winning Rate</td>'
        for goal in GOALS:
            html += '<td>%s</td>' % goal
        html += '</tr>\n'

        for bucket_info in self.bucketted_by_homeworld:
            homeworld = bucket_info.key
            win_points = bucket_info.win_points
            html += '<tr><td>%s</td><td>%.3f</td>' % (homeworld, win_points)
            for goal in GOALS:
                diff = (
                    self.keyed_by_homeworld_goal[(homeworld, goal)] -
                    win_points)
                html += '<td>%.3f</td>' % diff
            html += '</tr>\n'
        html += '</table>\n'
        return html

    def RenderToJson(self):
        ret = []
        for bucket_info in self.bucketted_by_homeworld:
            homeworld = bucket_info.key
            ret.append({'homeworld': homeworld,
                        'win_points': bucket_info.win_points,
                        'adjusted_rate': []})
            for goal in GOALS:
                ret[-1]['adjusted_rate'].append(
                    self.keyed_by_homeworld_goal[(homeworld, goal)])
        return json.dumps(ret)


# not called, might be broken by refactor of bucketinfo
def ComputeWinStatsByHomeworldSkillLevel(games, skill_ratings):
    untied_games = FilterOutTies(games)
    NUM_SKILL_BUCKETS = 5
    skill_buckets = skill_ratings.ComputeRatingBuckets(untied_games,
                                                       NUM_SKILL_BUCKETS)
    print skill_buckets

    def HomeworldSkillYielder(player_result, game):
        for p_result in game.PlayerList():
            if (skill_ratings.PlayerSkillBucket(
                    p_result.Name(), skill_buckets) != 
                NUM_SKILL_BUCKETS - 1):
                return

        name = player_result.Name()
        skill_bucket = skill_ratings.PlayerSkillBucket(name, skill_buckets)
        yield (player_result.Homeworld(), skill_bucket)

    bucketted_stats = ComputeStatsByBucketFromGames(untied_games,
                                                    HomeworldSkillYielder)
    keyed_by_hw_rough_skill = {}
    for bucket in bucketted_stats:
        keyed_by_hw_rough_skill[bucket.key] = bucket
                                               
    print keyed_by_hw_rough_skill
    ret = {}
    interesting_skill_range = range(NUM_SKILL_BUCKETS - 1, NUM_SKILL_BUCKETS)
    for homeworld in HOMEWORLDS:
        ret[homeworld] = []
        for i in interesting_skill_range:
            ret[homeworld].append(keyed_by_hw_rough_skill[(homeworld, i)])

    for k in ret:
        print k.ljust(25),
        for win_bucket in ret[k]:
            print ('%.3f' % win_bucket.win_points).ljust(8),
            print '+-', ('%.3f' % (win_bucket.win_points_ssd * 2)).ljust(8),
            print win_bucket.frequency
        print 

    return ret

class OverviewStats:
    def __init__(self, games):
        self.max_game_no = 0
        self.games_played = len(games)
        player_size = collections.defaultdict(int)
        race_type = collections.defaultdict(int)

        for game in games:
            self.max_game_no = max(self.max_game_no, game.GameNo())
            adv = ''
            if game.Advanced() == 1:
                adv = ' adv'

            players_size_str = '%dp%s' % ( len(game.PlayerList()), adv )
            player_size[players_size_str] += 1

            race_type_str = 'Base'
            if game.Expansion() == 1:
                race_type_str = 'Gathering Storm'
            if game.GoalGame():
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

def RenderCardWinGraph(out_file, card_win_info):
    out_file.write("""
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
    

def NonTiedGatheringStormGames(games):
    return FilterOutTies(
        [g for g in games if g.Expansion() == 1])
    
def RenderGoalVsNonGoalPage(games, rankings_by_game_type):
    overview = OverviewStats(games)
    out = open('output/goals_vs_nongoals.html', 'w')
    out.write('<html><head><title>' + TITLE + ' goal vs non-goal influence' +
              '</title>' + JS_INCLUDE + CSS + '</head>')
    gs_games = NonTiedGatheringStormGames(games)
    goal_influence_data = GoalInfluenceOnCardStats(
        PlayerResultsFromGames(gs_games), 
        rankings_by_game_type.AllGamesRatings())
    RenderCardAnimationGraph(out, goal_influence_data)
    open('output/goals_vs_nongoals.json', 'w').write(json.dumps(
        goal_influence_data))
    out.write('</html>')

def RenderGameSizePage(games, rankings_by_game_type):
    overview = OverviewStats(games)
    out = open('output/game_size.html', 'w')
    out.write('<html><head><title>' + TITLE + ' Game size influence on cards' +
              '</title>' + JS_INCLUDE + CSS + '</head>')
    gs_games = NonTiedGatheringStormGames(games)
    game_size_data = GameSizeInfluenceOnCardStats(
        PlayerResultsFromGames(gs_games), 
        rankings_by_game_type.AllGamesRatings())
    RenderCardAnimationGraph(out, game_size_data)
    open('output/game_size.json', 'w').write(json.dumps(
        game_size_data))
    out.write('</html>')

def RenderTopPage(games, rankings_by_game_type):
    overview = OverviewStats(games)
    top_out = open('output/index.html', 'w')

    top_out.write('<html><head><title>' + TITLE + '</title>' + JS_INCLUDE + 
                  CSS + '</head>\n')

    top_out.write('<body>')
    top_out.write(INTRO_BLURB)
    top_out.write(overview.RenderAsHTMLTable())

    gathering_storm_games = NonTiedGatheringStormGames(games)
    top_out.write(WINNING_RATE_VS_PLAY_RATE_DESCRIPTION)
    top_out.write('<p>From %d Gathering Storm games.</p><br>\n' %
                  len(gathering_storm_games))    
    card_win_info = ComputeWinningStatsByCardPlayed(
        PlayerResultsFromGames(gathering_storm_games), 
        rankings_by_game_type.AllGamesRatings())
    RenderCardWinGraph(top_out, card_win_info)
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
    # AdjustedWinPoints(card_win_info)

def PlayerToGameList(games):
    players_to_games = collections.defaultdict(list)
    for game in games:
        for player in game.PlayerList():
            players_to_games[player.Name()].append(game)
    return players_to_games

def WritePlayerFloatPairsAsTableRows(output_file, pairs):
    for s, f in pairs:
        output_file.write('<tr><td>%s</td><td>%.1f</td></tr>\n' % (s, f))

def TwoPlayerAdvanced(game):
    return len(game.PlayerList()) == 2 and game.Advanced()

def TwoPlayerNotAdvanced(game):
    return  len(game.PlayerList()) == 2 and not game.Advanced()

class RankingByGameTypeAnalysis:
    def __init__(self, games):
        self.filters = [
            ('all games', 10, lambda game: True),
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

def CountWinLossTie(games, source, target):
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

    return ('<a href="http://genie.game-host.org/game.htm?gid=%d">' +
            '<font color="%s">' + 
            '%s %s</font></a>') % (game.GameNo(), color,
                                   RenderTableauShort(source_result),
                                   RenderTableauShort(target_result))
    
def ComputeSinglePlayerWinningStats(player, player_games, rating_system):
    gathering_storm_tableaus = []
    for game in FilterOutTies(player_games):
        if game.Expansion() != 1:
            continue
        for player_result in game.PlayerList():
            if player_result.Name() == player:
                gathering_storm_tableaus.append(player_result)

    return ComputeWinningStatsByCardPlayed(gathering_storm_tableaus, 
                                           rating_system)

def RenderPlayerPage(player, player_games, by_game_type_analysis):
    overview = OverviewStats(player_games)
    player_out = open('output/' + PlayerFile(player), 'w')
    player_out.write('<html><head><title> %s %s'
                     '</title>%s</head><body>\n' % (TITLE, player, JS_INCLUDE))

    player_out.write('<a href="#overview">Overview</a> \n'
                     '<a href="#homeworld_flow">Homeworld Rating Flow</a> \n'
                     '<a href="#player_flow">Player Rating Flow</a> \n'
                     '<br>\n')
    player_out.write(overview.RenderAsHTMLTable())

    card_win_info = ComputeSinglePlayerWinningStats(
        player, player_games, by_game_type_analysis.AllGamesRatings())
        
    RenderCardWinGraph(player_out, card_win_info)

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
                     '<td>Net rating flow</td><td>Record</td></tr>\n')
    for opponent, skill_flow in all_games_ratings.GetRatingFlow(player):
        record = CountWinLossTie(paired_games[opponent], player, opponent)
        player_out.write('<tr><td>%s</td><td>%.1f</td>'
                         '<td><font color="%s">%d</font>-'
                         '<font color="%s">%d</font>-'
                         '<font color="%s">%d</font></td>' % (
                PlayerLink(opponent), skill_flow, 
                OUTCOME_TO_COLOR[WIN], record[WIN], 
                OUTCOME_TO_COLOR[LOSE], record[LOSE],
                OUTCOME_TO_COLOR[TIE], record[TIE]))
        for game in paired_games[opponent]:
            player_out.write('<td>')
            player_out.write(RenderGameWithPerspective(game, player, opponent))
            player_out.write('</td>')
        player_out.write('</tr>\n')
            

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
    open('card_attrs.js', 'w').write('var cardInfo = %s;' % 
                                     json.dumps(DeckInfo.card_info_dict, 
                                                indent=2))
    CopyOrLink('card_attrs.js', debugging_on)
    CopyOrLink('genie_analysis.js', debugging_on)
    CopyOrLink('style.css', debugging_on)
    CopyOrLink('condensed_games.json', debugging_on)
    
    if not os.access('output/flot', os.O_RDONLY):
        shutil.copytree('flot', 'output/flot')
    if not os.access('output/images', os.O_RDONLY):
        shutil.copytree('images', 'output/images')

def VivaFringeFormat(games, ratings, output_file):
    gs_2_player_games = [g for g in NonTiedGatheringStormGames(games) if
                         len(g.PlayerList()) == 2]
    #game_won, rating_1,rating_2,card_played_1,card_played_2,...

    for game in gs_2_player_games:
        cur_rating = []
        for player_result in game.PlayerList():
            cur_rating.append(
                ratings.RatingAtGameNo(game.GameNo(), player_result.Name()))
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

def ToNumpyMat(player_results):
    import numpy as np
    return np.array([result.FeatureVector() for result in player_results],
                    dtype=float)

from scipy.cluster.vq import *
def ClusterTableaus(tableau_mat, k):
    centroids, variance = kmeans(tableau_mat, k)
    code, distance = vq(tableau_mat, centroids)    
    return centroids, variance, code, distance

def t():
    games = [Game(g) for g in json.loads(open('condensed_games.json').read())]

    gs_games = [g for g in games if g.Expansion()]
    gs_tables = []
    for g in gs_games:
        gs_tables.extend(g.PlayerList())
    mat = ToNumpyMat(gs_tables)
    cents, var, code, dists = ClusterTableaus(mat, 15)

    clusters = collections.defaultdict(list)
    for tableau, code_val, dist in zip(gs_tables, code, dists):
        clusters[code_val].append((tableau, dist))


    import random
    for clust_ind, members in clusters.iteritems():
        print len(members)
        for member in sorted(members, key = lambda x: x[1])[:3]:
            print member
        for member in random.sample(members, 2):
            print member
        print
        
    return cents, var, code, dists, clusters

def main(argv):
    debugging_on = False
    if len(argv) > 1:
        debugging_on = True

    if not os.access('output', os.O_RDONLY):
        os.mkdir('output')

    if debugging_on:
        games = json.loads(open('terse_games.json').read())
    else:
        games = json.loads(open('condensed_games.json').read())
        open('terse_games.json', 'w').write(
            json.dumps(random.sample(games, 1000)))

    games = [Game(g) for g in games]
    by_game_type_analysis = RankingByGameTypeAnalysis(games)
    VivaFringeFormat(games, by_game_type_analysis.AllGamesRatings(),
                     open('gs_2_player.csv', 'w'))
    print 'exiting early'
    return
    
    if not os.access('output', os.O_RDONLY):
        os.mkdir('output')
    RenderTopPage(games, by_game_type_analysis)
    RenderGoalVsNonGoalPage(games, by_game_type_analysis)
    RenderGameSizePage(games, by_game_type_analysis)

    for player, player_games in PlayerToGameList(games).iteritems():
        RenderPlayerPage(player, player_games, by_game_type_analysis)
    CopySupportFilesToOutput(debugging_on)

if __name__ == '__main__':
    main(sys.argv)
