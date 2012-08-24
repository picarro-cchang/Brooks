"""
Copyright 2012 Picarro Inc.

Provides long-term tests to exercise the echo/playback capabilities of
DatEchoP3.
"""

from __future__ import with_statement

import random
import time
import subprocess
import pprint
import pickle
import shutil
import threading
import datetime
import urllib2
import math
import os.path

import simplejson as json
import psutil
import pytest

from Host.Common import SharedTypes


class TestDatEchoP3Stress(object):

    def setup_method(self, m):
        self.logTypeToFile = {'dat': 'User_Minimal',
                              'GPS_Raw': 'GPS_Raw',
                              'WS_Raw': 'WS_Raw'}

        self.driverEmulator = psutil.Process(
            subprocess.Popen(['python.exe',
                              './Helpers/DriverEmulatorServer.py']).pid)
        self.restServer = psutil.Process(
            subprocess.Popen(['python.exe', 'RESTEmulator.py',
                              '--unreliable']).pid)
        time.sleep(1.0)


        self.datEcho = None
        self.datRoot = os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'data')
        self.testDatDir = os.path.join(self.datRoot, 'test1')

        if os.path.isdir(self.testDatDir):
            shutil.rmtree(self.testDatDir)

        os.makedirs(self.testDatDir)

        self.writtenFiles = []
        self.writeFiles = True
        self.lock = threading.Lock()

    def teardown_method(self, m):
        self.driverEmulator.kill()
        self.restServer.kill()

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

    # Test against the unreliable server and the P3 dev environment.
    @pytest.mark.parametrize(('restUrl', 'identity', 'authSys', 'logType'), [
            ('http://localhost:5000/test/rest/',
             'id',
             'APITEST',
             'dat'),
            ('https://dev.picarro.com/dev/rest/',
             'NfC4L47cqVXWnuslGFaOvUljMahHpOmx7JPLVkCkGA8=',
             'dev',
             'dat'),
            ('https://dev.picarro.com/dev/rest/',
             'NfC4L47cqVXWnuslGFaOvUljMahHpOmx7JPLVkCkGA8=',
             'dev',
             'WS_Raw'),
            ('https://dev.picarro.com/dev/rest/',
             'NfC4L47cqVXWnuslGFaOvUljMahHpOmx7JPLVkCkGA8=',
             'dev',
             'GPS_Raw')])
    def testUnreliableServer(self, restUrl, identity, authSys, logType):
        random.seed(None)

        assert self.driverEmulator.is_running()
        assert os.path.isdir(self.testDatDir)
        assert not self.datEcho

        self.datEcho = self._launchDatEcho(restUrl, identity, authSys, logType)
        assert self.datEcho
        assert self.datEcho.is_running()

        threading.Thread(target=self._runFileWriter, args=(logType,)).start()

        start = time.time()
        # Run for 60 minutes
        while (time.time() - start) < 3600.0:
            # Mean time for failure is 60.0s
            time.sleep(random.expovariate(1.0 / 60.0))

            print "[%s] Kill DatEchoP3" % time.asctime(time.gmtime())
            assert self.datEcho.is_running()
            self.datEcho.kill()
            while self.datEcho.is_running():
                time.sleep(0.001)

            # Mean time to reconnect is 5.0s
            time.sleep(random.expovariate(1.0 / 5.0))

            print "[%s] Launch DatEchoP3" % time.asctime(time.gmtime())
            self.datEcho = self._launchDatEcho(restUrl, identity, authSys,
                                               logType)
            while not self.datEcho.is_running():
                time.sleep(0.001)

        with self.lock:
            self.writeFiles = False

        # Give it 30 uninterrupted minutes (server still unreliable)
        # to write any/all remaining files to P3.
        time.sleep(1800.0)

        self.datEcho.kill()
        while self.datEcho.is_running():
            time.sleep(0.001)

        # Only compute this once since we use the same file every time.
        localLines = self._logLinesToDict(
            os.path.join(self.datRoot,
                         "file2_%s.dat" % self.logTypeToFile[logType]))

        if 'localhost' in restUrl:
            # Test against fake P3 server.
            r = urllib2.urlopen('http://localhost:5000/filesRowsStats')
            stats = json.loads(r.read())

            pprint.pprint(stats)

            for k in stats:
                assert int(k[1]) == len(localLines)

                r = urllib2.urlopen("http://localhost:5000/getLines/%s" % k[0])
                serverLines = json.loads(r.read())

                # It's possible we pushed some lines multiple times
                # depending if the push was interrupted or not.
                nextRowIdx = 1
                uniqServerRows = []

                for line in serverLines:
                    if int(line['row']) == nextRowIdx:
                        uniqServerRows.append(line)
                        nextRowIdx += 1

                assert uniqServerRows == localLines

            assert len(self.writtenFiles) == len(stats)

        else:
            from MobileKit.ViewServer import P3ApiService

            p3 = P3ApiService.P3ApiService()
            p3.csp_url = restUrl.replace('/rest/', '')
            p3.ticket_url = "%ssec/dummy/1.0/Admin/" % restUrl
            p3.identity = identity
            p3.psys = authSys
            p3.rprocs = '["AnzLog:byPos"]'

            qryParams = {'qry': 'byPos',
                         'startPos': 0,
                         'logtype': "%s" % logType}

            intFields = ['INST_STATUS', 'ValveMask', 'ALARM_STATUS', 'species',
                         'row']

            # Some fields are correctly cast to integers by P3. Our
            # local file parser treats all numbers as doubles. We need
            # to update some fields in the local file as ints so we
            # can do a correct comparison with the returned server
            # rows.
            for row in localLines:
                for field in intFields:
                    if field in row:
                        row.update({field: int(row[field])})

            serverAddedFields = ['ANALYZER', 'shash', 'FILENAME_nint', 'ltype']

            # Test against the real P3.
            for dat in self.writtenFiles:
                qryParams.update(alog=dat)
                ret = p3.get('gdu', '1.0', 'AnzLog', qryParams)
                print "ret['error'] = %s" % ret['error']
                serverRows = ret['return']
                for i, row in enumerate(serverRows):
                    # Added by the server and not in the local file rows.
                    for field in serverAddedFields:
                        if field in row:
                            del row[field]

                    # Convert server None to NaN
                    for k in row:
                        if row[k] is None:
                            row[k] = 'NaN'

                    if row != localLines[i]:
                        print 'Server:'
                        pprint.pprint(row)
                        print 'Local:'
                        pprint.pprint(localLines[i])
                    assert row == localLines[i]

    def _runFileWriter(self, logType):
        with self.lock:
            writeFiles = self.writeFiles

        while writeFiles:
            t = datetime.datetime.utcnow()
            target = t.strftime("TEST25-%Y%m%d-%H%M%SZ-DataLog_$TYPE.dat")
            target = target.replace('$TYPE', self.logTypeToFile[logType])
            targetDir = os.path.join(self.testDatDir, t.strftime("%Y"),
                                     t.strftime("%m"), t.strftime("%d"))

            if not os.path.isdir(targetDir):
                os.makedirs(targetDir)

            self.writtenFiles.append(target)

            # Write the file out at ~1 Hz. Use unbuffered so we can
            # simulate unreliable writes to the file.
            with open(os.path.join(targetDir, target), 'w', 0) as newDat:
                fname = "file2_%s.dat" % self.logTypeToFile[logType]
                with open(os.path.join(self.datRoot, fname), 'r') as orig:
                    while True:
                        nBytes = int(math.ceil(random.expovariate(1.0/1000.0)))
                        data = orig.read(nBytes)

                        newDat.write(data)

                        if len(data) != nBytes:
                            break

                        time.sleep(random.expovariate(1.0))

            with self.lock:
                writeFiles = self.writeFiles

    def _launchDatEcho(self, restUrl, identity, authSys, logType):
        return psutil.Process(
            subprocess.Popen(
                ['python.exe', '../AnalyzerServer/DatEchoP3.py',
                 "--data-type=%s" % logType,
                 "-l%s/*.dat" % self.testDatDir,
                 '-n200',
                 "-i%sgdu/<TICKET>/1.0/AnzMeta/" % restUrl,
                 "-p%sgdu/<TICKET>/1.0/AnzLog/" % restUrl,
                 "-k%ssec/dummy/1.0/Admin/" % restUrl,
                 "--log-metadata-url=%sgdu/<TICKET>/1.0/AnzLogMeta/" % (
                        restUrl),
                 "-y%s" % identity,
                 "-s%s" % authSys,
                 "--driver-port=%d" % SharedTypes.RPC_PORT_DRIVER_EMULATOR],
                env=os.environ.update(
                    {'COVERAGE_PROCESS_START': 'covDatEchoP3StressTests.ini'})
                ).pid)
