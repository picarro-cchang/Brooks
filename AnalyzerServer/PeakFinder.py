from collections import deque
import fnmatch
import itertools
from numpy import *
import os
import sys
from optparse import OptionParser
import time
import datetime
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
# Generator-based linear interpolation
#######################################################################

def interpolator(source,interval):
    """
    Perform linear interpolation of the data in source at specified interval, where the 
    source generates data of the form
        (x,(d1,d2,d3,...))
    The data are re-gridded on equally spaced intervals starting with the multiple of
    "interval" which is no less than x.
    >>> src = (x for x in [(0,(2,)),(1,(3,)),(2,(5,)),(4,(9,))])
    >>> for t,d in interpolator(src,0.5): print t,d[0]
    0.0 2
    0.5 2.5
    1.0 3.0
    1.5 4.0
    2.0 5.0
    2.5 6.0
    3.0 7.0
    3.5 8.0
    4.0 9.0
    
    Next we test the situation in which the first interpolation point does not coincide
    with the start of the data array
    >>> src = (x for x in [(0.25,(2,)),(2.25,(4,))])
    >>> for t,d in interpolator(src,0.5): print t,d[0]
    0.5 2.25
    1.0 2.75
    1.5 3.25
    2.0 3.75
    """
    xi = None
    x_p, d_p = None, None
    for datum in source:
        x,d = datum
        if (x is None) or (d is None): # Indicates problem with data, re-initialize
            yield None, None
            xi = None
            x_p, d_p = None, None
            continue
        if xi is None:
            mult = ceil(x/interval)
            xi = interval*mult
        di = d
        while xi<=x:
            if x_p is not None:
                if x != x_p:
                    alpha = (xi-x_p)/(x-x_p)
                    di = d._make([alpha*y+(1-alpha)*y_p for y,y_p in zip(d,d_p)])
            yield xi, di
            mult += 1
            xi = interval*mult
        x_p, d_p = x, d
    
