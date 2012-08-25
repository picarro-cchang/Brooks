from Host.Common.namedtuple import namedtuple
from configobj import ConfigObj
import numpy as np
import sys

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

class PeakSelector(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        self.maxDist = 20.0    # Exclude peaks within maxDist
        self.dupDist = 30.0    # Exclude peaks within maxDist
        self.outFile = self.config["FILES"]["OUT_FILE"]
        self.rankFile = self.config["FILES"]["RANK_FILE"]
        
    def run(self):
        # Get peaks to include
        inc = self.config["INCLUDE"]
        iDict = {}
        for f in inc:
            fname,minAmpl = inc[f]
            minAmpl = float(minAmpl)
            p = aReadDatFile(fname + '.peaks')
            good = p.AMPLITUDE>=minAmpl
            for n in p._fields:
                if n not in iDict:
                    iDict[n] = []
                iDict[n].append(getattr(p,n)[good])
        for n in iDict:
            iDict[n] = np.concatenate(tuple(iDict[n]))
            print n,len(iDict[n])
        # Get peaks to exclude
        exc = self.config["EXCLUDE"]
        eDict = {}
        for f in exc:
            fname,minAmpl = exc[f]
            minAmpl = float(minAmpl)
            p = aReadDatFile(fname + '.peaks')
            good = p.AMPLITUDE>=minAmpl
            for n in p._fields:
                if n not in eDict:
                    eDict[n] = []
                eDict[n].append(getattr(p,n)[good])
        for n in eDict:
            eDict[n] = np.concatenate(tuple(eDict[n]))
            print n,len(eDict[n])
        # Find permutations that sort by longitude as primary key
        iperm = np.argsort(iDict['GPS_ABS_LONG'])
        eperm = np.argsort(eDict['GPS_ABS_LONG'])
        #
        result1 = []
        ilng, ilat, iampl = iDict['GPS_ABS_LONG'], iDict['GPS_ABS_LAT'], iDict['AMPLITUDE']
        elng, elat = eDict['GPS_ABS_LONG'], eDict['GPS_ABS_LAT']
        # Get median latitude and longitude for estimating distance scale
        medLat = np.median(ilat)
        medLng = np.median(ilat)
        mpd = distVincenty(medLat,medLng,medLat,medLng+1.0e-3)/1.0e-3 # Meters per degree of longitude
        dlng = self.maxDist/mpd
        elow = ehigh = 0
        for i in iperm:
            while elow<len(eperm)  and elng[eperm[elow]]  <  ilng[i]-dlng:  elow += 1
            while ehigh<len(eperm) and elng[eperm[ehigh]] <= ilng[i]+dlng: ehigh += 1
            for e in range(elow,ehigh):
                lng,lat = elng[eperm[e]],elat[eperm[e]]
                assert ilng[i]-dlng <= lng < ilng[i]+dlng
                if distVincenty(lng,lat,ilng[i],ilat[i])<=self.maxDist: break
            else: 
                result1.append(i)
        print len(result1)
        
        # Now try to coalasce peaks within the included set
        result2 = []
        elow = ehigh = 0
        dlng = self.dupDist/mpd
        for i in result1:
            while elow<len(result1)  and ilng[result1[elow]]  <  ilng[i]-dlng:  elow += 1
            while ehigh<len(result1) and ilng[result1[ehigh]] <= ilng[i]+dlng: ehigh += 1
            for e in range(elow,ehigh):
                j = result1[e]
                lng,lat,ampl = ilng[j],ilat[j],iampl[j]
                assert ilng[i]-dlng <= lng < ilng[i]+dlng
                if 0<distVincenty(lng,lat,ilng[i],ilat[i])<=self.dupDist:
                    if iampl[i]<ampl: break
                    elif iampl[i]==ampl and i<j: break
            else: 
                result2.append(i)
        print len(result2)
        # Quantities to place in peak data file, if they are available
        headings = ["EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA","WIND_N","WIND_E","WIND_DIR_SDEV"]
        hFormat  = ["%-14.2f","%-14.3f","%-14.6f","%-14.6f","%-14.3f","%-14.4f","%-14.3f","%-14.4f","%-14.4f","%-14.3f"]

        hList = []
        hfList = []
        for h,hf in zip(headings,hFormat):
            if h in iDict:
                hList.append(h)
                hfList.append(hf)
        
        handle = open(self.outFile, 'wb', 0) #open file with NO buffering
        handle.write((len(hList)*"%-14s"+"\r\n") % tuple(hList))
        for i in result1:
            handle.write(("".join(hfList)+"\r\n") % tuple([iDict[h][i] for h in hList]))
        handle.close()

        handle = open(self.rankFile, 'wb', 0) #open file with NO buffering
        handle.write((len(hList)*"%-14s"+"\r\n") % tuple(hList))
        # Sort rank file in decreasing order of amplitude
        ampList = np.asarray([iDict['AMPLITUDE'][i] for i in result2])
        result2 = np.asarray(result2)[np.argsort(-ampList)]
        for i in result2:
            handle.write(("".join(hfList)+"\r\n") % tuple([iDict[h][i] for h in hList]))
        handle.close()
        
if __name__ == "__main__":
    app = PeakSelector(sys.argv[1])
    app.run()