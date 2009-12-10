from numpy import *
from pylab import *

CO2peak = 6237.408
CH4peak = 6057.09
FSR = 0.020598
ref = r'..\..\Schemes\CFBDS02_FSR.sch'
sp = file(ref,"r")

fname = r'..\..\Schemes\001_Alpha_CO2_CH4_flux.sch'
lp = file(fname,"w")

for line in sp:
    toks = line.split()
    if len(toks) <= 1:
        print >> lp, line.strip()
    else:    
        toks += (6-len(toks)) * ["0"]
        waveNum = float(toks[0])
        if abs(waveNum-CO2peak) < abs(waveNum-CH4peak):
            waveNum = CO2peak + FSR * round((waveNum - CO2peak)/FSR)
        else:
            waveNum = CH4peak + FSR * round((waveNum - CH4peak)/FSR)
        toks[0] = "%.5f" % (waveNum,)
        print >>lp, " ".join(toks)

sp.close()
lp.close()
print "Written file %s" % (fname,)
