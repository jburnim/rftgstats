#!/usr/bin/python

from deck_info import DeckInfo
from deck_info import NOVELTY, RARE, GENES, ALIEN, WINDFALL, PRODUCTION
import collections

def ScoreAlienTechInstitute(card):
    if 'Alien' in card:
        return 2 + (DeckInfo.ProductionPower(card) == PRODUCTION)
    return 0

def ScoreFreeTradeAssociation(card):
    if card in ['Consumer Markets', 'Expanding Colony']:
        return 2
    if DeckInfo.GoodType(card) == NOVELTY:
        return 1 + (DeckInfo.ProductionPower(card) == PRODUCTION)
    return 0

def ScoreGalacticFederation(card):
    if DeckInfo.CardIsDev(card):
        return 1 + (DeckInfo.Cost(card) == 6)
    return 0

def ScoreGalacticGenomeProject(card):
    if card == 'Genetics Lab':
        return 3
    return 2 * (DeckInfo.GoodType(card) == GENES)

def ScoreGalacticImperium(card):
    if DeckInfo.IsMilWorld(card):
        return 1 + ('Rebel' in card)
    return 0

def ScoreGalacticRenaissance(card):
    bonus_list = ["Galactic Trendsetters", "Research Labs", "Artist Colony"]
    # vp calc handled by scorer
    return (card in bonus_list) * 3

def ScoreGalacticSurveySETI(card):
    if DeckInfo.HasExplorePower(card):
        return 1 + DeckInfo.CardIsWorld(card)
    return DeckInfo.CardIsWorld(card)

def ScoreImperiumLords(card):
    if 'Imperium' in card:
        return 2
    return DeckInfo.IsMilWorld(card)

def ScoreMerchantGuild(card):
    return (DeckInfo.ProductionPower(card) == PRODUCTION) * 2

def ScoreMiningLeague(card):
    if card in ['Mining Conglomerate', 'Mining Robots']:
        return 2
    return (DeckInfo.GoodType(card) == RARE) * (
        (DeckInfo.ProductionPower(card) == PRODUCTION) + 1)

def ScoreNewEconomy(card):
    return DeckInfo.HasConsumePower(card) * (DeckInfo.CardIsDev(card) + 1)

def ScoreNewGalacticOrder(card):
    return DeckInfo.MilitaryStrength(card)

def ScorePangalacticLeague(card):
    if card == 'Contact Specialist':
        return 3
    if DeckInfo.GoodType(card) == GENES:
        return 2
    return DeckInfo.IsMilWorld(card)

def ScoreTerraformingGuild(card):
    if 'Terraforming' in card:
        return 2
    return 2 * (DeckInfo.ProductionPower(card) == WINDFALL)

def ScoreTradeLeague(card):
    return DeckInfo.HasTradePower(card) * (DeckInfo.CardIsDev(card) + 1)

def GetScoreFunc(card):
    python_friendly_name = card.replace(' ', '').replace('-', '')
    score_func_name = 'Score' + python_friendly_name    
    return globals()[score_func_name]

def Score6DevTable():
    ret = collections.defaultdict(lambda: collections.defaultdict(int))
    for six_dev in DeckInfo.SixDevList():
        score_func = GetScoreFunc(six_dev)
        for card in DeckInfo.CardList():
            ret[six_dev][card] = score_func(card)
    return ret

_six_dev_score_table = Score6DevTable()

class TableauScorer:
    def __init__(self, card_list, vp=0):
        #self.bonus_points_per_card = collections.defaultdict(int)
        self.bonus_points_per_6_dev = collections.defaultdict(int)
        self.card_list = card_list
        self.vp = vp
        for card in card_list:
            if DeckInfo.Is6Dev(card):
                bonus_for_6 = self.ScoreFor6Dev(card)
                self.bonus_points_per_6_dev[card] += bonus_for_6
        
    def ScoreFor6Dev(self, card):
        score = 0
        if card == 'Galactic Renaissance':
            score += self.vp / 3
        table_for_this_dev = _six_dev_score_table[card]
        for other_card in self.card_list:
            score += table_for_this_dev[other_card]
            #if other_card != card:
            #    self.bonus_points_per_card[other_card] += bonus
        if not card in self.card_list:
            score += table_for_this_dev[card]
        return score

    def Hypothetical6DevScore(self, card):
        if card in self.bonus_points_per_6_dev:
            return self.bonus_points_per_6_dev[card]
        return self.ScoreFor6Dev(card)

    def BonusPer6Dev(self, card):
        return self.bonus_points_per_6_dev[card]

    def PointsPerCard(self, card):
        ret = DeckInfo.Value(card)
        for other_card in self.card_list:
            if DeckInfo.Is6Dev(other_card) and other_card != card:
                ret += GetScoreFunc(other_card)(card)
        return ret + self.BonusPer6Dev(card)