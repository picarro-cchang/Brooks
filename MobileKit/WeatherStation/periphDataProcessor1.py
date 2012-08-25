from Host.Common.namedtuple import namedtuple
from collections import deque
from threading import Lock
import Queue
import time

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import *
from scipy.optimize import leastsq
import itertools

SourceTuple = namedtuple('SourceTuple',['ts','valTuple'])

# periphDataProcessor.py is a script for the peripheral data processor

class RawSource(object):
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
    
gpsSource = GpsSource(QUEUES[0])
wsSource  = WsSource(QUEUES[1])

name = 'mygraph'
fig = Figure()
ax = fig.add_subplot(1,1,1)
x = []
y = []
line1, = ax.plot(x,y,'bo')
line2, = ax.plot(x,y,'y.')
line3, = ax.plot(x,y,'g.')
ax.set_xlim(-200.0,200.0)
ax.set_ylim(-200.0,200.0)
ax.grid(True)
ax.set_xlabel('GPS Heading (degrees)')
ax.set_ylabel('Magnetometer Heading (degrees)')

OFFSET = 0.0   # Offset for weather station magnetometer data to be in sync with GPS data

def syncSources(msInterval):
    """Yields timestamp, GPS data and weather station data, all interpolated
    onto a regular grid, sampled at interval msInterval (in milliseconds). These
    times are referenced to the GPS timestamps."""
    while True:
        ts1 = gpsSource.getOldestTimestamp()
        if ts1 is not None: break
        time.sleep(0.1)
    while True:
        ts2 = wsSource.getOldestTimestamp()
        if ts2 is not None: break
        time.sleep(0.1)
    ts = msInterval*(1+max(ts1,ts2)//msInterval)
    while True:
        while True:
            d1 = gpsSource.getData(ts)
            if d1 is not None: break
            time.sleep(0.1)
        while True:
            d2 = wsSource.getData(ts+OFFSET)
            if d2 is not None: break
            time.sleep(0.1)
        yield ts, d1.valTuple, d2.valTuple
        ts += msInterval

SyncCdataTuple = namedtuple('SyncCdataTuple',['ts','lon','lat','zPos','wHead','wVel'])

def cartSource(gpsSource):
    """Convert latitude and longitude to Cartesian coordinates relative to initial point"""
    lon_ref, lat_ref = None, None
    for lon,lat in gpsSource:
        if lon_ref is None:
            lon_ref, lat_ref = lon, lat
        x,y = toXY(lat,lon,lat_ref,lon_ref)
        yield lon,lat,x,y
        
# Split the synchronized sources into two, so that one can be passed to the Cartesian converter
src1, src2 = itertools.tee(syncSources(1000),2)
csrc1 = cartSource(((gps.GPS_ABS_LONG,gps.GPS_ABS_LAT) for ts,gps,ws in src1))

# Use izip to recombine the sources and produce the desired complex-valued tuple for analysis
def syncCdata(cartData,syncData):
    lon,lat,x,y = cartData
    ts,gps,ws = syncData
    zPos = y+1j*x
    wHead = ws.WS_COS_HEADING+1j*ws.WS_SIN_HEADING
    wVel = ws.WS_SPEED*(ws.WS_COS_DIR+1j*ws.WS_SIN_DIR)
    return SyncCdataTuple(ts,lon,lat,zPos,wHead,wVel)
syncCdataSource = (syncCdata(cartData,syncData) for cartData,syncData in itertools.izip(csrc1, src2))

# Compute the centered derivative of the GPS data and align it with the weather station data
#  We may later use Savitzky-Golay filtering here

DerivCdataTuple = namedtuple('DerivCdataTuple',['ts','lon','lat','zPos','wHead','wVel','zVel'])

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

# We wish to model relationship between GPS heading and weather station heading, but only over those points
#  where the speed of the vehicle is large enough. So we split the data into two pairs of lists, one pair
#  when the car is moving fast and the other when it is not
gps_head1 = []
gps_head2 = []
ws_head1 = []
ws_head2 = []
phi_new1 = [] 
lastPlot = 0
toDeg = 180.0/pi

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

def whichBin(phi,nBins):
    return int(min(nBins-1,floor(nBins*(mod(phi,2*pi)/(2*pi)))))
  
fp = file('compassFit.txt','w',0)
for i,d in enumerate(derivCdataSource(syncCdataSource)):
    now = time.time()
    phi = angle(d.zVel)
    theta = -angle(d.wHead)
    psi = angle(d.wVel)
    # Apply corrections to the wind velocity using the current magnetometer calibration
    # We need the inverse of the relation  theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
    #  to solve for phi in terms of theta.
    w = p1+1j*p2;
    b = -2.0*real(w*exp(-1j*(theta-p0)))
    c = abs(w)**2 - 1.0
    disc = b**2 - 4.0*c
    r = 0.5*(-b+sqrt(disc))
    phi_new = angle(r*exp(1j*(theta-p0))-w)
    # Corrected wind velocity relative to the vehicle
    cVel = d.wVel*exp(1j*(phi_new-theta+p0))
    # Subtract the velocity of the vehicle derived from GPS
    
    
    #
    if abs(d.zVel) > 2.0:  # Car is moving fast if speed > 2m/s. Use these for determining model
        # Determine which deque to put data onto 
        b = whichBin(phi,nBins)
        dataDeques[b].append((phi,theta))
        # Limit size of deque
        while len(dataDeques[b])>maxPoints: dataDeques[b].popleft()
        gps_head1.append(toDeg*phi)
        ws_head1.append(toDeg*theta)
        phi_new1.append(phi_new) 
        print>>fp,"%12.7f%12.7f%12.7f" % (phi,theta,psi)
    else:
        gps_head2.append(toDeg*phi)
        ws_head2.append(toDeg*theta)
    if now-lastPlot > 5.0:  # Do a plot and calculate magnetometer calibration every 5s
        phi = []
        theta = []
        for q in dataDeques:
            phi    += [p for (p,t) in q]
            theta  += [t for (p,t) in q]
        phi = asarray(phi)
        theta = asarray(theta)
        
        if len(phi)>50:
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
            x0 = array([0.0,0.0,0.0])
            x,ier = leastsq(fun,x0,Dfun=dfun)
            if ier in [1,2,3,4]:    # Successful return
                p0, p1, p2 = x[0], x[1], x[2]
            phifine=linspace(-pi,pi,500)
            N = len(phifine)    
            yfine = mock(x,phifine)
            # line3.set_data(toDeg*phifine,toDeg*arctan2(yfine[N:],yfine[:N]))
            print "%15.3f %15.3f %15.3f" % (x[0], x[1], x[2])
        line1.set_data(toDeg*phi,toDeg*theta)
        line2.set_data(gps_head2,ws_head2)
        line3.set_data(gps_head1,toDeg*asarray(phi_new1))
        ax.set_title('Line %d' % i)
        # ax.relim()
        # ax.autoscale_view()
        RENDER_FIGURE(fig,name)
        lastPlot = time.time()
        
