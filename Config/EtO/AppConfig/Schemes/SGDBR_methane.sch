$$$
import copy
schemeVersion = 1
repeat = 1
f_CH4 = 6057.09
fsr = 0.0206069
CH4_Laser = 0
CH4 = 25
pztCen = 8192   # Turns on pzt control from tuner
# pztCen = 0   #  Turns of pzt adjust
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
                       [(n, 20 if n==0 else 3) for n in range(-50,51)],
                       CH4 | pztCen, CH4_Laser)
schemeRows += copy.copy(schemeRows[::-1])
schemeRows[-1].subschemeId |= fit
$$$
