import xml.etree.ElementTree as ET

import time
import urllib2

def ReadGameNo(game_no):
    fn = '%d.xml' % game_no
    url = 'http://www.flexboardgames.com/games/%s' % fn
    output_fn = 'flex2/' + fn
    time.sleep(5)
    url_file = urllib2.urlopen(url)
    open(output_fn, 'w').write(url_file.read())
    print url

def ReadOngoingGames():
    ongoing_url = 'http://www.flexboardgames.com/games.xml?option=allOpenGames'
    contents = urllib2.urlopen(ongoing_url)
    root = ET.parse(contents).getroot()
    print root
    ids = []
    for id_node in root.findall('game/id'):
        ids.append(int(id_node.text))
    return set(ids)
    
def ReadCompletedGames():
    import scraper_util
    return scraper_util.ReadGameNos('condensed_flex.json')

if __name__ == '__main__':
    ongoing_games = ReadOngoingGames() 
    completed_games = ReadCompletedGames()
    max_game_no = max(ongoing_games):
    for game_no in range(1, max_game_no):
        if game_no in ongoing_games:
            print game_no, 'skipped because ongoing'
            continue
        if game_no in completed_games:
            print game_no, 'skipped because complete'
            continue
        if open('flex2/%.xml' % game_no).read() == 'error':
            print game_no, 'skipped because of previous error'
            continue
        
        
