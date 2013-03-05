import numpy as np
import pylab as pl

pl.close('all')
fname = r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120401\GPS_WSInst\windStats-Composite_fac1_10s.txt"
A = np.genfromtxt(fname,names=True)
wind = A["WIND_N"]+1j*A["WIND_E"]
carSpeed = A["CAR_SPEED"]
dirSdev = A["WIND_DIR_SDEV"]
sel = np.isfinite(wind) & (abs(wind)>1.0) & (abs(wind)<3.0) & (dirSdev>0)

print np.polyfit(abs(carSpeed[sel]),dirSdev[sel],1)

pl.loglog(abs(carSpeed[sel]),dirSdev[sel],'.')
pl.grid(True)
pl.show()

