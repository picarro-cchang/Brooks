from collections import deque
import glob
import itertools
from numpy import *
import scipy.stats
import os
import sys
import time
import traceback
from namedtuple import namedtuple

# Peak analyzer carries out Keeling plot analysis of peaks found by the isotopic methane
#  analyzer

class PeakAnalyzer(object):
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

        if 'sleep_seconds' in kwargs:
            self.sleep_seconds = float(kwargs['sleep_seconds'])
        else:
            self.sleep_seconds = 30.0

        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
            
    
    def run(self):
        '''
        '''
        posFields = 'long lat'
        restFields = 'time valves conc delta'
        PosData = namedtuple('PosData', posFields)
        RestData = namedtuple('RestData', restFields)
        SourceData = namedtuple('SourceData', '%s %s' % (posFields,restFields))

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
                
        def followLastUserFile(fname):
            fp = file(fname,'rb')
            counter = 0
            while True:
                line = fp.readline()
                if not line:
                    counter += 1
                    if counter == 10:
                        names = sorted(glob.glob(self.userlogfiles))
                        try:    # Stop iteration if we are not the last file
                            if fname != names[-1]: 
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
        
        def analyzerData(source):
            # Generates data from a minimal archive as a stream consisting of tuples:
            #  (dist,(long,lat),(epoch_time,valve_mask,methane_conc,delta)
            JUMP_MAX = 500.0
            dist = None
            lat_ref, long_ref = None, None
            line = source.next()
            atoms = fixed_width(line,26)
            headings = [a.replace(" ","_") for a in atoms]
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
                            yield dist,PosData(long,lat),RestData(entry['EPOCH_TIME'],entry['ValveMask'],entry['CH4'],entry['C13_Delta_Raw'])
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
        
        def doKeelingAnalysis(source):
            """Keep a buffer of recent concentrations within a certain time duration of the present. When the valve mask switches to the value
            indicating that the recorder has been activated, search the buffer for the peak value and the associated time and GPS location.
            Perform a Keeling analysis of the data during the interval that the recorder is being played back"""
            
            MAX_DURATION = 30
            collecting = lambda v: (v == int(v)) and (int(v) & 1) != 0
            tempStore = deque()
            keelingStore = []
            lastPeak = None
            BufferedData = namedtuple('BufferedData','dist sourceData')
            lastCollecting = False
            
            for dist,dtuple in source:
                if dist is None: continue
                d = SourceData(*dtuple)
                collectingNow = collecting(d.valves)
                if not collectingNow:
                    tempStore.append(BufferedData(dist,d))
                    while tempStore[-1].sourceData.time - tempStore[0].sourceData.time > MAX_DURATION:
                        tempStore.popleft()
                    if lastCollecting:  # Check to see if there are data for a Keeling plot
                        if len(keelingStore)>10:
                            conc = asarray([s.sourceData.conc for s in keelingStore])
                            delta = asarray([s.sourceData.delta for s in keelingStore])
                            protInvconc = 1/maximum(conc,0.001)
                            result = linfit(protInvconc,delta,11.0*protInvconc)
                            if abs(result.coeffs[1]+40) > 20:
                                print conc, delta
                            if lastPeak:
                                yield namedtuple('PeakData','time dist long lat conc delta uncertainty')(delta=result.coeffs[1],
                                            uncertainty=sqrt(result.cov[1][1]),**lastPeak._asdict())
                        del keelingStore[:]
                else:
                    keelingStore.append(BufferedData(dist,d))
                    if not lastCollecting:
                        if tempStore:
                            # We have just started collecting
                            print "Started collecting"
                            conc = asarray([s.sourceData.conc for s in tempStore])
                            dist = asarray([s.dist for s in tempStore])
                            epoch_time = asarray([s.sourceData.time for s in tempStore])
                            lat  = asarray([s.sourceData.lat  for s in tempStore])
                            long = asarray([s.sourceData.long for s in tempStore])
                            pk = conc.argmax()
                            lastPeak = namedtuple('PeakData1','time dist long lat conc')(epoch_time[pk],dist[pk],long[pk],lat[pk],conc[pk])
                            tempStore.clear()
                lastCollecting = collectingNow
            
        
        
        shift = self.shift
        
        while True:
            # Getting source
            names = sorted(glob.glob(self.userlogfiles))
            try:
                fname = names[-1]
            except:
                fname = None
                time.sleep(self.sleep_seconds)
                print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                # initializing peak output
                analysisFile = os.path.splitext(fname)[0] + '.analysis'
                try:
                    handle = open(analysisFile, 'wb+', 0) #open file with NO buffering
                except:
                    raise RuntimeError('Cannot open analysis output file %s' % analysisFile)
                
                handle.write("%-14s%-14s%-14s%-14s%-14s%-14s%-14s\r\n" % ("EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CONC","DELTA","UNCERTAINTY"))
 
                # Make a generator which yields (distance,(long,lat,valve_mask,epoch_time,methane,delta)))
                #  from the analyzer data by applying a shift to the concentration and
                #  time data to align the rows
                source = followLastUserFile(fname)
                alignedData = combiner(shifter(analyzerData(source),shift))
                
                for r in doKeelingAnalysis(alignedData):
                    print r
                    handle.write("%-14.2f%-14.3f%-14.6f%-14.6f%-14.3f%-14.2f%-14.2f\r\n" % (r.time,r.dist,r.long,r.lat,r.conc,r.delta,r.uncertainty))
                    
                handle.close()

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
        debug = sys.argv[2]
    else:
        debug = None
    
    data_dir = os.path.join('/data/mdudata/datalogAdd', analyzer) # P3 Server data location
    #data_dir = os.path.join(AppDir,'static/datalog') # local Analyzer data location
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
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()

    os.remove(pidpath)
    