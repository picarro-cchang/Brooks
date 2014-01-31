from collections import deque
import fnmatch
from numpy import *
import scipy.stats
import os
import sys
from optparse import OptionParser
import time
import datetime
import traceback

try:
    from collections import namedtuple
except:
    from Host.Common.namedtuple import namedtuple

import urllib2
import urllib
import socket
try:
    import simplejson as json
except:
    import json

NaN = 1e1000/1e1000

VALVE_STATE_EPSILON = 1.0e-4

# Permil
UNCERTAINTY_HIGH_THRESHOLD = 5.0
DELTA_NEGATIVE_THRESHOLD = -80.0
DELTA_POSITIVE_THRESHOLD = 0.0

CONCENTRATION_HIGH_THRESHOLD = 20.0

OUTPUT_COLUMNS = [
    'EPOCH_TIME',
    'DISTANCE',
    'GPS_ABS_LONG',
    'GPS_ABS_LAT',
    'CONC',
    'DELTA',
    'UNCERTAINTY',
    'REPLAY_MAX',
    'REPLAY_LMIN',
    'REPLAY_RMIN',
    'DISPOSITION']

DISPOSITIONS = [
    'COMPLETE',
    'USER_CANCELLATION',
    'UNCERTAINTY_OOR',
    'DELTA_OOR',
    'SAMPLE_SIZE_TOO_SMALL']


PeakData = namedtuple('PeakData',
                      'time dist lng lat conc delta uncertainty replay_max '
                      'replay_lmin replay_rmin disposition')


def genLatestFiles(baseDir,pattern):
    # Generate files in baseDir and its subdirectories which match pattern
    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=True)
        fileNames.sort(reverse=True)
        for name in fileNames:
            if fnmatch.fnmatch(name,pattern):
                yield os.path.join(dirPath,name)


def fixed_width(text,width):
    start = 0
    result = []
    while True:
        atom = text[start:start+width].strip()
        if not atom: return result
        result.append(atom)
        start += width
#######################################################################
# Longitude and latitude handling routines
#######################################################################

def distVincenty(lat1, lng1, lat2, lng2):
    # WGS-84 ellipsiod. lat and lng in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563;
    toRad = pi/180.0
    L = (lng2-lng1)*toRad
    U1 = arctan((1-f) * tan(lat1*toRad))
    U2 = arctan((1-f) * tan(lat2*toRad));
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)

    Lambda = L
    iterLimit = 100;
    for iter in range(iterLimit):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2*sinLambda) * (cosU2*sinLambda) +
                        (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
        if sinSigma==0:
            return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha*sinAlpha
        if cosSqAlpha == 0:
            cos2SigmaM = 0
        else:
            cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
        C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
        lambdaP = Lambda;
        Lambda = L + (1-C) * f * sinAlpha * \
          (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))
        if abs(Lambda-lambdaP)<=1.e-12: break
    else:
        raise ValueError("Failed to converge")

    uSq = cosSqAlpha * (a*a - b*b) / (b*b)
    A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-
                 B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
    return b*A*(sigma-deltaSigma)

def toXY(lat,lng,lat_ref,lng_ref):
    x = distVincenty(lat_ref,lng_ref,lat_ref,lng)
    if lng<lng_ref: x = -x
    y = distVincenty(lat_ref,lng,lat,lng)
    if lat<lat_ref: y = -y
    return x,y

#######################################################################
# Protected linear fit with uncertainties in y values
#######################################################################

