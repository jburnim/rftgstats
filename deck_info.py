#!/usr/bin/python

import csv

NO_GOOD, NOVELTY, RARE, GENES, ALIEN = GOOD_TYPES = range(5)
GOOD_TYPE_NAMES = ["", "Novelty", "Rare", "Genes", "Alien", "Any"]

NO_PROD, WINDFALL, PRODUCTION = PROD_TYPES = range(3)
PROD_TYPE_NAMES = [ "", "Windfall", "Production"]

BASE_HOMEWORLDS = ["Alpha Centauri", "Epsilon Eridani", "Old Earth",
                   "New Sparta", "Earths Lost Colony"]
                   
GS_HOMEWORLDS = ["Ancient Race", "Damaged Alien Factory", 
                 "Separatist Colony", "Doomed World"] + BASE_HOMEWORLDS

RVI_HOMEWORLDS = ["Galactic Developers", "Imperium Warlord", 
                  "Rebel Cantina"] + GS_HOMEWORLDS

BOW_HOMEWORLDS = ["Rebel Freedom Fighters", "Galactic Scavengers", "Alien Research Team", "Uplift Mercenary Force"] + RVI_HOMEWORLDS

EXPANSIONS = ["Race For the Galaxy", "Gathering Storm", "Rebel vs. Imperium", "Brink of War"]
DISCARDABLE_CARDS = ['Doomed World', 'Colony Ship', 'New Military Tactics',
                     'R and D Crash Program', 'Imperium Cloaking Technology',
                     'Imperium Invasion Fleet']

def ZeroUnset(d, k):
    if not d[k]:
        d[k] = 0

def InitDeckInfoDict(filt = lambda x: True):
    card_info = list(csv.DictReader(open('card_attributes3.csv', 'r')))
    card_info = filter(filt, card_info)
    card_info_dict = dict((x["Name"], x) for x in card_info)
    for per_card_info in card_info_dict.itervalues():
        for field in ['Strength', 'VP', 'Cost']:
            ZeroUnset(per_card_info, field)

    card_names = (x["Name"] for x in card_info)
    card_names = list(set(card_names)) # remove dup gambling world
    card_names.sort()
    card_name_order_dict = dict((name, idx) for idx, name in
                                enumerate(card_names))
    var_six_dev_list = [x for x in card_info_dict if
                        int(card_info_dict[x]['Cost']) == 6 and
                        card_info_dict[x]['Type'] == 'Development']
    if 'Pan-Galactic Research' in var_six_dev_list:
        var_six_dev_list.remove('Pan-Galactic Research')
    #pprint.pprint(card_name_order_dict)
    return card_info_dict, card_name_order_dict, var_six_dev_list

class DeckInfoImpl:
    def __init__(self, init_func):
        self.card_info_dict, self.card_name_order, self.six_dev_list = (
            init_func())
    
    def NumDupCards(self):
        return sum(self.CardFrequencyInDeck(c) for c in
                   self.card_info_dict)

    def SixDevList(self):
        return self.six_dev_list

    def CardList(self):
        return self.card_info_dict.keys()

    def CardFrequencyInDeck(self, card_name, version):
        card = self.card_info_dict[card_name]
        if card['Name'] == 'Contact Specialist':
            return 2 + (version >= 1)
        if card['Name'] == 'Research Labs':
            return 2 + (version >= 2)
        if card['Type'] == 'Development':
            return 2 - (card['Cost'] == '6')
        return 1
    
    def CardIndexByName(self, card_name):
        return self.card_name_order[card_name]

    def NumCards(self):
        return len(self.card_name_order)

    def CardIsDev(self, card_name):
        return self.card_info_dict[card_name]['Type'] == 'Development'
                
    def CardIsWorld(self, card_name):
        return self.card_info_dict[card_name]['Type'].strip() == 'World'

    def GoodType(self, card_name):
        return GOOD_TYPE_NAMES.index(
            self.card_info_dict[card_name]['Goods'].strip())

    def ProductionPower(self, card_name):
        return PROD_TYPE_NAMES.index(
            self.card_info_dict[card_name]['Production'].strip())

    def IsMilWorld(self, card_name):
        return bool(self.card_info_dict[card_name]['Military'].strip())

    def MilitaryStrength(self, card_name):
        return int(self.card_info_dict[card_name]['Strength'])

    def Cost(self, card_name):
        return int(self.card_info_dict[card_name]['Cost'])

    def Is6Dev(self, card_name):
        return self.Cost(card_name) == 6 and self.CardIsDev(card_name)

    def Value(self, card_name):
        return int(self.card_info_dict[card_name]['VP'])

    def HasExplorePower(self, card_name):
        return bool(self.card_info_dict[card_name]['Explore'].strip())

    def HasConsumePower(self, card_name):
        return bool(self.card_info_dict[card_name]['Consume'].strip())

    def HasTradePower(self, card_name):
        return bool(self.card_info_dict[card_name]['Trade'].strip())

    def Keywords(self, card_name):
        return self.card_info_dict[card_name]['Keywords']

    def Version(self, card_name):
        return EXPANSIONS.index(self.card_info_dict[card_name]['Set'])
    
DeckInfo = DeckInfoImpl(InitDeckInfoDict)
BoWDeckInfo = DeckInfoImpl(lambda : InitDeckInfoDict(
        lambda y: y['Set'] in EXPANSIONS[:4]))
RvIDeckInfo = DeckInfoImpl(lambda : InitDeckInfoDict(
        lambda y: y['Set'] in EXPANSIONS[:3]))
GSDeckInfo = DeckInfoImpl(lambda : InitDeckInfoDict(
        lambda y: y['Set'] in EXPANSIONS[:2]))
BaseDeckInfo = DeckInfoImpl(lambda : InitDeckInfoDict(
        lambda y: y['Set'] in EXPANSIONS[:1]))
    
def Diff(method):
    for card in DeckInfo.CardList():
        a = method(DeckInfo, card)
        b = method(DeckInfo2, card)
        if a != b:
            print str(method), card, a, b

def TestMethodsMatch():
    methods = [DeckInfoImpl.CardFrequencyInDeck,
               DeckInfoImpl.CardIndexByName,
               DeckInfoImpl.CardIsDev,
               DeckInfoImpl.CardIsWorld,
               DeckInfoImpl.GoodType,
               DeckInfoImpl.ProductionPower,
               DeckInfoImpl.IsMilWorld,
               DeckInfoImpl.MilitaryStrength,
               DeckInfoImpl.Cost,
               DeckInfoImpl.Is6Dev,
               DeckInfoImpl.Value,
               DeckInfoImpl.HasExplorePower,
               DeckInfoImpl.HasConsumePower,
               DeckInfoImpl.HasTradePower]
    for method in methods:
        Diff(method)

if __name__ == '__main__':
    for card in DeckInfo.CardList():
        def ValidateKeyword(substr, card):
            if substr in card:
                assert substr in DeckInfo.Keywords(card), card
        for keyword in ['Imperium', 'Rebel', 'Uplift', 'Alien', 'Terraforming']:
            ValidateKeyword(keyword, card)
    assert DeckInfo.MilitaryStrength('Lost Alien Battle Fleet') == 3
