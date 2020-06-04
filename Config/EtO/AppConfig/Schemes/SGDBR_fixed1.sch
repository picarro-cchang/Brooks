$$$
import copy
schemeVersion = 1
repeat = 1
f_CH4 = 6057.090
fsr = 0.0206069
CH4_Laser = 0
CH4 = 25
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
schemeRows += makeScan(f_CH4, fsr, 
                       [(15, 1000)],
                       CH4 | pztCen, CH4_Laser)
$$$
