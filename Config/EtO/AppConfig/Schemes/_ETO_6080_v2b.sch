$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 2
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
#  Version 2 tries to use RDs better, starting with more on the ETO peak

schemeRows = []
for i in range(-250,0,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1))
schemeRows.append(Row(f_eto,8,ETO,vLaser1))
for i in range(1,596,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1))
for i in range(595,0,-1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1))
schemeRows.append(Row(f_eto,8,ETO,vLaser1))
for i in range(-1,-250,-1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1))
schemeRows.append(Row(f_eto-170*fsr,1,ETO|fit,vLaser1))

$$$