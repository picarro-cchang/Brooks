from scipy.interpolate import interp1d
from Host.Common.namedtuple import namedtuple
from numpy import *
import traceback
import pylab as pl

#
# Test utility for peak finder 
#
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
#

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
    print npoints, nlevels
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
            print "Starting value of c", c
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
                #if i==36 and c-hList[i+1]==381:
                #    print ssbuff[30:50,380:383]
                isPeak,col = checkPeak(i-1,c-hList[i]-1)
                if isPeak and cache[0,col] > 0.0:
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

    #print ssbuff[0:10,343:349]
    #print checkPeak(0,346)
    #pl.imshow(ssbuff)
    #pl.show()


DataTuple = namedtuple("DataTuple",["EPOCH_TIME","CH4","GPS_ABS_LONG","GPS_ABS_LAT"])

lat0 = 35.0
lng0 = -120.0
t0 = 1300000000     # Starting epoch time
background = 2.0    # Background methane concentration
center = 130
sigma = 4
ampl = 1.0

mpd = distVincenty(lat0,lng0,lat0,lng0+1.0e-3)/1.0e-3 # Meters per degree of longitude

# Synthesize path going due east at a speed of 10m/s sampled
v = 10.0    # Speed of vehicle
dt = 1.0   # Time between samples
npoints = 50

tVec = t0 + arange(npoints)*dt
dVec = arange(npoints)*v*dt
latVec = lat0 + zeros(npoints)
lngVec = lng0 + arange(npoints)*v*dt/mpd
ch4Vec = background + ampl*exp(-0.5*((dVec-center)/sigma)**2)
def sourceGen():
    for d,t,ch4,lng,lat in zip(dVec,tVec,ch4Vec,lngVec,latVec):
        yield d,DataTuple(t,ch4,lng,lat)
        
alignedData = sourceGen()

dx = 1.0
sigmaMin = 2.0*dx
sigmaMax = 20.0*dx
minAmpl = 0.01

# Generate a range of scales. If we want to detect a peak of standard deviation
#  sigma, we get a peak in the space-scale plane when we convolve it with a kernel
#  of scale 2*sigma**2

factor = 1.2
t0 = 2*(sigmaMin/factor)**2
nlevels = int(ceil((log(2*sigmaMax**2)-log(t0))/log(factor)))+1
# Quantities to place in peak data file, if they are available
refinedData = refiner(alignedData)
intData = interpolator(refinedData,dx)

# dList = []
# ch4List = []
# for d,dat in intData:
    # dList.append(d)
    # ch4List.append(dat.CH4)

peakData = spaceScale(intData,dx,t0,nlevels,factor)
peakDataList = [(p.AMPLITUDE,p) for p in peakData]
#print "\n".join([("%20.2f %10.4f %10.4f" % (p.DISTANCE,a,p.SIGMA)) for a,p in sorted(peakDataList)])
print "\n".join([("%20.2f %10.4f %10.4f" % (p.DISTANCE,a,p.SIGMA)) for a,p in peakDataList])
    
from pylab import *
plot(dVec,ch4Vec)
show()

# peakData = spaceScale(intData,dx,t0,nlevels,factor)
# filteredPeakData = (pk for pk in peakData if pk.AMPLITUDE>minAmpl)
# content = []
# for pk in filteredPeakData:
# if not headerWritten:
    # # Get the list of variables and formats for the entries
    # #  in the peakData source
    # hList = []
    # hfList = []
    # for h,hf in zip(headings,hFormat):
        # if h in pk._fields:
            # hList.append(h)
            # hfList.append(hf)
    # if self.usedb:
        # peakname = fname.replace(".dat", ".peaks")
        # doc_hdrs = hList
        # doc_data = []
        # doc_row = 0
    # else:
        # peakFile = os.path.splitext(fname)[0] + '.peaks'
        # try:
            # handle = open(peakFile, 'wb+', 0) #open file with NO buffering
        # except:
            # raise RuntimeError('Cannot open peak output file %s' % peakFile)
        # handle.write((len(hList)*"%-14s"+"\r\n") % tuple(hList))
    # headerWritten = True
# if self.usedb:
    # doc = {}
    # #Note: please assure that value list and doc_hdrs are in the same sequence
    # for col, val in zip(doc_hdrs, [getattr(pk,h) for h in doc_hdrs]):
        # doc[col] = float(val)
    
    # doc_row += 1
    # doc["row"] = doc_row 
    # doc["ANALYZER"] = self.analyzerId

    # doc_data.append(doc)
        
    # pushData(peakname, doc_data)
    # doc_data = []
    
# else:
    # handle.write(("".join(hfList)+"\r\n") % tuple([getattr(pk,h) for h in hList]))

# if not self.usedb:
# handle.close()

# if self.noWait: break
