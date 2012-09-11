import xml.etree.ElementTree as ET

import os
import time
import urllib2

def ReadGameNo(game_no):
    url = 'http://www.keldon.net/rftg/showgame.cgi?gid=%d' % game_no
    output_fn = 'keldon/' + str(game_no)
    #time.sleep(30) # why?
    try:
        print 'getting', url
        url_file = urllib2.urlopen(url)
        contents = url_file.read()
        open(output_fn, 'w').write(contents)
    except urllib2.HTTPError, e:
        print e

def ReadAvailableGames():
    list_url = 'http://www.keldon.net/rftg/games.cgi'
    contents = urllib2.urlopen(list_url)
    ret = []
    for line in contents:
        if line.find('showgame.cgi') != -1:
            ret.append( int(line.split('gid=')[1].split('"')[0]) )
            
    return ret
    
def ReadCompletedGames():
    import scraper_util
    return scraper_util.ReadGameNosSet('condensed_keldon.json')

def main():
    available_games = ReadAvailableGames()
    completed_games = ReadCompletedGames() 

    for game_no in available_games:
    #for game_no in available_games[:1000]: #debugging version
        if ('http://www.keldon.net/rftg/showgame.cgi?gid=%d' % game_no) in completed_games:
            #print game_no, 'skipped because complete'
            continue
        output_fn = 'keldon/%d' % game_no
        if os.access(output_fn, os.O_RDONLY):
            print game_no, 'skipping because exists (but not condensed?)'
            continue
        #if open(output_fn).read() == 'error':
        #    print game_no, 'skipped because of previous error'
        #    continue
        try:
            ReadGameNo(game_no)
        except:
            print "Error getting game", game_no, "continuing..."

if __name__ == '__main__':
    main()
