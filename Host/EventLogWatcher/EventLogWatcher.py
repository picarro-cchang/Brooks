#!/usr/bin/python
#
"""
File Name: EventLogWatcher.py

Description:
    This application watches the event logs looking for errors that cause an app to crash.
    It keeps some basic information and statistics about the errors as well.

Notes:
    Relies on a specific format for event log files (which isn't likely to change much anyway).
    The filenames previously searched are logged in a cache so they aren't searched again.

    EventLogWatcher.json contains settings for the root folder to monitor, and the filenames
    for caching previously searched files, the error whitelist and logged results files.

    Whitelist file format:
        1. First line must be the version number for event log files (currently v1)
        2. Next line should be blank
        3. Next are the stack trace dump text groupings. Include the enclosing '~~ VERBOSE ~~ (nn)'
           and '~~ END VERBOSE ~~' text (just copy and paste them from an event log).
        4. Separate each stack trace text grouping by at least one blank line.

    Typical usage commands:

    1. Build the whitelist from a text file
         EventLogWatcher --loadWhitelist="<filename>"

    2. Run EventLogWatcher
       a. Single pass through the files and quit
            EventLogWatcher --once

       b. Monitor the event logs for the next 45 minutes (duration is in hours).
            EventLogWatcher --duration=0.75

    3. Reset the log files (event log and filename cache), then take a single pass through
       the event logs and quit
          EventLogWatcher --once --resetLogs

    4. Output a summary of event log errors, in csv format with two columns, and then quit:
       1) a hash for the normalized stack trace text (line numbers excluded)
       2) total incident count

       You can redirect this output to a file (the second example)

          EventLogWatcher --summary
          EventLogWatcher --summary > log.txt

    5. Output a detailed summary of event log errors, in csv format with three columns, and then quit:
       1) hash for the normalized stack trace text (line numbers excluded)
       2) hash for the raw stack trace text (line numbers included)
       3) incident count for the raw stack traces

          EventLogWatcher --summaryDetails

    6. Dump details about the whitelist, event log errors, or both, and then quit:

          EventLogWatcher --dumpWhitelist
          EventLogWatcher --dumpLog
          EventLogWatcher --dumpAll

    7. Combined output of summary and details

          EventLogWatcher --dumpAll --summary --summaryDetails


    Important: If you change the whitelist (--loadWhitelist option) then you must reset the event log and filename cache
               so they are cleared and regenerated. Otherwise the error counts and entries in the log will
               probably be incorrect.


File History:
    14-01-21=7 tw    Initial version
"""

from __future__ import with_statement

import sys
import re
#import traceback
import fnmatch
import os
import time
import datetime
import pickle
import hashlib

#from glob import glob
from optparse import OptionParser
#from ConfigParser import ConfigParser
#pylint: disable=F0401
try:
    import simplejson as json
except ImportError:
    import json
#pylint: enable=F0401

if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

_DEFAULT_CONFIG_NAME = "EventLogWatcher.json"
_DEFAULT_EVENT_LOG_PATH = "C:/Picarro/G2000/Log/Archive/EventLogs"
_DEFAULT_EVENT_LOG_SEARCH_FILENAME = "EventLog_*.txt"

_DEFAULT_EVENT_LOG_CACHE_FILENAME = ".EventLogWatcherCache"
_DEFAULT_EVENT_LOG_RESULTS_FILENAME = ".EventLogWatcherResults"
_DEFAULT_EVENT_LOG_WHITELIST_FILENAME = ".EventLogWatcherWhitelist"

WAIT_BETWEEN_FIND_FILES = 10.0    # number of seconds to wait after an iteration of watching all of the files in the log dir


g_logMsgLevel = 0   # should be 0 for check-in

SECONDS_PER_HOUR = 3600.0

ORIGIN = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)
UNIXORIGIN = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)


