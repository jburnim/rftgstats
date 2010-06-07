#!/usr/bin/python

import unittest
import tableau_scorer

class TestTableauScorer(unittest.TestCase):
    def testFreeTradeAssociation(self):
        t = tableau_scorer.TableauScorer(['Free Trade Association',
                                          'Gem World',
                                          'Consumer Markets',
                                          'Rebel Sympathizers',
                                          'Expanding Colony'])
        self.assertEquals(13, t.TotalPoints())
        self.assertEquals(7, t.BonusPer6Dev('Free Trade Association'))
        self.assertEquals(7, t.PointsPerCard('Free Trade Association'))
        self.assertEquals(5, t.PointsPerCard('Consumer Markets'))
        self.assertEquals(3, t.PointsPerCard('Gem World'))
        self.assertEquals(2, t.PointsPerCard('Rebel Sympathizers'))
        self.assertEquals(3, t.PointsPerCard('Expanding Colony'))

    def testAlienTechInstitute(self):
        t = tableau_scorer.TableauScorer(['Damaged Alien Factory',
                                          'Alien Tech Institute',
                                          'Alien Rosetta Stone World',
                                          'Alien Robot Scout Ship',
                                          'Expanding Colony'])
        self.assertEquals(17, t.TotalPoints())
        self.assertEquals(9, t.BonusPer6Dev('Alien Tech Institute'))
        self.assertEquals(9, t.PointsPerCard('Alien Tech Institute'))
        self.assertEquals(5, t.PointsPerCard('Damaged Alien Factory'))
        self.assertEquals(9, t.Hypothetical6DevScore('Alien Tech Institute'))
        self.assertEquals(2, t.Hypothetical6DevScore('Galactic Imperium'))
        self.assertEquals(5, t.Hypothetical6DevScore('Galactic Survey SETI'))

    def testScoreGalacticBankers(self):
        t = tableau_scorer.TableauScorer(['Galactic Bankers',
                                          'Investment Credits',
                                          'Interstellar Bank',
                                          'Mercenary Fleet',
                                          'Gambling World',
                                          'Pilgrimage World'])
        self.assertEquals(14, t.TotalPoints())
        self.assertEquals(8, t.BonusPer6Dev('Galactic Bankers'))
        self.assertEquals(3, t.PointsPerCard('Investment Credits'))
        self.assertEquals(3, t.PointsPerCard('Interstellar Bank'))
        self.assertEquals(2, t.PointsPerCard('Mercenary Fleet'))
        self.assertEquals(3, t.PointsPerCard('Gambling World'))
        self.assertEquals(2, t.PointsPerCard('Pilgrimage World'))

    def testGalacticExchange(self):
        t = tableau_scorer.TableauScorer(['Galactic Exchange',
                                          'Diversified Economy',
                                          'Plague World',
                                          'Smuggling World'])
        self.assertEquals(6, t.BonusPer6Dev('Galactic Exchange'))
        self.assertEquals(6, t.PointsPerCard('Galactic Exchange'))
        self.assertEquals(5, t.PointsPerCard('Diversified Economy'))
        self.assertEquals(0, t.PointsPerCard('Plague World'))
        self.assertEquals(0, t.PointsPerCard('Smuggling World'))

    def testGalacticExchange2(self):
        t = tableau_scorer.TableauScorer(['Galactic Exchange'])
        self.assertEquals(0, t.BonusPer6Dev('Galactic Exchange'))

    def testGalacticExchange3(self):
        t = tableau_scorer.TableauScorer(['Galactic Exchange',
                                          'Gem World',
                                          'Mining World',
                                          'Comet Zone',
                                          'Lost Species Ark World',
                                          'Alien Toy Shop'])
        self.assertEquals(10, t.BonusPer6Dev('Galactic Exchange'))
        self.assertEquals(1, t.PointsPerCard('Gem World'))
        self.assertEquals(2, t.PointsPerCard('Mining World'))
        self.assertEquals(2, t.PointsPerCard('Comet Zone'))
        self.assertEquals(3, t.PointsPerCard('Lost Species Ark World'))
        self.assertEquals(1, t.PointsPerCard('Alien Toy Shop'))
        

    def testGalacticFederation(self):
        t = tableau_scorer.TableauScorer(['Galactic Federation',
                                          'Investment Credits',
                                          'Free Trade Association',
                                          'Refugee World'])
        self.assertEquals(5, t.BonusPer6Dev('Galactic Federation'))
        self.assertEquals(5, t.PointsPerCard('Galactic Federation'))
        self.assertEquals(1, t.BonusPer6Dev('Free Trade Association'))
        self.assertEquals(3, t.PointsPerCard('Free Trade Association'))

    def testGalacticGenomeProject(self):
        t = tableau_scorer.TableauScorer(['Galactic Genome Project',
                                          'Genetics Lab',
                                          'Lost Species Ark World',
                                          'Avian Uplift Race',
                                          'Clandestine Uplift Lab'])
        self.assertEquals(7, t.BonusPer6Dev('Galactic Genome Project'))
        self.assertEquals(7, t.PointsPerCard('Galactic Genome Project'))
        self.assertEquals(5, t.PointsPerCard('Lost Species Ark World'))
        self.assertEquals(4, t.PointsPerCard('Avian Uplift Race'))
        self.assertEquals(2, t.PointsPerCard('Clandestine Uplift Lab'))
        
    def testGalacticImperium(self):
        t = tableau_scorer.TableauScorer(['Galactic Imperium',
                                          'Rebel Homeworld',
                                          'Rebel Warrior Race',
                                          'Former Penal Colony',
                                          'Rebel Pact'])
        self.assertEquals(5, t.BonusPer6Dev('Galactic Imperium'))
        self.assertEquals(5, t.PointsPerCard('Galactic Imperium'))
        self.assertEquals(9, t.PointsPerCard('Rebel Homeworld'))
        self.assertEquals(4, t.PointsPerCard('Rebel Warrior Race'))
        self.assertEquals(2, t.PointsPerCard('Former Penal Colony'))
        self.assertEquals(1, t.PointsPerCard('Rebel Pact'))

    def testGalacticRenaissance(self):
        t = tableau_scorer.TableauScorer(['Galactic Renaissance',
                                          'Galactic Trendsetters',
                                          'Research Labs',
                                          'Artist Colony',
                                          'Secluded World'], 4)
        self.assertEquals(21, t.TotalPoints())
        self.assertEquals(10, t.BonusPer6Dev('Galactic Renaissance'))
        self.assertEquals(10, t.PointsPerCard('Galactic Renaissance'))
        self.assertEquals(6, t.PointsPerCard('Galactic Trendsetters'))
        self.assertEquals(5, t.PointsPerCard('Research Labs'))
        self.assertEquals(4, t.PointsPerCard('Artist Colony'))

    def testGalacticSurveySETI(self):
        t = tableau_scorer.TableauScorer(['Galactic Survey SETI',
                                          'Research Labs',
                                          'Star Nomad Lair',
                                          'Investment Credits',
                                          'Expanding Colony'])
        self.assertEquals(5, t.BonusPer6Dev('Galactic Survey SETI'))
        self.assertEquals(5, t.PointsPerCard('Galactic Survey SETI'))
        self.assertEquals(3, t.PointsPerCard('Research Labs'))
        self.assertEquals(3, t.PointsPerCard('Star Nomad Lair'))
        self.assertEquals(1, t.PointsPerCard('Investment Credits'))
        self.assertEquals(2, t.PointsPerCard('Expanding Colony'))

    def testImperiumLords(self):
        t = tableau_scorer.TableauScorer(['Imperium Lords',
                                          'Galactic Imperium',
                                          'Rebel Homeworld',
                                          'Former Penal Colony'])
        self.assertEquals(6, t.BonusPer6Dev('Imperium Lords'))
        self.assertEquals(6, t.PointsPerCard('Imperium Lords'))
        self.assertEquals(3, t.BonusPer6Dev('Galactic Imperium'))
        self.assertEquals(5, t.PointsPerCard('Galactic Imperium'))
        self.assertEquals(10, t.PointsPerCard('Rebel Homeworld'))
        self.assertEquals(3, t.PointsPerCard('Former Penal Colony'))

    def testImperiumSeat(self):
        t = tableau_scorer.TableauScorer(['Imperium Seat',
                                          'Imperium Lords',
                                          'Rebel Underground',
                                          'Imperium Troops',
                                          'Insect Uplift Race',
                                          'Rebel Pact'])
        self.assertEquals(8, t.BonusPer6Dev('Imperium Seat'))
        self.assertEquals(8, t.BonusPer6Dev('Imperium Lords'))
        self.assertEquals(10, t.PointsPerCard('Imperium Seat'))
        self.assertEquals(10, t.PointsPerCard('Imperium Lords'))
        self.assertEquals(7, t.PointsPerCard('Rebel Underground'))
        self.assertEquals(5, t.PointsPerCard('Imperium Troops'))
        self.assertEquals(3, t.PointsPerCard('Insect Uplift Race'))
        self.assertEquals(1, t.PointsPerCard('Rebel Pact'))

    def testMerchantGuild(self):
        t = tableau_scorer.TableauScorer(['Merchant Guild',
                                          'Plague World',
                                          'Destroyed World'])
        self.assertEquals(2, t.BonusPer6Dev('Merchant Guild'))
        self.assertEquals(2, t.PointsPerCard('Merchant Guild'))
        self.assertEquals(2, t.PointsPerCard('Plague World'))
        self.assertEquals(0, t.PointsPerCard('Destroyed World'))

    def testMiningLeague(self):
        t = tableau_scorer.TableauScorer(['Mining League',
                                          'Mining World',
                                          'Comet Zone',
                                          'Smuggling Lair',
                                          'Mining Conglomerate',
                                          'Mining Robots',
                                          'Secluded World'])
        self.assertEquals(9, t.BonusPer6Dev('Mining League'))
        self.assertEquals(9, t.PointsPerCard('Mining League'))
        self.assertEquals(4, t.PointsPerCard('Comet Zone'))
        self.assertEquals(4, t.PointsPerCard('Mining World'))
        self.assertEquals(2, t.PointsPerCard('Smuggling Lair'))
        self.assertEquals(4, t.PointsPerCard('Mining Conglomerate'))
        self.assertEquals(3, t.PointsPerCard('Mining Robots'))
        self.assertEquals(1, t.PointsPerCard('Secluded World'))

    def testNewEconomy(self):
        t = tableau_scorer.TableauScorer(['New Economy',
                                          'Public Works',
                                          'Export Duties',
                                          'Secluded World',
                                          'Destroyed World'])
        self.assertEquals(5, t.BonusPer6Dev('New Economy'))
        self.assertEquals(5, t.PointsPerCard('New Economy'))
        self.assertEquals(3, t.PointsPerCard('Public Works'))
        self.assertEquals(1, t.PointsPerCard('Export Duties'))
        self.assertEquals(2, t.PointsPerCard('Secluded World'))
        self.assertEquals(0, t.PointsPerCard('Destroyed World'))

    def testNewGalacticOrder(self):
        t = tableau_scorer.TableauScorer(['New Galactic Order',
                                          'Lost Alien Battle Fleet',
                                          'Contact Specialist',
                                          'New Sparta',
                                          'Secluded World',
                                          'Space Mercenaries',
                                          'Hidden Fortress'])
        self.assertEquals(20, t.TotalPoints())
        self.assertEquals(10, t.BonusPer6Dev('New Galactic Order'))
        self.assertEquals(10, t.PointsPerCard('New Galactic Order'))
        self.assertEquals(7, t.PointsPerCard('Lost Alien Battle Fleet'))
        self.assertEquals(0, t.PointsPerCard('Contact Specialist'))
        self.assertEquals(3, t.PointsPerCard('New Sparta'))
        self.assertEquals(1, t.PointsPerCard('Secluded World'))
        self.assertEquals(1, t.PointsPerCard('Space Mercenaries'))
        self.assertEquals(3, t.PointsPerCard('Hidden Fortress'))

    def testNewGalacticOrder2(self):
        t = tableau_scorer.TableauScorer(['New Galactic Order',
                                          'Lost Alien Battle Fleet'])
        self.assertEquals(5, t.BonusPer6Dev('New Galactic Order'))
        self.assertEquals(5, t.PointsPerCard('New Galactic Order'))
        self.assertEquals(7, t.PointsPerCard('Lost Alien Battle Fleet'))

    def testPangalacticLeague(self):
        t = tableau_scorer.TableauScorer(['Pan Galactic League',
                                          'Contact Specialist',
                                          'Empath World',
                                          'Rebel Miners',
                                          'Secluded World'])
        self.assertEquals(6, t.BonusPer6Dev('Pan Galactic League'))
        self.assertEquals(6, t.PointsPerCard('Pan Galactic League'))
        self.assertEquals(4, t.PointsPerCard('Contact Specialist'))
        self.assertEquals(3, t.PointsPerCard('Empath World'))
        self.assertEquals(2, t.PointsPerCard('Rebel Miners'))
        self.assertEquals(1, t.PointsPerCard('Secluded World'))

    def testScorePangalacticResearch(self):
        t = tableau_scorer.TableauScorer(['Pan-Galactic Research',
                                          'Export Duties'])
        self.assertEquals(5, t.TotalPoints())
        self.assertEquals(0, t.BonusPer6Dev('Pan-Galactic Research'))
        self.assertEquals(4, t.PointsPerCard('Pan-Galactic Research'))
        self.assertEquals(1, t.PointsPerCard('Export Duties'))

    def testScoreProspectingGuild(self):
        t = tableau_scorer.TableauScorer(['Prospecting Guild',
                                          'Terraforming Robots',
                                          'Asteroid Belt',
                                          'Expanding Colony',
                                          'Mining World'])
        self.assertEquals(6, t.BonusPer6Dev('Prospecting Guild'))
        self.assertEquals(6, t.PointsPerCard('Prospecting Guild'))
        self.assertEquals(3, t.PointsPerCard('Terraforming Robots'))
        self.assertEquals(3, t.PointsPerCard('Asteroid Belt'))
        self.assertEquals(2, t.PointsPerCard('Expanding Colony'))
        self.assertEquals(4, t.PointsPerCard('Mining World'))

    def testScoreRebelAlliance(self):
        t = tableau_scorer.TableauScorer(['Rebel Alliance',
                                          'Rebel Miners',
                                          'Rebel Pact',
                                          'Lost Alien Battle Fleet'])
        self.assertEquals(7, t.BonusPer6Dev('Rebel Alliance'))
        self.assertEquals(7, t.PointsPerCard('Rebel Alliance'))
        self.assertEquals(3, t.PointsPerCard('Rebel Miners'))
        self.assertEquals(3, t.PointsPerCard('Rebel Pact'))
        self.assertEquals(5, t.PointsPerCard('Lost Alien Battle Fleet'))


    def testTerraformingGuild(self):
        t = tableau_scorer.TableauScorer(['Terraforming Guild',
                                          'Terraforming Robots',
                                          'Empath World',
                                          'Secluded World',
                                          'Improved Logistics'])
        self.assertEquals(6, t.BonusPer6Dev('Terraforming Guild'))
        self.assertEquals(6, t.PointsPerCard('Terraforming Guild'))
        self.assertEquals(4, t.PointsPerCard('Terraforming Robots'))
        self.assertEquals(3, t.PointsPerCard('Empath World'))
        self.assertEquals(1, t.PointsPerCard('Secluded World'))
        self.assertEquals(2, t.PointsPerCard('Improved Logistics'))

    def testTradeLeague(self):
        t = tableau_scorer.TableauScorer(['Trade League',
                                          'Export Duties',
                                          'Merchant World',
                                          'Deficit Spending'])
        self.assertEquals(5, t.BonusPer6Dev('Trade League'))        
        self.assertEquals(5, t.PointsPerCard('Trade League'))
        self.assertEquals(3, t.PointsPerCard('Export Duties'))
        self.assertEquals(3, t.PointsPerCard('Merchant World'))
        self.assertEquals(1, t.PointsPerCard('Deficit Spending'))

    def testScoreUpliftCode(self):
        t = tableau_scorer.TableauScorer(['Uplift Code',
                                          'Reptilian Uplift Race',
                                          'Abandoned Alien Uplift Camp',
                                          'New Vinland',
                                          'Devolved Uplift Race'])
        self.assertEquals(10, t.BonusPer6Dev('Uplift Code'))
        self.assertEquals(10, t.PointsPerCard('Uplift Code'))
        self.assertEquals(5, t.PointsPerCard('Reptilian Uplift Race'))
        self.assertEquals(4, t.PointsPerCard('Abandoned Alien Uplift Camp'))
        self.assertEquals(1, t.PointsPerCard('New Vinland'))
        self.assertEquals(4, t.PointsPerCard('Devolved Uplift Race'))

    def testK5995Tableau(self):
        t = tableau_scorer.TableauScorer(['Imperium Warlord', 
                                          'Interstellar Bank', 
                                          'Expedition Force', 
                                          'Terraforming Robots', 
                                          'Former Penal Colony', 
                                          'Galactic Advertisers', 
                                          'Rebel Underground', 
                                          'Aquatic Uplift Race', 
                                          'Galactic Imperium', 
                                          'Hive World', 
                                          'Outlaw World', 
                                          'Gambling World'])
        self.assertEquals(25, t.TotalPoints())
        self.assertEquals(6, t.BonusPer6Dev('Galactic Imperium'))

    def testR2540Tableau(self):
        t = tableau_scorer.TableauScorer(["New Sparta", 
                                          "Blaster Runners", 
                                          "Rebel Warrior Race", 
                                          "Public Works", 
                                          "Lost Species Ark World", 
                                          "Alien Robot Scout Ship", 
                                          "Insect Uplift Race", 
                                          "Alien Uplift Center", 
                                          "Universal Symbionts", 
                                          "Galactic Federation", 
                                          "Rebel Alliance", 
                                          "Galactic Imperium", 
                                          "Primitive Rebel World"], 8)
        self.assertEquals(53, t.TotalPoints())
        

                                          
        
if __name__ == '__main__':
    unittest.main()
