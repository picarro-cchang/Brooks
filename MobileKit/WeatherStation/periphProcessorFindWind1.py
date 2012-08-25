from Host.Common.namedtuple import namedtuple
from collections import deque
from threading import Lock
import Queue
import os
import sys
import time

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import *
from scipy.optimize import leastsq
import itertools

NOT_A_NUMBER = 1e1000/1e1000
SourceTuple = namedtuple('SourceTuple',['ts','valTuple'])

# periphProcessorFindWind.py is a script for finding the wind statistics

class RawSource(object):
    """RawSource objects are created from a data queue. They expose a getData method
    which is used to request the value of the source at a specified timestamp. Linear
    interpolation is used to calculate the source valTuple at the desired time, unless
    the requested timestamp is in the future of all the data present in the queue, in
    which case None is returned. Up to maxStore previous queue entries are buffered in
    a deque for the interpolation. If the requested timestamp is earlier than all the
    buffered entries, the first entry is returned.
    """
    def __init__(self,queue,maxStore=20):
        self.queue = queue
        self.DataTuple = None
        self.oldData = deque()
        self.maxStore = maxStore
        self.latestTimestamp = None
        
    def getDataTupleType(self,d):
        """Construct a named tuple appropriate for the data in the queue.
        The queue datum d is a tuple consisting of a timestamp and a dictionary"""
        self.DataTuple = namedtuple(self.__class__.__name__+'_tuple',sorted(d[1].keys()))
        
    def getFromQueue(self):
        """Gets a datum from the queue (if available) and adds it to the deque. Length of
        deque is always kept no greater than self.maxStore. Returns True if a point was added 
        to the deque"""
        try:
            d = self.queue.get(block=False)
            if self.DataTuple is None:
                self.getDataTupleType(d)
            self.oldData.append(SourceTuple(d[0],self.DataTuple(**d[1])))
            self.latestTimestamp = d[0]
            if len(self.oldData) > self.maxStore:
                self.oldData.popleft()
            # print self.oldData
            return True
        except Queue.Empty:
            return False
            
    def getOldestTimestamp(self):
        if not self.oldData:
            self.getFromQueue()            
        return self.oldData[0].ts if self.oldData else None
    
    def getData(self,requestTs):
        """Get data at timestamp "requestTs" using linear interpolation. Returns None if data
        are not available."""
        while self.latestTimestamp < requestTs:
            if not self.getFromQueue(): return None
        ts, savedTs = None, None
        valTuple, savedValTuple = None, None
        for (ts, valTuple) in reversed(self.oldData):
            if ts < requestTs:
                alpha = float(requestTs-ts)/(savedTs-ts)
                di = tuple([alpha*y+(1-alpha)*y_p for y,y_p in zip(savedValTuple,valTuple)])
                return SourceTuple(requestTs,self.DataTuple(*di))
            else:
                savedTs = ts
                savedValTuple = valTuple
        else:
            return self.oldData[0]
            
class GpsSource(RawSource):
    pass
    
class WsSource(RawSource):
    pass

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

