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

if __name__ == '__main__':
    for i in range(9200, 10500):
        ReadGameNo(i)
