$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = 0.0206069
laser = 0
id = 10
#pztCen = 8192   # Turns on pzt control from tuner
pztCen = 0   #  Turns of pzt adjust
fit = 32768

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

f_base = 6000.0
f_span = 2.0
schemeRows = []

jump = fsr * np.round(25.9/fsr)

for steps in range(14):
    offset = steps * f_span
    f_start = f_base + offset
    f_end = f_base + f_span + offset

    schemeRows += makeScan(f_start, fsr, 
                           [(n, 1) for n in range(0, int((f_end-f_start)/fsr))],
                           id | pztCen, laser)


    f_start = f_base + f_span + jump + offset
    f_end = f_base + jump + offset
                           
    schemeRows += makeScan(f_start, fsr, 
                           [(n, 1) for n in range(0, int((f_end-f_start)/fsr), -1)],
                           id | pztCen, laser)

    f_start = f_base + 2*jump + offset
    f_end = f_base + f_span + 2*jump + offset

    schemeRows += makeScan(f_start, fsr, 
                           [(n, 1) for n in range(0, int((f_end-f_start)/fsr))],
                           id | pztCen, laser)

    f_start = f_base + f_span + 3*jump + offset
    f_end = f_base + 3*jump + offset
                           
    schemeRows += makeScan(f_start, fsr, 
                           [(n, 1) for n in range(0, int((f_end-f_start)/fsr), -1)],
                           id | pztCen, laser)

    f_start = f_base + 4*jump + offset
    f_end = f_base + f_span + 4*jump + offset

    schemeRows += makeScan(f_start, fsr, 
                           [(n, 1) for n in range(0, int((f_end-f_start)/fsr))],
                           id | pztCen, laser)
                       
schemeRows[-1].subschemeId |= fit
$$$
