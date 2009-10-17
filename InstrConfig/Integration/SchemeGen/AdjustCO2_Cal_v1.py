from numpy import *
from pylab import *

peak = 6237.40800
FSR = 0.0203394651562
ref = r'R:\crd\CFADSxx\Schemes\CFADSxx_CO2_NW_Cal.sch'
sp = file(ref,"r")

fname = "CFADS03_v2_CO2_Cal_Out_v1.sch"
lp = file(fname,"w")

print >>lp, int(sp.readline()) # nrepeat
numEntries = int(sp.readline())
print >>lp, numEntries
for i in range(numEntries):
  toks = sp.readline().split()
  toks += (6-len(toks)) * ["0"]
  waveNum = float(toks[0])
  waveNum = peak + FSR * round((waveNum - peak)/FSR)
  toks[0] = "%.5f" % (waveNum,)
  print >>lp, " ".join(toks)
sp.close()
lp.close()
print "Written file %s" % (fname,)
