$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
laser = 0
id = 10
pztCen = 8192
fit = 32768

threshold = 6000
pzt_per_fsr = 17800

#  Special version for interleaved FSR data acquisition

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser,threshold,-0.5*pzt_per_fsr))
    return result

schemeRowsUp = []
fstart = 5995.0
fsr_steps = 5309
schemeRowsUp += makeScan(fstart, fsr, 
                       [(n, 2) for n in np.arange(fsr_steps)],
                       id, laser)
schemeRows = deepcopy(schemeRowsUp[::-1])
$$$
