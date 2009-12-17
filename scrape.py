import cookielib
import os
import re
import simplejson
import time
import urllib
import urllib2
import os

import condense_scraped_data

def ReadOngoingGames():
    url = 'http://genie.game-host.org/loginchk.htm'
    values = {'user': 'rrenaud_scraper',
              'password': 'scraperaccount'}

    # This API is terrible.
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    req = urllib2.Request('http://genie.game-host.org/gamelist.htm')
    ongoing_game_list_data = urllib2.urlopen(req).read()
    open('gamelist.htm', 'w').write(ongoing_game_list_data)
    return ongoing_game_list_data
    

gid_re = re.compile('(\d+)')

def StripHTMLTags(text):
    tag_list = ['<td>', '</td>', '<tr>', '</tr>', '<table>', '</table>']
    for tag in tag_list:
        text = text.replace(tag, ' ')
    return text

def ParseWaitingForRow(row):
    gid_match = gid_re.search(row)
    assert gid_match
    waiting_for_ind = row.find('Waiting for ')
    assert waiting_for_ind != -1
    row = row[waiting_for_ind + len('Waiting for '):]
    end_table_ind = row.find('</table')
    assert end_table_ind != -1
    row = row[:end_table_ind]
    # Last action is on the other side of end_table_ind
    row = StripHTMLTags(row)
    players = [p.strip() for p in row.split(',')]
    return int(gid_match.group(1)), players
    

def ParseGameList(content):
    last_action_ind = content.find('Last action')
    assert last_action_ind != -1
    last_action_end_ind = last_action_ind + len('Last action')
    end_script_tag_ind = content.find('text/javascript', last_action_end_ind)
    assert end_script_tag_ind != -1
    content = content[last_action_end_ind: end_script_tag_ind]
    rows = content.split('game.htm?gid=')[1:-1]
    return [ParseWaitingForRow(row) for row in rows]

def ReadCompletedGameNos():
    games = simplejson.loads(open('condensed_games.json', 'r').read())
    completed_game_nums = set([int(g['game_no']) for g in games])
    return completed_game_nums

def main():
    ongoing_game_info = ParseGameList(ReadOngoingGames())
    ongoing_game_nums = [row[0] for row in ongoing_game_info]
    print 'on going games are', ongoing_game_nums

    completed_game_nums = ReadCompletedGameNos()
    num_retrieved = 0

    for i in xrange(max(ongoing_game_nums), max(ongoing_game_nums) - 10000, -1):
        try:
            if i in completed_game_nums:
                print 'skipped because complete', i
                continue
            if i in ongoing_game_nums:
                print 'skipped because ongoing', i
                continue

            url_name = 'game.htm?gid=%d' % i
            url = 'http://genie.game-host.org/' + url_name
            output_file_name = 'data/' + url_name
            dead_name = output_file_name + '.dead'
            if os.path.exists(dead_name):
                print 'skipping', output_file_name, 'because dead'
                continue

            time.sleep(20)
            url_file = urllib2.urlopen(url)
            num_retrieved += 1
            open(output_file_name, 'w').write(url_file.read())
            print 'wrote', output_file_name
        except Exception, e:
            print 'error', e, 'skipping game ', i, 'at', url
            open(dead_name, 'w').write('')

    print 'pulled down ', num_retrieved, 'new games'
    # condense_scraped_data.main()

if __name__ == '__main__':
    main()
