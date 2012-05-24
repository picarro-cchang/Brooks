from collections import deque
import fnmatch
import itertools
from numpy import *
import scipy.stats
import os
import sys
import time
import traceback
from namedtuple import namedtuple

import urllib2
import urllib
import socket
try:
    import simplejson as json
except:
    import json

NaN = 1e1000/1e1000

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
            if hasattr(sys, "frozen"): #we're running compiled with py2exe
                AppPath = sys.executable
            else:
                AppPath = sys.argv[0]
            self.AppDir = os.path.split(AppPath)[0]

        if 'userlogfiles' in kwargs:
            self.userlogfiles = kwargs['userlogfiles']
        else:
            self.userlogfiles = '/data/mdudata/datalogAdd/*.dat'

        if 'sleep_seconds' in kwargs:
            self.sleep_seconds = float(kwargs['sleep_seconds'])
        else:
            self.sleep_seconds = 30.0
            
        if 'url' in kwargs:
            self.url = kwargs['url']
        else:
            self.url = 'http://p3.picarro.com/pcubed/rest/getData/'

        if 'timeout' in kwargs:
            self.timeout = int(kwargs['timeout'])
        else:
            self.timeout = 5

        if 'sleep_seconds' in kwargs:
            self.sleep_seconds = float(kwargs['sleep_seconds'])
        else:
            self.sleep_seconds = 30.0

        if 'usedb' in kwargs:
            self.usedb = kwargs['usedb']
        else:
            self.usedb = None
            
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
            
        self.noWait = 'nowait' in kwargs

        if 'samples_to_skip' in kwargs:
            self.samples_to_skip = int(kwargs['samples_to_skip'])
        else:
            self.samples_to_skip = 8
        
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
        counter = 0
        while True:
            line = fp.readline()
            if not line:
                counter += 1
                if counter == 10:
                    try:
                        # Get last file
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
            yield line

    def followLastUserLogDb(self):
        aname = self.analyzerId
        lastlog = self.getLastLog()  
        if lastlog:
            lastPos = 0
            while True:
                params = {"alog": lastlog, "startPos": lastPos, "limit": 20}
                postparms = {'data': json.dumps(params)}
                getAnalyzerDatLogUrl = self.url.replace("getData", "getAnalyzerDatLog")
                try:
                    socket.setdefaulttimeout(self.timeout)
                    resp = urllib2.urlopen(getAnalyzerDatLogUrl, data=urllib.urlencode(postparms))
                    rtn_data = resp.read()
                except:
                    time.sleep(1)
                    continue
                rslt = json.loads(rtn_data)
                if "result" in rslt:
                    if "data" in rslt["result"]:
                        dbdata = rslt["result"]["data"]
                        if len(dbdata) > 0:
                            for doc in dbdata:
                                if "row" in doc:
                                    lastPos = int(doc["row"]) + 1
                                yield doc
                        else:
                            time.sleep(5)
                            newlastlog = self.getLastLog()
                            if not lastlog == newlastlog:
                                print "\r\nClosing log stream\r\n"
                                return
                    else:
                        time.sleep(5)
                        newlastlog = self.getLastLog()
                        if not lastlog == newlastlog:
                            print "\r\nClosing log stream\r\n"
                            return
                    time.sleep(1)
                else:
                    time.sleep(5)
                    newlastlog = self.getLastLog()
                    if not lastlog == newlastlog:
                        print "\r\nClosing log stream\r\n"
                        return

    def getLastLog(self):
        # Get the name of the live (last) log file from the database
        aname = self.analyzerId
        lastlog = None
        params = {"analyzer": aname}
        postparms = {'data': json.dumps(params)}
        getLastLogUrl = self.url.replace("getData", "getLastLog")
        while True:
            try:
                socket.setdefaulttimeout(self.timeout)
                resp = urllib2.urlopen(getLastLogUrl, data=urllib.urlencode(postparms))
                rtn_data = resp.read()
            except:
                time.sleep(2)
                continue
            rslt = json.loads(rtn_data)
            if "result" in rslt:
                if "lastLog" in rslt["result"]:
                    lastlog = rslt["result"]["lastLog"]
            return lastlog

    #######################################################################
    # Perform REST call to push analysis data to the database
    #######################################################################

    def pushData(self, peakname, doc_data):
        err_rtn_str = 'ERROR: missing data:'
        rtn = "OK"
        if doc_data: 
            params = {peakname: doc_data}
        else:    
            params = {peakname: []}
        postparms = {'data': json.dumps(params)}
        dataPeakAddUrl = self.url.replace("getData", "gdu/dataAnalysisAdd")
        
        tctr = 0
        while True:
            try:
                # NOTE: socket only required to set timeout parameter for the urlopen()
                # In Python26 and beyond we can use the timeout parameter in the urlopen()
                socket.setdefaulttimeout(self.timeout)
                resp = urllib2.urlopen(dataPeakAddUrl, data=urllib.urlencode(postparms))
                rtn_data = resp.read()
                print rtn_data
                if err_rtn_str in rtn_data:
                    rslt = json.loads(rtn_data)
                    expect_ctr = rslt['result'].replace(err_rtn_str, "").strip()
                    break
                else:
                    break
            except Exception, e:
                print '\n%s\n' % e
                pass
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
        # Determine if there are extra data in the file
        for line in source:
            try:
                entry = {}
                if DataTuple is None:
                    DataTuple = namedtuple("DataTuple",line.keys())
                for  h in line.keys():
                    try:
                        entry[h] = float(line[h])
                    except:
                        entry[h] = NaN
                lng, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]
                if lat_ref == None or lng_ref == None:
                    lng_ref, lat_ref = lat, lng
                x,y = toXY(lat,lng,lat_ref,lng_ref)
                if dist is None:
                    jump = 0.0
                    dist = 0.0
                else:
                    jump = sqrt((x-x0)*(x-x0) + (y-y0)*(y-y0))
                    dist += jump
                x0, y0 = x, y
                if jump < JUMP_MAX:
                    yield dist,DataTuple(**entry)
                else:
                    yield None,None    # Indicate that dist is bad, and we must restart
                    dist = None
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
                    if lat_ref == None or lng_ref == None:
                        lng_ref, lat_ref = lat, lng
                    x,y = toXY(lat,lng,lat_ref,lng_ref)
                    if dist is None:
                        jump = 0.0
                        dist = 0.0
                    else:
                        jump = sqrt((x-x0)*(x-x0) + (y-y0)*(y-y0))
                        dist += jump
                    x0, y0 = x, y
                    if jump < JUMP_MAX:
                        yield DataTuple(dist,**entry)
                        # yield dist,SourceData(lng,lat,entry['EPOCH_TIME'],entry['ValveMask'],entry['CH4'],entry['HP_Delta_iCH4_Raw'])
                    else:
                        yield None      # Indicate that dist are bad, and we must restart
                        dist = None
                        lat_ref, lng_ref = None, None
            except:
                print traceback.format_exc()
                        
    #######################################################################
    # Perform analysis to determine the isotopic ratio
    #######################################################################

    def doKeelingAnalysis(self,source):
        """Keep a buffer of recent concentrations within a certain time duration of the present. When the valve mask switches to the value
        indicating that the recorder has been activated, search the buffer for the peak value and the associated time and GPS location.
        Perform a Keeling analysis of the data during the interval that the recorder is being played back"""
        
        MAX_DURATION = 30
        collecting = lambda v: abs(v - round(v))<1e-4 and (int(round(v)) & 1) == 1
        tempStore = deque()
        keelingStore = []
        lastPeak = None
        lastCollecting = False
        
        for dtuple in source:
            if dtuple is None: continue
            if 'HP_Delta_iCH4_Raw' not in dtuple._fields: break # Abort if there are no data
            collectingNow = collecting(dtuple.ValveMask)
            if not collectingNow:
                tempStore.append(dtuple)
                while tempStore[-1].EPOCH_TIME - tempStore[0].EPOCH_TIME > MAX_DURATION:
                    tempStore.popleft()
                if lastCollecting:  # Check to see if there are data for a Keeling plot
                    if len(keelingStore) > 10+self.samples_to_skip:
                        conc = asarray([s.CH4 for s in keelingStore])[self.samples_to_skip:]
                        delta = asarray([s.HP_Delta_iCH4_Raw for s in keelingStore])[self.samples_to_skip:]
                        protInvconc = 1/maximum(conc,0.001)
                        #print "Keeling plot data"
                        #for s in keelingStore:
                        #    print s.sourceData.conc, s.sourceData.delta, s.sourceData.valves
                        #print "-----------------"
                        result = linfit(protInvconc,delta,11.0*protInvconc)
                        if lastPeak:
                            yield namedtuple('PeakData','time dist lng lat conc delta uncertainty')(delta=result.coeffs[1],
                                        uncertainty=sqrt(result.cov[1][1]),**lastPeak._asdict())
                    del keelingStore[:]
            else:
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
                        
    def run(self):
        # Assemble the chain of generators which process the data from the logs in a file or in the database 
        handle = None
        while True:
            # Get source
            if self.usedb:
                lastlog = self.getLastLog()  
                if lastlog:
                    fname = lastlog
                else:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds
            else:
                try:
                    fname = genLatestFiles(*os.path.split(self.userlogfiles)).next()
                except:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                # Initialize output structure for writing to database or to analysis file
                if self.usedb:
                    peakname = fname.replace(".dat", ".peaks")
                    doc_hdrs = ["EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CONC","DELTA","UNCERTAINTY"]
                    doc_data = []
                    doc_row = 0
                else:
                    analysisFile = os.path.splitext(fname)[0] + '.analysis'
                    try:
                        handle = open(analysisFile, 'wb+', 0) #open file with NO buffering
                    except:
                        raise RuntimeError('Cannot open analysis output file %s' % analysisFile)
                    # Write file header
                    handle.write("%-14s%-14s%-14s%-14s%-14s%-14s%-14s\r\n" % ("EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CONC","DELTA","UNCERTAINTY"))
 
                # Make alignedData source from database or specified file
                if self.usedb:
                    source = self.followLastUserLogDb()
                    alignedData = self.analyzerDataDb(source)
                else:
                    if self.noWait:
                        source = self.sourceFromFile(fname)
                    else:
                        source = self.followLastUserFile(fname)
                    alignedData = self.analyzerData(source)
                
                # Process the aligned data and write results to database or to the analysis file
                for r in self.doKeelingAnalysis(alignedData):
                    if self.usedb:
                        doc = {}
                        #Note: please assure that value list and doc_hdrs are in the same sequence
                        for col, val in zip(doc_hdrs, [r.time,r.dist,r.lng,r.lat,r.conc,r.delta,r.uncertainty]):
                            doc[col] = float(val)
                        doc_row += 1
                        doc["row"] = doc_row 
                        doc["ANALYZER"] = self.analyzerId
                        doc_data.append(doc)
                            
                        self.pushData(peakname, doc_data)
                        doc_data = []
                    else:
                        handle.write("%-14.2f%-14.3f%-14.6f%-14.6f%-14.3f%-14.2f%-14.2f\r\n" % (r.time,r.dist,r.lng,r.lat,r.conc,r.delta,r.uncertainty))
                    
                if not self.usedb and handle is not None:
                    handle.close()

                if self.noWait: break

