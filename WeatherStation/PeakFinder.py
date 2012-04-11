from collections import deque
import fnmatch
import itertools
from numpy import *
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

class PeakFinder(object):
    '''
    Find peak values
    '''
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
            self.minAmpl = 0.03
    
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

        if 'usedb' in kwargs:
            self.usedb = kwargs['usedb']
        else:
            self.usedb = None
            
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
            
        self.noWait = 'nowait' in kwargs
            
    def run(self):
        '''
        '''        
        def distVincenty(lat1, lon1, lat2, lon2):
            # WGS-84 ellipsiod. lat and lon in DEGREES
            a = 6378137
            b = 6356752.3142
            f = 1/298.257223563;
            toRad = pi/180.0
            L = (lon2-lon1)*toRad
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
        
        def toXY(lat,lon,lat_ref,lon_ref):
            x = distVincenty(lat_ref,lon_ref,lat_ref,lon)
            if lon<lon_ref: x = -x
            y = distVincenty(lat_ref,lon,lat,lon)
            if lat<lat_ref: y = -y
            return x,y
            
        def fixed_width(text,width):
            start = 0
            result = []
            while True:
                atom = text[start:start+width].strip()
                if not atom: return result
                result.append(atom)
                start += width
        
        def followFile(fname):
            fp = file(fname,'rb')
            while True:
                line = fp.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                yield line
        
        def getLastLog():
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
            
        def followLastUserLogDb():
            aname = self.analyzerId
            
            lastlog = getLastLog()  
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
                                newlastlog = getLastLog()
                                if not lastlog == newlastlog:
                                    print "\r\nClosing log stream\r\n"
                                    return
                                
                        else:
                            time.sleep(5)
                            newlastlog = getLastLog()
                            if not lastlog == newlastlog:
                                print "\r\nClosing log stream\r\n"
                                return
                                
                        time.sleep(1)
                    else:
                        time.sleep(5)
                        newlastlog = getLastLog()
                        if not lastlog == newlastlog:
                            print "\r\nClosing log stream\r\n"
                            return
            
        def sourceFromFile(fname):
            fp = file(fname,'rb')
            while True:
                line = fp.readline()
                if line: yield line
                else: break
                
        def followLastUserFile(fname):
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
                    #if self.debug: sys.stderr.write('-')
                    continue
                #if self.debug: sys.stderr.write('.')
                yield line
        
        def analyzerDataDb(source):
            # Generates data from a minimal archive as a stream consisting of tuples:
            #  (dist,methane_conc,longitude,latitude,epoch_time)
            JUMP_MAX = 500.0
            dist = None
            lat_ref, lon_ref = None, None
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
                    lon, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]
                    if lat_ref == None or lon_ref == None:
                        lon_ref, lat_ref = lat, lon
                    x,y = toXY(lat,lon,lat_ref,lon_ref)
                    if dist is None:
                        jump = 0.0
                        dist = 0.0
                    else:
                        jump = sqrt((x-x0)**2 + (y-y0)**2)
                        dist += jump
                    x0, y0 = x, y
                    if jump < JUMP_MAX:
                        yield dist,DataTuple(**entry)
                    else:
                        yield None,None    # Indicate that dist is bad, and we must restart
                        dist = None
                        lat_ref, lon_ref = None, None
                except:
                    print traceback.format_exc()
            
        def analyzerData(source):
            # Generates data from a minimal archive as a stream consisting of tuples:
            #  (dist,methane_conc,longitude,latitude,epoch_time)
            JUMP_MAX = 500.0
            dist = None
            lat_ref, lon_ref = None, None
            line = source.next()
            atoms = fixed_width(line,26)
            headings = [a.replace(" ","_") for a in atoms]
            DataTuple = namedtuple("DataTuple",headings)
            for line in source:
                try:
                    entry = {}
                    atoms = fixed_width(line,26)
                    if not headings:
                        headings = [a.replace(" ","_") for a in atoms]
                    else:
                        for h,a in zip(headings,atoms):
                            try:
                                entry[h] = float(a)
                            except:
                                entry[h] = NaN
                        lon, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]

                        if lat_ref == None or lon_ref == None:
                            lon_ref, lat_ref = lat, lon
                        x,y = toXY(lat,lon,lat_ref,lon_ref)
                        if dist is None:
                            jump = 0.0
                            dist = 0.0
                        else:
                            jump = sqrt((x-x0)**2 + (y-y0)**2)
                            dist += jump
                        x0, y0 = x, y
                        if jump < JUMP_MAX:
                            yield dist,DataTuple(**entry)
                        else:
                            yield None,None    # Indicate that dist is bad, and we must restart
                            dist = None
                            lat_ref, lon_ref = None, None
                except:
                    print traceback.format_exc()
                        
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
                
        def refiner(source):
            """A basic methane only instrument collects a single concentration for each line in the data log file whereas a 
            FCDS style analyzer collects extra information which must be filtered according to species."""
            # Linear intepolation factory
            def lin_interp(alpha): return lambda old,new: (1-alpha)*old + alpha*new
            oldDist, oldData = None, None
            for dist,data in source:
                if dist is None:
                    yield None, None
                    continue
                if 'species' in data._fields:
                    if int(data.species) != 150: continue   # Not iso-methane
                yield dist,data
                        
        def spaceScale(source,dx,t_0,nlevels,tfactor):
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
            
            hList = []
            kernelList = []
            scaleList = []
            ta, tb = t_0, tfactor*t_0
            amp = (tfactor+1)/(tfactor-1)
            for i in range(nlevels):
                h = int(ceil(5*sqrt(tb)/dx))
                hList.append(h)
                x = arange(-h,h+1)*dx
                kernel = amp*(exp(-0.5*x**2/ta)/sqrt(2*pi*ta) - exp(-0.5*x**2/tb)/sqrt(2*pi*tb))*dx
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
            for dist,data in source:
                if dist is None:
                    initBuff = True
                    continue
                # Initialize 
                if initBuff:
                    ssbuff = zeros((nlevels,npoints),float)
                    # Define a cache for the distance and data so that the
                    #  coordinates and value of peaks can be looked up
                    cache = zeros((1+len(data),npoints),float)
                    # c is the where in ssbuff the center of the kernel is placed
                    c = cstart
                    # z is the column in ssbuff which has to be set to zero before adding
                    #  in the kernels
                    z = 0
                    for i in range(nlevels):
                        ssbuff[i,c-hList[i]:c+hList[i]+1] = -data.CH4*cumsum(kernelList[i])
                    initBuff = False
                if PeakTuple is None:
                    PeakTuple = namedtuple("PeakTuple",("DISTANCE",) + data._fields + ("AMPLITUDE","SIGMA"))
    
                cache[:,c] = (dist,) + data
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
                        if isPeak and cache[0,col]>0.0:
                            # A peak is disqualified if the valve settings in an interval before the 
                            #  peak arrives were in the collecting state. This means that the tape recorder
                            #  was on, and the peak was a replay of a previously collected one
                            reject = False
                            if 'ValveMask' in data._fields:
                                where = list(data._fields).index('ValveMask')
                                reject = collecting(mean([cache[where+1,j%npoints] for j in range(col-5,col+1)]))
                            if not reject:
                                amplitude = 0.5*ssbuff[i-1,col]/(3.0**(-1.5))
                                sigma = sqrt(0.5*scaleList[i-1])
                                peaks.append(PeakTuple(*([v for v in cache[:,col]]+[amplitude,sigma])))
                c += 1
                if c>=npoints: c -= npoints
                z += 1
                if z>=npoints: z -= npoints
                for peak in peaks: yield peak
        
        def pushData(peakname, doc_data):
            print "pushData: ", peakname, doc_data
            
            err_rtn_str = 'ERROR: missing data:'
            rtn = "OK"
            if doc_data: 
                params = {peakname: doc_data}
            else:    
                params = {peakname: []}
            postparms = {'data': json.dumps(params)}
            dataPeakAddUrl = self.url.replace("getData", "gdu/dataPeakAdd")
            
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
        
        dx = self.dx
        source = None
        sigmaMin = self.sigmaMin
        sigmaMax = self.sigmaMax   # Widest peak to be detected
        minAmpl = self.minAmpl
        # Generate a range of scales. If we want to detect a peak of standard deviation
        #  sigma, we get a peak in the space-scale plane when we convolve it with a kernel
        #  of scale 2*sigma**2
        factor = self.factor
        t0 = 2*(sigmaMin/factor)**2
        nlevels = int(ceil((log(2*sigmaMax**2)-log(t0))/log(factor)))+1
        # Quantities to place in peak data file, if they are available
        headings = ["EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA","WIND_N","WIND_E","WIND_DIR_SDEV","CAR_SPEED"]
        hFormat  = ["%-14.2f","%-14.3f","%-14.6f","%-14.6f","%-14.3f","%-14.4f","%-14.3f","%-14.4f","%-14.4f","%-14.3f","%-14.3f"]
        while True:
            # Getting source
            if self.usedb:
                lastlog = getLastLog()  
                if lastlog:
                    fname = lastlog
                else:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds
            else:
                try:
                    fname = genLatestFiles(*os.path.split(self.userlogfiles)).next()
                    print fname
                except:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                headerWritten = False
                # Make a generator which yields (distance,data)
                if self.usedb:
                    source = followLastUserLogDb()
                    alignedData = analyzerDataDb(source)
                else:
                    if self.noWait:
                        source = sourceFromFile(fname)
                    else:
                        source = followLastUserFile(fname)
                    alignedData = analyzerData(source)
                    
                refinedData = refiner(alignedData)
                intData = interpolator(refinedData,dx)
                peakData = spaceScale(intData,dx,t0,nlevels,factor)
                filteredPeakData = (pk for pk in peakData if pk.AMPLITUDE>minAmpl)
                content = []
                for pk in filteredPeakData:
                    if not headerWritten:
                        # Get the list of variables and formats for the entries
                        #  in the peakData source
                        hList = []
                        hfList = []
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
                        
                        doc_row += 1
                        doc["row"] = doc_row 
                        doc["ANALYZER"] = self.analyzerId
   
                        doc_data.append(doc)
                            
                        pushData(peakname, doc_data)
                        doc_data = []
                        
                    else:
                        handle.write(("".join(hfList)+"\r\n") % tuple([getattr(pk,h) for h in hList]))
                
                if not self.usedb:
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
    PEAKFILES = os.path.join(AppDir,'static/datalog/*.peaks')
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
    
    data_dir = os.path.join('/data/mdudata/datalogAdd', analyzer) # P3 Server data location
    #data_dir = os.path.join(AppDir,'static/datalog') # local Analyzer data location
    pidpath = os.path.join(data_dir, 'peakFinderMain.pid')
    
    try:
        testf = open(pidpath, 'r')
        raise RuntimeError('pidfile exists. Verify that there is not another peakFinderMain task for the directory. path: %s.' % data_dir)
    except:
        try:
            pidf = open(pidpath, 'wb+', 0) #open file with NO buffering
        except:
            raise RuntimeError('Cannot open pidfile for output. path: %s.' % pidpath)
    
    pid = os.getpid()
    pidf.write("%s" % (pid))
    pidf.close()
    
    ulog = os.path.join(data_dir, '*.dat')
    
    pf = PeakFinder()
    pf.analyzerId = analyzer
    pf.userlogfiles = ulog
    pf.url = url
    pf.debug = debug
    pf.usedb = True

    pf.run()

    os.remove(pidpath)
    