# SimGpsWsInst generates simulated data files for the GPS and weather station in 
#  instantaneous mode for testing of the wind processing algorithms

# We simulate a vehicle moving in a spiral. The point over the midpoint of the back
#  axle is z(t) = R(t)*exp(1j*phi(t)) where
# R(t) = (a*Rmin + t*Rmax)/(t+a)
# phi'(t) = (b*w0 + t*w_f)/(t+b)
#
# From these, phi(t) = b*(w0-w_f)*log(1+t/b) + w_f*t

from Host.Common.namedtuple import namedtuple
import numpy as np

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
        if np.abs(Lambda-lambdaP)<=1.e-12: break
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

class VehicleModel(object):
    # R(t) = (a*Rmin + t*Rmax)/(t+a)
    # phi'(t) = (b*w0 + t*w_f)/(t+b)
    #
    # From these, phi(t) = b*(w0-w_f)*log(1+t/b) + w_f*t
    def __init__(self):
        self.Rmin = 10.0
        self.Rmax = 100.0
        self.w0 = 0.33
        self.wf = 0.15
        self.a = 200
        self.b = 200
        self.wsOffset = 1.5j    # Position of weather station relative to rear axle
                                # Real part is lateral offset, Imaginary part is longitudinal offset

    def phi(self,t):
        return self.b*(self.w0-self.wf)*np.log(1.0+(t/self.b)) + self.wf*t
    
    def R(self,t):
        return (self.a*self.Rmin + t*self.Rmax)/(self.a + t)

    def phidot(self,t):
        return (self.b*self.w0 + t*self.wf)/(self.b + t)
        
    def Rdot(self,t):
        return self.a*(self.Rmax-self.Rmin)/(self.a + t)**2
    
    def zPos(self,t):
        return self.R(t)*np.exp(1j*self.phi(t))
        
    def zVel(self,t):
        return (self.Rdot(t)+1j*self.phidot(t)*self.R(t))*np.exp(1j*self.phi(t))
        
    def wsPos(self,t):
        return (self.R(t)+self.wsOffset)*np.exp(1j*self.phi(t))
    
    def wsVel(self,t):
        return (self.Rdot(t)+1j*self.phidot(t)*(self.R(t)+self.wsOffset))*np.exp(1j*self.phi(t))
    
GpsTuple = namedtuple('GpsTuple',["EPOCH_TIME","ALARM_STATUS","INST_STATUS","GPS_ABS_LAT","GPS_ABS_LONG","GPS_FIT"])

class GpsSim(object):
    def __init__(self):
        self.alarmStatus = 0
        self.instStatus = 963
        self.gpsfit = 2
        self.startEtm = 1300000000.0
        self.lat0 = 37.0
        self.lon0 = -120.0
        self.dt = 1.0
        self.npoints = 800
        self.vm = VehicleModel()
        
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
        pathlen = 2*np.pi*100.0
        tPath = pathlen/8.0
        #
        aStatus = self.alarmStatus
        iStatus = self.instStatus
        fit = self.gpsfit
        for k in range(self.npoints):
            t = k*self.dt
            etm = self.startEtm + t
            # Move clockwise around circle of radius self.radius, starting from 
            #  northernmost point at time self.startEtm.
            z = self.vm.zPos(t)
            lon = self.lon0 + np.imag(z)/d1
            lat = self.lat0 + np.real(z)/d2
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
        self.dt = 1.0
        self.npoints = 800
        self.psi = np.pi/6          # Angle between anemometer axis and vehicle axis
        self.mu = 1.0               # Earth's magnetic field (North pointing)
        self.beta = 0.2+0.1j        # Stray field due to vehicle
        self.delay = 1.5
        self.vm = VehicleModel()
        
    def run(self):
        tWind = 2.0*np.exp(1j*np.pi/4)    # Wind and bearing
        alpha = -tWind              # Velocity of wind relative to ground
        etmField = ["EPOCH_TIME"]
        intFields = ["ALARM_STATUS","INST_STATUS"]
        fp = open("ws.dat","w")
        # Write the headings
        for f in WsTuple._fields:
            fp.write("%-26s" % f)
        fp.write("\n")
        #
        aStatus = self.alarmStatus
        iStatus = self.instStatus
        for k in range(self.npoints):
            t = k*self.dt
            etm = self.startEtm + t
            # The sonic anemometer velocity is computed at t-self.delay
            zVel1 = self.vm.zVel(t-self.delay)
            phi1 = np.angle(zVel1)
            wsVel = self.vm.wsVel(t-self.delay)
            # Calculate the sonic wind bearing along anemometer principal axes
            sWind = -np.exp(-1j*(phi1+self.psi))*(alpha - wsVel)

            # Calculate magnetometer heading using sign convention of weather station
            #  This is calculated without the delay
            zVel2 = self.vm.zVel(t)
            phi2 = np.angle(zVel2)
            head = np.angle((self.mu+self.beta*np.exp(1j*phi2))*np.exp(-1j*(phi2+self.psi)))
            wHead = np.exp(1j*head)
            #
            vWind = sWind/wHead
            wsdat = WsTuple(etm,aStatus,iStatus,np.abs(vWind),np.cos(np.angle(vWind)),
                            np.sin(np.angle(vWind)),np.cos(np.angle(wHead)),
                            np.sin(np.angle(wHead)))
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
    