def linfit(x,y,sigma):
    # Calculate the linear fit of (x,y) to a line, where sigma are the errors in the y values
    S = sum(1/sigma**2)
    Sx = sum(x/sigma**2)
    Sy = sum(y/sigma**2)
    Sxx = sum(x**2/sigma**2)
    Sxy = sum(x*y/sigma**2)
    # Delta = S*Sxx - Sx**2
    # a = (Sxx*Sy - Sx*Sxy)/Delta
    # b = (S*Sxy - Sx*Sy)/Delta
    # sa2 = Sxx/Delta
    # sb2 = S/Delta
    # sab = -Sx/Delta
    # rab = -Sx/sqrt(S*Sxx)
    t = (x-Sx/S)/sigma
    Stt = sum(t**2)
    b = sum(t*y/sigma)/Stt
    a = (Sy-Sx*b)/S
    sa2 = (1+Sx**2/(S*Stt))/S
    sb2 = 1/Stt
    sab = -Sx/(S*Stt)
    rab = sab/sqrt(sa2*sb2)
    chisq = sum(((y-a-b*x)/sigma)**2)
    df = len(x)-2
    Q = scipy.stats.chi2.sf(chisq,df)
    return namedtuple('LinFit','coeffs cov rab chisq df Q')(asarray([b,a]),asarray([[sb2,sab],[sab,sa2]]),rab,chisq,df,Q)

# Peak analyzer carries out Keeling plot analysis of peaks found by the isotopic methane
#  analyzer

