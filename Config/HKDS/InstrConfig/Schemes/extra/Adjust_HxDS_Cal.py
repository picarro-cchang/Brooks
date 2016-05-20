from numpy import *
from pylab import *

peak = 7183.9728
FSR = 0.0206025035275
ref = r'R:\crd\227_HB041_v1.0\Schemes\HBDSxx_FSR_Cal.sch'
sp = file(ref,"r")

fname = "HBDSbeta7_FSR_Cal.sch"
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
