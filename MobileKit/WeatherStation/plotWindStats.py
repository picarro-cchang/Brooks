import numpy as np
import pylab as pl

pl.close('all')
fname = r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120401\GPS_WSInst\windStats-Composite_fac1_10s.txt"
A = np.genfromtxt(fname,names=True)
wind = A["WIND_N"]+1j*A["WIND_E"]
carSpeed = A["CAR_SPEED"]
dirSdev = A["WIND_DIR_SDEV"]
sel = np.isfinite(wind) & (carSpeed<5) & (carSpeed>3) & (abs(wind)>0) & (dirSdev>0)

x = np.log(abs(wind[sel]))
y = np.log(dirSdev[sel])
print np.polyfit(x,y,1)
c = np.mean(x+y)
print c

pl.loglog(abs(wind[sel]),dirSdev[sel],'.',abs(wind[sel]),np.exp(c)/abs(wind[sel]))
pl.grid(True)
pl.show()