class PeakAnalyzer(object):

    @staticmethod
    def getDisposition(cancelled, delta, uncertainty, tooFewPoints):
        disposition = 'COMPLETE'

        if cancelled:
            disposition = 'USER_CANCELLATION'

        elif tooFewPoints:
            disposition = 'SAMPLE_SIZE_TOO_SMALL'

        elif uncertainty >= UNCERTAINTY_HIGH_THRESHOLD:
            disposition = 'UNCERTAINTY_OOR'

        elif delta <= DELTA_NEGATIVE_THRESHOLD or \
            delta >= DELTA_POSITIVE_THRESHOLD:
            disposition = 'DELTA_OOR'

        return DISPOSITIONS.index(disposition)

    @staticmethod
    def valveIsCollecting(state):
        rounded = round(state)
        roundedErr = abs(state - rounded)

        return roundedErr < VALVE_STATE_EPSILON and (int(rounded) & 0x01) > 0

    @staticmethod
    def valveIsCancelling(state):
        rounded = round(state)
        roundedErr = abs(state - rounded)

        return roundedErr < VALVE_STATE_EPSILON and (int(rounded) & 0x10) > 0


    def __init__(self, *args, **kwargs):

        if 'legacyValveStop' in kwargs:
            self.legacyValveStop = kwargs['legacyValveStop']
        else:
            self.legacyValveStop = time.mktime(
                time.strptime('Fri Sep 27 23:59:59 2013'))

        if 'analyzerId' in kwargs:
            self.analyzerId = kwargs['analyzerId']
        else:
            self.analyzerId = "ZZZ"

        if 'appDir' in kwargs:
            self.appDir = kwargs['appDir']
        else:
            if hasattr(sys, "frozen"): #we're running compiled with py2exe
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
        #if not self.ticket_url:
        #    self.ticket_url = 'https://dev.picarro.com/node/gdu/abcdefg/1/AnzLog/'

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

        self.sleep_seconds = None
        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds']:
                self.sleep_seconds = float(kwargs['sleep_seconds'])
        if self.sleep_seconds == None:
            self.sleep_seconds = 10.0

        self.timeout = None
        if 'timeout' in kwargs:
            if kwargs['timeout']:
                self.timeout = int(kwargs['timeout'])
        if self.timeout == None:
            self.timeout = 5

        self.debug = None
        if 'debug' in kwargs:
            self.debug = kwargs['debug']


        self.samples_to_skip = None
        if 'samples_to_skip' in kwargs:
            if kwargs['samples_to_skip']:
                self.samples_to_skip = int(kwargs['samples_to_skip'])
        if self.samples_to_skip == None:
            self.samples_to_skip = 8

        self.logtype = "analysis"
        self.last_peakname = None
        self.sockettimeout = 10
    #######################################################################
    # Generators for getting data from files or the database
    #######################################################################
    def sourceFromFile(self,fname):
        # Generate lines from a specified user log file. Raise StopIteration at end of the file
        fp = file(fname,'rb')
        while True:
            line = fp.readline()
            if line: yield line
            else: break

    def followLastUserFile(self,fname):
        # Generate lines from the live (last) user log file. If we reach the end of the file,
        #  wait for a new line to become available, and periodically check to see if
        #  we are still the latest file. Raise StopIteration if a new file has become
        #  the live file.
        fp = file(fname,'rb')
        print "\r\nOpening source stream %s\r\n" % fname
        line = ""
        counter = 0
        while True:
            line += fp.readline()
            # Note that if the file ends with an incomplete line, fp.readline() will return a
            #  string with no terminating newline. We must NOT yield this incomplete line to
            #  avoid causing problems at the higher levels.
            if not line:
                counter += 1
                if counter == 10:
                    try:
                        if fname == os.path.join(self.file_path):
                            fp.close()
                            print "\r\nClosing source stream %s\r\n" % self.fname
                            return

                        lastName = genLatestFiles(*os.path.split(self.userlogfiles)).next()
                        # Stop iteration if we are not the last file
                        if fname != lastName:
                            fp.close()
                            print "\r\nClosing source stream\r\n"
                            return
                    except:
                        pass
                    counter = 0
                time.sleep(0.1)
                if self.debug: sys.stderr.write('-')
                continue
            if self.debug: sys.stderr.write('.')
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
                #params = {"alog": lastlog, "startPos": lastPos, "limit": 20}
                #postparms = {'data': json.dumps(params)}
                #getAnalyzerDatLogUrl = self.url.replace("getData", "getAnalyzerDatLog")
                try:
                    rtn_data = None

                    qry_with_ticket = '%s?qry=byPos&alog=%s&startPos=%s&limit=2000' % (self.anzlog_url.replace("<TICKET>", self.ticket), lastlog, lastPos)
                    if self.debug == True:
                        print "qry_with_ticket", qry_with_ticket

                    socket.setdefaulttimeout(self.sockettimeout)
                    resp = urllib2.urlopen(qry_with_ticket)
                    #resp = urllib2.urlopen(getAnalyzerDatLogUrl, data=urllib.urlencode(postparms))
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
                            print 'EXCEPTION in PeakFinder - followLastUserLogDb().\n%s\n' % err_str
                        pass

                except Exception, e:
                    print '\nfollowLastUserLogDb failed \n%s\n' % e
                    time.sleep(1)
                    continue

                if (rtn_data):
                    rslt = json.loads(rtn_data)
                    #print "followLastUserLogDb rslt: ", rslt
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
                qry_with_ticket = '%s?qry=byEpoch&anz=%s&startEtm=%s&limit=1&reverse=true' % (self.meta_url.replace("<TICKET>", self.ticket), self.analyzerId, self.lastEtm)
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
                        print 'EXCEPTION in PeakFinder - getLastLog().\n%s\n' % err_str
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

    def pushData(self, peakname, doc_data):
        err_rtn_str = 'ERROR: missing data:'
        rtn = "OK"
        if doc_data:
            # we want to replace (which removed old data for the log)
            # when we have a new log
            # but only for the very first push
            replace_log = "False"
            if not self.last_peakname == peakname:
                print "I should be doing a replace now"
                replace_log = "True"
                self.last_peakname = peakname
            params = [{"logname": peakname, "replace": replace_log, "logtype": self.logtype, "logdata": doc_data}]
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
    # Process data from log into a source consisting of distances between
    #  points followed by a DataTuple with the actual data
    #######################################################################

    def analyzerDataDb(self,source):
        # Generates data from a minimal archive in the database as a stream consisting
        #  of tuples (dist,DataTuple(<data from source>)). Yields (None,None) if there is a
        #  jump of more than JUMP_MAX meters between adjacent points
        JUMP_MAX = 500.0
        dist = None
        lat_ref, lng_ref = None, None
        DataTuple = None
        x0, y0 = 0, 0
        # Determine if there are extra data in the file
        for line in source:
            try:
                entry = {}
                if DataTuple is None:
                    DataTuple = namedtuple("DataTuple",["DISTANCE"] + line.keys())
                for  h in line.keys():
                    #if h not in ["_id", "ANALYZER", "SERVER_HASH"]:
                    try:
                        entry[h] = float(line[h])
                    except:
                        entry[h] = NaN

                lng, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]
                if "GPS_FIT" in entry and entry["GPS_FIT"] < 1:
                    if (lng != 0.0) or (lat != 0.0): continue
                if isnan(lng) or isnan(lat): continue
                if lat_ref == None or lng_ref == None:
                    lat_ref, lng_ref = lat, lng
                x,y = toXY(lat,lng,lat_ref,lng_ref)
                if dist is None:
                    jump = 0.0
                    dist = 0.0
                else:
                    jump = sqrt((x-x0)*(x-x0) + (y-y0)*(y-y0))
                x0, y0 = x, y
                if jump < JUMP_MAX:
                    dist += jump
                    if self.debug == True:
                        print "\ndist: ", dist
                        print "\nentry: ", entry
                    yield DataTuple(dist,**entry)
                else:
                    lat_ref, lng_ref = None, None
            except:
                print traceback.format_exc()

    def analyzerData(self,source):
        # Generates data from a minimal log file as a stream consisting
        #  of tuples DataTuple(dist,**<data from source>). Yields None if there is a
        #  jump of more than JUMP_MAX meters between adjacent points
        JUMP_MAX = 500.0
        dist = None
        lat_ref, lng_ref = None, None
        line = source.next()
        atoms = line.split()
        headings = [a.replace(" ","_") for a in atoms]
        DataTuple = namedtuple("DataTuple",["DISTANCE"] + headings)
        x0, y0 = 0, 0
        for line in source:
            try:
                entry = {}
                atoms = line.split()
                if not headings:
                    headings = [a.replace(" ","_") for a in atoms]
                else:
                    for h,a in zip(headings,atoms):
                        try:
                            entry[h] = float(a)
                        except:
                            entry[h] = NaN
                    lng, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]
                    if "GPS_FIT" in entry and entry["GPS_FIT"] < 1:
                        if (lng != 0.0) or (lat != 0.0): continue
                    if isnan(lng) or isnan(lat): continue
                    if lat_ref == None or lng_ref == None:
                        lat_ref, lng_ref = lat, lng
                    x,y = toXY(lat,lng,lat_ref,lng_ref)
                    if dist is None:
                        jump = 0.0
                        dist = 0.0
                    else:
                        jump = sqrt((x-x0)*(x-x0) + (y-y0)*(y-y0))
                    x0, y0 = x, y
                    if jump < JUMP_MAX:
                        dist += jump
                        yield DataTuple(dist,**entry)
                    else:
                        lat_ref, lng_ref = None, None
            except:
                print traceback.format_exc()
                raise

    #######################################################################
    # Perform analysis to determine the isotopic ratio
    #######################################################################

    def doKeelingAnalysis(self, source):
        """
        Keep a buffer of recent concentrations within a certain time
        duration of the present. When the valve mask switches to the
        value indicating that the recorder has been activated, search
        the buffer for the peak value and the associated time and GPS
        location.  Perform a Keeling analysis of the data during the
        interval that the recorder is being played back
        """

        MAX_DURATION = 30

        tempStore = deque()
        delayBuff = deque()
        keelingStore = []

        transportLag = 5
        notCollectingCount = 0
        doneAnalysisThreshold = 5
        endpointBufferOffset = 2

        lastAnalysis = None
        lastPeak = None
        lastCollecting = False
        cancelled = False
        tooFewPoints = False

        for dtuple in source:
            # Previously it was possible for None tuples to be
            # returned, but that functionality has been removed.
            assert dtuple is not None

            # Swallow data if there is no delta.
            if 'HP_Delta_iCH4_Raw' not in dtuple._fields:
                continue

            if dtuple.EPOCH_TIME > self.legacyValveStop and \
                PeakAnalyzer.valveIsCancelling(dtuple.ValveMask):
                cancelled = True

            collectingNow = PeakAnalyzer.valveIsCollecting(dtuple.ValveMask)

            if collectingNow:
                cancelled = False

            # Delay collecting now by a number of samples to
            # compensate for gas transport lag after valve switch.
            delayBuff.append(collectingNow)
            if len(delayBuff) >= transportLag:
                collectingNow = delayBuff.popleft()

            # An analysis is done (cancelled or completed) if we are
            # not in the collecting state for doneAnalysisThreshold
            # samples and there is some Keeling data to report.
            if (notCollectingCount > doneAnalysisThreshold) and \
                (lastAnalysis is not None):
                disp = PeakAnalyzer.getDisposition(cancelled,
                                                   lastAnalysis['delta'],
                                                   lastAnalysis['uncertainty'],
                                                   tooFewPoints)
                yield PeakData(disposition=disp, **lastAnalysis)

                lastAnalysis = None
                cancelled = False
                tooFewPoints = False

            if not collectingNow:
                notCollectingCount += 1
                tempStore.append(dtuple)

                while (tempStore[-1].EPOCH_TIME - tempStore[0].EPOCH_TIME) > MAX_DURATION:
                    tempStore.popleft()

                if lastCollecting:
                    if len(keelingStore) > 10 + self.samples_to_skip:
                        conc = asarray([s.CH4 for s in keelingStore])[self.samples_to_skip:-(doneAnalysisThreshold + endpointBufferOffset)]
                        delta = asarray([s.HP_Delta_iCH4_Raw for s in keelingStore])[self.samples_to_skip:-(doneAnalysisThreshold + endpointBufferOffset)]
                        protInvconc = 1/maximum(conc,0.001)
                        try:
                            replay_max = max(conc)
                        except:
                            replay_max = 0
                        m = argmax(conc)
                        try:
                            replay_lmin = min(conc[:m])
                        except:
                            replay_lmin = 0
                        try:
                            replay_rmin = min(conc[m:])
                        except:
                            replay_rmin = 0

                        result = linfit(protInvconc,delta,11.0*protInvconc)

                        if lastPeak:
                            lastAnalysis = dict(
                                delta=result.coeffs[1],
                                uncertainty=sqrt(result.cov[1][1]),
                                replay_max=replay_max,
                                replay_lmin=replay_lmin,
                                replay_rmin=replay_rmin,
                                **lastPeak._asdict())
                            lastPeak = None

                    else:
                        tooFewPoints = True
                        if lastPeak:
                            lastAnalysis = dict(
                                delta=0.0,
                                uncertainty=0.0,
                                replay_max=0.0,
                                replay_lmin=0.0,
                                replay_rmin=0.0,
                                **lastPeak._asdict())
                            lastPeak = None

                    del keelingStore[:]
            else:
                notCollectingCount = 0

                if dtuple.CH4 <= CONCENTRATION_HIGH_THRESHOLD:
                    # Exclude data points where the concentration is above
                    # the analyzer specification.
                    keelingStore.append(dtuple)

                if not lastCollecting:
                    if tempStore:
                        # We have just started collecting
                        print "Started collecting"
                        conc = asarray([s.CH4 for s in tempStore])
                        dist = asarray([s.DISTANCE for s in tempStore])
                        epoch_time = asarray([s.EPOCH_TIME for s in tempStore])
                        lat  = asarray([s.GPS_ABS_LAT  for s in tempStore])
                        lng = asarray([s.GPS_ABS_LONG for s in tempStore])
                        pk = conc.argmax()
                        lastPeak = namedtuple('PeakData1','time dist lng lat conc')(epoch_time[pk],dist[pk],lng[pk],lat[pk],conc[pk])
                        tempStore.clear()
            lastCollecting = collectingNow

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
            self.ticket = ticket;
            print "new ticket: ", self.ticket


    def run(self):
        # Assemble the chain of generators which process the data from the logs in a file or in the database
        print "PeakAnalyzer.run()"

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

                ##sys.exit()
            else:
                try:
                    if self.file_path:
                        fname = os.path.join(self.file_path)
                    else:
                        print "self.userlogfiles = '%s'" % self.userlogfiles
                        print "self.userlogfiles (abs) = '%s'" % os.path.abspath(self.userlogfiles)
                        fname = genLatestFiles(*os.path.split(self.userlogfiles)).next()
                except:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                # Initialize output structure for writing to database or to analysis file
                if self.usedb:
                    peakname = fname.replace(".dat", ".%s" % self.logtype)
                    doc_hdrs = OUTPUT_COLUMNS
                    doc_data = []
                    doc_row = 0
                else:
                    analysisFile = os.path.splitext(fname)[0] + '.analysis'
                    try:
                        handle = open(analysisFile, 'wb+', 0) #open file with NO buffering
                    except:
                        raise RuntimeError('Cannot open analysis output file %s' % analysisFile)
                    # Write file header
                    handle.write("%-14s" * len(OUTPUT_COLUMNS) %
                                 tuple(OUTPUT_COLUMNS))
                    handle.write("\n")

                # Make alignedData source from database or specified file
                if self.usedb:
                    source = self.followLastUserLogDb()
                    alignedData = self.analyzerDataDb(source)
                else:
                    if self.file_path:
                        source = self.sourceFromFile(fname)
                    else:
                        source = self.followLastUserFile(fname)
                    alignedData = self.analyzerData(source)

                # Process the aligned data and write results to database or to the analysis file
                for r in self.doKeelingAnalysis(alignedData):
                    if self.usedb:
                        doc = {}
                        #Note: please assure that value list and doc_hdrs are in the same sequence
                        dataPairs = zip(doc_hdrs,
                                        [r.time,
                                         r.dist,
                                         r.lng,
                                         r.lat,
                                         r.conc,
                                         r.delta,
                                         r.uncertainty,
                                         r.replay_max,
                                         r.replay_lmin,
                                         r.replay_rmin,
                                         r.disposition])

                        for col, val in dataPairs:
                            doc[col] = float(val)

                            # JSON does not support nan, so change to string "NaN"
                            # The server will handle appropriately
                            try:
                                if math.isnan(doc[col]):
                                    doc[col] = "NaN"
                            except:
                                #just skip on isnan error
                                skip = 1

                        doc_row += 1
                        doc["row"] = doc_row
                        doc["ANALYZER"] = self.analyzerId
                        doc_data.append(doc)

                        self.pushData(peakname, doc_data)
                        doc_data = []
                    else:
                        handle.write("%-14.2f%-14.3f%-14.6f%-14.6f%-14.3f"
                                     "%-14.2f%-14.2f%-14.3f%-14.3f%-14.3f"
                                     "%-14.1f\n" % (r.time, r.dist, r.lng,
                                                    r.lat, r.conc, r.delta,
                                                    r.uncertainty, r.replay_max,
                                                    r.replay_lmin, r.replay_rmin,
                                                    r.disposition))

                if not self.usedb and handle is not None:
                    handle.close()

                if self.logname:
                    break

                if self.file_path: break

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
                      help="timeout value for response from server.", metavar="<TIMEOUT>")
    parser.add_option("-u", "--anzlog-url", dest="anzlog_url",
                      help="rest url for AnzLog Resource. Use the string <TICKET> as the place-holder for the authentication ticket.", metavar="<LOG_URL>")
    parser.add_option("-m", "--meta-url", dest="meta_url",
                      help="rest url for AnzLogMeta Resource. Use the string <TICKET> as the place-holder for the authentication ticket.", metavar="<META_URL>")
    parser.add_option("-k", "--ticket-url", dest="ticket_url",
                      help="rest url for authentication ticket. Use the string 'dummy' as the place-holder for the authentication ticket.",  metavar="<TICKET_URL>")
    parser.add_option("-y", "--identity", dest="identity",
                      help="Authentication identity string.", metavar="<IDENTITY>")
    parser.add_option("-s", "--sys", dest="psys",
                      help="Authentication sys.", metavar="<SYS>")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="Debug mode")
    parser.add_option("--calc-samples_to_skip", dest="samples_to_skip",
                      help="Default calc value for samples_to_skip.", metavar="<CALC_samples_to_skip>")
    parser.add_option('--legacy-valve-stop', dest='legacyValveStop',
                      metavar='LEGACY_VALVE_STOP', type='float',
                      default=time.mktime(time.strptime('Fri Sep 27 23:59:59 2013')),
                      help=('The time at which to start interpreting the valve '
                            'masks and values as supporting the user '
                            'cancellation bit.'))

    (options, args) = parser.parse_args()

    # if not options.pid_path:
    #     parser.error("pid-path is required")

    if not options.analyzerId:
        if not options.logname:
            if not options.file_path:
                parser.error("One of analyzer, or logname, or file_path is required.")

    if options.listen_path and options.file_path:
        parser.error("listen-path and file-path are mutually exclusive.")

    if ((options.listen_path or options.file_path) and options.anzlog_url):
        parser.error("anzlog_url is mutually exclusive to listen-path and/or file-path.")

    if (options.logname or options.anzlog_url or options.meta_url or options.ticket_url or options.identity or options.psys):
        if not options.anzlog_url:
            parser.error("AnzLog Resource URL is required when other REST url's are provided.")
        if not options.meta_url:
            parser.error("AnzLogMeta Resource URL is required when other REST url's are provided.")
        if not options.ticket_url:
            parser.error("Authentication ticket Resource URL is required when other REST url's are provided.")
        if not options.identity:
            parser.error("Authentication identity string is required when other REST url's are provided.")
        if not options.psys:
            parser.error("Authentication sys name is required when other REST url's are provided.")

    class_opts = {}

    for copt in [
                 "pid_path"         #path for PID file
                 , "analyzerId"     #Analyzer ID
                 , "anzlog_url"     #URL for AnzLog resource
                 , "meta_url"       #URL for AnzLogMeta resource
                 , "ticket_url"     #URL for Admin (issueTicket) resource
                 , "logname"        #logname (when processing single log)
                 , "identity"       #identity (authentication)
                 , "psys"           #picarro sys (authentication)
                 , "usedb"          #True/False use REST DB calls (instead of file system)
                 , "listen_path"    #listen path (when processing file system)
                 , "file_path"      #file path (when procesing single log from file system)
                 , "samples_to_skip" #override default samples_to_skip value
                 , "sleep_seconds"  #override default sleep_seconds value
                 , "timeout"        #override default REST timeout value
                 , "debug"          #True/False show debug print (in stdout)
                 , 'legacyValveStop'
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

    if options.pid_path:
        try:
            testf = open(class_opts["pid_path"], 'r')
            testf.close()
            raise RuntimeError('pidfile exists. Verify that there is not another PeakAnalyzer task for the directory. path: %s.' % class_opts["pid_path"])
        except:
            try:
                pidf = open(class_opts["pid_path"], 'wb+', 0) #open file with NO buffering
            except:
                raise RuntimeError('Cannot open pidfile for output. path: %s.' % class_opts["pid_path"])

        pid = os.getpid()
        pidf.write("%s" % (pid))
        pidf.close()

    pf = PeakAnalyzer(**class_opts)

    pf.run()
    os.remove(class_opts["pid_path"])


if __name__ == "__main__":
    sys.exit(main())
