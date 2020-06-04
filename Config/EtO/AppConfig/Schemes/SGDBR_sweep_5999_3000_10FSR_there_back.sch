$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 100
cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
laser = 0
id = 10
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

schemeRows = []
fstart = 6050.0
fsr_steps = 200
schemeRows += makeScan(fstart, fsr, 
                       [(n, 1) for n in np.arange(0,fsr_steps,50)],
                       id, laser)
schemeRows += schemeRows[::-1]                       
schemeInfo = dict(name="SGDBR_sweep_5999_3000_50FSR_there_back", span=[fstart, fstart+fsr_steps*fsr])
$$$
