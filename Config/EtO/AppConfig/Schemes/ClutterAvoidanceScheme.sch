$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 30
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal_AVX9003.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
#fsr = 0.020610457
laser = 0
id = 100
CO2 = 12
H2O = 11
CH4 = 25
pztCen = 8192
fit = 32768

f0 = 6058.191276
ffile = open("..\..\AppConfig\Schemes\SelectedFrequencies.txt","r")


#this scheme is on an fsr grid aligned with 6056.50640
flist = [6056.50600, 6057.09,6057.8]
rlist = [0.1, 0.144, 0.105]
dwell_center = 5

def makeScan(base,incr,stepAndDwell,id,vLaser,extra1=0,extra2=0,extra3=0,extra4=0):
    result = []
    for s,d in stepAndDwell:
        nuset = base+s*incr
        multiplier = 1
        for nu_target, nu_range in zip(flist, rlist):
            if abs(nu_target - nuset) <= incr*2:
                multiplier = 2
                if abs(nu_target - nuset) <= incr/2: #add points on peak
                    multiplier = max(multiplier,dwell_center)
#            if abs(nu_target-nuset)>= 0.8*nu_range:
#                multiplier = 2
        d *= multiplier
        result.append(Row(nuset,d,id,vLaser,extra1=extra1,extra2=extra2,extra3=extra3,extra4=extra4))
    return result
    
### CO2 region
co2_up = makeScan(flist[0]-rlist[0],fsr,
                    [(n,1) for n in np.arange(round(2*rlist[0]/fsr))],
                   CO2, laser, extra1=13, extra2=11, extra3=0,extra4=3028253200)    
co2_down=deepcopy(co2_up[::-1])
co2_down[-1].subschemeId |= fit

### CH4 region
ch4_up = makeScan(flist[1]-rlist[1],fsr,
                    [(n,1) for n in np.arange(round(2*rlist[1]/fsr))],
                    CH4, laser, extra1=13, extra2=11, extra3=0,extra4=3028253200)    
ch4_down=deepcopy(ch4_up[::-1])
ch4_down[-1].subschemeId |= fit

### H2O region
h2o_up = makeScan(flist[2]-rlist[2],fsr,
                    [(n,1) for n in np.arange(round(2*rlist[2]/fsr))],
                    H2O, laser, extra1=13, extra2=11, extra3=0,extra4=3028253200)    
h2o_down=deepcopy(h2o_up[::-1])
h2o_down[-1].subschemeId |= fit

sweep_up = []
while True:
    line = ffile.readline()
    if not line: break
    values = line.split()
    mode = float(values[0])
    sweep_up.append(Row(f0+mode*fsr,1,id,laser,extra1=8,extra2=5,extra3=0,extra4=3028253200))
ffile.close()
sweep_down = deepcopy(sweep_up[::-1])
sweep_down[-1].subschemeId |= fit

schemeRows = []
schemeRows = co2_up + co2_down + ch4_up + ch4_down + h2o_up + h2o_down + sweep_up + sweep_down

$$$
