#!/usr/bin/python

import unittest
import compute_stats

class ComputeWinningStatsByBucketTest(unittest.TestCase):
    def testFoo(self):
        games = [{'game_no': 7,
                  'expansion': 0
                  'player_list': [
                      {'name': 'rrenaud',
                       'cards': ["Earth's Lost Colony", 'Alien Toy Shop']
                       'points': 26,
                       'hand': 0,
                       'chips': 24},
                      {'name': 'fairgr',
                       'cards': ["New Sparta", "Alien Robot Sentry",
                                 "Genetics Lab"],
                       'points': 10,
                       'hand': 5,
                       'chips': 0},
                      {'name': 'kingcong',
                       'cards': ["Doomed World", 'Contact Specialist',
                                 'Investment Credits']
                       'points': 20,
                       'hand': 7,
                       'chips': 0},
                      ]
                  },
                  {'game_no': 8,
                   'expansion': 0
                   'player_list': [
                      {'name': 'rrenaud',
                       'cards': ["Earth's Lost Colony", 'Plague World']
                       'points': 13,
                       'hand': 0,
                       'chips': 10},
                      {'name': 'Kesterer',
                       'cards': ["New Sparta", "New Economy",
                                 "New Vineland"],
                       'points': 10,
                       'hand': 5,
                       'chips': 0},
                      ]
                  }
                 ]
        def CardYielder(player_result):
            for card in player_result['cards']:
                yield card

        class MockRatingSystem:
            def ProbBeatWinnerAtGameNo(self, game_no, player_name):
                return {('fairgr', 7): .5,
                        ('kingcong', 7): .2,
                        ('Kesterer', 8): .6}[(player_no, game_no)]
        win_buckets = compute_stats.ComputeWinningStatsByBucket(
            games, CardYielder, MockRatingSystem())
        BucketInfo = compute_stats.BucketInfo
        expected_buckets = [
            BucketInfo("Earth's Lost Colony", 2.5, 2, (.5 + .8) * 3/2 + 
                  
            

if __name__ == '__main__':
    unittest.main()
