# SimGPSWS generates simulated data files for the GPS and weather station for testing of the
#  wind processing algorithms

from Host.Common.namedtuple import namedtuple
import numpy

def distVincenty(lat1, lon1, lat2, lon2):
    # WGS-84 ellipsiod. lat and lon in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563;
    toRad = numpy.pi/180.0
    L = (lon2-lon1)*toRad
    U1 = numpy.arctan((1-f) * numpy.tan(lat1*toRad))
    U2 = numpy.arctan((1-f) * numpy.tan(lat2*toRad));
    sinU1 = numpy.sin(U1)
    cosU1 = numpy.cos(U1)
    sinU2 = numpy.sin(U2)
    cosU2 = numpy.cos(U2)
  
    Lambda = L
    iterLimit = 100;
    for iter in range(iterLimit):
        sinLambda = numpy.sin(Lambda)
        cosLambda = numpy.cos(Lambda)
        sinSigma = numpy.sqrt((cosU2*sinLambda) * (cosU2*sinLambda) + 
                        (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
        if sinSigma==0: 
            return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = numpy.arctan2(sinSigma, cosSigma)
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
        if numpy.abs(Lambda-lambdaP)<=1.e-12: break
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


GpsTuple = namedtuple('GpsTuple',["EPOCH_TIME","ALARM_STATUS","INST_STATUS","GPS_ABS_LAT","GPS_ABS_LONG","GPS_FIT"])

class GpsSim(object):
    def __init__(self):
        self.alarmStatus = 0
        self.instStatus = 963
        self.gpsfit = 2
        self.startEtm = 1300000000.0
        self.lat0 = 37.0
        self.lon0 = -120.0
        self.speed = 8.0        # Speed in m/s
        self.radius = 200.0     # Radius of circular path
        self.nlaps = 1
        self.dt = 1.0
        
    def run(self):
        etmField = ["EPOCH_TIME"]
        intFields = ["ALARM_STATUS","INST_STATUS"]
        fp = open("gps.dat","w")
        # Write the headings
        for f in GpsTuple._fields:
            fp.write("%-26s" % f)
        fp.write("\n")
        # Distances for a 0.01 degree change in longitude and latitude
        #  Convert to meters per degree
        d1 = distVincenty(self.lat0, self.lon0, self.lat0, self.lon0+0.01)/0.01
        d2 = distVincenty(self.lat0, self.lon0, self.lat0+0.01, self.lon0)/0.01
        # Time to do laps around the path
        pathlen = 2*numpy.pi*self.radius
        tPath = self.nlaps*pathlen/self.speed
        dtheta = self.speed*self.dt/self.radius
        #
        aStatus = self.alarmStatus
        iStatus = self.instStatus
        fit = self.gpsfit
        for k in range(int(numpy.ceil(tPath/self.dt))):
            etm = self.startEtm + k*self.dt
            # Move clockwise around circle of radius self.radius, starting from 
            #  northernmost point at time self.startEtm.
            lon = self.lon0 + self.radius*numpy.sin(k*dtheta)/d1
            lat = self.lat0 + self.radius*numpy.cos(k*dtheta)/d2
            gpsdat = GpsTuple(etm,aStatus,iStatus,lat,lon,fit)
            for f in GpsTuple._fields:
                if f in intFields:
                    fp.write("%-26d" % getattr(gpsdat,f))
                elif f in etmField:
                    fp.write("%-26.3f" % getattr(gpsdat,f))
                else:
                    fp.write("%-26.10e" % getattr(gpsdat,f))
            fp.write("\n")
        fp.close()

WsTuple = namedtuple('WsTuple',["EPOCH_TIME","ALARM_STATUS","INST_STATUS","WS_SPEED","WS_COS_DIR","WS_SIN_DIR","WS_COS_HEADING","WS_SIN_HEADING"])

class WsSim(object):
    def __init__(self):
        self.alarmStatus = 0
        self.instStatus = 963
        self.startEtm = 1300000000
        self.lat0 = 37.0
        self.lon0 = -120.0
        self.speed = 8.0        # Speed in m/s
        self.radius = 200.0     # Radius of circular path
        self.nlaps = 1
        self.dt = 1.0
        
    def run(self):
        DELAY = 2.0
        etmField = ["EPOCH_TIME"]
        intFields = ["ALARM_STATUS","INST_STATUS"]
        fp = open("ws.dat","w")
        # Write the headings
        for f in WsTuple._fields:
            fp.write("%-26s" % f)
        fp.write("\n")
        # Distances for a 0.01 degree change in longitude and latitude
        #  Convert to meters per degree
        d1 = distVincenty(self.lat0, self.lon0, self.lat0, self.lon0+0.01)/0.01
        d2 = distVincenty(self.lat0, self.lon0, self.lat0+0.01, self.lon0)/0.01
        # Time to do laps around the path
        pathlen = 2*numpy.pi*self.radius
        tPath = self.nlaps*pathlen/self.speed
        dtheta = self.speed*self.dt/self.radius
        #
        aStatus = self.alarmStatus
        iStatus = self.instStatus
        #
        perturb = 0.1 + 0.2j
        theta0 = numpy.pi/3
        for k in range(int(numpy.ceil(tPath/self.dt))):
            etm = self.startEtm + k*self.dt
            # Move clockwise around circle, starting from northernmost point
            zPos = self.radius*numpy.exp(1j*k*dtheta)
            zVel = 1j*(dtheta/self.dt)*self.radius*numpy.exp(1j*k*dtheta)
            phi = numpy.angle(zVel)
            # Calculate the magnetometer heading for a given field perturbation 
            theta = theta0 + numpy.angle(numpy.exp(1j*phi)+perturb)
            wHead = numpy.exp(-1j*theta)  # Note magnetometer sign convention
            #
            vWind = (5.0*numpy.exp(1j*numpy.pi/4) + zVel*numpy.exp(-1j*(DELAY/self.dt)*dtheta))*numpy.exp(1j*(theta-theta0-phi))
            wsdat = WsTuple(etm,aStatus,iStatus,numpy.abs(vWind),numpy.cos(numpy.angle(vWind)),
                            numpy.sin(numpy.angle(vWind)),numpy.cos(numpy.angle(wHead)),
                            numpy.sin(numpy.angle(wHead)))
            for f in WsTuple._fields:
                if f in intFields:
                    fp.write("%-26d" % getattr(wsdat,f))
                elif f in etmField:
                    fp.write("%-26.3f" % getattr(wsdat,f))
                else:
                    fp.write("%-26.10e" % getattr(wsdat,f))
            fp.write("\n")
        fp.close()

        
if __name__ == "__main__":
    gpsSim = GpsSim()
    gpsSim.run()
    wsSim = WsSim()
    wsSim.run()
    
