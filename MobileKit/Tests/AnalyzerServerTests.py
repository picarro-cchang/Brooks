"""
Copyright 2013 Picarro Inc.
"""

from __future__ import with_statement

import subprocess
import time
import urllib2
import os.path

import psutil
import simplejson as json


class TestAnalyzerServer(object):

    def setup(self):
        self.url = 'http://localhost:5000/rest'
        self.server = None
        with open('configAnaylzerServer.ini', 'w') as fp:
            fp.write("[data_file]\n")

    def teardown(self):
        if self.server:
            self.server.kill()

    def testAPINoAnalyzer(self):
        self.server = psutil.Process(
            subprocess.Popen(
                ['python.exe',
                 os.path.join('..', 'AnalyzerServer', 'analyzerServer.py'),
                 '--no-analyzer']).pid)

        time.sleep(10.0)
        assert self.server.is_running()

        r = urllib2.urlopen("%s/restartDatalog" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/shutdownAnalyzer" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/getCurrentInlet" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'Mast'

        r = urllib2.urlopen("%s/setCurrentInlet" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/getCurrentReference" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'CONCENTRATION'

        r = urllib2.urlopen("%s/setCurrentReference" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/cancelIsotopicCapture" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/startTriggeredIsotopicCapture" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/startManualIsotopicCapture" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'OK'

        r = urllib2.urlopen("%s/getIsotopicCaptureState" % self.url)
        resp = json.loads(r.read())
        assert resp['result'] == 'IDLE'
