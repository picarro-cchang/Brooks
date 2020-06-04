$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = 0.020606900
laser = 0
id = 4
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,extra1=0):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser,extra1=extra1))
    return result

schemeRows = []

fstart = 6068.70105
fsr_steps = 894
schemeRows += makeScan(fstart, fsr, 
                       [(n, 1) for n in np.arange(fsr_steps)],
                       100, laser, extra1=id)

schemeRows[-1].subschemeId |= fit
$$$
