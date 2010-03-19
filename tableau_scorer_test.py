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
        self.assertEquals(9, t.BonusPer6Dev('Alien Tech Institute'))
        self.assertEquals(9, t.PointsPerCard('Alien Tech Institute'))
        self.assertEquals(5, t.PointsPerCard('Damaged Alien Factory'))

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
                                          'Rebel HomeWorld',
                                          'Rebel Warrior Race',
                                          'Former Penal Colony'])
        self.assertEquals(5, t.BonusPer6Dev('Galactic Imperium'))
        self.assertEquals(5, t.PointsPerCard('Galactic Imperium'))
        self.assertEquals(9, t.PointsPerCard('Rebel HomeWorld'))
        self.assertEquals(4, t.PointsPerCard('Rebel Warrior Race'))
        self.assertEquals(2, t.PointsPerCard('Former Penal Colony'))

    def testGalacticRenaissance(self):
        t = tableau_scorer.TableauScorer(['Galactic Renaissance',
                                          'Galactic Trendsetters',
                                          'Research Labs',
                                          'Artist Colony',
                                          'Secluded World'], 4)
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
                                          'Rebel HomeWorld',
                                          'Former Penal Colony'])
        self.assertEquals(6, t.BonusPer6Dev('Imperium Lords'))
        self.assertEquals(6, t.PointsPerCard('Imperium Lords'))
        self.assertEquals(3, t.BonusPer6Dev('Galactic Imperium'))
        self.assertEquals(5, t.PointsPerCard('Galactic Imperium'))
        self.assertEquals(10, t.PointsPerCard('Rebel HomeWorld'))
        self.assertEquals(3, t.PointsPerCard('Former Penal Colony'))

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
                                          'Space Mercenaries'])
        self.assertEquals(7, t.BonusPer6Dev('New Galactic Order'))
        self.assertEquals(7, t.PointsPerCard('New Galactic Order'))
        self.assertEquals(7, t.PointsPerCard('Lost Alien Battle Fleet'))
        self.assertEquals(0, t.PointsPerCard('Contact Specialist'))
        self.assertEquals(3, t.PointsPerCard('New Sparta'))
        self.assertEquals(1, t.PointsPerCard('Secluded World'))
        self.assertEquals(1, t.PointsPerCard('Space Mercenaries'))

    def testPangalacticLeague(self):
        t = tableau_scorer.TableauScorer(['Pan-galactic League',
                                          'Contact Specialist',
                                          'Empath World',
                                          'Rebel Miners',
                                          'Secluded World'])
        self.assertEquals(6, t.BonusPer6Dev('Pan-galactic League'))
        self.assertEquals(6, t.PointsPerCard('Pan-galactic League'))
        self.assertEquals(4, t.PointsPerCard('Contact Specialist'))
        self.assertEquals(3, t.PointsPerCard('Empath World'))
        self.assertEquals(2, t.PointsPerCard('Rebel Miners'))
        self.assertEquals(1, t.PointsPerCard('Secluded World'))

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
        
if __name__ == '__main__':
    unittest.main()