# Peak finder carries out space-scale analysis to find peaks in methane
#  concentration associated with leaks
class PeakFinder(object):
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
        #self.userlogfiles = '/data/mdudata/datalogAdd/*.dat'

        self.file_path = None
        if 'file_path' in kwargs:
            self.file_path = kwargs['file_path']

        if 'dx' in kwargs:
            self.dx = float(kwargs['dx'])
        else:
            self.dx = 0.5
    
        if 'sigmaMinFactor' in kwargs:
            sigmaMinFactor = float(kwargs['sigmaMinFactor'])
        else:
            sigmaMinFactor = 2.0
    
        self.sigmaMin = sigmaMinFactor*self.dx
    
        if 'sigmaMaxFactor' in kwargs:
            sigmaMaxFactor = float(kwargs['sigmaMaxFactor'])
        else:
            sigmaMaxFactor = 40.0
            
        self.sigmaMax = sigmaMaxFactor*self.dx   # Widest peak to be detected

        if 'minAmpl' in kwargs:
            self.minAmpl = float(kwargs['minAmpl'])
        else:
            self.minAmpl = 0.01
    
        if 'factor' in kwargs:
            self.factor = float(kwargs['factor'])
        else:
            self.factor = 1.1

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

        self.debug = None
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
            
        self.noWait = 'nowait' in kwargs
        self.logtype = "peaks"
        
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
        counter = 0
        while True:
            line = fp.readline()
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
            yield line

    def followLastUserLogDb(self):
        aname = self.analyzerId
        if self.logname:
            lastlog = self.logname
        else:
            lastlog = self.getLastLog()
            
        if lastlog:
            lastPos = 0
            rtn_data = None
            
            tctr = 0
            waitForRetryCtr = 0
            waitForRetry = True
            while True:
                #params = {"alog": lastlog, "startPos": lastPos, "limit": 20}
                #postparms = {'data': json.dumps(params)}
                #getAnalyzerDatLogUrl = self.url.replace("getData", "getAnalyzerDatLog")
                try:
                    qry_with_ticket = '%s?qry=byPos&alog=%s&startPos=%s&limit=20' % (self.anzlog_url.replace("<TICKET>", self.ticket), lastlog, lastPos)
                    if self.debug == True:
                        print "qry_with_ticket", qry_with_ticket
                
                    socket.setdefaulttimeout(self.timeout)
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
                        time.sleep(5)
                        newlastlog = self.getLastLog()
                        if not lastlog == newlastlog:
                            print "\r\nClosing log stream\r\n"
                            return
                else:
                    tctr += 1
                    if waitForRetry:
                        time.sleep(self.timeout)
                        
                    waitForRetry = True
                time.sleep(.050)

    def getLastLog(self):
        # Get the name of the live (last) log file from the database
        aname = self.analyzerId
        lastlog = None
        rtn_data = None
        
        tctr = 0
        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            try:
                qry_with_ticket = '%s?qry=byEpoch&anz=%s&startEtm=%s&limit=1&reverse=true' % (self.meta_url.replace("<TICKET>", self.ticket), self.analyzerId, self.lastEtm)
                if self.debug == True:
                    print "getLastLog() qry_with_ticket", qry_with_ticket
                
                socket.setdefaulttimeout(self.timeout)
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
            
            tctr += 1
            if waitForRetry:
                time.sleep(self.timeout)
                
            waitForRetry = True
            

    #######################################################################
    # Perform REST call to push peak data to the database
    #######################################################################

    def pushData(self, peakname, doc_data):
        err_rtn_str = 'ERROR: missing data:'
        rtn = "OK"
        if doc_data: 
            params = [{"logname": peakname, "replace": False, "logtype": self.logtype, "logdata": doc_data}]
            if self.debug == True:
                print "params: ", params
        else: 
            return   
            
        postparms = {'data': json.dumps(params)}
        
        tctr = 0
        waitForRetryCtr = 0
        waitForRetry = True
        
        while True:
            try:
                # NOTE: socket only required to set timeout parameter for the urlopen()
                # In Python26 and beyond we can use the timeout parameter in the urlopen()
                socket.setdefaulttimeout(self.timeout)

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

            tctr += 1
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
                    if self.debug == True:
                        print "\ndist: ", dist
                        print "\nentry: ", entry
                        
                    yield DataTuple(dist,**entry)
                else:
                    yield None      # Indicate that dist are bad, and we must restart
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
    # Space-scale analysis
    #######################################################################
    
    def spaceScale(self,source,dx,t_0,nlevels,tfactor):
        """Analyze source at a variety of scales using the differences of Gaussians of
        different scales. We define
            g(x;t) = exp(-0.5*x**2/t)/sqrt(2*pi*t)
        and let the convolution kernels be
            (tfactor+1)/(tfactor-1) * (g(x,t_i) - g(x,tfactor*t_i))
        where t_i = tfactor * t_i-1. There are a total of "nlevels" kernels each defined
        on a grid with an odd number of points which just covers the interval
        [-5*sqrt(tfactor*t_i),5*sqrt(tfactor*t_i)]
        """
        # The following is true when the tape recorder is playing back
        collecting = lambda v: abs(v-round(v))<1e-4 and (int(round(v)) & 1) == 1

        # The following is true when the surveyor is inactive
        inactive = lambda v: abs(v-round(v))<1 and ((int(round(v)) >> 4) & 1) == 1
        
        hList = []
        kernelList = []
        scaleList = []
        ta, tb = t_0, tfactor*t_0
        amp = (tfactor+1)/(tfactor-1)
        for i in range(nlevels):
            h = int(ceil(5*sqrt(tb)/dx))
            hList.append(h)
            x = arange(-h,h+1)*dx
            kernel = amp*(exp(-0.5*x*x/ta)/sqrt(2*pi*ta) - exp(-0.5*x*x/tb)/sqrt(2*pi*tb))*dx
            kernelList.append(kernel)
            scaleList.append(sqrt(ta*tb))
            ta, tb = tb, tfactor*tb
        scaleList = asarray(scaleList)
        # Define the computation buffer in which the space-scale representation
        #  is generated
        hmax = hList[-1]
        npoints = 2*hmax+4
        def checkPeak(level,pos):
            """Checks if the specified location in the ssbuff array is a peak
            relative to its eight neighbors"""
            col = pos % npoints
            colp = col + 1
            if colp>=npoints: colp -= npoints
            colm = col - 1
            if colm<0: colm += npoints
            v = ssbuff[level,col]
            isPeak = (v>ssbuff[level+1,colp]) and (v>ssbuff[level+1,col]) and (v>ssbuff[level+1,colm]) and \
                     (v>ssbuff[level,colp])   and (v>ssbuff[level,colm])  and \
                     (level==0 or ((v>ssbuff[level-1,colp]) and (v>ssbuff[level-1,col]) and (v>ssbuff[level-1,colm])))
            return isPeak, col         
        initBuff = True
        PeakTuple = None
        cstart = hmax+3
        for data in source:
            dist = data.DISTANCE
            if dist is None:
                initBuff = True
                continue
            # Initialize 
            if initBuff:
                ssbuff = zeros((nlevels,npoints),float)
                # Define a cache for the data so that the
                #  coordinates and value of peaks can be looked up
                cache = zeros((len(data),npoints),float)
                # c is the where in ssbuff the center of the kernel is placed
                c = cstart
                # z is the column in ssbuff which has to be set to zero before adding
                #  in the kernels
                z = 0
                for i in range(nlevels):
                    ssbuff[i,c-hList[i]:c+hList[i]+1] = -data.CH4*cumsum(kernelList[i])
                initBuff = False
            if PeakTuple is None:
                PeakTuple = namedtuple("PeakTuple",data._fields + ("AMPLITUDE","SIGMA"))

            cache[:,c] = data
            distIndex  = list(data._fields).index('DISTANCE')
            valveIndex = list(data._fields).index('ValveMask')
            # Zero out the old data
            ssbuff[:,z] = 0
            # Do the convolution by adding in the current methane concentration
            #  multiplied by the kernel at each level
            peaks = []
            for i in range(nlevels):
                # Add the kernel into the space-scale buffer, taking into account wrap-around
                #  into the buffer
                if c-hList[i]<0:
                    ssbuff[i,:c+hList[i]+1] += data.CH4*kernelList[i][hList[i]-c:]
                    ssbuff[i,npoints-hList[i]+c:] += data.CH4*kernelList[i][:hList[i]-c]
                elif c+hList[i]>=npoints:
                    ssbuff[i,c-hList[i]:] += data.CH4*kernelList[i][:npoints-c+hList[i]]
                    ssbuff[i,:c+hList[i]+1-npoints] += data.CH4*kernelList[i][npoints-c+hList[i]:]
                else:
                    ssbuff[i,c-hList[i]:c+hList[i]+1] += data.CH4*kernelList[i]
                if i>0:
                    # Check if we have found a peak in space-scale representation
                    # If so, add it to a list of peaks which are stored as tuples
                    #  of the form (dist,*dataTuple,amplitude,sigma)
                    isPeak,col = checkPeak(i-1,c-hList[i]-1)
                    if isPeak and cache[distIndex,col]>0.0:
                        # A peak is disqualified if the valve settings in an interval before the 
                        #  peak arrives were in the collecting state. This means that the tape recorder
                        #  was on, and the peak was a replay of a previously collected one
                        reject = False
                        if valveIndex >= 0:
                            coll= collecting(mean([cache[valveIndex,j%npoints] for j in range(col-5,col+1)]))
                            inact = inactive(cache[valveIndex,col%npoints])
                            reject = (coll or inact)
                        if not reject:
                            amplitude = 0.5*ssbuff[i-1,col]/(3.0**(-1.5))
                            sigma = sqrt(0.5*scaleList[i-1])
                            peaks.append(PeakTuple(*([v for v in cache[:,col]]+[amplitude,sigma])))
            c += 1
            if c>=npoints: c -= npoints
            z += 1
            if z>=npoints: z -= npoints
            for peak in peaks: yield peak

    def getTicket(self):
        self.ticket = None
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
        dx = self.dx
        source = None
        sigmaMin = self.sigmaMin
        sigmaMax = self.sigmaMax   # Widest peak to be detected
        minAmpl = self.minAmpl
        # Generate a range of scales. If we want to detect a peak of standard deviation
        #  sigma, we get a peak in the space-scale plane when we convolve it with a kernel
        #  of scale 2*sigma**2
        factor = self.factor
        t0 = 2*(sigmaMin/factor)*(sigmaMin/factor)
        nlevels = int(ceil((log(2*sigmaMax*sigmaMax)-log(t0))/log(factor)))+1
        # Quantities to place in peak data file, if they are available
        headings = ["EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA","WIND_N","WIND_E","WIND_DIR_SDEV","CAR_SPEED"]
        hFormat  = ["%-14.2f","%-14.3f","%-14.6f","%-14.6f","%-14.3f","%-14.4f","%-14.3f","%-14.4f","%-14.4f","%-14.3f","%-14.3f"]
        handle = None
        while True:
            # Getting source
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
                        fname = genLatestFiles(*os.path.split(self.userlogfiles)).next()

                except:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                headerWritten = False
                # Make a generator which yields (distance,data)
                if self.usedb:
                    source = self.followLastUserLogDb()
                    alignedData = self.analyzerDataDb(source)
                else:
                    if self.noWait:
                        source = self.sourceFromFile(fname)
                    else:
                        source = self.followLastUserFile(fname)
                    alignedData = self.analyzerData(source)
                    
                # Filter by spectrumID for isomethane analyzer
                selectedData = ((data.DISTANCE,data) for data in alignedData if 'species' not in data._fields or int(data.species)==150)
                    
                intData = (data for dist,data in interpolator(selectedData,dx))
                peakData = self.spaceScale(intData,dx,t0,nlevels,factor)
                filteredPeakData = (pk for pk in peakData if pk.AMPLITUDE>minAmpl)

                # Write results to database or to the analysis file
                for pk in filteredPeakData:
                    if not headerWritten:
                        # Get the list of variables and formats for the entries
                        #  in the peakData source
                        hList, hfList = [], []
                        for h,hf in zip(headings,hFormat):
                            if h in pk._fields:
                                hList.append(h)
                                hfList.append(hf)
                        if self.usedb:
                            peakname = fname.replace(".dat", ".peaks")
                            doc_hdrs = hList
                            doc_data = []
                            doc_row = 0
                        else:
                            peakFile = os.path.splitext(fname)[0] + '.peaks'
                            try:
                                handle = open(peakFile, 'wb+', 0) #open file with NO buffering
                            except:
                                raise RuntimeError('Cannot open peak output file %s' % peakFile)
                            handle.write((len(hList)*"%-14s"+"\r\n") % tuple(hList))
                        headerWritten = True
                    if self.usedb:
                        doc = {}
                        #Note: please assure that value list and doc_hdrs are in the same sequence
                        for col, val in zip(doc_hdrs, [getattr(pk,h) for h in doc_hdrs]):
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
                        handle.write(("".join(hfList)+"\r\n") % tuple([getattr(pk,h) for h in hList]))
                
                if not self.usedb and handle is not None:
                    handle.close()

                if self.logname:
                    break
                
                if self.noWait: break

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
    parser.add_option("-a", "--analyzer", dest="analyzer",
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
    
    (options, args) = parser.parse_args()

    if not options.pid_path:
        parser.error("pid-path is required")

    if not options.analyzer:
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
        
    if options.pid_path:
        pid_path = options.pid_path
    else:
        pid_path = None
        
    if options.listen_path:
        listen_path = options.listen_path
    else:
        listen_path = None
        
    if options.file_path:
        file_path = options.file_path
    else:
        file_path = None

    if options.analyzer:
        analyzer = options.analyzer
    else:
        analyzer = None
        
    if options.logname:
        logname = options.logname
    else:
        logname = None

    if options.timeout:
        timeout = options.timeout
        timeout = int(timeout)
    else:
        timeout = 10

    usedb = False
    if options.anzlog_url:
        anzlog_url = options.anzlog_url
        usedb = True
    else:
        anzlog_url = None #'https://dev.picarro.com/node/gdu/<TICKET>/1/AnzLog/'

    if options.meta_url:
        meta_url = options.meta_url
    else:
        meta_url = None #'https://dev.picarro.com/node/gdu/<TICKET>/1/AnzLog/'

    if options.ticket_url:
        ticket_url = options.ticket_url
    else:
        ticket_url = None #'https://dev.picarro.com/node/gdu/dummy/1/Admin/'

    if options.psys:
        psys = options.psys
    else:
        psys = None

    if options.identity:
        identity = options.identity
    else:
        identity = None
        
    debug = False
    if options.debug:
        debug = True

    if not analyzer:
        if logname:
            fbase = logname
        else:
            if file_path:
                fbase = os.path.basename(file_path)
        
        if fbase:         
            analyzer, sep, part = fbase.partition('-')
        else:
            parser.error("Analyzer Name not provided, and could not be determined from logname or file-path.")


    print "pid_path", pid_path
    print "listen_path", listen_path
    print "file_path", file_path
    print "usedb (computed)", usedb
    print "analyzer", analyzer
    print "logname", logname
    print "timeout", timeout
    print "anzlog_url", anzlog_url
    print "meta_url", meta_url
    print "ticket_url", ticket_url
    print "identity", identity
    print "psys", psys
    print "debug", debug

    try:
        testf = open(pid_path, 'r')
        raise RuntimeError('pidfile exists. Verify that there is not another peakFinder task for the directory. path: %s.' % data_dir)
    except:
        try:
            pidf = open(pid_path, 'wb+', 0) #open file with NO buffering
        except:
            raise RuntimeError('Cannot open pidfile for output. path: %s.' % pid_path)
    
    pid = os.getpid()
    pidf.write("%s" % (pid))
    pidf.close()
    
    pf = PeakFinder(analyzerId=analyzer
                    , listen_path=listen_path
                    , file_path=file_path
                    , logname=logname
                    , anzlog_url=anzlog_url
                    , meta_url=meta_url
                    , ticket_url=ticket_url
                    , identity=identity
                    , psys=psys
                    , usedb=usedb
                    , timeout=timeout
                    , debug=debug
                    )
    
    pf.run()
    os.remove(pid_path)


if __name__ == "__main__":
    sys.exit(main())
    