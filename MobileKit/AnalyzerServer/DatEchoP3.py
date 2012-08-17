'''
DatEchoP3 - Listen to a path of .dat (type) files on the local system,
and echo new rows to the P3 archive
'''
from __future__ import with_statement

import sys
import re
import traceback
import fnmatch
import os
import time
import urllib2
import urllib
import math
import pprint
import threading
import socket
import datetime
import cPickle
import optparse

#pylint: disable=F0401
try:
    import simplejson as json
except ImportError:
    import json
#pylint: enable=F0401

from Host.Common import CmdFIFO
from Host.Common import SharedTypes
from Host.Common import Win32


SECONDS_IN_DAY = 86400.0


def genLatestFiles(baseDir, pattern):
    """
    A generator that returns files matching 'pattern' in the root
    'baseDir' in reverse chronological order (newest to oldest).
    """

    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=True)
        fileNames.sort(reverse=True)
        for name in fileNames:
            if fnmatch.fnmatch(name, pattern):
                yield os.path.join(dirPath, name)


class DataEchoP3(object):
    DATLOG_RX = re.compile(r'.*-(?P<year>\d{4})(?P<month>\d{2})'
                           r'(?P<day>\d{2})-(?P<hour>\d{2})'
                           r'(?P<minute>\d{2})(?P<second>\d{2})Z-.*')

    RANGE_QRY = "%s?qry=byEpoch&anz=%s&startEtm=%s&stopEtm=%s&returnLastRow=1"

    # The number of blank lines returned before we check to see if the
    # current .dat file is still alive or not.
    DEAD_LINE_MAX = 10

    def __init__(self, **kwargs):
        self.listenPath = kwargs['listenPath']
        self.urls = {
            'ip': kwargs['ipUrl'],
            'push': kwargs['pushUrl'],
            'ticket': kwargs['ticketUrl'],
            'logMeta': kwargs['logMetaUrl']
            }

        self.timeout = kwargs['timeout']
        self.dataType = kwargs['dataType']
        self.identity = kwargs['identity']
        self.authenticationSys = kwargs['authenticationSys']
        self.lines = kwargs['lines']
        self.historyRangeDays = kwargs['historyRangeDays']
        self.driverPort = kwargs['driverPort']

        self.ticket = 'None'
        self.ipRegistered = False
        self.docs = []

    def _getTicket(self):
        """
        Request a new ticket from P3.
        """

        self.ticket = 'None'

        rprocs = ('["AnzMeta:data", "AnzLog:data", "AnzLogMeta:byEpoch"]')

        params = {'qry': 'issueTicket',
                  'sys': self.authenticationSys,
                  'identity': self.identity,
                  'rprocs': rprocs}

        try:
            resp = urllib2.urlopen(self.urls['ticket'],
                                   data=urllib.urlencode(params))
            data = json.loads(resp.read())

            self.ticket = data.get('ticket', 'None')
            print "New ticket: %s" % self.ticket

        except urllib2.HTTPError, ex:
            print '\nissueTicket failed \n%s\n' % ex

        except Exception, ex:
            print '\nissueTicket failed \n%s\n' % ex

    def run(self):
        """
        Main process to push data to P3.
        """

        if not self.ticket:
            self.ticket = 'Invalid'

        self.ipRegistered = self._registerLocalIp()

        while True:
            end = time.time()
            assert self.historyRangeDays > 0.0
            begin = end - (self.historyRangeDays * SECONDS_IN_DAY)
            filesToCheck = self._getFilesInRange(begin, end)

            nextFile, lastRow = self._findIncomplete(filesToCheck)

            while nextFile is not None:
                print "Pushing partial file (lastRow = %s) '%s'." % (lastRow,
                                                                     nextFile)
                path, fname = os.path.split(nextFile)
                self._processFile(path, fname, lastRow)
                # Update time limits again?
                filesToCheck = self._getFilesInRange(begin, end)
                nextFile, lastRow = self._findIncomplete(filesToCheck)

            print 'Done with partial files...'

            # Don't use the earliest file on the server since it could
            # still be "later" than the earliest time we are
            # interested in. If there was a file the server didn't
            # know about and it came before the earliest file reported
            # to us, we would miss it.
            earlyServerTime = datetime.datetime.utcfromtimestamp(begin)

            localPaths = {}

            for fullPath in genLatestFiles(*os.path.split(self.listenPath)):
                path, fname = os.path.split(fullPath)

                print "Next latest file: %s, %s" % (path, fname)

                group = self.DATLOG_RX.search(fname).groupdict()
                assert 'year' in group
                assert 'month' in group
                assert 'day' in group
                assert 'hour' in group
                assert 'minute' in group
                assert 'second' in group

                group = dict((k, int(group[k])) for k in group)

                fTime = datetime.datetime(group['year'], group['month'],
                                          group['day'], group['hour'],
                                          group['minute'], group['second'])

                if fTime < earlyServerTime:
                    print "File time (%s) < earliest server time (%s)" % (
                        fTime, earlyServerTime)
                    break

                localPaths[fname] = path

            # Compute the set of files we know about locally but that
            # the server does not.
            localFiles = set([k for k in localPaths])
            serverFiles = set([f[0] for f in filesToCheck])

            serverUnknowns = localFiles - serverFiles

            pprint.pprint(serverUnknowns)

            nextFile = None

            if len(serverUnknowns) == 1:
                print 'Found a single unknown file; could be live.'
                nextFile = serverUnknowns.pop()

            elif len(serverUnknowns) > 1:
                print("Found %d files locally that are not known to "
                      "the server." % len(serverUnknowns))
                # We must process the oldest file first. In
                # previous versions we used whatever the next file
                # was that set.pop() returned. The problem with
                # this is that once you hit the "listen" file you
                # don't get a chance to go through the missing
                # file list again until either DatEchoP3 restarts
                # or the listen file is completed and a new one
                # opens.
                nextFile = sorted(serverUnknowns)[0]

            else:
                print 'No unknown files.'

            if nextFile is not None:
                self._processFile(localPaths[nextFile], nextFile)

    def _processFile(self, path, fname, lastRow=None):
        """
        Parse the specified file and send its data to P3. If lastRow is set,
        .dat file playback will resume from that location.
        """

        headers = None

        assert len(self.docs) is 0

        self.docs = []

        ipPushWaitIdx = 0
        firstRow = True

        if lastRow is not None:
            rowIdx = lastRow
        else:
            rowIdx = 0

        for line in self._datFile(path, fname, lastRow):
            vals = line.split()

            ipPushWaitIdx += 1

            if firstRow:
                print 'Got headers'
                firstRow = False
                headers = vals
                continue

            assert headers is not None

            if len(vals) != len(headers):
                print "Malformed line: # vals = %s, expected = %s" % (
                    len(vals), len(headers))
                continue

            doc = {}

            for col, val in zip(headers, vals):
                try:
                    doc[col] = float(val)

                    # In Python > v2.5 float(x) will understand
                    # strings of the form returned by the underlying
                    # Windows CRT: -1.#IND, etc. This means that
                    # doc[col] will be set to an actual float NaN
                    # representation, but JS won't understand it. So
                    # we need to attempt to use the isnan() method if
                    # it exists. If it doesn't exist, that means we
                    # are running < v2.5 and the 'NaN' string is
                    # created by the original ValueError on float().
                    try:
                        #pylint: disable=E1101
                        if math.isnan(doc[col]):
                            doc[col] = 'NaN'
                        #pylint: enable=E1101

                    except Exception:
                        pass

                except ValueError:
                    # Treat these as NaNs. Further, JS is happy to
                    # convert "NaN" into the appropriate internal
                    # representation.
                    doc[col] = 'NaN'

            rowIdx += 1
            doc['row'] = rowIdx

            self.docs.append(doc)

            # Throttle how often we push data to P3
            if len(self.docs) == self.lines:
                print "# rows = %d, rowIdx = %d, pushing to P3." % (
                    len(self.docs), rowIdx)

                self.pushToP3(fname)

                self.docs = []

                if ipPushWaitIdx > 5000 or not self.ipRegistered:
                    # Re-register in case local IP has changed
                    # recently.
                    self.ipRegistered = self._registerLocalIp()
                    ipPushWaitIdx = 0

    def _registerLocalIp(self):
        """
        Identify ourself to P3 and register the Analyzer's local IP address.
        """

        analyzerId = self._getLocalAnalyzerId()
        assert analyzerId is not None

        if analyzerId == '':
            print "No analyzer Id available. Skipping local IP registration."
            return

        ipRegistered = False

        if self.urls['ip'] is not None:
            # Only want to push IPs if we are live on the Analyzer
            assert self.listenPath is not None

            datarow = {'ANALYZER': analyzerId}

            for addr in self._getIPAddresses():
                if addr != '0.0.0.0':
                    datarow['PRIVATE_IP'] = "%s:5000" % addr
                    break

            if 'PRIVATE_IP' not in datarow:
                print ('Unable to find an IP address for this analyzer. '
                       'Skipping IP address registration.')
                return

            postParams = {'data': json.dumps([datarow])}

            # Try to be robust in the face of possible connectivity issues.
            tryAgain = True
            ticketAttempts = 0

            while not ipRegistered and tryAgain:
                tryAgain = False

                try:
                    # Python 2.5 requires that the timeout be set this
                    # way. In Python 2.6 and higher we can use an
                    # argument to urllib2.urlopen().
                    socket.setdefaulttimeout(self.timeout)
                    url = self.urls['ip'].replace('<TICKET>', self.ticket)
                    urllib2.urlopen(url, data=urllib.urlencode(postParams))
                    ipRegistered = True

                except urllib2.HTTPError, ex:
                    msg = ex.read()

                    if 'invalid ticket' in msg:
                        print "Invalid/expired ticket (code = %s)" % ex.code
                        ticketAttempts += 1

                        if ticketAttempts < 10:
                            tryAgain = True

                        self._getTicket()
                    else:
                        # Otherwise swallow this exception and we just won't
                        # have the IP pushed.
                        print "HTTP exception (code = %s): \n%s\n" % (ex.code,
                                                                      msg)

                except Exception:
                    print "Unknown error:"
                    traceback.print_exc()

        return ipRegistered

    def _getFilesInRange(self, begin, end):
        """
        Get the files known to P3 in the range (begin, end). Returns a
        list of (filename, last known row) tuples.
        """

        analyzerId = self._getLocalAnalyzerId()
        assert analyzerId is not None

        url = self.RANGE_QRY % (self.urls['logMeta'].replace('<TICKET>',
                                                        self.ticket),
                                analyzerId, begin, end)

        recentFiles = None
        receivedFiles = False
        tryAgain = True
        ticketAttempts = 0

        while not receivedFiles and tryAgain:
            tryAgain = False

            try:
                resp = urllib2.urlopen(url)
                recentFiles = json.loads(resp.read())

                receivedFiles = True

            except urllib2.HTTPError, ex:
                msg = ex.read()

                if 'invalid ticket' in msg:
                    print "Invalid/expired ticket (errno = %s)" % ex.code
                    ticketAttempts += 1

                    if ticketAttempts < 10:
                        tryAgain = True

                    self._getTicket()

                elif ex.code == 404:
                    print "Unknown analyzer '%s' (errno = %s)" % (analyzerId,
                                                                  ex.code)

                else:
                    print "HTTP exception (errno = %s): \n%s\n" % (ex.code,
                                                                   msg)

            except Exception:
                # Eat this exception
                print 'Unknown error:'
                print traceback.format_exc()

        if recentFiles is None:
            print ('Unable to retrieve results for time range: '
                   "'%s' - '%s'" % (time.asctime(time.gmtime(begin)),
                                    time.asctime(time.gmtime(end))))
            return []

        recentFileTuples = []
        for doc in recentFiles:
            if 'lastRow' not in doc:
                # Assume no rows unfortunately.
                print "No 'lastRow' field in '%s'" % doc['LOGNAME']
                doc.update({'lastRow': '0'})

            assert 'lastRow' in doc
            recentFileTuples.append((doc['LOGNAME'], doc['lastRow']))

        return recentFileTuples

    def _findIncomplete(self, files):
        """
        Search for any incomplete files and return the next one or None if all
        reported files are caught up.
        """

        assert self.listenPath is not None

        datRoot, _ = os.path.split(self.listenPath)

        for fname, row in files:
            print "Checking '%s' for rows beyond %s..." % (fname, row)
            group = self.DATLOG_RX.search(fname).groupdict()
            assert 'year' in group
            assert 'month' in group
            assert 'day' in group

            group = dict((k, int(group[k])) for k in group)

            path = os.path.join(datRoot, "%d" % group['year'],
                                "%02d" % group['month'], "%02d" % group['day'],
                                fname)

            if not os.path.isfile(path):
                print "Missing local file: %s" % path
                continue

            rowCache = "%s.row" % path

            lastRow = 0

            if os.path.isfile(rowCache):
                print '...found row cache. Using it.'
                with open(rowCache, 'rb') as fp:
                    lastRow = cPickle.load(fp)

                # If the row cache was generated while the file was
                # incomplete, we need to recalculate it.
                if lastRow < int(row):
                    print '...rescanning file to generate cache.'
                    lastRow = self._createUpdateRowCache(path, rowCache)

            else:
                print "...no cache. Scanning file."
                lastRow = self._createUpdateRowCache(path, rowCache)

            if lastRow != int(row):
                print ("...detected incomplete file. Server row: %s, "
                       "local: %s" % (row, lastRow))
                return path, int(row)

        print 'No incomplete files.'
        return None, 0

    def _createUpdateRowCache(self, path, rowCache):
        """
        Create/update the specified row cache using the supplied .dat
        file. Returns the number of rows in the .dat file.
        """

        with open(path, 'rb') as fp:
            nRows = len(fp.readlines()) - 1

        assert nRows > 0

        with open(rowCache, 'wb') as fp:
            print "Creating cache '%s' (# rows = %s)" % (rowCache, nRows)
            cPickle.dump(nRows, fp)

        return nRows

    def _datFile(self, path, fname, lastRow=None):
        """
        Yields lines from the specified .dat file. Handles all issues
        pertaining to listening to an open file.
        """
        with open(os.path.join(path, fname), 'rb') as fp:
            print "\nOpening source stream: %s\n" % fname
            print "lastRow = %s" % lastRow

            deadLineCount = 0
            lineCount = 0
            line = ''

            while True:
                line += fp.readline()
                sys.stderr.write('.')

                if line == '':
                    # Push any data that we already have.
                    if self.docs:
                        print "Push %s rows to P3" % len(self.docs)
                        self.pushToP3(fname)
                        self.docs = []

                    deadLineCount += 1

                    if deadLineCount == 10:
                        print 'Checking for latest file...'
                        latest = genLatestFiles(*os.path.split(
                                self.listenPath)).next()

                        if fname != os.path.split(latest)[1]:
                            print "New file available: %s" % latest
                            return

                        deadLineCount = 0

                    time.sleep(0.1)
                    continue

                lineCount += 1

                # We always want to return the header even if we are
                # resuming playback.
                if (lineCount != 1 and lastRow is not None and
                    lineCount <= (lastRow + 1) and line.endswith("\n")):
                    line = ''
                    continue

                if line.endswith("\n"):
                    yield line
                    line = ''

    def pushToP3(self, fname):
        """
        Sends existing data to P3.
        """

        assert len(self.docs) is not 0

        postParams = {'data': json.dumps(
                [{'logname': fname,
                  'replace': 0,
                  'logtype': self.dataType,
                  'logdata': self.docs}])}

        waitForRetryCtr = 0
        waitForRetry = True

        while True:
            try:
                # NOTE: socket only required to set timeout parameter
                # for the urlopen() In Python26 and beyond we can use
                # the timeout parameter in the urlopen()
                socket.setdefaulttimeout(self.timeout)
                url = self.urls['push'].replace('<TICKET>', self.ticket)
                resp = urllib2.urlopen(url, data=urllib.urlencode(postParams))

                rtnData = resp.read()
                # An HTTP exception should cause a subsequent
                # retry. Should only be here on success.
                if rtnData != '"OK"':
                    pprint.pprint(rtnData)
                    assert False

                return

            except urllib2.HTTPError, ex:
                msg = ex.read()

                if 'invalid ticket' in msg:
                    print "Invalid/expired ticket (errno = %s)" % ex.code
                    waitForRetryCtr += 1

                    if waitForRetryCtr < 100:
                        waitForRetry = False

                    self._getTicket()

                else:
                    print "HTTP exception (errno = %s): \n%s\n" % (ex.code,
                                                                   msg)

            except Exception:
                # Eat this exception
                print 'Unknown error:'
                print traceback.format_exc()

            sys.stderr.write('-')

            if waitForRetry:
                time.sleep(self.timeout)

            waitForRetry = True

    def _getIPAddresses(self):
        """
        Generate a sequence of IP addresses using the Win32 API.
        """

        for adapter in Win32.Iphlpapi.getAdaptersInfo():
            adNode = adapter.ipAddressList
            while adNode:
                ipAddr = adNode.ipAddress

                if ipAddr:
                    yield ipAddr

                adNode = adNode.next

    def _getLocalAnalyzerId(self):
        """
        Retrieve the ID of the Analyzer as required for subsequent
        calls to P3.  If running as a listener we expect that the
        program is being run on an actual Analyzer (or sufficient
        spooing code is in place for testing).  Otherwise for the
        scenario where individual files are being push to P3 we can
        simply parse the ID individually from each file.
        """

        analyzerId = self._getAnalyzerIdFromDriver()
        print "Found analyzer Id = %s" % analyzerId

        return analyzerId

    def _getAnalyzerIdFromDriver(self):
        """
        Retrieve the ID directly from the Analyzer driver. It is an unchecked
        error to try and get the Id when there is no driver RPC available.
        """

        driver = CmdFIFO.CmdFIFOServerProxy(
            "http://localhost:%d" % self.driverPort, ClientName='DatEchoP3')
        vals = driver.fetchLogicEEPROM()[0]
        return "%s%s" % (vals['Analyzer'], vals['AnalyzerNum'])


