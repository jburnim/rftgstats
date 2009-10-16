#!/usr/bin/python

import unittest
import compute_stats

class ComputeWinningStatsByBucketTest(unittest.TestCase):
    def testFoo(self):

        def CardYielder(player_result):
            for card in player_result['cards']:
                yield card

        class MockRatingSystem:
            def ProbBeatWinnerAtGameNo(self, game_no, player_name):
                return {('fairgr', 7): .5,
                        ('kingcong', 7): .2,
                        ('Kesterer', 8): .6}[(player_name, game_no)]

        games = [{'game_no': 7,
                  'expansion': 0,
                  'player_list': [
                      {'name': 'rrenaud',
                       'cards': ["Earth's Lost Colony", 'Alien Toy Shop'],
                       'points': 26,
                       },
                      {'name': 'fairgr',
                       'cards': ["New Sparta", "Alien Robot Sentry",
                                 "Genetics Lab"],
                       'points': 10,
                       },
                      {'name': 'kingcong',
                       'cards': ["Doomed World", 'Contact Specialist',
                                 'Investment Credits'],
                       'points': 20,
                       },
                      ]
                  },
                  {'game_no': 8,
                   'expansion': 0,
                   'player_list': [
                      {'name': 'rrenaud',
                       'cards': ["Earth's Lost Colony", 'Plague World'],
                       'points': 13,
                       },
                      {'name': 'Kesterer',
                       'cards': ["New Sparta", "New Economy",
                                 "New Vineland"],
                       'points': 10,
                       },
                      ]
                  }
                 ]
        for g in games:
            for p in g['player_list']:
                p['goods'] = 0
                p['hand'] = 0
        win_buckets = compute_stats.ComputeWinningStatsByBucket(
            games, CardYielder, MockRatingSystem())
        BInfo = compute_stats.BucketInfo
        n1r = (.5 + .8) * 3./2
        n2r = .4 * 2.0
        n1f = (.5 + .8) * 3./2
        n1k = .2 * .3 / 2
        n2k = .6 * 2.0
        expected_buckets = {
            "Earth's Lost Colony": (5, 2, n1r + n2r, 2),
            "Alien Toy Shop":      (3, 1, n1r      , 1),
            "Plague World":        (2, 1, n2r      , 1),
            "New Sparta":          (0, 2, n1f + n2k, 2),
            "Alien Robot Sentry":  (0, 1, n1f      , 1),
            "Genetics Lab":        (0, 1, n1f      , 1),
            "Doomed World":        (0, 1, n1k      , 1),
            "Contact Specialist":  (0, 1, n1k      , 1),
            "Investment Credits":  (0, 1, n1k      , 1),
            "New Economy":         (0, 1, n2k      , 1),
            "New Vineland":        (0, 1, n2k      , 1),
        }
        for bucket in win_buckets:
            self.expectTrue(win_bucket.key() in expected_buckets)
            

if __name__ == '__main__':
    unittest.main()
