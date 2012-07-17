"""
Copyright 2012 Picarro Inc.
"""

from __future__ import with_statement

import sys
import subprocess
import threading
import os.path
import time
import urllib2

import simplejson as json
import psutil

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
                             'AnalyzerServer'))
import DatEchoP3


class TestDatEchoP3(object):

    def setup_method(self, m):
        self.basicDat = os.path.join('.', 'data',
                                     'fcds2008-20120610-131326Z-'
                                     'Datalog_User_Minimal.dat')

        p = subprocess.Popen(['python.exe', 'RESTEmulator.py'])

        # Let it stabilize
        time.sleep(1.0)

        self.server = psutil.Process(p.pid)

    def teardown_method(self, m):
        print "Killing process..."
        self.server.kill()

    def testCleanLaunch(self):
        d = DatEchoP3.DataEchoP3(
            file_path=self.basicDat,
            ip_url='http://localhost:5000/test/rest/gdu/<TICKET>/1.0/AnzMeta/',
            push_url='http://localhost:5000/test/rest/gdu/<TICKET>/1.0/AnzLog/',
            ticket_url='http://localhost:5000/test/rest/sec/dummy/1.0/Admin/',
            psys='APITEST',
            identity='id',
            lines=200,
            logtype='dat')
        t = threading.Thread(target=d.run)
        t.start()

        time.sleep(10.0)

        assert t.isAlive()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) is 1
        assert int(stats['localIpReqs']) is 2
        assert int(stats['pushDataReqs']) is 7
