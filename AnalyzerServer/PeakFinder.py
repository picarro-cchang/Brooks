from collections import deque
import glob
import itertools
from numpy import *
import os
import sys
import time
import traceback

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
            self.dx = 2.0
    
        if 'sigmaMinFactor' in kwargs:
            sigmaMinFactor = float(kwargs['sigmaMinFactor'])
        else:
            sigmaMinFactor = 0.75
    
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


        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
            
    
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
            #  (dist,methane_conc,longitude,latitude,epoch_time)
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
                            yield dist,(long,lat),(entry['EPOCH_TIME'],entry['CH4'])
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
                long,lat,epochTime,methane = y
                if initBuff:
                    ssbuff = zeros((nlevels,npoints),float)
                    # Define a cache for the position and concentration data so that the
                    #  coordinates and value of peaks can be looked up
                    cache = zeros((4,npoints),float)
                    # c is the where in ssbuff the center of the kernel is placed
                    c = hmax+2
                    # z is the column in ssbuff which has to be set to zero before adding
                    #  in the kernels
                    z = 0
                    for i in range(nlevels):
                        ssbuff[i,c-hList[i]:c+hList[i]+1] = -methane*cumsum(kernelList[i])
                    initBuff = False
                cache[:,c] = (x,long,lat,methane)
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
                            peaks.append(tuple([v for v in cache[:,col]]) + (0.5*ssbuff[i,col]/(3.0**(-1.5)),sqrt(0.5*scaleList[i]),))
                c += 1
                if c>=npoints: c -= npoints
                z += 1
                if z>=npoints: z -= npoints
                for peak in peaks: yield peak
        
        
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
            names = sorted(glob.glob(self.userlogfiles))
            try:
                fname = names[-1]
            except:
                fname = None
                time.sleep(self.sleep_seconds)
                print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            if fname:
                # initializing peak output
                peakFile = os.path.splitext(fname)[0] + '.peaks'
                try:
                    handle = open(peakFile, 'wb+', 0) #open file with NO buffering
                except:
                    raise RuntimeError('Cannot open peak output file %s' % peakFile)
                
                handle.write("%-14s%-14s%-14s%-14s%-14s%-14s\r\n" % ("DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA"))
 
                # Make a generator which yields (distance,(long,lat,epoch_time,methane))
                #  from the analyzer data by applying a shift to the concentration and
                #  time data to align the rows
                source = followLastUserFile(fname)
                alignedData = combiner(shifter(analyzerData(source),shift))
                intData = interpolator(alignedData,dx)
                peakData = spaceScale(intData,dx,t0,nlevels,factor)
                filteredPeakData = ((dist,long,lat,methane,amplitude,sigma) for dist,long,lat,methane,amplitude,sigma in peakData if amplitude>minAmpl)
                content = []
                for dist,long,lat,methane,amplitude,sigma in filteredPeakData:
                    handle.write("%-14.3f%-14.6f%-14.6f%-14.3f%-14.4f%-14.3f\r\n" % (dist,long,lat,methane,amplitude, sigma))
                    
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
        debug = sys.argv[2]
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
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()

    os.remove(pidpath)
    