if __name__ == "__main__":

    '''
    if hasattr(sys, "frozen"): #we're running compiled with py2exe
        AppPath = sys.executable
    else:
        AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    USERLOGFILES = os.path.join(AppDir,'static/datalog/*.dat')
    ANALYSISFILES = os.path.join(AppDir,'static/datalog/*.analysis')
    '''

    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    if 1 < len(sys.argv):
        analyzer = sys.argv[1]
    else:
        analyzer = 'ZZZ'
        
    if 2 < len(sys.argv):
        url=sys.argv[2]
    else:
        #url='http://p3.picarro.com/pcubed/rest/getData/'
        url = 'http://10.100.2.97:8080/rest/getData/'
        #url = 'http://192.168.2.104:8080/rest/getData/'
        #url = 'http://10.0.1.13:8080/rest/getData/'
        
    if 3 < len(sys.argv):
        debug = sys.argv[3]
    else:
        debug = None
    
    #data_dir = os.path.join('/data/mdudata/datalogAdd', analyzer) # P3 Server data location
    data_dir = 'C:/UserData/AnalyzerServer' # local Analyzer data location
    pidpath = os.path.join(data_dir, 'peakAnalyzerMain.pid')
    
    try:
        testf = open(pidpath, 'r')
        raise RuntimeError('pidfile exists. Verify that there is not another peakAnalyzerMain task for the directory. path: %s.' % data_dir)
    except:
        try:
            pidf = open(pidpath, 'wb+', 0) #open file with NO buffering
        except:
            raise RuntimeError('Cannot open pidfile for output. path: %s.' % pidpath)
    
    pid = os.getpid()
    pidf.write("%s" % (pid))
    pidf.close()
    
    ulog = os.path.join(data_dir, '*.dat')
    
    pf = PeakAnalyzer()
    pf.analyzerId = analyzer
    pf.userlogfiles = ulog
    pf.url = url
    pf.debug = debug
    pf.usedb = False
    
    pf.run()
    
    os.remove(pidpath)
    