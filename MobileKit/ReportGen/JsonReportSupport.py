#!/usr/bin/python
#
"""
File Name: JsonReportSupport.py
Purpose: Generate JSON files for use with JavaScript based report generation

File History:
    11-Nov-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
import cPickle
import geohash
import json
import math
import numpy as np
import os
import re
import sys
import threading
import time
import traceback

import Host.Common.SurveyorInstStatus as sis
from Host.Common.SwathProcessor import process

from P3ApiService import P3ApiService

from ReportCommon import getMsUnixTime, getTicket, merge_dictionary
from ReportCommon import msUnixTimeToTimeString, RptGenStatus, strToEtm, timeStringAsDirName

if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# Executable for HTML to PDF conversion
# configFile = os.path.splitext(appPath)[0] + ".ini"
# if os.path.exists(configFile):
#    config = ConfigObj(configFile)
#    WKHTMLTOPDF = config["HelperApps"]["wkhtml_to_pdf"]
#    IMGCONVERT = config["HelperApps"]["image_convert"]
#    APIKEY = config["P3Logs"].get("apikey", None)

SVCURL = "http://localhost:5300/rest"
RTD = 180.0 / math.pi
DTR = math.pi / 180.0
EARTH_RADIUS = 6378100
NOT_A_NUMBER = 1e1000 / 1e1000


# Implement status using a pickled file which is appended to
#  The current status is found by merging the dictionaries in the pickles
def readStatus(filename):
    """Read status from a pickled file"""
    statusDict = {}
    try:
        with file(filename, "rb") as fp:
            while True:
                try:
                    statusDict = merge_dictionary(statusDict, cPickle.load(fp))
                except EOFError:
                    break
    except IOError:
        pass
    return statusDict


def writeStatus(filename, statusDict):
    if os.path.exists(filename):
        with file(filename, "ab") as fp:
            cPickle.dump(statusDict, fp)
    else:
        with file(filename, "wb") as fp:
                cPickle.dump(statusDict, fp)


class P3ServiceFactory(object):
    """Factory for obtaining P3 service objects (can be called from several threads)"""
    def __init__(self, csp, sys, identity):
        self.csp = "https://" + csp
        self.sys = sys
        self.identity = identity

    def getService(self):
        service = P3ApiService()
        service.csp_url = self.csp
        service.ticket_url = self.csp + "/rest/sec/dummy/1.0/Admin/"
        service.identity = self.identity
        service.psys = self.sys
        service.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo"]'
        service.debug = True
        service.timeout = 60
        service.sockettimeout = 15
        return service

# To obtain a new P3 service, call p3Services.getService()
p3Services = P3ServiceFactory("dev.picarro.com/dev", "APITEST2", "dc1563a216f25ef8a20081668bb6201e")


def genLrtResults(p3Service, svc, ver, rsc, qryparms_obj):
    """Generate results from a long running task"""
    maxAttempts = 5
    for i in range(maxAttempts):
        result = p3Service.get(svc, ver, rsc, qryparms_obj)
        if 'error' in result and result['error']:
            print "Error on attempt %d: %s" % (i, result)
            time.sleep(2.0)
            continue
        else:
            ret = result['return']
            if ret["lrt_start_ts"] == ret["request_ts"]:
                print "This is a new request, made at %s" % ret["lrt_start_ts"]
            else:
                print "This is a duplicate of a request made at %s" % ret["lrt_start_ts"]
            print "Request status: %d" % ret["status"]
            lrt_parms_hash = ret["lrt_parms_hash"]
            lrt_start_ts = ret["lrt_start_ts"]
            break
    else:
        raise RuntimeError("Command failed after %d attempts" % (maxAttempts,))
    #
    # Ask for status of long running task
    #
    while ret["status"] == 0:       # Loop until status is successful
        print "Waiting"
        time.sleep(5.0)
        qryparms = {'prmsHash': lrt_parms_hash, 'startTs':
                    lrt_start_ts, 'qry': 'getStatus'}
        result = p3Service.get(svc, ver, "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            print "Error getting status"
        else:
            ret = result['return']
            print "Request status: %d" % ret["status"]
    count = ret["count"]    # Number of result rows
    print "Result rows:", count
    #
    # Get back the data in chunks
    #
    qryparms = {'prmsHash': lrt_parms_hash, 'startTs': lrt_start_ts,
                'qry': 'firstSet', 'limit': 5000, 'doclist': True}
    result = p3Service.get(svc, ver, "AnzLrt", qryparms)
    if 'error' in result and result['error'] and '404 resource error' in result['error']:
        raise StopIteration
    yield result

    while True:
        qryparms = {
            'prmsHash': lrt_parms_hash, 'startTs': lrt_start_ts, 'qry': 'nextSet', 'limit': 5000, 'doclist': True,
            'sortPos': result['return']['result']['lrt_sortpos'][-1]}
        result = p3Service.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] and '404 resource error' in result['error']:
            raise StopIteration
        yield result

# Parameters for calculating additional wind direction standard deviation
ASTD_PARAMS = dict(a=0.15 * math.pi, b=0.25, c=0.0)


def astd(wind, vcar):
    a = ASTD_PARAMS["a"]
    b = ASTD_PARAMS["b"]
    c = ASTD_PARAMS["c"]
    return min(math.pi, a * (b + c * vcar) / (wind + 0.01))


def dol2lod(dictOfList):
    if dictOfList:
        lengths = {}
        for k in dictOfList:
            lengths[k] = len(dictOfList[k])
        n = max(lengths.values())
        validKeys = [k for k in lengths if lengths[k] == n]
        result = []
        for i in range(n):
            d = {}
            for k in validKeys:
                d[k] = dictOfList[k][i]
            result.append(d)
        return result
    else:
        return []


def extract_dictionary(src, keys):
    """Create a new dictionary from src containing only the specified keys"""
    result = {}
    for k in keys:
        result[k] = src[k]
    return result


def getPossibleNaN(d, k, default):
    try:
        result = float(d.get(k, default))
    except:
        result = NOT_A_NUMBER
    return result


def lod2dol(listOfDict):
    """Starting with a list of dictionaries all of which have the same keys, convert to a dictionary
    of lists that can be more compactly JSON encoded"""
    result = {}
    if listOfDict:
        for k in listOfDict[0].keys():
            result[k] = [d[k] for d in listOfDict]
    return result


class ThreadPool(object):
    """Collect statistics about threads used for report generation. Threads are stored in a
    dictionary whose key indicates the request that started the thread and whose value is a
    list of the threads started."""
    def __init__(self):
        self.startTimeString = getMsUnixTime()
        self.threads = {}
        self.activeThreads = 0
        self.totalThreads = 0

    def register(self, thread, key):
        if key not in self.threads:
            self.threads[key] = [thread]
        else:
            self.threads[key].append(thread)
        self.totalThreads += 1
        self.updateStats()

    def updateStats(self):
        nActive = 0
        empty = []
        for k in self.threads:
            self.threads[k][:] = [th for th in self.threads[k] if th.isAlive()]
            if self.threads[k]:
                nActive += len(self.threads[k])
            else:
                empty.append(k)
        for k in empty:
            del self.threads[k]
        self.activeThreads = nActive
        print "Number of threads [active/total]: %d / %d" % (self.activeThreads, self.totalThreads)


threadPool = ThreadPool()


class ParamsValidator(object):
    """Fetches parameters from paramsDict and checks if they satisfy checkList.

    The elements of checkList are tuples:
            (name, required, type_or_predicate_or_regex, default_value)

        name:           name of the parameter
        required:       Boolean indicating if the parameter must be present in paramsDict
        type_or_predicate_or_regex: Used to validate the parameter value. It can be
            - A type or tuple of types: We check using isinstance if value is of this type
            - A predicate function: This is applied to the value and returns a Boolean
                                     if it is valid
            - A regex: Used to determine if the parameter matches the pattern.
        default_value:  If the parameter is not required and is not present, this is the value
                         None is used if no default_value is specified

    The validation takes place when the ParamsValidator object is created. Methods are
        used to report if validation passed and retrieve error messages. Parameter values
        may be retrieved by calling the ParamsValidator object with the parameter name
        as the argument.
    """
    def __init__(self, paramsDict, checkList):
        self.resultDict = {}
        self.errorList = []
        for c in checkList:
            name, required, type_or_predicate_or_regex = c[:3]
            if name not in paramsDict:
                if not required:
                    # Use the default value
                    self.resultDict[name] = c[3] if len(c) >= 4 else None
                else:
                    self.errorList.append("Required parameter %s missing" % name)
            else:
                value = paramsDict[name]
                # We have a parameter, validate it
                if isinstance(type_or_predicate_or_regex, str):  # We have a regex
                    m = re.match(type_or_predicate_or_regex, value)
                    if m and m.end() == m.endpos:
                        self.resultDict[name] = value
                    else:
                        self.errorList.append("Parameter %s fails regex based validation" % name)
                elif hasattr(type_or_predicate_or_regex, '__call__'):  # We have a predicate
                    if type_or_predicate_or_regex(value):
                        self.resultDict[name] = value
                    else:
                        self.errorList.append("Parameter %s fails predicate based validation" % name)
                else:  # Test using isinstance
                    if isinstance(value, type_or_predicate_or_regex):
                        self.resultDict[name] = value
                    else:
                        self.errorList.append("Parameter %s fails type based validation" % name)

    def ok(self):
        return not self.errorList

    def errors(self):
        return "\n".join(self.errorList)

    def __call__(self, name):
        return self.resultDict[name]


class ReportGenStatus(object):
    def __init__(self, reportDir, requestDict):
        self.reportDir = reportDir
        self.requestDict = requestDict

    def run(self):
        # Check validity of contents_hash and start_ts
        p = ParamsValidator(self.requestDict,
                            [("contents_hash", True, "[0-9a-fA-F]{32}"),
                             ("start_ts", True, "\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")])
        if p.ok():
            targetDir = os.path.join(self.reportDir, p("contents_hash"),
                                     timeStringAsDirName(p("start_ts")))
            if os.path.exists(targetDir):
                result = readStatus(os.path.join(targetDir, "status.dat"))
                if not result:
                    result = {"status": RptGenStatus.NOT_STARTED}
            else:
                result = {"status": RptGenStatus.TASK_NOT_FOUND}
        else:
            result = {"status": RptGenStatus.BAD_PARAMETERS, "msg": p.errors()}

        for k in self.requestDict:
            result[k] = self.requestDict[k]

        return result


class JsonReportGen(object):
    def __init__(self, reportDir, contents):
        self.reportDir = reportDir
        self.contents = contents
        self.instructions = None
        self.ticket = None
        self.request_msUnixTime = None

    def run(self, params):
        # Use the json module to parse the contents into an object to
        #  verify that it is syntacticlly valid JSON
        try:
            self.instructions = json.loads(self.contents)
        except:
            raise ValueError("Instructions are not in valid JSON notation")
        # We first find the ticket which is a MD5 hash of the contents
        # The contents are placed in a file instructions.json in a directory
        # named by the ticket
        self.ticket = getTicket(self.contents)
        self.request_ts = msUnixTimeToTimeString(getMsUnixTime())
        targetDir = os.path.join(self.reportDir, "%s" % self.ticket)
        instrFname = os.path.join(self.reportDir,
                                  "%s/instructions.json" % self.ticket)
        # Create the ticket directory and the instructions file
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
            with open(instrFname, "wb") as ip:
                ip.write(self.contents)
        else:
            # If the ticket directory already exists, the instructions file there
            #  must match the contents. Otherwise an unrecoverable hash collision
            #  has taken place
            with open(instrFname, "rb") as ip:
                if ip.read() != self.contents:
                    raise ValueError("MD5 hash collision in instructions")
            # If the force parameter is False, we look for previous requests with this hash
            if not params["force"]:
                # We go to the most recent timestamped subdirectory to find the status
                #  when this request was last issued
                dirname, dirnames, _ = os.walk(targetDir).next()
                if dirnames:
                    lastSubdir = sorted(dirnames)[-1]
                    start_ts = msUnixTimeToTimeString(int(lastSubdir))
                    # raw_input("Fetched time for subdir: %s" % start_ts)
                    # TODO: Fetch status from subdirectory
                    result = readStatus(os.path.join(dirname, lastSubdir, "status.dat"))
                    if not result:
                        result = {"status": RptGenStatus.NOT_STARTED,
                                  "rpt_contents_hash": self.ticket,
                                  "rpt_start_ts": start_ts,
                                  "request_ts": self.request_ts}
                    else:
                        result["request_ts"] = self.request_ts
                    # This is a repeat of a previous request, so do not start it again
                    return result
        # We get here if this request needs to be executed
        targetDir = os.path.join(targetDir, timeStringAsDirName(self.request_ts))
        os.makedirs(targetDir)
        writeStatus(os.path.join(targetDir, "status.dat"),
                    {"rpt_contents_hash": self.ticket,
                     "rpt_start_ts": self.request_ts,
                     "request_ts": self.request_ts,
                     "status": RptGenStatus.IN_PROGRESS})
        try:
            o = Supervisor(targetDir, self.instructions)
            th = threading.Thread(target=o.run)
            threadPool.register(th, (self.ticket, self.request_ts))
            th.setDaemon(True)
            th.start()
        except:
            writeStatus(os.path.join(targetDir, "status.dat"),
                        {"status": RptGenStatus.FAILED,
                         "msg": traceback.format_exc()})
        result = readStatus(os.path.join(targetDir, "status.dat"))
        # This is a repeat of a previous request, so do not start it again
        return result


class Supervisor(object):
    # Start up various report generation tasks.
    def __init__(self, targetDir, instr):
        self.instructions = instr
        self.targetDir = targetDir
        self.statusFile = os.path.join(self.targetDir, "status.dat")

    def run(self):
        time.sleep(0.1)
        try:
            if self.instructions["instructions_type"] == "ignore":
                writeStatus(self.statusFile, {"status": RptGenStatus.DONE})
            elif self.instructions["instructions_type"] == "getPathData":
                ReportPathData(self.targetDir, self.instructions, self.statusFile).run()
                writeStatus(self.statusFile, {"status": RptGenStatus.DONE})
            elif self.instructions["instructions_type"] == "getPeaksData":
                ReportPeaksData(self.targetDir, self.instructions, self.statusFile).run()
                writeStatus(self.statusFile, {"status": RptGenStatus.DONE})
            else:
                raise ValueError("Bad instructions_type")
        except:
            msg = traceback.format_exc()
            writeStatus(self.statusFile,
                        {"status": RptGenStatus.FAILED, "msg": msg})
        """
        errors = False
        statusFname = os.path.join(
            self.reportDir, "%s/json.status" % self.ticket)
        for i, r in enumerate(self.instructions["regions"]):
            bd = ReportBaseData(
                self.reportDir, self.ticket, self.instructions, i)
            bdThread = threading.Thread(target=bd.run)
            bdThread.setDaemon(True)
            bdThread.start()

            pd = ReportPathData(
                self.reportDir, self.ticket, self.instructions, i)
            pdThread = threading.Thread(target=pd.run)
            pdThread.setDaemon(True)
            pdThread.start()

            pk = ReportPeaksData(
                self.reportDir, self.ticket, self.instructions, i)
            pkThread = threading.Thread(target=pk.run)
            pkThread.setDaemon(True)
            pkThread.start()
            # Wait for processing in this region to complete before proceeding
            # to the next
            pdThread.join()
            pkThread.join()
        if errors:
            updateStatus(statusFname, {"error": 1, "end":
                         time.strftime("%Y%m%dT%H%M%S")})
        else:
            updateStatus(statusFname, {"done": 1, "end":
                         time.strftime("%Y%m%dT%H%M%S")})
        """


class NamesToIndices(object):
    # Class whose instances convert a collection of names to distinct indices. It is possible to lookup
    # the name for an index and the index for a name. This is useful for
    # compact storage of names as integers.
    def __init__(self):
        self.indexByName = {}
        self.nameByIndex = []

    def getIndex(self, name):
        "Returns index for given name, creating one if not already present"
        if name not in self.indexByName:
            self.indexByName[name] = len(self.nameByIndex)
            self.nameByIndex.append(name)
        return self.indexByName[name]

    def getName(self, index):
        "Returns name for given index, raising IndexError if not available"
        return self.nameByIndex[index]


class ReportPathData(object):
    # Path segment types
    NORMAL = 0
    ANALYZING = 1
    INACTIVE = 2
    BADSTATUS = 3

    def __init__(self, reportDir, instructions, statusFile):
        self.reportDir = reportDir
        self.instructions = instructions
        self.statusFile = statusFile

    def run(self):
        swCorner = self.instructions["swCorner"]
        neCorner = self.instructions["neCorner"]
        runsData = self.instructions.get("runs", [])
        paths, swaths, surveys, runs = self.makePathData(swCorner, neCorner, runsData)
        for i, s in enumerate(surveys):
            self.pathDataFname = os.path.join(
                self.reportDir, "pathData.%d.json" % (i,))
            op = file(self.pathDataFname, "wb")
            try:
                json.dump(dict(PATHS=[p for p in paths if p["SURVEY"] == i],
                               SWATHS=[s for s in swaths if s["SURVEY"] == i],
                               SURVEYS=surveys, RUNS=runs), op)
            finally:
                op.close()

    def makePathData(self, swCorner, neCorner, runsData):

        def geohashPath(p):
            raw = [geohash.encode(lat, lng) for lat, lng in zip(
                p["GPS_ABS_LAT"], p["GPS_ABS_LONG"])]
            unique = []
            for i, pos in enumerate(raw):
                if i == 0 or pos != raw[i - 1]:
                    unique.append(i)
            del p["GPS_ABS_LAT"]
            del p["GPS_ABS_LONG"]
            for k in p:
                p[k] = [p[k][i] for i in unique]
            p["PATH"] = [raw[i] for i in unique]
            return p

        def geohashSwath(s):
            path = [geohash.encode(lat, lng) for lat, lng in zip(
                s["GPS_ABS_LAT"], s["GPS_ABS_LONG"])]
            edge = [geohash.encode(lat + dlat, lng + dlng) for lat, lng, dlat, dlng in zip(
                s["GPS_ABS_LAT"], s["GPS_ABS_LONG"], s["DELTA_LAT"], s["DELTA_LONG"])]
            unique = []
            for i in range(len(path)):
                if i == 0 or path[i] != path[i - 1] or edge[i] != edge[i - 1]:
                    unique.append(i)
            del s["GPS_ABS_LAT"]
            del s["GPS_ABS_LONG"]
            del s["DELTA_LAT"]
            del s["DELTA_LONG"]
            for k in s:
                s[k] = [s[k][i] for i in unique]
            s["PATH"] = [path[i] for i in unique]
            s["EDGE"] = [edge[i] for i in unique]
            return s

        beginTime = time.clock()
        swathTime = 0
        makePath = True
        makeSwath = True
        self.minLat, self.minLng = swCorner
        self.maxLat, self.maxLng = neCorner
        surveys = NamesToIndices()
        for ir, params in enumerate(runsData):
            lastType = [self.NORMAL]

            def getPathType(mask, instStatus):
                # Determine type of path from valve mask and instrument status
                pType = lastType[0]
                imask = int(round(mask, 0))
                if (instStatus & sis.INSTMGR_STATUS_MASK) != sis.INSTMGR_STATUS_GOOD:
                    pType = self.BADSTATUS
                elif abs(mask - imask) <= 1e-4:
                    if imask & 1:
                        pType = self.ANALYZING
                    elif imask & 16:
                        pType = self.INACTIVE
                    else:
                        pType = self.NORMAL
                lastType[0] = pType
                return pType

            startEtm = strToEtm(params["startEtm"])
            endEtm = strToEtm(params["endEtm"])
            analyzer = params["analyzer"]
            minAmpl = params["minAmpl"]
            stabClass = params["stabClass"]

            # Swath generation parameters
            nWindow = 10
            minLeak = 1.0

            savedSwath = []
            savedPath = []
            lastRow = -1
            pathLatLng = []         # Path in lats and lngs
            bufferedPath = []       # Path for calculation of swath
            currentPathType = self.NORMAL
            currentSurveyIndex = None
            newPath = True
            swathkeys = ["GPS_ABS_LONG", "GPS_ABS_LAT", "DELTA_LONG", "DELTA_LAT"]

            p3 = p3Services.getService()
            # qryparms = {'qry': 'byGeo', 'anz': analyzer,
            #            'startEtm': startEtm, 'endEtm': endEtm, 'limit': 50000,
            #            'box': [self.minLng, self.minLat, self.maxLng, self.maxLat],
            #            'resolveLogname':True, 'doclist': True}
            qryparms = {'qry': 'byEpoch', 'anz': analyzer,
                        'startEtm': startEtm, 'endEtm': endEtm, 'limit': 'all',
                        'minLng': self.minLng, 'minLat': self.minLat,
                        'maxLng': self.maxLng, 'maxLat': self.maxLat,
                        'resolveLogname': True, 'doclist': True,
                        'rtnFmt': 'lrt'}
            for res in genLrtResults(p3, "gdu", "1.0", "AnzLog", qryparms):
                result = res['return']['result']
                if "EPOCH_TIME" in result:
                    print "Fetched pathData from P3", len(result["EPOCH_TIME"])
                for i, m in enumerate(dol2lod(result)):
                    fit = m.get("GPS_FIT", 1)
                    mask = m.get("ValveMask", 0)
                    row = m.get("row", 0)   # Used to detect contiguous points
                    instStatus = m.get("INST_STATUS", 0)
                    surveyName = m.get("LOGNAME", "")
                    surveyIndex = surveys.getIndex(surveyName)
                    pathType = getPathType(mask, instStatus)
                    # newPath = True means that there is to be a break in the path. A simple change
                    #  of color gives a new path which joins onto the last
                    if fit >= 1 and (row == lastRow + 1):
                        if newPath or pathType != currentPathType or surveyIndex != currentSurveyIndex:
                            if pathLatLng:  # Draw out old path
                                if makePath:
                                    p = geohashPath(lod2dol(pathLatLng))
                                    p["TYPE"] = currentPathType
                                    p["RUN"] = ir
                                    p["SURVEY"] = currentSurveyIndex
                                    savedPath.append(p)
                                if makeSwath and currentPathType == self.NORMAL:
                                    start = time.clock()
                                    result = process(
                                        bufferedPath, nWindow, stabClass, minLeak, minAmpl, ASTD_PARAMS)
                                    swathTime += time.clock() - start
                                    s = geohashSwath(
                                        extract_dictionary(result, swathkeys))
                                    s["RUN"] = ir
                                    s["SURVEY"] = currentSurveyIndex
                                    savedSwath.append(s)
                                if newPath:
                                    pathLatLng = []
                                    bufferedPath = []
                                else:
                                    pathLatLng = [pathLatLng[-1]]
                                    bufferedPath = [bufferedPath[-1]]
                            currentPathType = pathType
                            currentSurveyIndex = surveyIndex
                        bufferedPath.append(m)
                        latlng = extract_dictionary(m, ["GPS_ABS_LAT", "GPS_ABS_LONG"])
                        pathLatLng.append(latlng)
                        newPath = False
                    else:
                        newPath = True
                    if i % 100 == 0:
                        print "Run: %d, processing: %d" % (ir, i)
                    lastRow = row
            if pathLatLng:
                if makePath:
                    p = geohashPath(lod2dol(pathLatLng))
                    p["TYPE"] = currentPathType
                    p["RUN"] = ir
                    p["SURVEY"] = currentSurveyIndex
                    savedPath.append(p)
                if makeSwath and currentPathType == self.NORMAL:
                    start = time.clock()
                    result = process(bufferedPath, nWindow,
                                     stabClass, minLeak, minAmpl, ASTD_PARAMS)
                    swathTime += time.clock() - start
                    s = geohashSwath(extract_dictionary(result, swathkeys))
                    s["RUN"] = ir
                    s["SURVEY"] = currentSurveyIndex
                    savedSwath.append(s)
        print "Swath processing time", swathTime, "Report path time", time.clock() - beginTime
        return savedPath, savedSwath, surveys.nameByIndex, runsData


class ReportBaseData(object):
    def __init__(self, reportDir, ticket, instructions, region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.baseDataFname = os.path.join(
            self.reportDir, "%s/baseData.%d.json" % (self.ticket, self.region))
        self.statusFname = os.path.join(
            self.reportDir, "%s/baseData.%d.status" % (self.ticket, self.region))

    def run(self):
        name = self.instructions["regions"][self.region]["name"]
        swCorner = self.instructions["regions"][self.region]["swCorner"]
        neCorner = self.instructions["regions"][self.region]["neCorner"]
        baseType = self.instructions["regions"][self.region]["baseType"]
        updateStatus(
            self.statusFname, {"start": time.strftime("%Y%m%dT%H%M%S")}, True)
        base = self.makeBaseData(name, baseType, swCorner, neCorner)
        op = file(self.baseDataFname, "wb")
        try:
            json.dump(dict(BASE=base), op)
        finally:
            op.close()
        updateStatus(self.statusFname, {"done": 1, "end":
                     time.strftime("%Y%m%dT%H%M%S")})

    def makeBaseData(self, name, baseType, swCorner, neCorner):
        return dict(name=name, swCorner=swCorner, neCorner=neCorner, baseType=baseType)


class ReportPeaksData(object):
    def __init__(self, reportDir, ticket, instructions, region):
        self.reportDir = reportDir
        self.ticket = ticket
        self.instructions = instructions
        self.region = region
        self.peaksDataFname = os.path.join(
            self.reportDir, "%s/peaksData.%d.json" % (self.ticket, self.region))
        self.statusFname = os.path.join(
            self.reportDir, "%s/peaksData.%d.status" % (self.ticket, self.region))

    def run(self):
        swCorner = self.instructions["regions"][self.region]["swCorner"]
        neCorner = self.instructions["regions"][self.region]["neCorner"]
        runsData = self.instructions.get("runs", [])
        updateStatus(
            self.statusFname, {"start": time.strftime("%Y%m%dT%H%M%S")}, True)
        peaks, surveys, runs = self.makePeaksData(swCorner, neCorner, runsData)
        op = file(self.peaksDataFname, "wb")
        try:
            json.dump(dict(PEAKS=peaks, SURVEYS=surveys, RUNS=runs), op)
        finally:
            op.close()
        updateStatus(self.statusFname, {"done": 1, "end":
                     time.strftime("%Y%m%dT%H%M%S")})

    def thinPeaks(self, pList, exclRadius):
        # From the list of peaks pList, select those which have hiighest amplitudes within regions
        #  of radius exclRadius
        result = []
        ilat, ilng, iampl = [], [], []
        # We need to remove peaks which are closer to each other than the exclusion radius, keeping
        #  only the largest in each group
        for amp, m, run, survey in pList:
            ilat.append(m["GPS_ABS_LAT"])
            ilng.append(m["GPS_ABS_LONG"])
            iampl.append(m["AMPLITUDE"])
        ilat = np.asarray(ilat)
        ilng = np.asarray(ilng)
        iampl = np.asarray(iampl)

        # Get median latitude for estimating distance scale
        medLat = np.median(ilat)
        mpdLat = DTR * EARTH_RADIUS  # Meters per degree of latitude
        mpdLng = mpdLat * np.cos(DTR * medLat)
                                 # Meters per degree of longitude

        # Find points which are close to a given location
        # Find permutations that sort by longitude as primary key
        perm = np.argsort(ilng)
        elow = ehigh = 0
        dlng = exclRadius / mpdLng
        for i in perm:
            while elow < len(perm) and ilng[perm[elow]] < ilng[i] - dlng:
                elow += 1
            while ehigh < len(perm) and ilng[perm[ehigh]] <= ilng[i] + dlng:
                ehigh += 1
            for e in range(elow, ehigh):
                j = perm[e]
                lng, lat, ampl = ilng[j], ilat[j], iampl[j]
                assert ilng[i] - dlng <= lng < ilng[i] + dlng
                dx = mpdLng * (lng - ilng[i])
                dy = mpdLat * (lat - ilat[i])
                if 0 < dx * dx + dy * dy <= exclRadius * exclRadius:
                    if iampl[i] < ampl:
                        break
                    elif iampl[i] == ampl and i < j:
                        break
            else:
                # This is the largest peak in the exclusion zone
                result.append(i)
        return [pList[i] for i in result]

    def makePeaksData(self, swCorner, neCorner, runsData):

        def geohashLocations(m):
            if m:
                m["LOCATION"] = [geohash.encode(lat, lng) for lat, lng in zip(
                    m["GPS_ABS_LAT"], m["GPS_ABS_LONG"])]
                del m["GPS_ABS_LAT"]
                del m["GPS_ABS_LONG"]
                m["CH4"] = [round(x, 2) for x in m["CH4"]]
                m["AMPLITUDE"] = [round(x, 3) for x in m["AMPLITUDE"]]
                m["WIND_DIR_MEAN"] = [round(x, 1) for x in m["WIND_DIR_MEAN"]]
                m["WIND_DIR_SDEV"] = [round(x, 1) for x in m["WIND_DIR_SDEV"]]
                m["EPOCH_TIME"] = [int(round(x)) for x in m["EPOCH_TIME"]]
            else:
                m["LOCATION"] = []
            return m

        beginTime = time.clock()
        self.minLat, self.minLng = swCorner
        self.maxLat, self.maxLng = neCorner
        surveys = NamesToIndices()
        peaks = []
        for ir, params in enumerate(runsData):
            startEtm = strToEtm(params["startEtm"])
            endEtm = strToEtm(params["endEtm"])
            analyzer = params["analyzer"]
            exclRadius = params["exclRadius"]
            minAmpl = params["minAmpl"]

            p3 = p3Services.getService()
            # qryparms = {'qry': 'byGeo', 'anz': analyzer, 'logtype': 'peaks',
            #            'startEtm': startEtm, 'endEtm': endEtm, 'limit': 50000,
            #            'box': [self.minLng, self.minLat, self.maxLng, self.maxLat],
            #            'resolveLogname':True, 'doclist': True}
            results = []
            qryparms = {'qry': 'byEpoch', 'anz': analyzer, 'logtype': 'peaks',
                        'startEtm': startEtm, 'endEtm': endEtm, 'limit': 'all',
                        'minLng': self.minLng, 'minLat': self.minLat,
                        'maxLng': self.maxLng, 'maxLat': self.maxLat,
                        'resolveLogname': True, 'doclist': True,
                        'rtnFmt': 'lrt'}
            pList = []
            for res in genLrtResults(p3, "gdu", "1.0", "AnzLog", qryparms):
                result = res['return']['result']
                if "EPOCH_TIME" in result:
                    print "Fetched peaksData from P3", len(result["EPOCH_TIME"])
                for m in dol2lod(result):
                    surveyName = m.get("LOGNAME", "")
                    surveyIndex = surveys.getIndex(surveyName)
                    if (self.minLat <= m["GPS_ABS_LAT"] < self.maxLat) and (self.minLng <= m["GPS_ABS_LONG"] < self.maxLng) and (m["AMPLITUDE"] >= minAmpl):
                        pList.append((m["AMPLITUDE"], m, ir, surveyIndex))
                # Within a run, filter using the exclusion radius
                if exclRadius > 0:
                    peaks += self.thinPeaks(pList, exclRadius)
                else:
                    peaks += pList
        # We now have peaks from all runs. Sort them in by decreasing amplitude
        peaks.sort()
        peaks.reverse()
        # Add the wind information for the wedges (LISAs)
        self.addWedgesInfo(peaks)
        result = []
        for amp, m, run, survey in peaks:
            pk = extract_dictionary(
                m, ["ANALYZER", "EPOCH_TIME", "GPS_ABS_LONG", "GPS_ABS_LAT",
                    "WIND_DIR_MEAN", "WIND_DIR_SDEV", "AMPLITUDE", "CH4"])
            pk["SURVEY"] = survey
            pk["RUN"] = run
            result.append(pk)
        result = geohashLocations(lod2dol(result))

        print "Peaks data time", time.clock() - beginTime
        return result, surveys.nameByIndex, runsData

    def addWedgesInfo(self, peaks):
        for amp, m, run, survey in peaks:
            vcar = getPossibleNaN(m, "CAR_SPEED", 0.0)
            windN = getPossibleNaN(m, "WIND_N", 0.0)
            windE = getPossibleNaN(m, "WIND_E", 0.0)
            dstd = DTR * getPossibleNaN(m, "WIND_DIR_SDEV", 0.0)
            meanBearing = 0.0
            windSdev = 180.0
            if np.isfinite(dstd):
                wind = math.hypot(windE, windN)
                meanBearing = RTD * math.atan2(windE, windN)
                dstd = math.hypot(dstd, astd(wind, vcar))
                windSdev = RTD * dstd
            m["WIND_DIR_MEAN"] = meanBearing
            m["WIND_DIR_SDEV"] = windSdev
