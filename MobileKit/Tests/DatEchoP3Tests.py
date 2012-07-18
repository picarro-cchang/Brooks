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


class TestDatEchoP3(object):

    def setup_method(self, m):
        self.basicDat = os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'data', 'FCDS2008-20120610-131326Z-'
                                     'Datalog_User_Minimal.dat')
        self.emptyDatDir = os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'data', 'empty')

        self.localUrl = 'http://localhost:5000/test/rest/'

        p = subprocess.Popen(['python.exe', 'RESTEmulator.py'])
        time.sleep(3.0)
        self.server = psutil.Process(p.pid)

    def teardown_method(self, m):
        self.server.kill()
        time.sleep(5.0)

    def testCleanLaunch(self):
        datEcho = psutil.Process(
            subprocess.Popen(['python.exe', '../AnalyzerServer/DatEchoP3.py',
                              '-ddat',
                              "-f%s" % self.basicDat,
                              '-n200',
                              "-i%sgdu/<TICKET>/1.0/AnzMeta/" % self.localUrl,
                              "-p%sgdu/<TICKET>/1.0/AnzLog/" % self.localUrl,
                              "-k%ssec/dummy/1.0/Admin/" % self.localUrl,
                              '-yid',
                              '-sAPITEST']).pid)

        time.sleep(10.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) is 1
        assert int(stats['localIpReqs']) is 2
        assert int(stats['pushDataReqs']) is 6

    def testLaunchNoMissingFiles(self):
        datEcho = psutil.Process(
            subprocess.Popen(['python.exe', '../AnalyzerServer/DatEchoP3.py',
                              '-ddat',
                              "-l%s/*.dat" % self.emptyDatDir,
                              '-n200',
                              "-i%sgdu/<TICKET>/1.0/AnzMeta/" % self.localUrl,
                              "-p%sgdu/<TICKET>/1.0/AnzLog/" % self.localUrl,
                              "-k%ssec/dummy/1.0/Admin/" % self.localUrl,
                              '-yid',
                              '-sAPITEST']).pid)

        time.sleep(10.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) is 0
        assert int(stats['localIpReqs']) is 0
        assert int(stats['pushDataReqs']) is 0
