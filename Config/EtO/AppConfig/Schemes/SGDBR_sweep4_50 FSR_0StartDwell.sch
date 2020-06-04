$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 5
cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
laser = 0
id = 150
pztCen = 8192
fit = 32768

schemeRows = []
Ndweller = 0
def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        if Ndweller != 0:
            result.append(Row(base+s*incr,Ndweller,id,vLaser))
        result.append(Row(base+s*incr,d-Ndweller,id,vLaser))
    return result

schemeRows = []

Nhops = 4
fsr_steps = 50
fstart = 6083.0 - int(Nhops/2)*fsr_steps*fsr
dwell = 100
schemeRows += makeScan(fstart, fsr, 
                       [(n*fsr_steps, dwell) for n in range(Nhops+1)],
                       id, laser)
schemeRows += schemeRows[::-1]                       
infotxt = 'NJUMP_%.3d_DWELL_%d_FIRSTDWELL_%d_NHOPS_%d_NUSTART_%d' % (fsr_steps,dwell,Ndweller, Nhops,fstart*1000)
schemeInfo = dict(info=infotxt, span=[fstart, fstart+fsr_steps*fsr])
$$$
