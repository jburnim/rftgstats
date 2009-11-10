import urllib2
import os
import time

if __name__ == '__main__':
    games = eval(open('condensed_games.json', 'r').read())
    completed_game_nums = set([int(g['game_no']) for g in games])
    for i in range(1, 55500):
        try:
            url_name = 'game.htm?gid=%d' % i
            url = 'http://genie.game-host.org/' + url_name
            output_file_name = 'data/' + url_name
            dead_name = output_file_name + '.dead'
            if i in completed_game_nums:
                print 'skipped because complete', i
                continue
            if os.path.exists(dead_name):
                print 'skipping', output_file_name, 'because dead'
                continue

            time.sleep(5)
            url_file = urllib2.urlopen(url)
            open(output_file_name, 'w').write(url_file.read())
            print 'wrote', output_file_name
        except Exception, e:
            print 'error', e, 'skipping game ', i, 'at', url
            open(dead_name, 'w').write('')
            
