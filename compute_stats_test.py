#!/usr/bin/python

import unittest
import compute_stats

def GameList():
    games = [{'game_no': 7,
              'expansion': 0,
              'player_list': [
                {'name': 'rrenaud',
                 'cards': ["Earth's Lost Colony", 'Alien Toy Shop',
                           'Interstellar Bank'],
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
                           "New Vinland"],
                 'points': 10,
                 },
                ]
              }
             ]
    for g in games:
        for p in g['player_list']:
            p['goods'] = 0
            p['hand'] = 0
    compute_stats.LabelGamesWithWinPoints(games)
    return games

def ExpectedBuckets():
    n1r = .4 * 3
    n1f = .4 * 3
    n1k = .2 * 3
    n2r = .4 * 2
    n2k = .6 * 2
    return {
        "Earth's Lost Colony": (5, n1r + n2r, 2),
        "Alien Toy Shop":      (3, n1r      , 1),
        "Interstellar Bank":   (3, n1r      , 1),
        "Plague World":        (2, n2r      , 1),
        "New Sparta":          (0, n1f + n2k, 2),
        "Alien Robot Sentry":  (0, n1f      , 1),
        "Genetics Lab":        (0, n1f      , 1),
        "Doomed World":        (0, n1k      , 1),
        "Contact Specialist":  (0, n1k      , 1),
        "Investment Credits":  (0, n1k      , 1),
        "New Economy":         (0, n2k      , 1),
        "New Vinland":         (0, n2k      , 1),
    }

TOTAL_TABLEAUS = 5

FREQUENCY_DICT = {
        "Earth's Lost Colony": 1.0,
        "Alien Toy Shop":      1.0,
        "Interstellar Bank":   2.0,
        "Plague World":        1.0,
        "New Sparta":          1.0,
        "Alien Robot Sentry":  1.0,
        "Genetics Lab":        2.0,
        "Doomed World":        1.0,
        "Contact Specialist":  3.0,
        "Investment Credits":  2.0,
        "New Economy":         1.0,
        "New Vinland":         1.0
}

class MockRatingSystem():
    def ProbWonAtGameNo(self, game_no, player_name):
        return {('rrenaud', 7): .4,
                ('fairgr', 7): .4,
                ('kingcong', 7): .2,
                ('rrenaud', 8): .4,
                ('Kesterer', 8): .6}[(player_name, game_no)]


def CardYielder(player_result, game):
    for card in player_result['cards']:
        yield card

class ComputeWinningStatsByBucketTest(unittest.TestCase):
    def testComputeWinningStatsByBucketTest(self):
        win_buckets = compute_stats.ComputeWinningStatsByBucket(
            GameList(), CardYielder, MockRatingSystem())

        expected_buckets = ExpectedBuckets()
        self.assertEquals(len(win_buckets), len(expected_buckets))
        win_buckets_keys = set([b.key for b in win_buckets])
        self.assertEquals(set(expected_buckets.keys()), win_buckets_keys)
        for bucket in win_buckets:
            self.assertTrue(bucket.key in expected_buckets)
            expected_bucket = expected_buckets[bucket.key]
            self.assertEquals(expected_bucket[0], bucket.win_points)
            self.assertEquals(expected_bucket[1], bucket.norm_exp_win_points)
            self.assertEquals(expected_bucket[2], bucket.frequency)

class ComputeByCardStatsTest(unittest.TestCase):
    def CompareValWithMsg(self, val1, val2, msg):
        expanded_msg = '%f != %f <%s>' % (val1, val2, msg)
        self.assertEquals(val1, val2, expanded_msg)

    def testComputeWinningStatsByCard(self):
        card_stats = compute_stats.ComputeWinningStatsByCardPlayed(
            GameList(), MockRatingSystem())
        expected_buckets = ExpectedBuckets()
        nonhw_keys = [b for b in expected_buckets if not b in 
                         compute_stats.HOMEWORLDS]
        self.assertEquals(set(nonhw_keys).symmetric_difference(
                set(card_stats.keys())), set())
        for card_name in card_stats:
            base_msg = card_name + ' ' + str(card_stats[card_name])
            self.assertTrue(card_name in nonhw_keys)

            self.CompareValWithMsg(expected_buckets[card_name][0],
                                   card_stats[card_name]["win_rate"],
                                   base_msg)

            self.CompareValWithMsg(expected_buckets[card_name][0] / 
                                   expected_buckets[card_name][1],
                                   card_stats[card_name]["norm_win_rate"],
                                   base_msg)

            self.CompareValWithMsg(expected_buckets[card_name][2] / 
                                   (FREQUENCY_DICT[card_name] * TOTAL_TABLEAUS),
                                   card_stats[card_name]["prob_per_card"],
                                   base_msg)

class MeanVarDictTest(unittest.TestCase):
    def testSimple(self):
        d = compute_stats.MeanVarDict()
        d.AddEvent('a', 4)
        d.AddEvent('a', 16)
        d.AddEvent('a', 13)
        d.AddEvent('a', 7)
        self.assertEquals(d.Frequency('a'), 4)
        # var should be ~= 29.3333

if __name__ == '__main__':
    unittest.main()