def main():
    usage = """
%prog [options]

Runs an echo server that sends data to P3.
"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-d', '--data-type', dest='dataType', default='dat',
                      metavar='DATATYPE', help='Log file data type '
                      '(dat, etc.)')
    parser.add_option('-l', '--listen-path', dest='listenPath',
                      metavar='LISTENPATH', default='C:/UserData/'
                      'AnalyzerServer/*_Minimal.dat', help='Search path for '
                      'constant updates.')
    parser.add_option('-t', '--timeout', dest='timeout', metavar='TIMEOUT',
                      default=10, type='int', help='timeout value for '
                      'response from server.')
    parser.add_option('-n', '--nbr-lines', dest='lines', metavar='NBRLINES',
                      default=1000, type='int', help='Number of lines per '
                      'push to P3.')
    parser.add_option('-i', '--ip-req-url', dest='ipUrl', metavar='IPREQURL',
                      help='REST URL for local IP address registration. Use '
                      'the string <TICKET> as the place-holder for the '
                      'authentication ticket.')
    parser.add_option('-p', '--push-url', dest='pushUrl', metavar='PUSHURL',
                      help='REST URL for data push to server. Use the string '
                      '<TICKET> as the place-holder for the authentication '
                      'ticket.')
    parser.add_option('-k', '--ticket-url', dest='ticketUrl',
                      metavar='TICKETURL', help='REST URL for authentication '
                      'ticket.')
    parser.add_option('--log-metadata-url', dest='logMetaUrl',
                      metavar='LOGMETADATAURL', help='REST URL for analysis '
                      'log metadata. Use the string <TICKET> as the '
                      'place-holder for the authentication ticket.')
    parser.add_option('-y', '--identity', dest='identity', metavar='IDENTITY',
                      help='Authentication identity string.')
    parser.add_option('-s', '--sys', dest='authenticationSys', metavar='SYS',
                      help='System to authenticate the identity against.')
    parser.add_option('-c', '--cmdfifo-port', dest='cport',
                      metavar='CMDFIFOPORT',
                      default=SharedTypes.RPC_PORT_ECHO_P3_BASE, type='int',
                      help='Port for supervisor CmdFIFO ping.')
    parser.add_option('--history-range', dest='historyRangeDays',
                      metavar='DAYS', default=5.0, type='float',
                      help='The number of days to check for missing/'
                      'incomplete files on P3.')
    parser.add_option('--driver-port', dest='driverPort',
                      metavar='DRIVER_PORT', type='int',
                      default=SharedTypes.RPC_PORT_DRIVER, help='Driver RPC '
                      'port. Normally used for running tests with a driver '
                      'emulator.')

    options, _ = parser.parse_args()

    if (options.cport < SharedTypes.RPC_PORT_ECHO_P3_BASE or
        options.cport > SharedTypes.RPC_PORT_ECHO_P3_MAX):
        parser.error("CmdFIFO port (%s) outside valid range (%s, %s)" % (
                options.cport, SharedTypes.RPC_PORT_ECHO_P3_BASE,
                SharedTypes.RPC_PORT_ECHO_P3_MAX))

    if options.identity is None:
        parser.error('Identity required for authentication.')

    datEcho = DataEchoP3(**vars(options))

    appThread = threading.Thread(target=datEcho.run)
    appThread.setDaemon(True)
    appThread.start()

    rpcServer = CmdFIFO.CmdFIFOServer(('', options.cport),
                                      ServerName='DatEchoP3',
                                      ServerDescription='DatEchoP3',
                                      ServerVersion='1.0',
                                      threaded=True)
    try:
        while True:
            rpcServer.daemon.handleRequests(0.5)
            if not appThread.isAlive():
                break

        print "Supervised DatEchoP3 thread stopped"
        return 1

    except Exception:
        print "CmdFIFO stopped:"
        print traceback.format_exc()
        return 0

if __name__ == '__main__':
    sys.exit(main())
