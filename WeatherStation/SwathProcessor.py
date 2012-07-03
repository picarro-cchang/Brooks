#!/usr/bin/python
#
"""
File Name: SwathProcessor.py
Purpose: Helper for AnalyzerServer which calculates the field of view
  from a collection of points along the path and the wind statistics

File History:
    17-Apr-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
from collections import deque
from numpy import arange, arcsin, arctan2, asarray, cos, isfinite, isnan
from numpy import log, pi, sin, sqrt, unwrap
from collections import namedtuple
from scipy.special import erf

EARTH_RADIUS = 6378100
DTR = pi/180.0
RTD = 180.0/pi

# Calculate maximum width of field of view about the point (x_N,y_N) based on a path of 2N+1 points (x_0,y_0) through (x_{2N},y_{2N})
#  where the mean wind bearing is (u=WIND_E,v=WIND_N) and there is a standard deviation of the wind direction given by d_sdev
def angleRange(x,y,N,dist,u,v,dmax=100.0):
    """
    Consider a segment of path specified by (x[0],y[0]) through (x[2*N],y[2*N]). A line is drawn through (x[N],y[N]) in the 
    direction of (u,v) and the trial source position is placed at a distance "dist" along this line. This function calculates
    the angle range subtended by the path segment at the trial source position, where zero angle corresponds to the line joining
    the source to (x[N],y[N]). The angle range is returned as a list containing tuples 
    [(minAngle_1,maxAngle_1),(minAngle_2,maxAngle_2),...] which together determine the angles covered by the path.
    Angles are in radians.
    """
    x = asarray([x[i] for i in range(0,2*N+1)])
    y = asarray([y[i] for i in range(0,2*N+1)])
    w = sqrt(u*u+v*v)
    uhat, vhat = u/w, v/w
    # Calculate trial source position
    sx, sy = x[N]+dist*uhat, y[N]+dist*vhat
    alist = arctan2(sy-y,sx-x)
    # Unwrap, ignoring non finite quantities
    mask = isfinite(alist)
    alist[mask] = unwrap(alist[mask])
    d = sqrt((sx-x)**2+(sy-y)**2)
    good = isfinite(d) & (d<=dmax)
    da = alist-alist[N]
    # Go through "good" to find groups of valid path segments. These contribute to the covered angles
    i = start = 0
    groups = []
    while i<=2*N:
        if good[i]:
            while i<=2*N and good[i]: i+= 1
            groups.append((da[start:i].min(),da[start:i].max()))
        while i<=2*N and not good[i]: i+= 1
        start = i
    return groups

def coverProb(angleRanges,sigma):
    """Find the probability that in covered by a set of angleRanges [(amin1,amax1),(amin2,amax2)...] for a normal probability
    distribution with zero mean and standard deviation sigma
       Angles are in radians.
    """
    z = asarray(angleRanges)/sigma
    if z.size == 0: return 0.0
    p = 0.5*erf(z/sqrt(2))
    return sum(p[:,1]-p[:,0])

def maxDist(x,y,N,u,v,sigma,dmax=100,thresh=0.8,tol=1.0):
    """Find the maximum width of the swath (to a tolerance of tol) attached to the point x[N],y[N] in
    the direction of (u,v) when the standard deviation of the wind direction is sigma. The swath width 
    is never greater than dmax, and the probability that the path covers the the range of wind directions
    exceeds thresh
    Angles are in Radians.
    """
    dmin = 0.1
    if isnan(x[N]) or isnan(y[N]):
        return 0.0
    func = lambda d: coverProb(angleRange(x,y,N,d,u,v,dmax),sigma)-thresh
    fdmin = func(dmin)
    fdmax = func(dmax)
    if fdmax>0: 
        return dmax
    elif fdmin<0:
        return 0.0
    else:
        return binSearch(dmin,dmax,fdmin,fdmax,tol,func)
    
def binSearch(xmin,xmax,fxmin,fxmax,tol,func):
    """
    Use binary search to find a zero of func lying between xmin and xmax to a tolerance tol
    """
    xcen = 0.5*(xmax+xmin)
    if fxmin*fxmax > 0:
        raise ValueError("No zero between %s and %s" % (xmin,xmax))
    elif xmax-xmin < tol:
        return xcen
    else:
        fxcen = func(xcen)
        if fxmin*fxcen < 0:
            return binSearch(xmin,xcen,fxmin,fxcen,tol,func)
        else:            
            return binSearch(xcen,xmax,fxcen,fxmax,tol,func)

class PasquillGiffordApprox(object):
    def __init__(self):
        PGTuple = namedtuple("PGTuple",["power","scale"])
        self.classConstants = { 'A':PGTuple(1.92607854134,7.06164265123),
                                'B':PGTuple(1.85109993492,9.23174186112),
                                'C':PGTuple(1.83709437442,14.0085461312),
                                'D':PGTuple(1.79141020506,21.8533325178),
                                'E':PGTuple(1.74832538645,29.2243762172),
                                'F':PGTuple(1.72286808749,46.0503577192)}

    def getConc(self,stabClass,Q,u,x):
        """Get concentration in ppm from a point source of Q cu ft/hr at 
        distance x m downwind when the wind speed is u m/s."""
        pg = self.classConstants[stabClass.upper()]
        return (Q/u)*(x/pg.scale)**(-pg.power)
        
    def getMaxDist(self,stabClass,Q,u,conc,u0=0,a=1,q=2):
        """Get the maximum distance at which a source of rate Q cu ft/hr can
        be located if it is to be found with an instrument capable of measuring
        concentration "conc" above ambient, when the wind speed is u m/s.
        
        Since this would normally diverge at small u, a regularization is applied
        so that the maximum distance is made to vary as u**a for u<u0. The 
        sharpness of the transition at u0 is controlled by 1<q<infinity
        """
        pg = self.classConstants[stabClass.upper()]
        d = pg.scale*((u*conc)/Q)**(-1.0/pg.power)
        if u0>0:
            v = u/u0
            d *= v**a/(v**(a*q)+v**(-float(q)/pg.power))**(1.0/q)
        return d

pga = PasquillGiffordApprox()

# Function defining the additional wind direction standard deviation based
#  on the wind speed and vehicle speed
# Angles are in RADIANS
def astd(wind,vcar,params):
    # a = 0.15*pi
    # b = 0.25
    # c = 0.0
    return min(pi,params["a"]*(params["b"]+params["c"]*vcar)/(wind+0.01))
                
def process(source,maxWindow,stabClass,minLeak,minAmpl,astdParams):
    fields = ["EPOCH_TIME","GPS_ABS_LAT","GPS_ABS_LONG","DELTA_LAT","DELTA_LONG"]
    fovBuff = deque()
    N = maxWindow              # Use 2*N+1 samples for calculating FOV
    result = {}
    for f in fields: result[f] = []
    for newdat in source:
        while len(fovBuff) >= 2*N+1: fovBuff.popleft()
        fovBuff.append(newdat)
        if len(fovBuff) == 2*N+1:
            d = fovBuff[N]
            lng = d["GPS_ABS_LONG"]
            lat = d["GPS_ABS_LAT"]
            cosLat = cos(lat*DTR)
            t = d["EPOCH_TIME"]
            fit = d["GPS_FIT"]
            windN = d["WIND_N"]
            windE = d["WIND_E"]
            vcar = d.get("CAR_SPEED",0.0)
            dstd = DTR*d["WIND_DIR_SDEV"]
            mask = d["ValveMask"]
            if (fit>0) and (mask<1.0e-3):
                bearing = arctan2(windE,windN)
                wind = sqrt(windE*windE + windN*windN)
                xx = asarray([fovBuff[i]["GPS_ABS_LONG"] for i in range(2*N+1)])
                yy = asarray([fovBuff[i]["GPS_ABS_LAT"] for i in range(2*N+1)])
                xx = DTR*(xx-lng)*EARTH_RADIUS*cosLat
                yy = DTR*(yy-lat)*EARTH_RADIUS
                asdev = astd(wind,vcar,astdParams)
                dstd = sqrt(dstd*dstd + asdev*asdev)
                dmax = pga.getMaxDist(stabClass,minLeak,wind,minAmpl,u0=0.5)
                width = maxDist(xx,yy,N,windE,windN,dstd,dmax,thresh=0.7,tol=1.0)
                # print "Wind speed: %.2f, Wind stdDev (deg): %.2f, dmax: %.2f, Width: %.2f" % (wind,dstd*RTD,dmax,width)
                deltaLat = RTD*width*cos(bearing)/EARTH_RADIUS
                deltaLng = RTD*width*sin(bearing)/(EARTH_RADIUS*cosLat)
            else:
                deltaLat = 0.0
                deltaLng = 0.0
            if isnan(deltaLat) or isnan(deltaLng):
                deltaLat = 0.0
                deltaLng = 0.0
            result["EPOCH_TIME"].append(t)
            result["GPS_ABS_LAT"].append(lat)
            result["GPS_ABS_LONG"].append(lng)
            result["DELTA_LAT"].append(deltaLat)
            result["DELTA_LONG"].append(deltaLng)
    return result

def ltqnorm( p ):
    """
    Modified from the author's original perl code (original comments follow below)
    by dfield@yahoo-inc.com.  May 3, 2004.

    Lower tail quantile for standard normal distribution function.

    This function returns an approximation of the inverse cumulative
    standard normal distribution function.  I.e., given P, it returns
    an approximation to the X satisfying P = Pr{Z <= X} where Z is a
    random variable from the standard normal distribution.

    The algorithm uses a minimax approximation by rational functions
    and the result has a relative error whose absolute value is less
    than 1.15e-9.

    Author:      Peter John Acklam
    Time-stamp:  2000-07-19 18:26:14
    E-mail:      pjacklam@online.no
    WWW URL:     http://home.online.no/~pjacklam
    """

    if p <= 0 or p >= 1:
        # The original perl code exits here, we'll throw an exception instead
        raise ValueError( "Argument to ltqnorm %f must be in open interval (0,1)" % p )

    # Coefficients in rational approximations.
    #a = (-3.969683028665376e+01,  2.209460984245205e+02, \
    #     -2.759285104469687e+02,  1.383577518672690e+02, \
    #     -3.066479806614716e+01,  2.506628277459239e+00)
    #b = (-5.447609879822406e+01,  1.615858368580409e+02, \
    #     -1.556989798598866e+02,  6.680131188771972e+01, \
    #     -1.328068155288572e+01 )
    c = (-7.784894002430293e-03, -3.223964580411365e-01, \
         -2.400758277161838e+00, -2.549732539343734e+00, \
          4.374664141464968e+00,  2.938163982698783e+00)
    d = ( 7.784695709041462e-03,  3.224671290700398e-01, \
          2.445134137142996e+00,  3.754408661907416e+00)

    # Define break-points.
    plow  = 0.02425
    phigh = 1 - plow

    # Rational approximation for lower region:
    if p < plow:
        q  = sqrt(-2*log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for upper region:
    if phigh < p:
        q  = sqrt(-2*log(1-p))    

def cnorm(z):
    # Calculate probability that a normal random variable will be 
    #  less than the mean + z standard deviations 
    p = 0.5*erf(z/sqrt(2))
    return p
       
if __name__ == "__main__":
    R = 30
    N = 10
    t = arange(-N,N+1)
    x = R*cos(2*pi*t/(2*N))
    y = R*sin(2*pi*t/(2*N))
    # First test that the angle range makes sense 
    u = 1.0
    v = 0.0
    # Calculate the theoretical subtended angle
    dist = 100.0
    th = arcsin(R/(R+dist))
    print angleRange(x,y,N,dist,u,v,dmax=1000.0)
    print th
    # Next consider a specific direction standard deviation
    sdevDeg = 18.0
    sigma = DTR*sdevDeg
    thresh = 0.7
    d = maxDist(x,y,N,u,v,sigma,dmax=1000.0,thresh=thresh)
    th = arcsin(R/(R+d))
    # We should find that at the distance d, the probability of coverage is thresh
    print "Wind perpendicular to path"
    print "Direction std dev (deg) = ", sdevDeg, "Swath width = ", d
    print "Cone semivertex angle (degrees)", RTD*th
    print "Expected Probability ", cnorm(th/sigma)-cnorm(-th/sigma)
    ar = angleRange(x,y,N,d,u,v,dmax=1000.0)
    print "Probability ", coverProb(ar,sigma)
    #
    phi = DTR*20.0
    u = sin(phi)
    v = cos(phi)
    d = maxDist(x,y,N,u,v,sigma,dmax=1000.0,thresh=thresh)
    th = arcsin(R/sqrt((R+d*u)*(R+d*u)+(d*v)*(d*v)))
    twist = arctan2(R+d*u,d*v)-phi

    print "Wind at",phi/DTR," degrees to path"
    print "Direction std dev (deg) = ", sdevDeg, "Swath width = ", d
    print "Cone semivertex angle (degrees)", RTD*th
    print twist*RTD
    print "Expected Probability ", cnorm((-twist+th)/sigma)-cnorm((-twist-th)/sigma)
    ar = angleRange(x,y,N,d,u,v,dmax=1000.0)
    print "Probability ", coverProb(ar,sigma)
