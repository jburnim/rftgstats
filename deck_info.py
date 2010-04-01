#!/usr/bin/python

import csv

NO_GOOD, NOVELTY, RARE, GENES, ALIEN = GOOD_TYPES = range(5)
GOOD_TYPE_NAMES = ["", "Novelty", "Rare", "Genes", "Alien"]

NO_PROD, WINDFALL, PRODUCTION = PROD_TYPES = range(3)
PROD_TYPE_NAMES = [ "", "Windfall", "Production"]

HOMEWORLDS = ["Alpha Centauri", "Epsilon Eridani", "Old Earth",
              "Ancient Race", "Damaged Alien Factory",
              "Earth's Lost Colony", "New Sparta",
              "Separatist Colony", "Doomed World"]

def InitDeckInfoDict():
    card_info = list(csv.DictReader(open('card_attributes.csv', 'r')))
    card_info_dict = dict((x["Name"], x) for x in card_info)
    card_names = (x["Name"] for x in card_info)
    card_names = list(set(card_names)) # remove dup gambling world
    card_names.sort()
    card_name_order_dict = dict((name, idx) for idx, name in
                                enumerate(card_names))
    six_dev_list = [x for x in card_info_dict if
                    int(card_info_dict[x]['Cost']) == 6 and
                    card_info_dict[x]['Type'] == 'Development']
    #pprint.pprint(card_name_order_dict)
    return card_info_dict, card_name_order_dict, six_dev_list

class DeckInfo:
    card_info_dict, card_name_order, six_dev_list = InitDeckInfoDict()


    @staticmethod
    def NumDupCards():
        return sum(DeckInfo.CardFrequencyInDeck(c) for c in
                   DeckInfo.card_info_dict)

    @staticmethod
    def SixDevList():
        return DeckInfo.six_dev_list

    @staticmethod
    def CardList():
        return DeckInfo.card_info_dict.keys()

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
        return DeckInfo.card_info_dict[card_name]['Type'] == 'Development'
                
    @staticmethod
    def CardIsWorld(card_name):
        return DeckInfo.card_info_dict[card_name]['Type'].strip() == 'World'

    @staticmethod
    def GoodType(card_name):
        return GOOD_TYPE_NAMES.index(
            DeckInfo.card_info_dict[card_name]['Goods'].strip())

    @staticmethod
    def ProductionPower(card_name):
        return PROD_TYPE_NAMES.index(
            DeckInfo.card_info_dict[card_name]['Production'].strip())

    @staticmethod
    def IsMilWorld(card_name):
        return bool(DeckInfo.card_info_dict[card_name]['Military'].strip())

    @staticmethod
    def MilitaryStrength(card_name):
        return int(DeckInfo.card_info_dict[card_name]['Strength'])

    @staticmethod
    def Cost(card_name):
        return int(DeckInfo.card_info_dict[card_name]['Cost'])

    @staticmethod
    def Is6Dev(card_name):
        return DeckInfo.Cost(card_name) == 6 and DeckInfo.CardIsDev(card_name)

    @staticmethod
    def Value(card_name):
        return int(DeckInfo.card_info_dict[card_name]['VP'])

    @staticmethod
    def HasExplorePower(card_name):
        return DeckInfo.card_info_dict[card_name]['Explore'] == 'X'

    @staticmethod
    def HasConsumePower(card_name):
        return DeckInfo.card_info_dict[card_name]['Consume'] == 'X'

    @staticmethod
    def HasTradePower(card_name):
        return DeckInfo.card_info_dict[card_name]['Trade'] == 'X'
    