def datetimeToTimestamp(t):
    td = t - ORIGIN
    return float((td.days * 86400 + td.seconds) * 1000 + td.microseconds // 1000)

def timestampToUtcDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to UTC datetime"""
    return ORIGIN + datetime.timedelta(microseconds=1000 * timestamp)

def formatTime(dateTime):
    # Event logs only have second resolution
    #ms = dateTime.microsecond // 1000
    #return dateTime.strftime("%Y-%m-%d %H:%M:%S") + (".%03d" % ms)
    return dateTime.strftime("%Y-%m-%d %H:%M:%S")

def timestampToString(timestamp):
    """Converts 64-bit timestamp value to a string in UTC time"""
    ts = timestampToUtcDatetime(timestamp)
    return formatTime(ts)

def LogErrmsg(str):
    print >> sys.stderr, str


def LogMsg(level, str):
    if level <= g_logMsgLevel:
        print str


def genLatestFiles(baseDir, pattern):
    """
    A generator that returns files matching 'pattern' in the root
    'baseDir' in chronological order (oldest to newest).
    """
    LogMsg(5, "genLatestFiles: baseDir='%s'  pattern='%s'" % (baseDir, pattern))
    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=False)
        fileNames.sort(reverse=False)
        for name in fileNames:
            if fnmatch.fnmatch(name, pattern):
                yield os.path.join(dirPath, name)
    return


class InvalidFileFormatError(Exception):
    """Exception for when the search file is not the correct format"""
    pass


"""
def printBufWait(buf):
    linesInGroup = 50
    ccLines = 0


    for ii in range(len(buf)):
        print "byte[%2d] = 0x%.2x  '%c'" % (ii, buf[ii], chr(buf[ii]))
        ccLines += 1

        if ccLines >= linesInGroup:
            ccLines = 0
            time.sleep(2)

    print ""


def printBuf(buf):
    #print ""
    for ii in range(len(buf)):
        print "byte[%2d] = 0x%.2x  '%c'" % (ii, buf[ii], chr(buf[ii]))
    print ""


def ModbusCRC16(buf):
    # Brute force method
    crc = 0xffff

    for pos in range(len(buf)):
        crc ^= buf[pos]

        for ii in range(8, 0, -1):
            lsb = crc & 0x0001
            crc = crc >> 1

            if lsb != 0:
                crc ^= 0xA001

    # high and low bytes are swapped
    # so put them in the proper order
    crc = ((crc & 0xff00) >> 8) | ((crc & 0x00ff) << 8)
    return crc


def ModbusCRC16Lines(lines):
    # lines argument is an array of text lines
    #
    # first fill a byte buffer with text chars from lines
    buf = []

    for line in lines:
        # TODO: Remove 'line n,' from the string so if lines are
        #       shifted due to code changes they hash to the same
        #       value so the whitelist doesn't change.
        for ix in range(len(line)):
            buf.append(ord(line[ix:ix+1]))

    #print "buf=", buf
    #printBufWait(buf)

    # now compute a CRC for the hash
    crc = ModbusCRC16(buf)
    return crc
"""

# regexp to hunt for ", line nn, " in stack trace text
LINENUM_RX = re.compile(r'(?P<linenum>, line \d+, )')



def getNormalizedText(line):
    # we may also need to normalize paths here
    return LINENUM_RX.sub("", line)


def computeMD5hash(string):
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


def hashLines(lines, includeRawHash=False):
    """
    lines argument is list of text lines

    returns a MD5 hash of the raw and normalized strings (without the "line nn," in stack traces)
    """
    # Construct single raw and normalized string from the lines list
    rawText = ""
    normText = ""
    for line in lines:
        rawText = rawText + line

        normLine = getNormalizedText(line)
        normText = normText + LINENUM_RX.sub("", normLine)

    """
    print "*******"
    print "rawText:'%s'" % rawText
    print ""
    print "normText:'%s'" % normText
    print "*******"
    """

    # compute hash values, returning the normalized string hash,
    # and also the raw hash if the caller wants it
    hashNorm = computeMD5hash(normText)

    if not includeRawHash:
        return hashNorm

    hashRaw = computeMD5hash(rawText)
    return hashNorm, hashRaw


class ErrorIncident(object):
    def __init__(self, hash, stackTraceLines, errorLine, timestamp):
        """
        Arguments:
        hash                typically should be a raw hash of stackTraceLines,
                            not the hash for a normalized string
        stackTraceLines     a list of strings (the stack trace)
        errorLine           the previous line (can be None for a whitelist entry)
        timestamp           epoch time (can be None for a whitelist entry)
        """
        assert hash is not None
        assert stackTraceLines is not None

        self.hash = hash
        self.stackTraceLines = stackTraceLines
        self.errorLine = errorLine
        self.timestampList = []

        if timestamp is not None:
            self.timestampList.append(timestamp)

        self.count = int(1)

    def getHash(self):
        return self.hash

    def getTimestamps(self):
        return self.timestampList

    def incCount(self):
        self.count += 1

    def addOccurrence(self, timestamp):
        self.count += 1
        self.timestampList.append(timestamp)

    def dump(self):
        print "    hash=", self.hash
        print "    count=", self.count
        print "    timestamps=", self.timestampList

        for ix, ts in enumerate(self.timestampList):
            tsStr = timestampToString(ts)
            print "    timestamp[%d]= %s" % (ix, tsStr)

        if self.errorLine is not None:
            print "    prevLine=", self.errorLine

        for line in self.stackTraceLines:
            #print "    ", line
            print "  >>  ", line


class ErrorItem(object):
    def __init__(self, hash):
        """
        Arguments:
        hash    typically should be normalized hash (without the "line nn," in the stack trace strings)
        """
        self.hash = hash

        # total number of incidents of this error
        self.ccIncidents = 0

        # list of ErrorIncident classes
        self.errorIncidents = []

    def getHash(self):
        return self.hash

    def getCount(self):
        return self.ccIncidents

    def getNextErrorIncident(self):
        for ei in self.errorIncidents:
            yield ei
        return

    def findErrorIncident(self, hash):
        for ei in self.errorIncidents:
            if hash == ei.getHash():
                return ei
        return None

    def addErrorIncident(self, errorIncident):
        self.errorIncidents.append(errorIncident)
        self.incCount()

    def incCount(self):
        self.ccIncidents += 1

    def isIncidentInItem(self, hash):
        pass

    def dump(self):
        print "  ******"
        print "  hash=", self.hash
        print "  total incident count=", self.ccIncidents

        for ei in self.getNextErrorIncident():
            ei.dump()


class ErrorCollection(object):
    """
    Used for both logging the results and for the whitelist
    """
    # for extracting the timestamp for conversion to epoch time
    DATLOG_RX = re.compile(r'(?P<year>\d{4})-(?P<month>\d{2})-'
                           r'(?P<day>\d{2}) (?P<hour>\d{2}):'
                           r'(?P<minute>\d{2}):(?P<second>\d{2})*')

    def __init__(self, filename, isWhitelist):
        self.filename = filename
        self.errorList = []     # this is an array of errorItem
        self.isWhitelist = isWhitelist

        # load up any previously saved error items
        if os.path.isfile(self.filename):
            f = open(self.filename, 'rb')
            done = False

            while done is False:
                try:
                    errorItem = pickle.load(f)
                    self.errorList.append(errorItem)

                except EOFError:
                    done = True

            f.close()

        # else make sure the output dir exists so we can save to it
        else:
            path = os.path.split(self.filename)[0]

            if not os.path.isdir(path):
                os.makedirs(path)

    def isInCollection(self, stackTraceLines):
        hashNorm = hashLines(stackTraceLines, False)
        #print "hashNorm='%s'" % hashNorm

        retVal = False
        if self._isHashInCollection(hashNorm) is not None:
            retVal = True

        return retVal

    def save(self, stackTraceLines, errorLine):
        #print "ErrorCollection::save():  saving results"
        #print "  errorLine='%s'" % errorLine

        # we don't bother with the timestamp for a whitelist
        if self.isWhitelist is True:
            timestamp = None

        else:
            # extract the timestamp from the error line if it is not None or an empty string
            if errorLine is not None and errorLine != "":
                # tokens are tab-separated, the timestamp is the second token
                tsText = errorLine.split("\t")[1]

                # convert to epoch time
                #print "ErrorCollection::save()  tsText=", tsText

                group = self.DATLOG_RX.search(tsText).groupdict()
                assert 'year' in group
                assert 'month' in group
                assert 'day' in group
                assert 'hour' in group
                assert 'minute' in group
                assert 'second' in group

                group = dict((k, int(group[k])) for k in group)

                dt = datetime.datetime(group['year'], group['month'],
                                       group['day'], group['hour'],
                                       group['minute'], group['second'])

                timestamp = datetimeToTimestamp(dt)

            else:
                assert self.isWhitelist is True

                timestamp = 0.0

        # compute a hash on the stack trace (faster than
        # comparing strings)
        hashNorm, hashRaw = hashLines(stackTraceLines, True)

        #print "hashNorm='%s'" % hashNorm
        #print "hashRaw='%s'" % hashRaw

        # determine if item is already in the dictionary
        # use the normalized hash
        errorItem = self._isHashInCollection(hashNorm)

        if errorItem is None:
            # not in the dictionary, create a new error item and save it
            errorItem = ErrorItem(hashNorm)

            # we don't care about saving off the preceding error line for a whitelist
            if self.isWhitelist:
                prevLine = None
            else:
                prevLine = errorLine

            # create a new incident with this error
            errorIncident = ErrorIncident(hashRaw, stackTraceLines, prevLine, timestamp)

            # add this incident to the error item, this also bumps the count
            errorItem.addErrorIncident(errorIncident)

            # add this new error item to our list
            self.errorList.append(errorItem)

        else:
            # It's in the error list already. If not a whitelist,
            # update the item and count. If it is a whitelist,
            # we don't need to do anything since we don't care about
            # the count.
            if not self.isWhitelist:
                # check if this unique incident
                errorIncident = errorItem.findErrorIncident(hashRaw)

                if errorIncident is None:
                    errorIncident = ErrorIncident(hashRaw, stackTraceLines, errorLine, timestamp)

                    # add this unique error incident to the list, this also bumps the total count
                    errorItem.addErrorIncident(errorIncident)

                else:
                    # incident is already present, so add timestamp for this occurrence to it
                    # and bump the total incident count
                    errorIncident.addOccurrence(timestamp)
                    errorItem.incCount()

        # update the collection file on disk
        f = open(self.filename, 'wb')

        for errorItem in self.errorList:
            pickle.dump(errorItem, f)

        f.close()

    def _isHashInCollection(self, hashNorm):
        #print "ErrorCollection::_isInCollection()"
        retVal = None

        # look through the dictionary
        for errorItem in self.errorList:
            if hashNorm == errorItem.getHash():
                retVal = errorItem
                break

        #print "  returning retVal=", retVal
        return retVal

    def dump(self, msg):
        print msg
        print "filename=", self.filename
        print "isWhitelist=", self.isWhitelist

        if len(self.errorList) == 0:
            if os.path.isfile(self.filename):
                print "Collection is empty."
            else:
                LogErrmsg("Collection file '%s' not found!" % self.filename)

        for ei in self.errorList:
            ei.dump()

    def summary(self):
        print "hash, count"
        for errorItem in self.errorList:
            hashNorm = errorItem.getHash()
            ccErrors = errorItem.getCount()
            print "%s, %d" % (hashNorm, ccErrors)

    def summaryDetails(self):
        print "hash, hashRaw, timestamp"
        for errorItem in self.errorList:
            hashNorm = errorItem.getHash()

            for ei in errorItem.getNextErrorIncident():
                hashRaw = ei.getHash()
                timestamps = ei.getTimestamps()

                for ts in timestamps:
                    print "%s, %s, %f" % (hashNorm, hashRaw, ts)


class FileSearcher(object):
    """
    Search the log file for error text
    """
    ERROR_HEADER_SEARCH = r'~~ VERBOSE ~~ '
    ERROR_FOOTER_SEARCH = r'~~ END VERBOSE ~~'

    # line count is the number within the parentheses
    LINECOUNT_RX = re.compile(r'((\d+))')

    def __init__(self, filename):
        # open the file
        f = open(filename)

        # first line must be 'v1'
        line = f.readline().strip("\n")

        if line != "v1":
            f.close()
            raise InvalidFileFormatError("Invalid file format for '%s'" % filename)

        # save off the file
        self.f = f
        self.filename = filename

    def findNextError(self):
        # iterate through the file looking for a matching header
        prevLine = ""

        try:
            while True:
                line = self.f.readline()

                #print "line=", line

                LogMsg(5, "line='%s'" % line)

                if not line:
                    # EOF reached
                    break

                elif line.startswith(self.ERROR_HEADER_SEARCH):
                    LogMsg(2, "Found error wrapper start")

                    # value within the parentheses in the wrapper header tells us how many of the following lines are the stack trace
                    result = self.LINECOUNT_RX.search(line)
                    assert result is not None

                    lineCount = int(result.group())
                    #print "lineCount=", lineCount

                    # get the stack trace error lines, strip off line endings
                    stackTraceLines = []
                    for i in range(lineCount):
                        line = self.f.readline().strip("\n")
                        stackTraceLines.append(line)

                    line = self.f.readline()

                    # sanity check -- this line should match the ending wrapper text
                    if line.startswith(self.ERROR_FOOTER_SEARCH):
                        LogMsg(2, "Validated error wrapper end")
                        pass
                    else:
                        raise InvalidFileFormatError("Missing ending error wrapper text in '%s'" % self.filename)

                    # prevLine contains the error message and timestamp information that was output just before the stack trace
                    yield stackTraceLines, prevLine

                # save off this line as the previous line
                # in the event we find the error wrapper header we'll need it as it contains the timestamp
                prevLine = line

                # Useful delay between lines for debugging
                #if g_logMsgLevel >= 1:
                #    time.sleep(0.5)

        except GeneratorExit:
            # normally this should not happen
            LogMsg(0, "Caught GeneratorExit exception")
            pass

        #print "FileSearcher::findNextError - done"
        self.f.close()

        # Useful delay after parsing file complete for debugging
        if g_logMsgLevel >= 1:
            time.sleep(3)
        return


class EventLogFilenameCache(object):
    def __init__(self, cacheFilename):
        self.filename = cacheFilename

        self.cacheDict = { "SearchedFiles": [],
                           "SearchedFilesInvalid": []
                         }

        # load the file if it exists
        if os.path.isfile(self.filename):
            f = open(self.filename, 'rb')
            self.cacheDict = pickle.load(f)
            f.close()

        # else make sure the dir exists so the file can be written on saves
        else:
            path = os.path.split(self.filename)[0]
            if not os.path.isdir(path):
                os.makedirs(path)


            #self.config.read(cacheFilename)

        """
        # create sections for previously searched filenames (valid and invalid)
        # and initialize the file counter to 0
        if not self.config.has_section("SearchedFiles"):
            self.config.add_section("SearchedFiles")
            self.config.set("SearchedFiles", "count", "0")

        if not self.config.has_section("SearchedFilesInvalid"):
            self.config.add_section("SearchedFilesInvalid")
            self.config.set("SearchedFilesInvalid", "count", "0")
        """

    def isInCache(self, filename):
        # always search/store using the full path
        filename = os.path.realpath(filename)

        # we need to search both valid and invalid sections
        fFound = False

        if filename in self.cacheDict["SearchedFiles"]:
            fFound = True
        elif filename in self.cacheDict["SearchedFilesInvalid"]:
            fFound = True

        #print "isInCache: fFound=", fFound
        return fFound

    def addFilenameToCache(self, filename, fIsValid=True):
        filename = os.path.realpath(filename)

        # add the file to the cache if it is not already there
        if not self.isInCache(filename):
            if fIsValid:
                self.cacheDict["SearchedFiles"].append(filename)
            else:
                self.cacheDict["SearchedFilesInvalid"].append(filename)

        #print "cacheDict=", self.cacheDict

        # write out the cache
        LogMsg(2, "writing out filename cache to '%s'" % self.filename)
        f = open(self.filename, 'wb')
        pickle.dump(self.cacheDict, f)
        f.close()


class EventLogWatcher(object):
    """
    # This won't compile (the *s seem to be a problem)
    DATLOG_RX = re.compile(r'*_(?P<year>\d{4})_(?P<month>\d{2})'
                           r'_(?P<day>\d{2})_(?P<hour>\d{2})'
                           r'(?P<minute>\d{2})_(?P<second>\d{2})Z.*')
    """

    DATLOG_RX = re.compile(r'_(?P<year>[0-9][0-9][0-9][0-9])_'
                           r'(?P<month>[0-1][0-9])_'
                           r'(?P<day>[0-3][0-9])_'
                           r'(?P<hour>[0-2][0-9])_'
                           r'(?P<minute>[0-6][0-9])_'
                           r'(?P<second>[0-6][0-9])Z'
                           )

    def __init__(self, options):
        #print "EventLogWatcher::__init__()"

        #self.historyRangeDays = kwargs['historyRangeDays']

        # set self.listenPath from the ini file

        # initial settings
        self.configFile = os.path.join(os.path.dirname(AppPath), _DEFAULT_CONFIG_NAME)
        self.logPath = _DEFAULT_EVENT_LOG_PATH
        self.logCache = None
        self.logResults = None
        self.logResultsFilename = None
        self.logWhitelistFilename = None

        # <=0 means run test infinitely
        self.duration = float(0.0)

        # get config filename
        fConfigExists = True
        if options.configFile is not None:
            self.configFile = options.configFile

        if not os.path.isfile(self.configFile):
            LogErrmsg("JSON config file '%s' does not exist, using internal defaults." % self.configFile)
            fConfigExists = False
            #sys.exit(1)

        # load settings from config file if it exists
        CONFIGS = {}

        if fConfigExists:
            with open(self.configFile, 'r') as config:
                CONFIGS.update(json.load(config))

        if "LogFileDir" in CONFIGS:
            self.logPath = CONFIGS["LogFileDir"]

        if "LogCacheFilename" in CONFIGS:
            self.logCacheFilename = CONFIGS["LogCacheFilename"]

        if "LogResultsFilename" in CONFIGS:
            self.logResultsFilename = CONFIGS["LogResultsFilename"]

        if "LogResultsFilename" in CONFIGS:
            self.logWhitelistFilename = CONFIGS["LogWhitelistFilename"]

        #print "self.logPath=", self.logPath
        #print "self.logCacheFilename=", self.logCacheFilename
        #print "self.logResultsFilename", self.logResultsFilename
        #print "self.logWhitelistFilename", self.logWhitelistFilename

        # command line options override config file
        self.handleOptions(options)

    def handleOptions(self, options):
        if options.logPath is not None:
            self.logPath = options.logPath

        # Folder containing logs is where we'll drop the cache and results files
        logdir = self.logPath

        if not os.path.isdir(logdir):
            LogErrmsg("Event log folder '%s' does not exist!" % logdir)
            sys.exit(1)

        # append search string to match for event log filenames
        self.logSearchPath = os.path.normpath(os.path.join(self.logPath, _DEFAULT_EVENT_LOG_SEARCH_FILENAME))

        # construct cache and results filename if not in JSON file or options
        # default is to drop them in the folder that contains the logs
        if self.logCacheFilename is None:
            self.logCacheFilename = os.path.normpath(os.path.join(logdir, _DEFAULT_EVENT_LOG_CACHE_FILENAME))

        if self.logResultsFilename is None:
            self.logResultsFilename = os.path.normpath(os.path.join(logdir, _DEFAULT_EVENT_LOG_RESULTS_FILENAME))

        if self.logWhitelistFilename is None:
            self.logWhitelistFilename = os.path.normpath(os.path.join(logdir, _DEFAULT_EVENT_LOG_WHITELIST_FILENAME))

        LogMsg(5, "EventLogWatcher::handleOptions: logSearchPath = '%s" % self.logSearchPath)
        LogMsg(5, "EventLogWatcher::handleOptions: logCacheFilename = '%s" % self.logCacheFilename)
        LogMsg(5, "EventLogWatcher::handleOptions: logResultsFilename = '%s" % self.logResultsFilename)
        LogMsg(5, "EventLogWatcher::handleOptions: logWhitelistFilename = '%s" % self.logWhitelistFilename)

        # dump and summary commands take precedence
        # outputs whitelist and/or results and exits
        dumpLog = options.dumpLog
        dumpWhitelist = options.dumpWhitelist
        summary = options.summary
        summaryDetails = options.summaryDetails
        exitAfterDump = False

        if options.dumpAll is True:
            dumpLog = True
            dumpWhitelist = True

        # output summary first
        if summary is True:
            # output results as a summary
            exitAfterDump = True
            d = ErrorCollection(self.logResultsFilename, False)
            d.summary()

            # stick in a blank line if anything else is being dumped
            if dumpWhitelist is True or dumpLog is True or summaryDetails is True:
                print ""

        # output summary details next (with timestamps)
        if summaryDetails is True:
            # output results as a summary
            exitAfterDump = True
            d = ErrorCollection(self.logResultsFilename, False)
            d.summaryDetails()

            # stick in a blank line if anything else is being dumped
            if dumpWhitelist is True or dumpLog is True:
                print ""

        if dumpWhitelist is True:
            # dump the whitelist
            exitAfterDump = True
            d = ErrorCollection(self.logWhitelistFilename, True)
            d.dump("****** Whitelist ******")

        if dumpLog is True:
            # dump the results
            exitAfterDump = True
            d = ErrorCollection(self.logResultsFilename, False)

            if dumpLog is True:
                d.dump("****** Results ******")

        # exit now if we dumped any output
        if exitAfterDump is True:
            sys.exit(0)

        #print "options.resetLogs=", options.resetLogs

        if options.resetLogs is True:
            # blow away the cache, results buffer, and whitelist if reset flag is set
            LogMsg(1, "Resetting logs")
            if os.path.isfile(self.logCacheFilename):
                print "Deleting '%s'" % self.logCacheFilename
                os.remove(self.logCacheFilename)

            if os.path.isfile(self.logResultsFilename):
                print "Deleting '%s'" % self.logResultsFilename
                os.remove(self.logResultsFilename)

        # instantiate the results logger, not a whitelist
        self.resultsLog = ErrorCollection(self.logResultsFilename, False)

        if options.loadWhitelistFromFilename is not None:
            # blow away existing whitelist
            if os.path.isfile(self.logWhitelistFilename):
                print "deleting '%s'" % self.logWhitelistFilename
                os.remove(self.logWhitelistFilename)

            # load up the whitelist from the text file
            self.loadWhitelistFromFile(options.loadWhitelistFromFilename)

            # if we returned then the load was successful
            print "Successfully initialized whitelist from '%s', exiting." % options.loadWhitelistFromFilename
            sys.exit(0)

        else:
            # instantiate the existing whitelist
            self.whitelist = ErrorCollection(self.logWhitelistFilename, True)

        # TODO: if updating the whitelist do it here and exit
        #       - option to set the whitelist from a file (clears it first; remove items already in results log??)
        #       - option to update the whitelist from a file (appends to whitelist; remove ites  already in results log??)

        if options.duration is not None:
            self.duration = float(options.duration)

        self.doOnePass = options.doOnePass

        # instantiate the cache of previously searched files
        self.filenameCache = EventLogFilenameCache(self.logCacheFilename)


    def loadWhitelistFromFile(self, filename):
        if not os.path.isfile(filename):
            LogErrmsg("Whitelist text file '%s' does not exist, aborting!" % filename)
            sys.exit(1)

        # instantiate an error collection object for the whitelist
        self.whitelist = ErrorCollection(self.logWhitelistFilename, True)

        try:
            fs = FileSearcher(filename)

            for stackTraceLines, errorMsg in fs.findNextError():
                #print "****  loadWhitelistFromFile: returned from findNextError"
                LogMsg(1, "loadWhitelistFromFile(): number of stack trace lines=%d" % len(stackTraceLines))

                # add the stack trace to the whitelist, we don't care about the prev line (which
                # usually will be an empty string)
                self.whitelist.save(stackTraceLines, None)

        except InvalidFileFormatError:
                    # file is not the correct format, log it as if we've already searched it
                    LogErrmsg("Whitelist input text file not the correct format, aborting! filename='%s'" % filename)
                    sys.exit(1)

    def run(self):
        #print "EventLogWatcher::run()"
        #print "logSearchPath = '%s" % self.logSearchPath
        #print "logCacheFilename = '%s" % self.logCacheFilename
        #print "logResultsFilename = '%s" % self.logResultsFilename
        #print "logWhitelistFilename = '%s" % self.logWhitelistFilename

        # open the cache and results files, creating them if they don't yet exist
        # they are in the config file format, for easy parsing

        begin = 0.0
        endTime = 0.0

        if self.duration > 0.0:
            endTime = time.time() + self.duration * SECONDS_PER_HOUR

        while True:
            LogMsg(1, "Checking for files")

            # build event log file list
            end = time.time()

            # if a duration to monitor the logs was set, we are done
            # if now past the end time
            if self.duration > 0.0 and end > endTime:
                break

            filesInRange = self._getFilesInRange(begin, end)

            LogMsg(4, "len(filesInRange)=%d" % len(filesInRange))

            for logfile in filesInRange:
                # check if we've searched this file already
                # for now assume we haven't
                fSearched = self.filenameCache.isInCache(logfile)

                if not fSearched:
                    # file is in time range, search it for errors
                    LogMsg(4, "logfile= '%s'" % logfile)

                    try:
                        fs = FileSearcher(logfile)

                        for stackTraceLines, errorMsg in fs.findNextError():
                            #print "****  returned from findNextError"
                            LogMsg(1, "number of stack trace lines=%d" % len(stackTraceLines))

                            #for stl in stackTraceLines:
                            #    print "    ", stl

                            # compare vs. the whitelist, log it if it's not there
                            if self.whitelist.isInCollection(stackTraceLines) is False:
                                # add the stack trace and error message to the results log
                                self.resultsLog.save(stackTraceLines, errorMsg)

                        # add this filename to the search cache, has valid format
                        self.filenameCache.addFilenameToCache(logfile, True)

                    except InvalidFileFormatError:
                        # file is not the correct format, log it as if we've already searched it
                        LogMsg(1, "Log file is not the correct format, filename='%s'" % logfile)

                        # add this to the search cache, has an invalid format
                        self.filenameCache.addFilenameToCache(logfile, False)

                        # log this as an error??
                        pass

            # exit now if doing only a single pass
            if self.doOnePass is True:
                break

            # done with this iteration, do another round
            begin = end

            # since processed all of the files we found initially
            # wait a bit before looking for more
            time.sleep(WAIT_BETWEEN_FIND_FILES)

        # Done monitoring files, exit normally
        LogMsg(1, "Finished monitoring event logs, exiting.")

    def _getFilesInRange(self, begin, end):
        fileList = []

        LogMsg(5, "_getFilesInRange: logSearchPath = '%s'" % self.logSearchPath)
        files = genLatestFiles(*os.path.split(self.logSearchPath))

        for fullPath in files:
            LogMsg(4, "fullPath=%s" % fullPath)

            path, fname = os.path.split(fullPath)
            LogMsg(4, "Next latest file: %s, %s" % (path, fname))

            # extract the date and time information from the filename
            group = self.DATLOG_RX.search(fname).groupdict()
            LogMsg(4, "group= %s" % group)

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

            LogMsg(4, "fTime=%s" % fTime)

            datetimeBegin = datetime.datetime.utcfromtimestamp(begin)
            datetimeEnd = datetime.datetime.utcfromtimestamp(end)

            LogMsg(4, "datetimeBegin=%s" % datetimeBegin)
            LogMsg(4, "datetimeEnd=%s" % datetimeEnd)

            # see if it is within the current range
            if fTime >= datetimeBegin and fTime <= datetimeEnd:
                LogMsg(1, "file '%s' is within range" % fname)
                fileList.append(fullPath)

        return fileList


def main():
    usage = """
%prog [options]

Application to monitor event logs, looking for crashers.
"""
    global g_logMsgLevel

    parser = OptionParser(usage=usage)

    parser.add_option('-v', '--version', dest='getVersion',
                      default=None, help=('Return the version number for this application.'))

    parser.add_option('-c', '--config', dest='configFile',
                      default=None, help=('File containing run-time configuration '
                                          'data for this application.'))

    parser.add_option('-d', '--dumpAll', dest='dumpAll',
                      action='store_true', default=False,
                      help=('Dump the whitelist and log data in a human-readable format.'))

    parser.add_option('--dumpLog', dest='dumpLog',
                      action='store_true', default=False,
                      help=('Dump the results in a human-readable format.'))

    parser.add_option('--dumpWhitelist', dest='dumpWhitelist',
                      action='store_true', default=False,
                      help=('Dump the whitelist in a human-readable format.'))

    parser.add_option('--summary', dest='summary',
                      action='store_true', default=False,
                      help=('Output a summary of the overall results in CSV format.'))

    parser.add_option('--summaryDetails', dest='summaryDetails',
                      action='store_true', default=False,
                      help=('Output a details of the overall results in CSV format. '
                            'This includes timestamps and hashes for similar hits.'))

    parser.add_option('--duration', dest='duration', action='store', type='string',
                      default=None, help=('Duration to watch the event logs, in hours. Default is to '
                                          'monitor the logs infinitely.'))

    parser.add_option('--once', dest='doOnePass',
                      action='store_true', default=False,
                      help=('Do a single pass through the event logs and exit. Ignores the duration setting.'))

    parser.add_option('-r', '--resetLogs', dest='resetLogs',
                      action='store_true', default=False,
                      help=('Refresh the logs by clearing the cached file list and results buffer before '
                            'searching the event logs for errors.'))

    parser.add_option('--loadWhitelist', dest='loadWhitelistFromFilename',
                      default=None, help=('Load the whitelist from the error strings in the specified file. '
                        'Clears the existing whitelist first.'))

    parser.add_option('--logpath', dest='logPath', action='store',
                      default=None, help=('Specify the folder path '
                      'for the event logs (overrides the config file setting).'))

    parser.add_option('-l', '--loglevel', dest='loglevel', action='store', type='int',
                      default=g_logMsgLevel, help=('Use this option to specify logging level to '
                                                   'debug this application. 0=highest, 5=lowest (noisy)'))

    options, args = parser.parse_args()
    #print "options=", options

    g_logMsgLevel = options.loglevel

    watcher = EventLogWatcher(options)
    watcher.run()



if __name__ == '__main__':
    main()


