$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = 0.0206069
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

peak75_center = 6057.8000

fstart0 = 5995.0
numfsr = int((peak75_center - fstart0)/fsr)
fstart = peak75_center - numfsr*fsr

fsr_steps = 4600
fstart2 = fstart + fsr_steps * fsr
schemeRows += makeScan(fstart2, fsr, 
                       [(n, 1) for n in np.arange(fsr_steps-250)],
                       id, laser)

schemeRows[-1].subschemeId |= fit
schemeInfo = {'extsdfra5':1300, 'Chsdfris':6666}
$$$
