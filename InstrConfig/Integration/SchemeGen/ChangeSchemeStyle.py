from numpy import *
from pylab import *
from glob import glob

dname = "C:\CFBDS01\Apache\InstrConfig\Schemes"
for fname in glob("%s\*.sch" % dname):
    result = []
    for i,x in enumerate(file(fname,"r")):
        if i in [0,1]:
            result.append(x.strip())
        elif i > 2:
            atoms = x.split()
            if not atoms: break
            subschemeId = int(atoms[2])
            cal  = (subschemeId & 1024) != 0
            last = (subschemeId & 2048) != 0
            subschemeId = subschemeId - (subschemeId & 3072)
            if cal: subschemeId += 4096 
            if last: subschemeId += 32768
            atoms[2] = "%d" % subschemeId
            result.append(" ".join(atoms))
    op = file(fname.replace(".sch",".out"),"w")
    op.write("\n".join(result))
    
# CO2peak = 6237.408
# CH4peak = 6057.09
# FSR = 0.0201071575896
# ref = r'CFADS03_CO2nocal_CH4cal1.sch'
# sp = file(ref,"r")

# fname = r'CFADS03_CO2nocal_CH4cal1_v2.sch'
# lp = file(fname,"w")

# for line in sp:
    # toks = line.split()
    # if len(toks) <= 1:
        # print >> lp, line.strip()
    # else:    
        # toks += (6-len(toks)) * ["0"]
        # waveNum = float(toks[0])
        # if abs(waveNum-CO2peak) < abs(waveNum-CH4peak):
            # waveNum = CO2peak + FSR * round((waveNum - CO2peak)/FSR)
        # else:
            # waveNum = CH4peak + FSR * round((waveNum - CH4peak)/FSR)
        # toks[0] = "%.5f" % (waveNum,)
        # print >>lp, " ".join(toks)

# sp.close()
# lp.close()
# print "Written file %s" % (fname,)
