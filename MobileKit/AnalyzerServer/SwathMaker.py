#!/usr/bin/python
#
"""
File Name: SwathMaker.py
Purpose: Calculates the field of view associated with the data in a minimal
data log file which contains wind information. This version operates on the
entire data set and produces an output data set suitable for inserting into
the database

File History:
    01-Feb-2013  sze  Initial version.

Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
import fnmatch
from numpy import *
import os
import sys
from optparse import OptionParser
import time
import datetime
import traceback
from Host.Common.SwathProcessor import processGen

import urllib2
import urllib
import socket
try:
    import simplejson as json
except:
    import json

NaN = 1e1000 / 1e1000


def genLatestFiles(baseDir, pattern):
    # Generate files in baseDir and its subdirectories which match pattern
    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=True)
        fileNames.sort(reverse=True)
        for name in fileNames:
            if fnmatch.fnmatch(name, pattern):
                yield os.path.join(dirPath, name)


class SwathMaker(object):
    # Default parameter values
    startRow = 0
    maxWindow = 10
    stabClass = "*"
    minLeak = 1.0
    minAmpl = 0.05
    astd_a = 0.47
    astd_b = 0.25
    astd_c = 0.00
    sleep_seconds = 30
    timeout = 5

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if 'analyzerId' in kwargs:
            self.analyzerId = kwargs['analyzerId']
        else:
            self.analyzerId = "ZZZ"

        if 'appDir' in kwargs:
            self.appDir = kwargs['appDir']
        else:
            if hasattr(sys, "frozen"):  # we're running compiled with py2exe
                AppPath = sys.executable
            else:
                AppPath = sys.argv[0]
            self.AppDir = os.path.split(AppPath)[0]

        self.anzlog_url = None
        if 'anzlog_url' in kwargs:
            self.anzlog_url = kwargs['anzlog_url']

        self.logname = None
        if 'logname' in kwargs:
            self.logname = kwargs['logname']

        self.meta_url = None
        if 'meta_url' in kwargs:
            self.meta_url = kwargs['meta_url']

        self.ticket_url = None
        if 'ticket_url' in kwargs:
            self.ticket_url = kwargs['ticket_url']

        self.identity = None
        if 'identity' in kwargs:
            self.identity = kwargs['identity']

        self.psys = None
        if 'psys' in kwargs:
            self.psys = kwargs['psys']

        if 'usedb' in kwargs:
            self.usedb = kwargs['usedb']
        else:
            self.usedb = None

        self.ticket = "NONE"
        self.startTime = datetime.datetime.now()
        self.lastEtm = 0.0

        self.listen_path = None
        if 'listen_path' in kwargs:
            self.listen_path = kwargs['listen_path']
        self.userlogfiles = self.listen_path

        self.file_path = None
        if 'file_path' in kwargs:
            self.file_path = kwargs['file_path']

        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds'] is not None:
                self.sleep_seconds = float(kwargs['sleep_seconds'])

        if 'timeout' in kwargs:
            if kwargs['timeout'] is not None:
                self.timeout = int(kwargs['timeout'])

        if 'startRow' in kwargs:
            if kwargs['startRow'] is not None:
                self.startRow = int(kwargs['startRow'])

        if 'maxWindow' in kwargs:
            if kwargs['maxWindow'] is not None:
                self.maxWindow = int(kwargs['maxWindow'])

        if 'stabClass' in kwargs:
            if kwargs['stabClass'] is not None:
                self.stabClass = kwargs['stabClass']

        if 'minLeak' in kwargs:
            if kwargs['minLeak'] is not None:
                self.minLeak = float(kwargs['minLeak'])

        if 'minAmpl' in kwargs:
            if kwargs['minAmpl'] is not None:
                self.minAmpl = float(kwargs['minAmpl'])

        if 'astd_a' in kwargs:
            if kwargs['astd_a'] is not None:
                self.astd_a = float(kwargs['astd_a'])

        if 'astd_b' in kwargs:
            if kwargs['astd_b'] is not None:
                self.astd_b = float(kwargs['astd_b'])

        if 'astd_c' in kwargs:
            if kwargs['astd_c'] is not None:
                self.astd_c = float(kwargs['astd_c'])

        self.debug = None
        if 'debug' in kwargs:
            self.debug = kwargs['debug']

        self.logtype = "swath"
        self.last_name = None
        self.sockettimeout = 10
    #######################################################################
    # Generators for getting data from files or the database
    #######################################################################

    def sourceFromFile(self, fname):
        # Generate lines from a specified user log file. Raise StopIteration
        # at end of the file
        fp = file(fname, 'rb')
        while True:
            line = fp.readline()
            if line:
                yield line
            else:
                break

    def followLastUserFile(self, fname):
        # Generate lines from the live (last) user log file. If we reach the
        #  end of the file, wait for a new line to become available, and
        #  periodically check to see if we are still the latest file. Raise
        #  StopIteration if a new file has become the live file.
        fp = file(fname, 'rb')
        print "\r\nOpening source stream %s\r\n" % fname
        line = ""
        counter = 0
        while True:
            line += fp.readline()
            # Note that if the file ends with an incomplete line, fp.readline()
            #  will return a string with no terminating newline. We must NOT
            #  yield this incomplete line to avoid causing problems at the
            #  higher levels.
            if not line:
                counter += 1
                if counter == 10:
                    try:
                        if fname == os.path.join(self.file_path):
                            fp.close()
                            print "\r\nClosing source stream %s\r\n" \
                                % self.fname
                            return

                        lastName = genLatestFiles(
                            *os.path.split(self.userlogfiles)).next()
                        # Stop iteration if we are not the last file
                        if fname != lastName:
                            fp.close()
                            print "\r\nClosing source stream\r\n"
                            return
                    except:
                        pass
                    counter = 0
                time.sleep(0.1)
                if self.debug:
                    sys.stderr.write('-')
                continue
            if self.debug:
                sys.stderr.write('.')
            # Only yield complete lines, otherwise loop for more characters
            if line.endswith("\n"):
                yield line
                line = ""

    def followLastUserLogDb(self):
        aname = self.analyzerId
        if self.logname:
            lastlog = self.logname
        else:
            lastlog = self.getLastLog()

        if lastlog:
            lastPos = 0
            waitForRetryCtr = 0
            waitForRetry = True
            while True:
                # params = {"alog": lastlog, "startPos": lastPos, "limit": 20}
                # postparms = {'data': json.dumps(params)}
                # getAnalyzerDatLogUrl = self.url.replace(
                #   "getData", "getAnalyzerDatLog")
                try:
                    rtn_data = None

                    qry_with_ticket = '%s?qry=byPos&alog=%s&startPos=%s&limit=2000' \
                        % (self.anzlog_url.replace("<TICKET>", self.ticket), lastlog,
                            lastPos)
                    if self.debug == True:
                        print "qry_with_ticket", qry_with_ticket

                    socket.setdefaulttimeout(self.sockettimeout)
                    resp = urllib2.urlopen(qry_with_ticket)
                    # resp = urllib2.urlopen(getAnalyzerDatLogUrl,
                    #  data=urllib.urlencode(postparms))
                    rtn_data = resp.read()

                except urllib2.HTTPError, e:
                    err_str = e.read()
                    if "invalid ticket" in err_str:
                        if self.debug == True:
                            print "We Have an invalid or expired ticket"
                        self.getTicket()
                        waitForRetryCtr += 1
                        if waitForRetryCtr < 100:
                            waitForRetry = None

                    else:
                        if "Log not found" in err_str:
                            if self.logname == lastlog:
                                print "\r\nLog complete. Closing log stream\r\n"
                                return

                        # We didn't find a log, so wait 5 seconds, and then see if there is a new lastlog
                        time.sleep(5)
                        newlastlog = self.getLastLog()
                        if not lastlog == newlastlog:
                            print "\r\nClosing log stream\r\n"
                            return

                        if self.debug == True:
                            print 'EXCEPTION in SwathMaker - followLastUserLogDb().\n%s\n' % err_str
                        pass

                except Exception, e:
                    print '\nfollowLastUserLogDb failed \n%s\n' % e
                    time.sleep(1)
                    continue

                if (rtn_data):
                    rslt = json.loads(rtn_data)
                    # print "followLastUserLogDb rslt: ", rslt
                    dbdata = rslt
                    if len(dbdata) > 0:
                        for doc in dbdata:
                            if "row" in doc:
                                lastPos = int(doc["row"]) + 1

                            if self.debug == True:
                                print "doc: ", doc

                            yield doc
                    else:
                        # no dbdata, so wait 5 seconds, then check for new last log
                        time.sleep(5)
                        newlastlog = self.getLastLog()
                        if not lastlog == newlastlog:
                            print "\r\nClosing log stream\r\n"
                            return
                else:
                    if waitForRetry:
                        time.sleep(self.timeout)

                    waitForRetry = True
                time.sleep(.050)

    def getLastLog(self):
        # Get the name of the live (last) log file from the database
        aname = self.analyzerId
        lastlog = None
        rtn_data = None

        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            try:
                qry_with_ticket = '%s?qry=byEpoch&anz=%s&startEtm=%s&limit=1&reverse=true' % (
                    self.meta_url.replace("<TICKET>", self.ticket), self.analyzerId, self.lastEtm)
                if self.debug == True:
                    print "getLastLog() qry_with_ticket", qry_with_ticket

                socket.setdefaulttimeout(self.sockettimeout)
                resp = urllib2.urlopen(qry_with_ticket)
                rtn_data = resp.read()

            except urllib2.HTTPError, e:
                err_str = e.read()
                if "invalid ticket" in err_str:
                    if self.debug == True:
                        print "We Have an invalid or expired ticket"
                    self.getTicket()
                    waitForRetryCtr += 1
                    if waitForRetryCtr < 100:
                        waitForRetry = None

                else:
                    if self.debug == True:
                        print 'EXCEPTION in SwathMaker - getLastLog().\n%s\n' % err_str
                    pass

            except Exception, e:
                print '\ngetLastLog failed \n%s\n' % e

                time.sleep(2)
                continue

            if (rtn_data):
                rslt = json.loads(rtn_data)
                if self.debug == True:
                    print "rslt: ", rslt

                for robj in rslt:
                    if robj["LOGNAME"]:
                        lastlog = robj["LOGNAME"]
                        if self.debug == True:
                            print "lastlog found: ", lastlog
                        return lastlog

                print '\ngetLastLog failed \n%s\n' % "No LOGNAME found"
                time.sleep(2)

            if waitForRetry:
                time.sleep(self.timeout)

            waitForRetry = True

    #######################################################################
    # Perform REST call to push analysis data to the database
    #######################################################################

    def pushData(self, swathname, doc_data):
        err_rtn_str = 'ERROR: missing data:'
        rtn = "OK"
        if doc_data:
            # we want to replace (which removed old data for the log)
            # when we have a new log
            # but only for the very first push
            replace_log = "False"
            if not self.last_swathname == swathname:
                print "I should be doing a replace now"
                replace_log = "True"
                self.last_swathname = swathname
            params = [{"logname": swathname, "replace": replace_log, "logtype": self.logtype, "logdata": doc_data}]
            if self.debug == True:
                print "params: ", params
        else:
            return

        postparms = {'data': json.dumps(params)}

        # Normally we will wait for a timeout period before retrying the urlopen
        # However, after an expired ticket error, we want to immediately retry
        # BUT, we do not want to skip the timeout forever (even with an invalid ticket)
        # So we instantiate a retry counter, and only skip timeout when the
        # counter is < 100.  After that, we will continue to retry forever, but
        # WITH a timeout between retry events.
        waitForRetryCtr = 0
        waitForRetry = True

        while True:
            try:
                # NOTE: socket only required to set timeout parameter for the urlopen()
                # In Python26 and beyond we can use the timeout parameter in the urlopen()
                socket.setdefaulttimeout(self.sockettimeout)

                myDat = urllib.urlencode(postparms)
                push_with_ticket = self.anzlog_url.replace("<TICKET>", self.ticket)

                resp = urllib2.urlopen(push_with_ticket, data=myDat)
                rtn_data = resp.read()

                if self.debug == True:
                    print rtn_data

                if err_rtn_str in rtn_data:
                    rslt = json.loads(rtn_data)
                    expect_ctr = rslt['result'].replace(err_rtn_str, "").strip()
                    break
                else:
                    break

            except urllib2.HTTPError, e:
                err_str = e.read()
                if "invalid ticket" in err_str:
                    if self.debug == True:
                        print "We Have an invalid or expired ticket"
                    self.getTicket()
                    waitForRetryCtr += 1
                    if waitForRetryCtr < 100:
                        waitForRetry = None

                else:
                    if self.debug == True:
                        print 'Data EXCEPTION in pushData, send data to server.\n%s\n' % err_str
                    pass

            except Exception, e:
                print 'EXCEPTION in pushData\n%s\n' % e
                pass

            if waitForRetry:
                time.sleep(self.timeout)

            waitForRetry = True

        return

    #######################################################################
    # Turn data from analyzer into a stream of dictionaries
    #######################################################################

    def anzDatAsDictDb(self, source):
        # Generates data from a minimal archive in the database as a
        #  stream of dicts
        for line in source:
            try:
                entry = {}
                for h in line.keys():
                    # if h not in ["_id", "ANALYZER", "SERVER_HASH"]:
                    try:
                        entry[h] = float(line[h])
                    except:
                        entry[h] = NaN

                yield entry
            except:
                print traceback.format_exc()
                raise

    def anzDatAsDict(self, source):
        # Generates data from a minimal log file as a stream of dicts
        line = source.next()
        atoms = line.split()
        headings = [a.replace(" ", "_") for a in atoms]
        for line in source:
            try:
                entry = {}
                atoms = line.split()
                if not headings:
                    headings = [a.replace(" ", "_") for a in atoms]
                else:
                    for h, a in zip(headings, atoms):
                        try:
                            entry[h] = float(a)
                        except:
                            entry[h] = NaN
                    yield entry
            except:
                print traceback.format_exc()
                raise

    def getTicket(self):
        self.ticket = "NONE"
        ticket = None
        qry = "issueTicket"
        sys = self.psys
        identity = self.identity
        rprocs = '["AnzLogMeta:byEpoch", "AnzLog:data", "AnzLog:byPos"]'

        params = {"qry": qry, "sys": sys, "identity": identity, "rprocs": rprocs}
        try:
            print "ticket_url", self.ticket_url
            resp = urllib2.urlopen(self.ticket_url, data=urllib.urlencode(params))
            rtndata_str = resp.read()
            rtndata = json.loads(rtndata_str)
            if "ticket" in rtndata:
                ticket = rtndata["ticket"]

        except urllib2.HTTPError, e:
            err_str = e.read()
            print '\nissueTicket failed \n%s\n' % err_str

        except Exception, e:
            print '\nissueTicket failed \n%s\n' % e

        if ticket:
            self.ticket = ticket
            print "new ticket: ", self.ticket

    def run(self):
        # Assemble the chain of generators which process the data from the logs in a file or in the database
        handle = None
        while True:
            # Get source
            if self.usedb:
                if self.logname:
                    lastlog = self.logname
                else:
                    lastlog = self.getLastLog()

                if lastlog:
                    fname = lastlog
                else:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

                # sys.exit()
            else:
                try:
                    if self.file_path:
                        fname = os.path.join(self.file_path)
                    else:
                        fname = genLatestFiles(*os.path.split(self.userlogfiles)).next()

                except:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                # Initialize output structure for writing to database or to analysis file
                doc_row = self.startRow
                if self.usedb:
                    swathname = fname.replace(".dat", ".%s" % self.logtype)
                    doc_hdrs = ["EPOCH_TIME", "GPS_ABS_LONG", "GPS_ABS_LAT", "DELTA_LONG",
                                "DELTA_LAT", "INST_STATUS"]
                    doc_data = []
                else:
                    swathFile = os.path.splitext(fname)[0] + '.swath'
                    try:
                        handle = open(swathFile, 'wb+', 0)  # open file with NO buffering
                    except:
                        raise RuntimeError('Cannot open swath output file %s' % swathFile)
                    # Write file header
                    handle.write("%-14s%-14s%-14s%-14s%-14s%-14s\r\n" % (
                        "EPOCH_TIME", "GPS_ABS_LONG", "GPS_ABS_LAT", "DELTA_LONG", "DELTA_LAT",
                        "INST_STATUS"))
                # Make alignedData source from database or specified file
                if self.usedb:
                    source = self.followLastUserLogDb()
                    alignedData = self.anzDatAsDictDb(source)
                else:
                    if self.file_path:
                        source = self.sourceFromFile(fname)
                    else:
                        source = self.followLastUserFile(fname)
                    alignedData = self.anzDatAsDict(source)

                # Process the aligned data and write results to database or to the analysis file

                astdParams = {"a": self.astd_a, "b": self.astd_b, "c": self.astd_c}

                print "\nNew dat file for swath processing\n", fname
                for skip in range(doc_row):
                    alignedData.next()
                for i, r in enumerate(processGen(alignedData, self.maxWindow, self.stabClass,
                                                 self.minLeak, self.minAmpl, astdParams)):
                    if i % 100 == 0:
                        sys.stdout.write('.')
                    if self.usedb:
                        doc = {}
                        # Note: please assure that value list and doc_hdrs are in the same sequence
                        for col, val in zip(doc_hdrs, [r["EPOCH_TIME"], r["GPS_ABS_LONG"],
                                            r["GPS_ABS_LAT"], r["DELTA_LONG"], r["DELTA_LAT"],
                                            r["INST_STATUS"]]):
                            doc[col] = float(val)

                            # JSON does not support nan, so change to string "NaN"
                            # The server will handle appropriately
                            try:
                                if isnan(doc[col]):
                                    doc[col] = "NaN"
                            except:
                                # just skip on isnan error
                                pass

                        doc_row += 1
                        doc["row"] = doc_row
                        doc["ANALYZER"] = self.analyzerId
                        doc_data.append(doc)

                        self.pushData(swathname, doc_data)
                        doc_data = []
                    else:
                        handle.write("%-14.2f%-14.6f%-14.6f%-14.6f%-14.6f%-14.0f\r\n" % (
                                     r["EPOCH_TIME"], r["GPS_ABS_LONG"], r["GPS_ABS_LAT"],
                                     r["DELTA_LONG"], r["DELTA_LAT"], r["INST_STATUS"]))
                if not self.usedb and handle is not None:
                    handle.close()

                if self.logname:
                    break

                if self.file_path:
                    break


def main(argv=None):
    if argv is None:
        argv = sys.argv

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--pid-path", dest="pid_path",
                      help="path to specific pid (to test for running process).", metavar="<PID_PATH>")
    parser.add_option("-l", "--listen-path", dest="listen_path",
                      help="Search path for constant updates.", metavar="<LISTEN_PATH>")
    parser.add_option("-f", "--file-path", dest="file_path",
                      help="path to specific file to upload.", metavar="<FILE_PATH>")
    parser.add_option("-a", "--analyzer", dest="analyzerId",
                      help="Analyzer Name.", metavar="<ANALYZER>")
    parser.add_option("-g", "--logname", dest="logname",
                      help="Log Name.", metavar="<LOGNAME>")
    parser.add_option("-t", "--timeout", dest="timeout",
                      help="timeout value for response from server [%s seconds]." % SwathMaker.timeout, metavar="<TIMEOUT>")
    parser.add_option("-u", "--anzlog-url", dest="anzlog_url",
                      help="rest url for AnzLog Resource. Use the string <TICKET> as the place-holder for the authentication ticket.", metavar="<LOG_URL>")
    parser.add_option("-m", "--meta-url", dest="meta_url",
                      help="rest url for AnzLogMeta Resource. Use the string <TICKET> as the place-holder for the authentication ticket.", metavar="<META_URL>")
    parser.add_option("-k", "--ticket-url", dest="ticket_url",
                      help="rest url for authentication ticket. Use the string 'dummy' as the place-holder for the authentication ticket.", metavar="<TICKET_URL>")
    parser.add_option("-y", "--identity", dest="identity",
                      help="Authentication identity string.", metavar="<IDENTITY>")
    parser.add_option("-s", "--sys", dest="psys",
                      help="Authentication sys.", metavar="<SYS>")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="Debug mode")

    parser.add_option("--startRow", dest="startRow",
                      help="Start row [%d]." % SwathMaker.startRow, metavar="<startRow>")
    parser.add_option("--calc-maxWindow", dest="maxWindow",
                      help="Default value for maxWindow [%d]." % SwathMaker.maxWindow, metavar="<CALC_maxWindow>")
    parser.add_option("--calc-stabClass", dest="stabClass",
                      help="Default value for stabClass [%s]." % SwathMaker.stabClass, metavar="<CALC_stabClass>")
    parser.add_option("--calc-minLeak", dest="minLeak",
                      help="Default value for minLeak [%s cuft/hr]." % SwathMaker.minLeak, metavar="<CALC_minLeak>")
    parser.add_option("--calc-minAmpl", dest="minAmpl",
                      help="Default value for minAmpl [%s ppm]." % SwathMaker.minAmpl, metavar="<CALC_minAmpl>")
    parser.add_option("--calc-astd_a", dest="astd_a",
                      help="Default value for astd_a [%s radians]." % SwathMaker.astd_a, metavar="<CALC_astd_a>")
    parser.add_option("--calc-astd_b", dest="astd_b",
                      help="Default value for astd_b [%s m/s]." % SwathMaker.astd_b, metavar="<CALC_astd_b>")
    parser.add_option("--calc-astd_c", dest="astd_c",
                      help="Default value for astd_c [%s]." % SwathMaker.astd_c, metavar="<CALC_astd_c>")

    (options, args) = parser.parse_args()

    if not options.pid_path:
        parser.error("pid-path is required")

    if not options.analyzerId:
        if not options.logname:
            if not options.file_path:
                parser.error("One of analyzer, or logname, or file_path is required.")

    if options.listen_path and options.file_path:
        parser.error("listen-path and file-path are mutually exclusive.")

    if ((options.listen_path or options.file_path) and options.anzlog_url):
        parser.error(
            "anzlog_url is mutually exclusive to listen-path and/or file-path.")

    if (options.logname or options.anzlog_url or options.meta_url or
            options.ticket_url or options.identity or options.psys):
        if not options.anzlog_url:
            parser.error(
                "AnzLog Resource URL is required when other REST url's are provided.")
        if not options.meta_url:
            parser.error(
                "AnzLogMeta Resource URL is required when other REST url's are provided.")
        if not options.ticket_url:
            parser.error(
                "Authentication ticket Resource URL is required when other REST url's are provided.")
        if not options.identity:
            parser.error(
                "Authentication identity string is required when other REST url's are provided.")
        if not options.psys:
            parser.error(
                "Authentication sys name is required when other REST url's are provided.")

    class_opts = {}

    for copt in [
        "pid_path",  # path for PID file
        "analyzerId",  # Analyzer ID
        "anzlog_url",  # URL for AnzLog resource
        "meta_url",  # URL for AnzLogMeta resource
        "ticket_url",  # URL for Admin (issueTicket) resource
        "logname",  # logname (when processing single log)
        "identity",  # identity (authentication)
        "psys",  # picarro sys (authentication)
        "usedb",  # True/False use REST DB calls (instead of file system)
        "listen_path",  # listen path (when processing file system)
        "file_path",  # file path (when procesing single log from file system)
        "sleep_seconds",  # override default sleep_seconds value
        "startRow",   # override default startRow
        "maxWindow",  # override default maxWindow
        "stabClass",  # override default stabClass
        "minLeak",    # override default minLeak
        "minAmpl",    # override default minAmpl
        "astd_a",     # override default astd_a
        "astd_b",     # override default astd_b
        "astd_c",     # override default astd_c
        "timeout",  # override default REST timeout value
        "debug"  # True/False show debug print (in stdout)
    ]:
        if copt in dir(options):
            class_opts[copt] = getattr(options, copt)
        else:
            class_opts[copt] = None

    if class_opts["anzlog_url"]:
        class_opts["usedb"] = True
    else:
        class_opts["usedb"] = False

    if not class_opts["analyzerId"]:
        if class_opts["logname"]:
            fbase = class_opts["logname"]
        else:
            if class_opts["file_path"]:
                fbase = os.path.basename(class_opts["file_path"])

        if fbase:
            class_opts["analyzerId"], sep, part = fbase.partition('-')
        else:
            parser.error("Analyzer Name not provided, and could not be determined from logname or file-path.")

    for copt in class_opts:
        print copt, class_opts[copt]

    try:
        testf = open(class_opts["pid_path"], 'r')
        testf.close()
        raise RuntimeError('pidfile exists. Verify that there is not another SwathMaker task for the directory. path: %s.' %
                           class_opts["pid_path"])
    except:
        try:
            pidf = open(class_opts["pid_path"], 'wb+', 0)  # open file with NO buffering
        except:
            raise RuntimeError('Cannot open pidfile for output. path: %s.' % class_opts["pid_path"])

    pid = os.getpid()
    pidf.write("%s" % (pid))
    pidf.close()

    pf = SwathMaker(**class_opts)

    pf.run()
    os.remove(class_opts["pid_path"])


if __name__ == "__main__":
    sys.exit(main())