def syncSources(sourceList,msOffsetList,msInterval,sleepTime=0.01):
    """Use linear interpolation to synchronize a collection of decendents of RawSource (in 
    sourceList) to a grid of times which are multiples of msInterval. A per-source offset is 
    specified in offsetList to compensate for timestamp differences. Each source either returns None
    or a SourceTuple (which is a millisecond timestamp together with a valTuple) when 
    its getData method is called.
    
    This is a generator which yields a timestamp and a list of valTuples from each source.
    A StopIteration is thrown if the DONE() function returns True."""
    
    # First determine when to start synchronized timestamps
    oldestTs = []
    for s in sourceList:
        while True:
            ts = s.getOldestTimestamp()
            if ts is not None:
                oldestTs.append(ts)
                break
            time.sleep(sleepTime)
            
    oldestAvailableFromAll = max([ts-offset for ts,offset in zip(oldestTs,msOffsetList)])
    # Round to the grid of times which are multiples of msInterval
    ts = msInterval*(1+oldestAvailableFromAll//msInterval)
    
    # Get all the valTuples at the specified timestamp
    while True:
        valTuples = []
        for s,offset in zip(sourceList,msOffsetList):
            while True:
                d = s.getData(ts+offset)
                # if DONE(): return
                if d is not None:
                    valTuples.append(d.valTuple)
                    break
                time.sleep(sleepTime)
        yield ts, valTuples
        ts += msInterval
        
SyncCdataTuple  = namedtuple('SyncCdataTuple',['ts','lon','lat','fit','zPos','mHead','aHead','aVel'])
DerivCdataTuple = namedtuple('DerivCdataTuple',SyncCdataTuple._fields + ('zVel',))
CalibCdataTuple = namedtuple('CalibCdataTuple',DerivCdataTuple._fields + ('tVel','calParams'))
StatsCdataTuple = namedtuple('StatsCdataTuple',CalibCdataTuple._fields + ('wMean','aStdDev'))
    
def syncCdataSource(syncDataSource):
    """Convert GPS lat and lon to Cartesian coordinates and represent vectors of interest 
    as complex numbers (North)+1j*(East) so that the argument of the complex number is the 
    bearing. Note that x and y remain at zero until the GPS is good"""
    lon_ref, lat_ref = None, None
    x, y = 0.0, 0.0
    gpsOkThreshold = 4  # Need these many good GPS points before using data
    
    gpsCount = gpsOkThreshold
    for ts,[gps,mag,anem] in syncDataSource:
        lat, lon, fit = gps.GPS_ABS_LAT, gps.GPS_ABS_LONG, gps.GPS_FIT
        if gpsCount>0: gpsCount -= 1
        if fit < 1.0: gpsCount = gpsOkThreshold # Indicate bad GPS
        if lat_ref is None and gpsCount == 0:
            lat_ref, lon_ref = lat, lon
        if lat_ref is not None:
            if gpsCount == 0:
                x,y = toXY(lat,lon,lat_ref,lon_ref)
            else:
                x,y = NOT_A_NUMBER, NOT_A_NUMBER
        zPos = y+1j*x
        mHead = mag.WS_COS_HEADING+1j*mag.WS_SIN_HEADING
        aHead = anem.WS_COS_HEADING+1j*anem.WS_SIN_HEADING
        aVel  = anem.WS_SPEED*(anem.WS_COS_DIR+1j*anem.WS_SIN_DIR)
        yield SyncCdataTuple(ts,lon,lat,fit,zPos,mHead,aHead,aVel)

# Compute the centered derivative of the GPS position data. We may later use Savitzky-Golay filtering here.

def derivCdataSource(syncCdataSource):
    dBuff = []
    for d in syncCdataSource:
        dBuff.append(d)
        dBuff[:] = dBuff[-3:]
        if len(dBuff) == 3:
            d2 = dBuff[2]
            d1 = dBuff[1]
            d0 = dBuff[0]
            zVel = 1000.0*(d2.zPos-d0.zPos)/(d2.ts-d0.ts)
            yield DerivCdataTuple(*(d1+(zVel,)))

def calCompass(phi,theta,params0=[0.0,0.0,0.0]):
    """Use least-squares fit to calibrate the compass heading theta against
        the GPS derived heading phi. The initial value of the parameters may 
        be set. params = [p0,p1,p2] where
        
        theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
    """
    phi = asarray(phi)
    theta = asarray(theta)
    data = concatenate((cos(theta),sin(theta)))
    def mock(params,phi):    # Generates mock data
        p0,p1,p2 = params
        th = p0 + arctan2(p2+sin(phi),p1+cos(phi))
        return concatenate((cos(th),sin(th)))
    def fun(params):    # Function whose sum of squares is to be minimized
        return mock(params,phi)-data
    def dfun(params):   # Jacobian of fun
        N = len(phi)
        dm = mock(params,phi)
        cth = dm[:N]
        sth = dm[N:]
        p0,p1,p2 = params
        f1 = p1+cos(phi)
        f2 = p2+sin(phi)
        den = f1**2 + f2**2
        c0 = concatenate((-sth,cth))
        c1 = concatenate((sth*f2/den,-cth*f2/den))
        c2 = concatenate((-sth*f1/den,cth*f1/den))
        return column_stack((c0,c1,c2))
    x0 = asarray(params0)
    x,ier = leastsq(fun,x0,Dfun=dfun)
    if ier in [1,2,3,4]:    # Successful return
        return x
    else:
        raise RuntimeError("Calibration failed")
        
# First generate a true wind source that does no averaging but simply subtracts the vehicle velocity
#  from the anemometer velocity, after applying the magnetometer correction
def trueWindSource(derivCdataSource):
    #
    # We want to fit the most recent magnetometer data to a model consisting of a static bias field.
    #  This model maps the GPS derived heading phi to the magnetometer heading theta. Data are required 
    #  over a range of phi to get a good fit. We divide the range of phi into four bins. In each bin, we
    #  have a deque of recent data points consisting of (phi,theta) pairs. Each deque has a certain 
    #  maximum number of points. The fit is carried out on the points which are currently in the deques

    p0 = 0  # Parameters of magnetometer calibration
    p1 = 0  #  theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
    p2 = 0

    nBins = 4
    maxPoints = 200
    dataDeques = [deque() for i in range(nBins)]
    
    # Scalars for determining scaling between weather station and GPS speeds
    zVelSsq = 0.0
    zVelcVel = 0.0
    
    def whichBin(phi,nBins):
        return int(min(nBins-1,floor(nBins*(mod(phi,2*pi)/(2*pi)))))
    
    for i,d in enumerate(derivCdataSource):
        # Apply corrections to the anemometer wind velocity using the current magnetometer 
        #  calibration. The anemometer readings appropriate for the current GPS data are
        #  in aHead and aVel. 
        # 
        # theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
        #
        #  where theta is the observed magnetometer heading and phi is the corresponding
        #  GPS heading. The rotation required for aVel to get the bearing relative to the
        #  vehicle is phi-theta+p0
        theta = -angle(d.aHead) # Negative sign appears to be the magnetometer convention for angles
        w = p1 + 1j*p2;
        b = -2.0*real(w*exp(-1j*(theta-p0)))
        c = abs(w)**2 - 1.0
        disc = b**2 - 4.0*c
        r = 0.5*(-b+sqrt(disc))
        phi = angle(r*exp(1j*(theta-p0))-w)
        # Corrected wind velocity relative to the vehicle
        cVel = d.aVel*exp(1j*(phi-theta+p0))
        # Compute statistics for estimating scale factor between GPS and weather station speeds
        if not isnan(d.zVel):
            zVelSsq += abs(d.zVel)**2
            zVelcVel += real(d.zVel*conj(cVel))
        
        # Following is scale factor to apply to weather station speed before subtraction of GPS velocity
        # print zVelSsq/zVelcVel

        # Subtract the velocity of the vehicle derived from GPS to get the wind bearing relative to ground
        scaleFac = 1.0
        tVel = scaleFac*cVel - d.zVel
        
        # Update the parameters of the calibration from time to time
        phi0 = angle(d.zVel)
        theta0 = -angle(d.mHead)
        if not isnan(d.zVel):      # Reject bad GPS data
            if abs(d.zVel) > 2.0:  # Car is moving fast if speed > 2m/s. Use these for calibrating
                                   # magnetometer against GPS
                # Determine which deque to put data onto 
                b = whichBin(phi0,nBins)
                dataDeques[b].append((phi0,theta0))
                # Limit size of deque
                while len(dataDeques[b])>maxPoints: dataDeques[b].popleft()
        if i%50 == 0: # Carry out the compass calibration based on available data
            phi0, theta0 = [], []
            for q in dataDeques:
                phi0    += [p for (p,t) in q]
                theta0  += [t for (p,t) in q]
            phi0 = asarray(phi0)
            theta0 = asarray(theta0)
            
            if len(phi0)>=50:
                try:
                    p0,p1,p2 = calCompass(phi0,theta0,[p0,p1,p2])
                    print "Compass params: %10.2f %10.2f %10.2f" % (p0, p1, p2)
                except:
                    pass
        yield CalibCdataTuple(*(d+(tVel,[p0,p1,p2]))) 

# Calculate the statistics of the wind velocity by averaging the northerly and easterly components of the wind velocity
#  as well as the Yamartino standard deviation of the wind direction taken over some interval of time

def windStatistics(windSource,statsInterval):
    wSum = 0.0
    aSum = 0.0
    buff = deque()    
    for w in windSource:
        if isnan(w.tVel):
            wSum = 0.0
            aSum = 0.0
            buff.clear()
            wMean   = NOT_A_NUMBER+1j*NOT_A_NUMBER
            aStdDev = NOT_A_NUMBER
        else:
            buff.append(w.tVel)
            wSum += w.tVel
            aSum += exp(1j*angle(w.tVel))
            if len(buff)>statsInterval:
                oldest = buff.popleft()
                wSum -= oldest
                aSum -= exp(1j*angle(oldest))
            n = len(buff)
            wMean = wSum/n
            if n>0:
                eps = sqrt(1-abs(aSum/n)**2)
                aStdDev = arcsin(eps)*(1+0.1547*eps**3)
            else:
                aStdDev = pi/2.0
            aStdDev = 180.0/pi * aStdDev
        yield StatsCdataTuple(*(w+(wMean,aStdDev))) 

def main():
    gpsSource = GpsSource(SENSORLIST[0])
    wsSource  = WsSource(SENSORLIST[1])
    msOffsets = [0,0,2000]  # ms offsets for GPS, magnetometer and sonic anemometer
    syncDataSource = syncSources([gpsSource,wsSource,wsSource],msOffsets,1000)
    statsAvg = 20
    for i,d in enumerate(windStatistics(trueWindSource(derivCdataSource(syncCdataSource(syncDataSource))),statsAvg)):
        WRITEOUTPUT(d.ts,[float(real(d.wMean)),float(imag(d.wMean)),d.aStdDev])

main()
