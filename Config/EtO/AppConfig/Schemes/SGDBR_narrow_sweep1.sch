$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = 0.0202458
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
fstart = 6040.0
fsr_steps = 1250
schemeRows += makeScan(fstart, fsr, 
                       [(n, 4) for n in np.arange(fsr_steps)],
                       id, laser)
$$$
