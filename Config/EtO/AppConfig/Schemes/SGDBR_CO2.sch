$$$
import copy
schemeVersion = 1
repeat = 1
f_start = 6160.0
f_end = 6210.0
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

fsr = 0.0206069
schemeRows = []
schemeRows += makeScan(f_start, fsr, 
                       [(n, 2) for n in range(0, int((f_end-f_start)/fsr))],
                       id | pztCen, laser)
schemeRows += copy.copy(schemeRows[::-1])
schemeRows[-1].subschemeId |= fit
$$$
