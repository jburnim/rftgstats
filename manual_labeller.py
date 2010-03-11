#!/usr/bin/python

import compute_stats
import collections
import random
import simplejson as json
import pprint

def IsInt(v):
    try:
        y = int(v)
        return True
    except:
        return False

def GetLabels(keys, name):
    good_input = False
    while not good_input:
        good_input = True
        x = raw_input('label(s) for ' + name + ': ')
        vals = x.split()
        ret = []
        for val in vals:
            if IsInt(val):
                val = int(val)
                if 0 <= val < len(keys):
                    ret.append(keys[val])
                else:
                    good_input = False
                    print 'bad index', val
                    break
            else:
                print 'warning new key', val
                keys.append(val)
                keys.sort()
                ret.append(val)
        good_input = good_input and len(ret) > 0
    return ret
                    

def ReadLabels():
    labels = set()
    games = set()
    for line in open('golden_labels.csv', 'r'):
        split_line = line.strip().split(',')
        for label in split_line[2:]:
            labels.add(label)
        games.add(int(split_line[1]))
    labels = sorted(list(labels))
    return labels, games

def main():
    games = map(compute_stats.Game, json.load(open('terse_games.json', 'r')))
    keys, labelled_games = ReadLabels()

    random.shuffle(games)
    output_file = open('golden_labels2.csv', 'a', 0)
    for game in games:
        if game.GameNo() in labelled_games:
            print 'skipping labelled game', game
            continue
        print game
        for idx, key in enumerate(keys):
            print idx, key
        for player_result in game.PlayerList():
            labels = GetLabels(keys, player_result.Name())
            output_file.write(
                '%s,%d,%s\n' % (player_result.Name(), game.GameNo(), 
                                ','.join(labels))
                )

                                
                

if __name__ == '__main__':
    main()
