import urllib2
import os
import time

if __name__ == '__main__':
    for i in range(2500, 3500):
        try:
            url_name = 'game.htm?gid=%d' % i
            output_file_name = 'data/' + url_name
            dead_name = output_file_name + '.dead'
            if (os.path.exists(output_file_name) or
                os.path.exists(dead_name)):
                print 'skipped', output_file_name
                continue
            url = 'http://genie.game-host.org/' + url_name
            time.sleep(5)
            url_file = urllib2.urlopen(url)
            open(output_file_name, 'w').write(url_file.read())
            print 'wrote', output_file_name
        except Exception, e:
            print 'error', e, 'skipping game ', i, 'at', url
            open(dead_name, 'w').write('')
            
