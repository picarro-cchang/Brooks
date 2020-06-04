$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
laser = 0
id = 181
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

schemeRows = []
fstart = 6060.0 
fend = 6100.0
fsr_steps = (fend-fstart)//fsr #8000 #5309
#fsr_steps = 2000 #5309
schemeRows += makeScan(fstart, fsr, 
                       [(n, 2) for n in np.arange(fsr_steps)],
                       id, laser)
schemeRows  += schemeRows[::-1]
                       
#schemeInfo = dict(name="SGDBR_sweep1", span=[fstart, fstart+fsr_steps*fsr])
#schemeInfo = {'setSolenoidValve': [1], 'setCavityPressure': [130.0, 140.0, 150.0]}
$$$
