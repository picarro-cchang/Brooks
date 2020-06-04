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
fsr_steps = 100
npass = 13
span = fsr_steps * npass
fstart = 6140.0
for k in range(npass):
    schemeRows += makeScan(fstart, fsr, 
                          [(n, 2) for n in fsr_steps*k + np.arange(fsr_steps)],
                          id | pztCen, laser)
    schemeRows += makeScan(fstart+span*fsr, fsr, 
                          [(n, 2) for n in fsr_steps*k + np.arange(fsr_steps)],
                          id | pztCen, laser)

schemeRows += schemeRows[::-1]
schemeRows[-1].subschemeId |= fit
$$$
