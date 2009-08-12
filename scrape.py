import urllib2
import os
import time
import condense_scraped_data

def GameComplete(file_name):
    class MockInfo:
        def __getitem__(self, key):
            return {'exp. 1': True, 'name': 'foo'}
    return condense_scraped_data.ParseGame(open(file_name, 'r').read(),
                                           MockInfo()) != None

if __name__ == '__main__':
    for i in range(7000, 10500):
        try:
            url_name = 'game.htm?gid=%d' % i
            url = 'http://genie.game-host.org/' + url_name
            output_file_name = 'data/' + url_name
            dead_name = output_file_name + '.dead'
            if os.path.exists(output_file_name):
                completed = GameComplete(output_file_name)
                print output_file_name, 'exists, completed?', completed
                if completed:
                    print 'skipped because complete', output_file_name
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
            
