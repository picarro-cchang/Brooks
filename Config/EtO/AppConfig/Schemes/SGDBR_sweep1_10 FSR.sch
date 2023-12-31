$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 100
cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
laser = 0
id = 110
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

schemeRows = []
fstart = 6057.0
Nhops = 1
fsr_steps = 10
dwell = 1
schemeRows += makeScan(fstart, fsr, 
                       [(n*fsr_steps, dwell) for n in range(Nhops+1)],
                       id, laser)
#schemeRows += schemeRows[::-1]                       
infotxt = 'NJUMP_%.3d_DWELL_%d_NHOPS_%d_NUSTART_%d' % (fsr_steps,dwell,Nhops,fstart*1000)
schemeInfo = dict(info=infotxt, span=[fstart, fstart+fsr_steps*fsr])
$$$
