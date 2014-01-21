from collections import namedtuple
import httplib
import numpy as np
import matplotlib as mpl
import pylab as pl
import sys
import PIL
from PIL import Image
import cStringIO

NOT_A_NUMBER = 1e1000/1e1000
EARTH_RADIUS = 6378100

def distVincenty(lat1, lon1, lat2, lon2):
    # WGS-84 ellipsiod. lat and lon in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563;
    toRad = np.pi/180.0
    L = (lon2-lon1)*toRad
    U1 = np.arctan((1-f) * np.tan(lat1*toRad))
    U2 = np.arctan((1-f) * np.tan(lat2*toRad));
    sinU1 = np.sin(U1)
    cosU1 = np.cos(U1)
    sinU2 = np.sin(U2)
    cosU2 = np.cos(U2)
  
    Lambda = L
    iterLimit = 100;
    for iter in range(iterLimit):
        sinLambda = np.sin(Lambda)
        cosLambda = np.cos(Lambda)
        sinSigma = np.sqrt((cosU2*sinLambda) * (cosU2*sinLambda) + 
                        (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
        if sinSigma==0: 
            return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = np.arctan2(sinSigma, cosSigma)
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

def pFloat(x):
    try:
        return float(x)
    except:
        return NOT_A_NUMBER
        
def xReadDatFile(fileName):
    # Read a data file with column headings and yield a list of named tuples with the file contents
    fp = open(fileName,'r')
    headerLine = True
    for l in fp:
        if headerLine:
            colHeadings = l.split()
            DataTuple = namedtuple("Bunch",colHeadings)
            headerLine = False
        else:
            yield DataTuple(*[pFloat(v) for v in l.split()])
    fp.close()

def list2cols(datAsList):
    datAsCols = []
    if datAsList:
        for f in datAsList[0]._fields:
            datAsCols.append(np.asarray([getattr(d,f) for d in datAsList]))
        return datAsList[0]._make(datAsCols)
    
def aReadDatFile(fileName):
    # Read a data file into a collection of numpy arrays
    return list2cols([x for x in xReadDatFile(fileName)])

EARTH_RADIUS = 6378100
DTR = np.pi/180.0
RTD = 180.0/np.pi

class GoogleMap(object):
    def __init__(self):
        self.conn = httplib.HTTPConnection("maps.googleapis.com")
    def close(self):
        self.conn.close()
    def getMap(self,latCen,lonCen,zoom,nx,ny,scale=1,satellite=True):
        if satellite:
            self.conn.request("GET","/maps/api/staticmap?center=%.6f,%.6f&zoom=%d&maptype=satellite&size=%dx%d&scale=%d&sensor=false" % 
                              (latCen,lonCen,zoom,nx,ny,scale))
        else:
            self.conn.request("GET","/maps/api/staticmap?center=%.6f,%.6f&zoom=%d&size=%dx%d&scale=%d&sensor=false" % 
                              (latCen,lonCen,zoom,nx,ny,scale))
        r1 = self.conn.getresponse()
        if r1.status != 200:
            raise RuntimeError("%d %s" % (r1.status,r1.reason))
        return r1.read()
            
def xform(lng,lat,minlng,maxlng,minlat,maxlat,imsize):
    """Get pixel in image of size "imsize" corresponding to "lng", "lat"
       where pixel (0,0) is (minlng,minlat) and (imsize[0]-1,imsize[1]-1)
       is (maxlng,maxlat)"""
    nx,ny = imsize
    x = int((nx-1)*(lng-minlng)/(maxlng-minlng))
    y = int((ny-1)*(lat-maxlat)/(minlat-maxlat))
    return x,y

    

def selectBy(data, sel):
    """Select data using the boolean vector sel.
    """
    assert isinstance(data, tuple)
    selectedValues = {}
    for f in data._fields:
        selectedValues[f] = getattr(data, f)[sel]
    return data._replace(**selectedValues)
    
def filterBy(data, keys, pred):
    """Filter data using the specified predicate on the attribute named key.
    """
    assert isinstance(data, tuple)
    # Compute boolean array sel which selects elements satisfying pred
    vpred = np.vectorize(pred)
    sel = vpred(*[getattr(data, key) for key in keys])
    filteredValues = {}
    for f in data._fields:
        filteredValues[f] = getattr(data, f)[sel]
    return data._replace(**filteredValues)

def sortBy(data, key):
    """Sort data by the attribute named key.
    """
    assert isinstance(data, tuple)
    perm = np.argsort(getattr(data, key))
    sortedValues = {}
    for f in data._fields:
        sortedValues[f] = getattr(data, f)[perm]
    return data._replace(**sortedValues)

def findMatches(tol, lat1, lng1, lat2, lng2):
    """Find which points (lat1, lng1) have a corresponding point in (lat2, lng2) withing the 
    specified tolerance tol"""
    medLat = np.median(lat2)
    medLng = np.median(lng2)
    mpd = distVincenty(medLat,medLng,medLat,medLng+1.0e-3)/1.0e-3 # Meters per degree of longitude
    elow = 0
    ehigh = 0
    dlng = tol/mpd
    sel = []
    for lat, lng in zip(lat1, lng1):
        while elow < len(lat2)  and lng2[elow]  <  lng-dlng:  elow += 1
        while ehigh < len(lat2) and lng2[ehigh] <= lng+dlng: ehigh += 1
        for e in range(elow,ehigh):
            if distVincenty(lng, lat, lng2[e], lat2[e]) < tol: # We have found a matching point
                sel.append(True)
                break
        else:
            sel.append(False)
    sel = np.asarray(sel)
    return sel

class DrawOnMap(object):
    def __init__(self, minLat, maxLat, minLng, maxLng):
        self.latCen = 0.5*(minLat + maxLat)
        self.lngCen = 0.5*(minLng + maxLng)
        self.latRange = maxLat - minLat
        self.lngRange = maxLng - minLng
        self.satellite = 0
        
    def run(self):
        self.gMap = GoogleMap()
        self._draw()
            
    def _draw(self):
        mx,my = 640, 640
        scale = 2
        xzoom = np.log((mx*360.0)/(256.0*self.lngRange))/np.log(2.0)
        yzoom = np.log((my*360.0*np.cos(self.latCen*DTR))/(256.0*self.latRange))/np.log(2.0)
        self.zoom = np.floor(min(xzoom, yzoom))
        a = pl.imread(cStringIO.StringIO(self.gMap.getMap(self.latCen,self.lngCen,self.zoom,mx,my,scale,self.satellite)))
        # 1 pxl = 360/(256*scale*2**zoom) degrees longitude
        # 1 pxl = 360*cos(latitude)/(256*scale*2**zoom) degrees latitude
        dlngpp = 360.0/(256.0*scale*2**(self.zoom))
        dlatpp = dlngpp*np.cos(self.latCen*np.pi/180.0)
        minlng, maxlng = self.lngCen-(mx*scale/2)*dlngpp, self.lngCen+(mx*scale/2)*dlngpp
        minlat, maxlat = self.latCen-(my*scale/2)*dlatpp, self.latCen+(my*scale/2)*dlatpp
        pl.imshow(a, extent=[minlng, maxlng, minlat, maxlat])
        pl.gca().set_aspect(1.0/np.cos(self.latCen * DTR))
        pl.gca().xaxis.set_major_locator(mpl.ticker.MaxNLocator(4))
        pl.gca().xaxis.set_major_formatter(mpl.ticker.ScalarFormatter(useOffset=False))
        pl.gca().yaxis.set_major_locator(mpl.ticker.MaxNLocator(4))
        pl.gca().yaxis.set_major_formatter(mpl.ticker.ScalarFormatter(useOffset=False))

if __name__ == "__main__":
    # fname1 = r"C:\UserData\AnalyzerServer\FDDS2006-20130430-111046Z-DataLog_User_Minimal.peaks_current_algorithm"
    # fname2 = r"C:\UserData\AnalyzerServer\FDDS2006-20130430-111046Z-DataLog_User_Minimal.peaks_bad_algorithm"

    fname1 = r"C:\UserData\AnalyzerServer\PGE_Duplicate\FDDS2006-20130909-102849Z-DataLog_User_Minimal.peaks.current_algorithm"
    fname2 = r"C:\UserData\AnalyzerServer\PGE_Duplicate\FDDS2006-20130909-102849Z-DataLog_User_Minimal.peaks.bad_algorithm"

    tol = 5.0 # Tolerance of 10m
    minAmp = 0.03
    
    coll1 = aReadDatFile(fname1)
    coll2 = aReadDatFile(fname2)
    # Select points which have amplitude above a threshold
    coll1 = filterBy(coll1, ["AMPLITUDE"], lambda a: a>=minAmp)
    coll2 = filterBy(coll2, ["AMPLITUDE"], lambda a: a>=minAmp)
    # Sort both collections by longitude
    coll1 = sortBy(coll1, "GPS_ABS_LONG")
    coll2 = sortBy(coll2, "GPS_ABS_LONG")

    # Go through each position of collection 1, finding the nearest point in collection 2
    result = []
    elow = ehigh = 0

    lat1 = coll1.GPS_ABS_LAT
    lng1 = coll1.GPS_ABS_LONG
    lat2 = coll2.GPS_ABS_LAT
    lng2 = coll2.GPS_ABS_LONG
    
    sel1 = findMatches(tol, lat1, lng1, lat2, lng2)
    coll1Match = selectBy(coll1, sel1)
    coll1Miss = selectBy(coll1, ~sel1)
    
    sel2 = findMatches(tol, lat2, lng2, lat1, lng1)
    coll2Match = selectBy(coll2, sel2)
    coll2Miss = selectBy(coll2, ~sel2)

    print len(coll1Match.EPOCH_TIME)
    print len(coll1Miss.EPOCH_TIME)
    print len(coll2Match.EPOCH_TIME)
    print len(coll2Miss.EPOCH_TIME)
    
    d = DrawOnMap(lat2.min(), lat2.max(), lng2.min(), lng2.max())
    d.run()
    
    pl.plot(coll1Match.GPS_ABS_LONG, coll1Match.GPS_ABS_LAT, 'o')
    pl.plot(coll1Miss.GPS_ABS_LONG, coll1Miss.GPS_ABS_LAT, 'bx', ms=4)
    pl.plot(coll2Miss.GPS_ABS_LONG, coll2Miss.GPS_ABS_LAT, 'rx', ms=4)
    pl.xlabel('Longitude')
    pl.ylabel('Latitude')
    pl.show()