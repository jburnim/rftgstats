#!/usr/bin/python

import unittest
import compute_stats

class ComputeWinningStatsByBucketTest(unittest.TestCase):
    def testFoo(self):

        def CardYielder(player_result, game):
            for card in player_result['cards']:
                yield card

        class MockRatingSystem:
            def ProbWonAtGameNo(self, game_no, player_name):
                return {('rrenaud', 7): .4,
                        ('fairgr', 7): .4,
                        ('kingcong', 7): .2,
                        ('rrenaud', 8): .4,
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

        n1r = .4 * 3
        n1f = .4 * 3
        n1k = .2 * 3
        n2r = .4 * 2
        n2k = .6 * 2
        expected_buckets = {
            "Earth's Lost Colony": (5, n1r + n2r, 2),
            "Alien Toy Shop":      (3, n1r      , 1),
            "Plague World":        (2, n2r      , 1),
            "New Sparta":          (0, n1f + n2k, 2),
            "Alien Robot Sentry":  (0, n1f      , 1),
            "Genetics Lab":        (0, n1f      , 1),
            "Doomed World":        (0, n1k      , 1),
            "Contact Specialist":  (0, n1k      , 1),
            "Investment Credits":  (0, n1k      , 1),
            "New Economy":         (0, n2k      , 1),
            "New Vineland":        (0, n2k      , 1),
        }

        win_buckets = compute_stats.ComputeWinningStatsByBucket(
            games, CardYielder, MockRatingSystem())

        self.assertEquals(len(win_buckets), len(expected_buckets))
        win_buckets_keys = set([b.key for b in win_buckets])
        self.assertEquals(set(expected_buckets.keys()), win_buckets_keys)
        for bucket in win_buckets:
            self.assertTrue(bucket.key in expected_buckets)
            expected_bucket = expected_buckets[bucket.key]
            self.assertEquals(expected_bucket[0], bucket.win_points)
            self.assertEquals(expected_bucket[1], bucket.norm_exp_win_points)
            self.assertEquals(expected_bucket[2], bucket.frequency)

if __name__ == '__main__':
    unittest.main()
