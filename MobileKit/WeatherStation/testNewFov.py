import numpy as np
fname = r"R:\crd_G2000\FCDS\1102-FCDS2006_v4.0\Survey20120401\OUT\FCDS2006-20120401-095924Z-DataLog_User_Minimal.dat"
A = np.genfromtxt(fname,names=True)
lngMin, lngMax, latMin, latMax = -121.3989,-121.3908,38.7104,38.7193
# Select rows in middle left of plat
lat = A['GPS_ABS_LAT']
lng = A['GPS_ABS_LONG']
# Find points along road with small coverage
print np.flatnonzero((lng>lngMin) & (lng<0.5*lngMin+0.5*lngMax) & (lat>0.6*latMin + 0.4*latMax) & (lat<0.5*latMin + 0.5*latMax))
