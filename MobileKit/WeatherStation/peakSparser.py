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

class PeakSparser(object):
    def __init__(self, iniFile):
        self.config = ConfigObj(iniFile)
        self.maxDist = 10.0    # Exclude peaks within maxDist
        self.outFile = self.config["FILES"]["AGGREGATE_FILE"]
        
    def run(self):
        # Go through all the runs, and make a dictionary containing the fields from the peak files
        #  which are present in all of the runs and which satisfy the amplitude filter. Create an 
        #  additional field "RUN" which labels which run each peak belongs to
        pkDict = {"RUN":[]}
        for r in self.config:
            if r.startswith("RUN"):
                sec = self.config[r]
                runNum = int(r[4:])
                for f in self.config[r]:
                    if f.startswith("PEAKS"):
                        fname,minAmpl = sec[f]
                        minAmpl = float(minAmpl)
                        p = aReadDatFile(fname + '.peaks')
                        good = p.AMPLITUDE>=minAmpl
                        maxLen = 0
                        for n in p._fields:
                            if n not in pkDict:
                                pkDict[n] = []
                            data = getattr(p,n)[good]
                            pkDict[n].append(data)
                            maxLen = max(maxLen,len(data))
                        pkDict["RUN"].append(runNum*np.ones(maxLen))
                            
        maxLen = 0
        for n in pkDict:
            pkDict[n] = np.concatenate(tuple(pkDict[n]))
            maxLen = max(maxLen,len(pkDict[n]))
        # Remove fields which are not in every file
        badFields = []
        for n in pkDict:
            if len(pkDict[n])<maxLen: badFields.append(n)
        for n in badFields: del pkDict[n]
        
        print "Original number of peaks satisfying amplitude filter", maxLen
        
        
        # Get median latitude and longitude for estimating distance scale
        ilng, ilat, iampl = pkDict['GPS_ABS_LONG'], pkDict['GPS_ABS_LAT'], pkDict['AMPLITUDE']
        medLat = np.median(ilat)
        medLng = np.median(ilat)
        mpd = distVincenty(medLat,medLng,medLat,medLng+1.0e-3)/1.0e-3 # Meters per degree of longitude

        # Find permutations that sort by longitude as primary key
        perm = np.argsort(ilng)

        # Now try to coalasce peaks within the included set
        result = []
        elow = ehigh = 0
        dlng = self.maxDist/mpd
        for i in perm:
            while elow<len(perm)  and ilng[perm[elow]]  <  ilng[i]-dlng:  elow += 1
            while ehigh<len(perm) and ilng[perm[ehigh]] <= ilng[i]+dlng: ehigh += 1
            for e in range(elow,ehigh):
                j = perm[e]
                lng,lat,ampl = ilng[j],ilat[j],iampl[j]
                assert ilng[i]-dlng <= lng < ilng[i]+dlng
                if 0<distVincenty(lng,lat,ilng[i],ilat[i])<=self.maxDist:
                    if iampl[i]<ampl: break
                    elif iampl[i]==ampl and i<j: break
            else: 
                result.append(i)
                
        print "Number of peaks after coalascing", len(result)
        # Quantities to place in peak data file, if they are available
        headings = ["EPOCH_TIME","DISTANCE","GPS_ABS_LONG","GPS_ABS_LAT","CH4","AMPLITUDE","SIGMA","WIND_N","WIND_E","WIND_DIR_SDEV","RUN"]
        hFormat  = ["%-14.2f","%-14.3f","%-14.6f","%-14.6f","%-14.3f","%-14.4f","%-14.3f","%-14.4f","%-14.4f","%-14.3f","%-14.0f"]

        hList = []
        hfList = []
        for h,hf in zip(headings,hFormat):
            if h in pkDict:
                hList.append(h)
                hfList.append(hf)
        
        handle = open(self.outFile, 'wb', 0) #open file with NO buffering
        handle.write((len(hList)*"%-14s"+"\r\n") % tuple(hList))

        ampList = np.asarray([pkDict['AMPLITUDE'][i] for i in result])
        result = np.asarray(result)[np.argsort(-ampList)]
        for i in result:
            handle.write(("".join(hfList)+"\r\n") % tuple([pkDict[h][i] for h in hList]))
        handle.close()
        
if __name__ == "__main__":
    app = PeakSparser(sys.argv[1])
    app.run()