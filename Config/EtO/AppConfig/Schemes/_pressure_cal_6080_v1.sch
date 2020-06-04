$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 30
f_eto = 6080.0630
f_ref = 6079.563376
ETO = 181
cal = 4096
pztcen = 8192
fit = 32768
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4
vLaser6 = 5
vLaser7 = 6
vLaser8 = 7

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result
    
#  Version 1 of a scheme to measurement ethylene oxide with the widely tunable laser.  "Cal" flag turned off.

schemeRows = []
for i in range(-180,35,2):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1))

for i in range(35,81,1):
    schemeRows.append(Row(f_eto+i*fsr,4,ETO,vLaser1))
    
for i in range(80,34,-1):
    schemeRows.append(Row(f_eto+i*fsr,4,ETO,vLaser1))
    
for i in range(34,-181,-2):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1))
    
schemeRows.append(Row(f_eto-180*fsr,1,ETO|fit,vLaser1))

$$$