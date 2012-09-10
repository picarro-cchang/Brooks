"""
Copyright 2012 Picarro Inc.
"""

from __future__ import with_statement

import sys
import subprocess
import os.path
import time
import datetime
import urllib2
import datetime
import shutil
import pickle
import pprint

import simplejson as json
import psutil

from Host.Common import SharedTypes


class TestDatEchoP3(object):

    def setup_method(self, m):
        self.datRoot = os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'data')
        self.emptyDatDir = os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'data', 'empty')

        self.localUrl = 'http://localhost:5000/test/rest/'

        p = subprocess.Popen(['python.exe', 'RESTEmulator.py'])
        time.sleep(3.0)
        self.server = psutil.Process(p.pid)

        # Other things we may need to cleanup later
        self.driverEmulator = None

        for d in ['test2', 'test3', 'test4', 'test5', 'test6', 'test7', 'test8',
                  'test9', 'test10', 'test11', 'test12']:
            path = os.path.join(self.datRoot, d)
            if os.path.isdir(path):
                shutil.rmtree(path)

    def teardown_method(self, m):
        self.server.kill()
        time.sleep(5.0)

        if self.driverEmulator is not None:
            self.driverEmulator.kill()
            self.driverEmulator = None

    def _logLinesToDict(self, logPath):
        """
        Parse the requested log file into an array of dict entries suitable for
        comparison to the values returned by the REST emulator.
        """

        ret = []

        with open(logPath, 'r') as fp:
            header = None
            rowIdx = 0

            for line in fp.readlines():
                vals = line.split()
                doc = {}

                if header is None:
                    header = vals
                    continue

                for col, val in zip(header, vals):
                    # See the comment in DatEchoP3.py for an explanation of this
                    # logic.
                    try:
                        doc[col] = float(val)

                        try:
                            if math.isnan(doc[col]):
                                doc[col] = 'NaN'

                        except:
                            pass

                    except ValueError, e:
                        doc[col] = 'NaN'

                rowIdx += 1
                doc['row'] = rowIdx
                ret.append(doc)

        return ret

    def testCleanLaunch(self):
        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen([
                    'python.exe', '../AnalyzerServer/DatEchoP3.py',
                    '-ddat',
                    "-l%s/*.dat" % self.emptyDatDir,
                    '-n200',
                    "-i%sgdu/<TICKET>/1.0/AnzMeta/" % self.localUrl,
                    "-p%sgdu/<TICKET>/1.0/AnzLog/" % self.localUrl,
                    "-k%ssec/dummy/1.0/Admin/" % self.localUrl,
                    "--log-metadata-url=%sgdu/<TICKET>/1.0/AnzLogMeta/" % (
                        self.localUrl),
                    '-yid',
                    '-sAPITEST',
                    "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR]
                             ).pid)

        time.sleep(10.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) == 2
        assert int(stats['pushDataReqs']) == 0
        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

    def testOneMissedFile(self):
        testDatDir = os.path.join(self.datRoot, 'test2')
        assert not os.path.isdir(testDatDir)

        # Use date/times close to today so we trigger the 5-day check on
        # the server.
        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test2'),
                 '-n200',
                 "-i%sgdu/<TICKET>/2.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/2.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/2.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/2.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(100.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1
        # Target .dat file has 16207 rows. We push in chunks of 200.
        assert int(stats['pushDataReqs']) == 82

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

    def testRowCacheCreation(self):
        # Should return a file that we have copied already and verify that the
        # cache is created (and contains the correct data).
        testDatDir = os.path.join(self.datRoot, 'test3')
        assert not os.path.isdir(testDatDir)

        # Use date/times close to today so we trigger the 5-day check on
        # the server.
        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        r = urllib2.urlopen("http://localhost:5000/setLogDate/%d/%d/%d"
                            "/%d/%d/%d" % (targetDt.year, targetDt.month,
                                           targetDt.day, targetDt.hour,
                                           targetDt.minute, targetDt.second))
        r.read()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test3'),
                 '-n200',
                 "-i%sgdu/<TICKET>/3.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/3.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/3.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/3.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
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

        assert int(stats['pushDataReqs']) == 0

        # Verify the row cache was created and is correct
        assert os.path.isfile(os.path.join(targetDir, "%s.row" % target))

        nRows = 0
        with open(os.path.join(targetDir, "%s.row" % target), 'rb') as fp:
            nRows = pickle.load(fp)

        assert nRows == 16207

    def testIncompleteFile(self):
        # Should return a file that we have copied already and verify that the
        # cache is created (and contains the correct data).
        testDatDir = os.path.join(self.datRoot, 'test4')
        assert not os.path.isdir(testDatDir)

        # Use date/times close to today so we trigger the 5-day check on
        # the server.
        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        r = urllib2.urlopen("http://localhost:5000/setLogDate/%d/%d/%d"
                            "/%d/%d/%d" % (targetDt.year, targetDt.month,
                                           targetDt.day, targetDt.hour,
                                           targetDt.minute, targetDt.second))
        r.read()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test4'),
                 '-n200',
                 "-i%sgdu/<TICKET>/4.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/4.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/4.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/4.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(60.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1

        # Should be 207 remaining lines to push. With N = 200, the last push
        # should have 7 lines in it.
        assert stats['lastNLines'] == 7

        # Target .dat file has 16207 rows. We push in chunks of 200.
        assert int(stats['pushDataReqs']) == 2

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

    def testOneMissedFileAndThenLive(self):
        testDatDir = os.path.join(self.datRoot, 'test5')
        assert not os.path.isdir(testDatDir)

        # Use date/times close to today so we trigger the 5-day check on
        # the server.
        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test5'),
                 '-n200',
                 "-i%sgdu/<TICKET>/5.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/5.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/5.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/5.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(100.0)

        assert datEcho.is_running()

        # Inject a new live file
        targetDt = datetime.datetime.utcnow()

        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        time.sleep(100.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1
        # Target .dat file has 16207 rows. We push in chunks of 200.
        assert int(stats['pushDataReqs']) == 164

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        assert stats['pushedFiles'] == 2

    def testEmptyDirThenLive(self):
        testDatDir = os.path.join(self.datRoot, 'test6')
        assert not os.path.isdir(testDatDir)

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test6'),
                 '-n200',
                 "-i%sgdu/<TICKET>/6.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/6.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/6.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/5.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(10.0)

        assert datEcho.is_running()

        # Inject a new live file
        targetDt = datetime.datetime.utcnow()

        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        time.sleep(100.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1
        # Target .dat file has 16207 rows. We push in chunks of 200.
        assert int(stats['pushDataReqs']) == 82

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        assert stats['pushedFiles'] == 1

    def testDayRolloverUnknownFile(self):
        """
        The stress test revealed that when the day rolled over, any
        unprocessed files in the previous day's directory were
        missed. We will reproduce this by writing a file into the
        current day's directory, let it start processing and then
        write a second file into today. Lastly before it finishes on
        the initial file we will write a new file into today + 1. Let
        the process sit for a while until we think all files should be
        sent. We can then query the server to verify that they have
        all been completely sent.
        """

        testDatDir = os.path.join(self.datRoot, 'test7')
        assert not os.path.isdir(testDatDir)

        files = []

        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        files.append(target)
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test7'),
                 '-n200',
                 "-i%sgdu/<TICKET>/7.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/7.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/7.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/7.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(15.0)

        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        files.append(target)
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        try:
            os.makedirs(targetDir)
        except:
            pass

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        # DatEchoP3 should still be processing the initial file from
        # "two" days ago, so now write out one that is on a different
        # day.

        targetDt = datetime.datetime.utcnow()
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        files.append(target)
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        try:
            os.makedirs(targetDir)
        except:
            pass

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        # Give DatEchoP3 a chance to send back everything
        time.sleep(300.0)

        assert datEcho.is_running()
        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/filesRowsStats')
        filesAndRows = json.loads(r.read())

        assert len(filesAndRows) == len(files)
        for fr in filesAndRows:
            assert int(fr[1]) == 16207
        assert set([fr[0] for fr in filesAndRows]) == set(files)


    def testNoLogFiles(self):
        """
        If there are no log files for an analyzer we expect error code 404,
        but the process should continue running.
        """

        testDatDir = os.path.join(self.datRoot, 'test8')
        assert not os.path.isdir(testDatDir)

        os.makedirs(testDatDir)

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test8'),
                 '-n200',
                 "-i%sgdu/<TICKET>/8.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/8.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/8.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/8.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(15.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1
        assert int(stats['pushDataReqs']) == 0

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        assert stats['pushedFiles'] == 0

    def testNoEmptyIdSent(self):
        """
        We should never send a blank analyzer Id to P3.
        """

        testDatDir = os.path.join(self.datRoot, 'test9')
        assert not os.path.isdir(testDatDir)

        os.makedirs(testDatDir)

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py',
                              '--empty-id']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test9'),
                 '-n200',
                 "-i%sgdu/<TICKET>/9.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/9.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/9.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/9.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(5.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/analyzerIds')

        for a in json.loads(r.read()):
            assert a != ''

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 0
        assert int(stats['localIpReqs']) == 0
        assert int(stats['pushDataReqs']) == 0

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        assert stats['pushedFiles'] == 0

    def testMissingReturnLastRow(self):
        """
        Currently, P3 sometimes will not include the lastRow field
        when returnLastRow is set.
        """

        testDatDir = os.path.join(self.datRoot, 'test10')
        assert not os.path.isdir(testDatDir)

        os.makedirs(testDatDir)

        # Use date/times close to today so we trigger the 5-day check on
        # the server.
        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        r = urllib2.urlopen("http://localhost:5000/setLogDate/%d/%d/%d"
                            "/%d/%d/%d" % (targetDt.year, targetDt.month,
                                           targetDt.day, targetDt.hour,
                                           targetDt.minute, targetDt.second))
        r.read()

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test10'),
                 '-n200',
                 "-i%sgdu/<TICKET>/9.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/9.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/9.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/10.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(100.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/analyzerIds')

        for a in json.loads(r.read()):
            assert a != ''

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1

        # Target .dat file has 16207 rows. We push in chunks of 200.
        assert int(stats['pushDataReqs']) == 82

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        assert stats['pushedFiles'] == 1

    def testFileContents(self):
        """
        Verify that the pushed contents match the actual on-disk content.
        """

        testDatDir = os.path.join(self.datRoot, 'test11')
        assert not os.path.isdir(testDatDir)

        # Use date/times close to today so we trigger the 5-day check on
        # the server.
        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test11'),
                 '-n200',
                 "-i%sgdu/<TICKET>/11.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/11.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/11.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/11.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(100.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1
        # Target .dat file has 16207 rows. We push in chunks of 200.
        assert int(stats['pushDataReqs']) == 82

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        r = urllib2.urlopen("http://localhost:5000/getLines/%s" % target)
        serverLines = json.loads(r.read())

        # It's possible we pushed some lines multiple times depending if the
        # push was interrupted or not.
        nextRowIdx = 1
        uniqServerRows = []

        for line in serverLines:
            if int(line['row']) == nextRowIdx:
                uniqServerRows.append(line)
            nextRowIdx += 1

        localLines = self._logLinesToDict(os.path.join(targetDir, target))

        assert serverLines == localLines

    def testHandleEmptyDatFile(self):
        """
        Make sure we delete any empty dat files that we encounter since they
        can cause newer files to never be seen.
        """

        testDatDir = os.path.join(self.datRoot, 'test12')
        assert not os.path.isdir(testDatDir)

        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=2.0)
        emptyTarget = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                        "_Minimal.dat")
        emptyTargetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                      targetDt.strftime("%m"),
                                      targetDt.strftime("%d"))
        os.makedirs(emptyTargetDir)

        with open(os.path.join(emptyTargetDir, emptyTarget), 'wb') as fp:
            # Create empty file
            pass

        assert os.stat(os.path.join(emptyTargetDir, emptyTarget))[6] == 0

        targetDt = datetime.datetime.utcnow() - datetime.timedelta(days=1.0)
        target = targetDt.strftime("TEST23-%Y%m%d-%H%M%SZ-DataLog_User"
                                   "_Minimal.dat")
        targetDir = os.path.join(testDatDir, targetDt.strftime("%Y"),
                                 targetDt.strftime("%m"),
                                 targetDt.strftime("%d"))
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(self.datRoot, 'file1.dat'),
                        os.path.join(targetDir, target))

        assert self.driverEmulator is None

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        time.sleep(1.0)
        assert self.driverEmulator.is_running()

        datEcho = psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 '-ddat',
                 "-l%s/*.dat" % os.path.join(self.datRoot, 'test12'),
                 '-n200',
                 "-i%sgdu/<TICKET>/12.0/AnzMeta/" % self.localUrl,
                 "-p%sgdu/<TICKET>/12.0/AnzLog/" % self.localUrl,
                 "-k%ssec/dummy/12.0/Admin/" % self.localUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/12.0/AnzLogMeta/" % (
                        self.localUrl),
                 '-yid',
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR,
                 '-sAPITEST']).pid)

        time.sleep(120.0)

        assert datEcho.is_running()

        datEcho.kill()

        r = urllib2.urlopen('http://localhost:5000/stats')
        r.read()

        assert os.path.isfile('stats.json')

        stats = None
        with open('stats.json', 'rb') as f:
            stats = json.load(f)

        assert int(stats['ticketReqs']) == 1
        assert int(stats['localIpReqs']) > 1
        assert int(stats['pushDataReqs']) == 82

        assert stats['lastRangeReq'] is not None
        begin, end = stats['lastRangeReq']
        beginDt = datetime.datetime.utcfromtimestamp(begin)
        endDt = datetime.datetime.utcfromtimestamp(end)
        assert (endDt - beginDt).days == 5.0

        assert stats['pushedFiles'] == 1

        assert not os.path.exists(os.path.join(emptyTargetDir, emptyTarget))
        assert os.path.exists(os.path.join(emptyTargetDir,
                                           "%s.empty" % emptyTarget))
