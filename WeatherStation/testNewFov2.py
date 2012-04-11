import numpy as np
import pylab as pl
import findFovWidth as fw
#
NOT_A_NUMBER = 1e1000/1e1000
EARTH_RADIUS = 6378100
DTR = np.pi/180.0
RTD = 180.0/np.pi

# fname = r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120401\OUT\FCDS2006-20120401-095924Z-DataLog_User_Minimal.dat"
fname = r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120401\OUT\extract1.dat"
A = np.genfromtxt(fname,names=True)
t = A['EPOCH_TIME']
lat = A['GPS_ABS_LAT']
lng = A['GPS_ABS_LONG']

cosLat = np.cos(lat[0]*DTR)
windN = A['WIND_N']
windE = A['WIND_E']
windSdev = A['WIND_DIR_SDEV']
xx = DTR*(lng-lng[0])*EARTH_RADIUS*cosLat
yy = DTR*(lat-lat[0])*EARTH_RADIUS
dstd = DTR*windSdev
N = 10
dmax = 200

times = []
width = []
for i in range(len(xx)-2*N-1):
    w = fw.maxDist(xx[i:i+2*N+1],yy[i:i+2*N+1],N,windE[i+N],windN[i+N],dstd[i+N],dmax,thresh=0.7,tol=1.0)
    times.append(t[i+N])
    width.append(w)

pl.figure(1); pl.plot(t,xx,'.')
pl.figure(2); pl.plot(t,yy,'.')
pl.figure(3); pl.plot(t,(180/np.pi)*np.angle(windN+1j*windE),'.')
pl.figure(4); pl.plot(t,windSdev,'.')
pl.figure(5); pl.plot(np.asarray(times),np.asarray(width),'.')
pl.show()