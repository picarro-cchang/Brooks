"""
Copyright 2012 Picarro Inc.

Sample script for evaluating the reference gas injection as
implemented via AnalyzerServer.
"""

import urllib2
import subprocess
import pprint
import time
import os.path

import psutil
import simplejson as json


class AnalyzerServer(object):

    def __init__(self):
        self.process = None

    def start(self):
        if self.process:
            self.stop()

        self.process = psutil.Process(subprocess.Popen(
                ['python.exe',
                 os.path.join('..', 'AnalyzerServer', 'analyzerServer.py')]).pid)

    def stop(self):
        if self.process:
            self.process.kill()
            self.process = None

def main():
    # server = AnalyzerServer()
    # print 'Starting analyzerServer'
    # server.start()

    # time.sleep(5.0)

    try:
        urlBase = 'http://localhost:5000'

        print 'Priming gas line'
        r = urllib2.urlopen("%s/rest/startRefCalibration" % urlBase).read()
        response = json.loads(r)

        pprint.pprint(response)
        assert response['result']['value'] == 'OK'

        print 'Polling to do calibration injection'
        r = urllib2.urlopen("%s/rest/tryInject" % urlBase).read()
        response = json.loads(r)
        pprint.pprint(response)

        while response['result']['injected'] == 'false':
            time.sleep(0.1)
            r = urllib2.urlopen("%s/rest/tryInject" % urlBase).read()
            response = json.loads(r)
            pprint.pprint(response)

            print 'Injection complete'

    finally:
        pass
#        server.stop()

if __name__ == '__main__':
    main()
