$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = 0.0206069
laser = 0
id = 2
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

schemeRows = []

fstart = 6041.08780
fsr_steps = 2236
schemeRows += makeScan(fstart, fsr, 
                       [(n, 1) for n in np.arange(fsr_steps)],
                       id, laser)

schemeRows[-1].subschemeId |= fit
$$$
