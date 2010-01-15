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
    n1r = .3 * 3
    n1f = .5 * 3
    n1k = .2 * 3
    n2r = .4 * 2
    n2k = .6 * 2
    
    # ELC norm win rate.
    # 2. / n1r == 3/.9 = 3.3333,
    # 3. / n2r == 2/.8 = 2.5
    # 3.333 + 2.5 ~= 2.91

    return {
        "Earth's Lost Colony": ((2 + 3) / 2., (3. / n1r + 2. / n2r) / 2, 2),
        "Alien Toy Shop":      (3, 3. /n1r                  , 1),
        "Interstellar Bank":   (3, 3. /n1r                  , 1),
        "Plague World":        (2, 2. /n2r      , 1),
        "New Sparta":          (0, (0. / n1f + 0./ n2k) / 1 , 2),
        "Alien Robot Sentry":  (0, 0. / n1f                 , 1),
        "Genetics Lab":        (0, 0. / n1f                 , 1),
        "Doomed World":        (0, 0. / n1k                 , 1),
        "Contact Specialist":  (0, 0. / n1k                 , 1),
        "Investment Credits":  (0, 0. / n1k                 , 1),
        "New Economy":         (0, 0. / n2k                 , 1),
        "New Vinland":         (0, 0. / n2k                 , 1),
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
        return {('rrenaud', 7): .3,
                ('fairgr', 7): .5,
                ('kingcong', 7): .2,
                ('rrenaud', 8): .4,
                ('Kesterer', 8): .6}[(player_name, game_no)]


def CardYielder(player_result, game):
    for card in player_result['cards']:
        yield card

class BaseTestCase(unittest.TestCase):
    def CompareValWithMsg(self, val1, val2, msg):
        expanded_msg = '%f != %f <%s>' % (val1, val2, msg)
        self.assertEquals(val1, val2, expanded_msg)


class ComputeWinningStatsByBucketTest(BaseTestCase):
    def testComputeWinningStatsByBucketTest(self):
        win_buckets = compute_stats.ComputeWinningStatsByBucket(
            GameList(), CardYielder, MockRatingSystem())

        expected_buckets = ExpectedBuckets()
        self.assertEquals(len(win_buckets), len(expected_buckets))
        win_buckets_keys = set([b.key for b in win_buckets])
        self.assertEquals(set(expected_buckets.keys()), win_buckets_keys)
        for bucket in win_buckets:
            self.assertTrue(bucket.key in expected_buckets)
            msg = bucket.key
            expected_bucket = expected_buckets[bucket.key]
            self.CompareValWithMsg(expected_bucket[0], bucket.win_points, msg)
            self.CompareValWithMsg(expected_bucket[1], bucket.norm_win_points, 
                                   msg)
            self.CompareValWithMsg(expected_bucket[2], bucket.frequency, msg)

class ComputeByCardStatsTest(BaseTestCase):
    
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
                                   card_stats[card_name]["win_points"],
                                   base_msg)

            self.CompareValWithMsg(expected_buckets[card_name][1],
                                   card_stats[card_name]["norm_win_points"],
                                   base_msg)

            self.CompareValWithMsg(expected_buckets[card_name][2] / 
                                   (FREQUENCY_DICT[card_name] * TOTAL_TABLEAUS),
                                   card_stats[card_name]["prob_per_card"],
                                   base_msg)

class RandomVariableObserver(unittest.TestCase):
    def testSimple(self):
        d = compute_stats.RandomVariableObserver()
        d.AddOutcome(4)  # 10 - 4 = 6, 6^2 = 36
        d.AddOutcome(16) # 16 - 10 = 6, 6^2 = 36
        d.AddOutcome(13) # 13 - 10 = 3, 3^2 = 9
        d.AddOutcome(7)  # 10 - 7 = 3, 3^2 = 9
        #  36 + 36 + 9 + 9 = 90, 90 / 3 = 30
        self.assertEquals(d.Frequency(), 4)
        self.assertEquals(d.Mean(), 10)
        self.assertEquals(d.Variance(), 30.0)

class TestLabelGameWithWinPoints(unittest.TestCase):
    def testTie(self):
        player_list = [
                {'name': 'rrenaud', 'points': 20, 'goods': 0, 'hand': 0}, 
                {'name': 'suboptimalrob', 'points': 19, 'goods': 0, 'hand': 0},
                {'name': 'fairgr', 'points': 20, 'goods': 0, 'hand': 0}
                ]
        g = {'player_list': player_list}
        compute_stats.LabelGameWithWinPoints(g)
        correct_points = {'rrenaud': 1.5, 'suboptimalrob': 0, 'fairgr': 1.5}
        for p in player_list:
            self.assertEquals(p['win_points'], correct_points[p['name']])


if __name__ == '__main__':
    unittest.main()
