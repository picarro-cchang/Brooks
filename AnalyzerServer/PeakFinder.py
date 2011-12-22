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

def genLatestFiles(baseDir,pattern):
    # Generate files in baseDir and its subdirectories which match pattern
    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=True)
        fileNames.sort(reverse=True)
        for name in fileNames:
            if fnmatch.fnmatch(name,pattern):
                yield os.path.join(dirPath,name)

# Convert a minimal .dat file to a text file for Matlab processing
#  The columns in the output file are distance(m), methane 
#  concentration(ppm), longitude(deg), latitude(deg) and 
#  time.
# N.B. NO SHIFT is applied to the data
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

        if 'shift' in kwargs:
            self.shift = int(kwargs['shift'])
        else:
            self.shift = -4

        if 'dx' in kwargs:
            self.dx = float(kwargs['dx'])
        else:
            self.dx = 1.0
    
        if 'sigmaMinFactor' in kwargs:
            sigmaMinFactor = float(kwargs['sigmaMinFactor'])
        else:
            sigmaMinFactor = 0.8
    
        self.sigmaMin = sigmaMinFactor*self.dx
    
        if 'sigmaMaxFactor' in kwargs:
            sigmaMaxFactor = float(kwargs['sigmaMaxFactor'])
        else:
            sigmaMaxFactor = 10.0
            
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
            
    def run(self):
        '''
        '''
        posFields = 'long lat'
        baseFields = 'time conc valves'
        extraFields  = 'conc_up conc_down conc_dt species'
        allFields = posFields+' '+baseFields+' '+extraFields
        
        PosData  = namedtuple('PosData',  posFields)
        BaseData = namedtuple('BaseData', baseFields)
        FullData = namedtuple('FullData', baseFields+" "+extraFields)
        PosBaseData = namedtuple('PosBaseData', posFields+" "+baseFields)
        PosFullData = namedtuple("PosFullData",allFields)
        
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
        
        def toXY(lat,long,lat_ref,long_ref):
            x = distVincenty(lat_ref,long_ref,lat_ref,long)
            if long<long_ref: x = -x
            y = distVincenty(lat_ref,long,lat,long)
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
            lat_ref, long_ref = None, None
            # Determine if there are extra data in the file
            for line in source:
                try:
                    entry = {}
                    extra = "CH4dt" in line
                    for  h in line.keys():
                        try:
                            entry[h] = float(line[h])
                        except:
                            entry[h] = NaN
                    long, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]
                    pos = PosData(long,lat)
                    if not 'ValveMask' in entry: entry['ValveMask'] = 0
                    if extra: 
                        data = FullData(entry['EPOCH_TIME'],entry['CH4'],entry['ValveMask'],entry['CH4up'],entry['CH4down'],entry['CH4dt'],entry['species'])
                    else:
                        data = BaseData(entry['EPOCH_TIME'],entry['CH4'],entry['ValveMask'])

                    if lat_ref == None or long_ref == None:
                        long_ref, lat_ref = lat, long
                    x,y = toXY(lat,long,lat_ref,long_ref)
                    if dist is None:
                        jump = 0.0
                        dist = 0.0
                    else:
                        jump = sqrt((x-x0)**2 + (y-y0)**2)
                        dist += jump
                    x0, y0 = x, y
                    if jump < JUMP_MAX:
                        yield dist,pos,data
                    else:
                        yield None,None,None    # Indicate that dist is bad, and we must restart
                        dist = None
                        lat_ref, long_ref = None, None
                except:
                    print traceback.format_exc()
            
        def analyzerData(source):
            # Generates data from a minimal archive as a stream consisting of tuples:
            #  (dist,methane_conc,longitude,latitude,epoch_time)
            JUMP_MAX = 500.0
            dist = None
            lat_ref, long_ref = None, None
            line = source.next()
            atoms = fixed_width(line,26)
            headings = [a.replace(" ","_") for a in atoms]
            # Determine if there are extra data in the file
            extra = "CH4dt" in headings
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
                        long, lat = entry["GPS_ABS_LONG"], entry["GPS_ABS_LAT"]
                        pos = PosData(long,lat)
                        if not 'ValveMask' in entry: entry['ValveMask'] = 0
                        if extra: 
                            data = FullData(entry['EPOCH_TIME'],entry['CH4'],entry['ValveMask'],entry['CH4up'],entry['CH4down'],entry['CH4dt'],entry['species'])
                        else:
                            data = BaseData(entry['EPOCH_TIME'],entry['CH4'],entry['ValveMask'])

                        if lat_ref == None or long_ref == None:
                            long_ref, lat_ref = lat, long
                        x,y = toXY(lat,long,lat_ref,long_ref)
                        if dist is None:
                            jump = 0.0
                            dist = 0.0
                        else:
                            jump = sqrt((x-x0)**2 + (y-y0)**2)
                            dist += jump
                        x0, y0 = x, y
                        if jump < JUMP_MAX:
                            yield dist,pos,data
                        else:
                            yield None,None,None    # Indicate that dist is bad, and we must restart
                            dist = None
                            lat_ref, long_ref = None, None
                except:
                    print traceback.format_exc()
                    
        def shifter(source,shift=0):
            """ Applies the specified shift (in samples) to the output of
            "source" to align the unshifted data colums with the shifted
            data columns. For example, consider a source generating the following:
            >>> src = (e for e in [('x0','U0','S0'),('x1','U1','S1'),('x2','U2','S2'), \
                                   ('x3','U3','S3'),('x4','U4','S4'),('x5','U5','S5')])
        
            We now split this into several sources for the following tests:
            >>> src1,src2,src3 = itertools.tee(src,3)
            
            and the shift is zero, the result should just be the original data:
            >>> for e in shifter(src1,0): print e
            ('x0', 'U0', 'S0')
            ('x1', 'U1', 'S1')
            ('x2', 'U2', 'S2')
            ('x3', 'U3', 'S3')
            ('x4', 'U4', 'S4')
            ('x5', 'U5', 'S5')
            
            If the shift is negative, we move the shifted data up relative to the unshifted data:
            >>> for e in shifter(src2,-2): print e
            ('x0', 'U0', 'S2')
            ('x1', 'U1', 'S3')
            ('x2', 'U2', 'S4')
            ('x3', 'U3', 'S5')
        
            If the shift is positive, we move the shifted data down relative to the unshifted data:
            >>> for e in shifter(src3,2): print e
            ('x2', 'U2', 'S0')
            ('x3', 'U3', 'S1')
            ('x4', 'U4', 'S2')
            ('x5', 'U5', 'S3')
            """
            tempStore = deque()
            if shift == 0:
                for x,u,s in source:
                    yield x,u,s
            elif shift < 0:
                for i,(x,u,s) in enumerate(source):
                    tempStore.append((x,u))
                    if i>=-shift:
                        yield tempStore.popleft()+(s,)
            else:
                for i,(x,u,s) in enumerate(source):
                    tempStore.append(s)
                    if i>=shift:
                        yield x,u,tempStore.popleft() 
        
        def combiner(source):
            """
            The source produces triples of the form (x,u,s) where u and s represent unshifted and
            shifted data. If x, u and s are all not None, yield (x,u+s). If any is None, yield (None,None)
            """
            for x,u,s in source:
                if (x is None) or (u is None) or (s is None):
                    yield (None,None)
                else:
                    yield (x,u+s)
                        
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
                            di = tuple([alpha*y+(1-alpha)*y_p for y,y_p in zip(d,d_p)])
                    yield xi, di
                    mult += 1
                    xi = interval*mult
                x_p, d_p = x, d
                
        def refiner(source):
            """A basic methane only instrument collects a single concentration for each line in the data log file whereas a 
            FCDS style analyzer collects extra information which must be filtered according to species."""
                
            # Linear intepolation factory
            def lin_interp(alpha): return lambda old,new: (1-alpha)*old + alpha*new

            baseLength  = len(PosData._fields) + len(BaseData._fields)
            fieldList = (posFields+" "+baseFields).split()
            oldDist, oldData = None, None
            for dist,data in source:
                if dist is None:
                    yield None, None
                    continue
                if len(data) == baseLength:
                    oldDist, oldData = None, None
                    yield dist,PosBaseData(*data)
                else: # extra fields present
                    data = PosFullData(*data)
                    if int(data.species) != 150: continue   # Not iso-methane
                    yield dist,PosBaseData(*[getattr(data,field) for field in fieldList])
                        
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
                         (v>ssbuff[level-1,colp]) and (v>ssbuff[level-1,col]) and (v>ssbuff[level+1,colm])
                return isPeak, col         
            initBuff = True
            for x,y in source:
                if x is None:
                    initBuff = True
                    continue
                # Initialize 
                long,lat,epochTime,methane,valves = y
                if initBuff:
                    ssbuff = zeros((nlevels,npoints),float)
                    # Define a cache for the position and concentration data so that the
                    #  coordinates and value of peaks can be looked up
                    cache = zeros((6,npoints),float)
                    # c is the where in ssbuff the center of the kernel is placed
                    c = hmax+2
                    # z is the column in ssbuff which has to be set to zero before adding
                    #  in the kernels
                    z = 0
                    for i in range(nlevels):
                        ssbuff[i,c-hList[i]:c+hList[i]+1] = -methane*cumsum(kernelList[i])
                    initBuff = False
                cache[:,c] = (epochTime,x,long,lat,methane,valves)
                # Zero out the old data
                ssbuff[:,z] = 0
                # Do the convolution by adding in the current methane concentration
                #  multiplied by the kernel at each level
                peaks = []
                for i in range(nlevels):
                    # Add the kernel into the space-scale buffer, taking into account wrap-around
                    #  into the buffer
                    if c-hList[i]<0:
                        ssbuff[i,:c+hList[i]+1] += methane*kernelList[i][hList[i]-c:]
                        ssbuff[i,npoints-hList[i]+c:] += methane*kernelList[i][:hList[i]-c]
                    elif c+hList[i]>=npoints:
                        ssbuff[i,c-hList[i]:] += methane*kernelList[i][:npoints-c+hList[i]]
                        ssbuff[i,:c+hList[i]+1-npoints] += methane*kernelList[i][npoints-c+hList[i]:]
                    else:
                        ssbuff[i,c-hList[i]:c+hList[i]+1] += methane*kernelList[i]
                    if i>0 and i<nlevels-1:
                        # Check if we have found a peak in space-scale representation
                        # If so, add it to a list of peaks which are stored as tuples
                        #  of the form (dist,long,lat,methane,amplitude,sigma)
                        isPeak,col = checkPeak(i,c-hList[i]-1)
                        if isPeak:
                            # A peak is disqualified if the valve settings in an interval before the 
                            #  peak arrives were in the collecting state. This means that the tape recorder
                            #  was on, and the peak was a replay of a previously collected one
                            if not(collecting(mean([cache[5,j%npoints] for j in range(col-5,col+1)]))):
                                peaks.append(tuple([v for v in cache[:,col]]) + (0.5*ssbuff[i,col]/(3.0**(-1.5)),sqrt(0.5*scaleList[i]),))
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
        
        shift = self.shift
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
                except:
                    fname = None
                    time.sleep(self.sleep_seconds)
                    print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                # initializing peak output
                if self.usedb:
                    peakname = fname.replace(".dat", ".peaks")
                    doc_hdrs = ["EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA"]
                    doc_data = []
                    doc_row = 0
                else:
                    peakFile = os.path.splitext(fname)[0] + '.peaks'
                    try:
                        handle = open(peakFile, 'wb+', 0) #open file with NO buffering
                    except:
                        raise RuntimeError('Cannot open peak output file %s' % peakFile)
                    
                    handle.write("%-14s%-14s%-14s%-14s%-14s%-14s%-14s\r\n" % ("EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA"))

                # Make a generator which yields (distance,(long,lat,epoch_time,methane))
                #  from the analyzer data by applying a shift to the concentration and
                #  time data to align the rows
                if self.usedb:
                    source = followLastUserLogDb()
                    alignedData = combiner(shifter(analyzerDataDb(source),shift))
                else:
                    source = followLastUserFile(fname)
                    alignedData = combiner(shifter(analyzerData(source),shift))
                    
                refinedData = refiner(alignedData)
                intData = interpolator(refinedData,dx)
                peakData = spaceScale(intData,dx,t0,nlevels,factor)
                filteredPeakData = ((epoch_time,dist,long,lat,methane,amplitude,sigma) for epoch_time,dist,long,lat,methane,valves,amplitude,sigma in peakData if amplitude>minAmpl)
                content = []
                for epoch_time,dist,long,lat,methane,amplitude,sigma in filteredPeakData:
                    if self.usedb:
                        doc = {}
                        #Note: please assure that value list and doc_hdrs are in the same sequence
                        for col, val in zip(doc_hdrs, [epoch_time,dist,long,lat,methane,amplitude,sigma]):
                            doc[col] = float(val)
                        
                        doc_row += 1
                        doc["row"] = doc_row 
                        doc["ANALYZER"] = self.analyzerId
   
                        doc_data.append(doc)
                            
                        pushData(peakname, doc_data)
                        doc_data = []
                        
                    else:
                        handle.write("%-14.2f%-14.3f%-14.6f%-14.6f%-14.3f%-14.4f%-14.3f\r\n" % (epoch_time,dist,long,lat,methane,amplitude,sigma))
                
                if not self.usedb:
                    handle.close()


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
    