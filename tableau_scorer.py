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

def HypotheticalScorer(original_scorer, additional_card):
    return TableauScorer(original_scorer.cardlist + [additional_card],
                         original_scorer.vp)

class TableauScorer:
    def __init__(self, card_list, vp=0):
        self.bonus_points_per_card = collections.defaultdict(int)
        self.bonus_points_per_6_dev = collections.defaultdict(int)
        self.cardlist = card_list
        self.vp = vp
        for card in card_list:
            if DeckInfo.Is6Dev(card):
                python_friendly_name = card.replace(' ', '').replace('-', '')
                score_func_name = 'Score' + python_friendly_name
                if card == 'Galactic Renaissance':
                    self.bonus_points_per_6_dev[card] += self.vp / 3
                score_func = globals()[score_func_name]
                for other_card in card_list:
                    bonus = score_func(other_card)
                    self.bonus_points_per_6_dev[card] += bonus
                    if other_card != card:
                        self.bonus_points_per_card[other_card] += bonus

    def BonusPer6Dev(self, card):
        return self.bonus_points_per_6_dev[card]

    def PointsPerCard(self, card):
        return (self.BonusPer6Dev(card) + self.bonus_points_per_card[card] +
                DeckInfo.Value(card))
