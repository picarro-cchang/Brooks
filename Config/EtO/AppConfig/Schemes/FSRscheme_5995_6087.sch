$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = 0.02060690
laser = 0
id = 0
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,extra1=0):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser,extra1=extra1))
    return result

schemeRows = []

fstart = 5995.01078
fsr_steps = 894
subschemesteps = 5

for nss in range(subschemesteps):
    thisStart = fstart + nss*fsr_steps*fsr
    schemeRows += makeScan(thisStart, fsr, 
                           [(n, 1) for n in np.arange(fsr_steps)],
                           100, laser,extra1=id+nss)

    schemeRows[-1].subschemeId |= fit
$$$
