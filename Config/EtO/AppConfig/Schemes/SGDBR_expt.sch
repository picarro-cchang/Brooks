$$$
import copy
schemeVersion = 1
repeat = 500
f_CH4 = 6057.09
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
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

schemeRows = []
schemeRows += makeScan(f_CH4, fsr, 
                       [(n, 2) for n in [-32,32]],
                       CH4 | pztCen, CH4_Laser)
schemeRows += copy.copy(schemeRows[::-1])
schemeRows[-1].subschemeId |= fit
$$$
