"""
Copyright 2012 Picarro Inc.

Sample script for evaluating the reference gas injection as
implemented via Peak Detector in DSP
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
    states = ["Idle", "Armed", "Trigger Pending", "Triggered", "Inactive", "Cancelling", "Priming", "Purging", "Injection Pending"]
    # server = AnalyzerServer()
    # print 'Starting analyzerServer'
    # server.start()

    # time.sleep(5.0)
    try:
        urlBase = 'http://localhost:5000'

        print 'Priming and purging gas line'
        r = urllib2.urlopen("%s/rest/driverRpc?func=wrDasReg&args=['PEAK_DETECT_CNTRL_STATE_REGISTER','PEAK_DETECT_CNTRL_PrimingState']" % urlBase).read()
        response = json.loads(r)
        pprint.pprint(response)
        
        while True:
            r = urllib2.urlopen("%s/rest/driverRpc?func=rdDasReg&args=['PEAK_DETECT_CNTRL_STATE_REGISTER']" % urlBase).read()
            response = json.loads(r)
            pprint.pprint(response)
            state = response["result"]["value"]
            print '%s state. Polling to await injection pending' % states[state]
            if state == 8: break
            time.sleep(1.0)
        
        print "Switching to capture mode"
        r = urllib2.urlopen("%s/rest/driverRpc?func=wrDasReg&args=['PEAK_DETECT_CNTRL_STATE_REGISTER','PEAK_DETECT_CNTRL_ArmedState']" % urlBase).read()
        response = json.loads(r)
        pprint.pprint(response)
        
        print "Injecting reference gas"
        r = urllib2.urlopen("%s/rest/injectCal?valve=3&flagValve=4&samples=2" % urlBase).read()
        response = json.loads(r)
        pprint.pprint(response)
        
        while True:
            r = urllib2.urlopen("%s/rest/driverRpc?func=rdDasReg&args=['PEAK_DETECT_CNTRL_STATE_REGISTER']" % urlBase).read()
            response = json.loads(r)
            pprint.pprint(response)
            state = response["result"]["value"]
            print '%s state. Polling to await idle state' % states[state]
            if state == 0: break
            time.sleep(1.0)
        
    finally:
        pass
#        server.stop()

if __name__ == '__main__':
    main()
