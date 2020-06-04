$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 10
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
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
fstart = 6003.0 
fend = 6032.0
fsr_steps = (fend-fstart)//(fsr)
schemeRows += makeScan(fstart, fsr, 
                       [(n, 5) for n in np.arange(fsr_steps)],
                       id|pztCen, laser)
fstart = 6049.0
fend = 6187.0
fsr_steps = (fend-fstart)//(fsr)
schemeRows += makeScan(fstart, fsr, 
                       [(n, 5) for n in np.arange(fsr_steps)],
                       id|pztCen, laser)
#schemeRows  += schemeRows[::-1]
                       
#schemeInfo = dict(name="SGDBR_sweep1", span=[fstart, fstart+fsr_steps*fsr])
#schemeInfo = {'setSolenoidValve': [1], 'setCavityPressure': [130.0, 140.0, 150.0]}
$$$
