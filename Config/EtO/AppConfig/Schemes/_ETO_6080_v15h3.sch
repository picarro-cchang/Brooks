$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_450torr.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 10
f_eto = 6080.0600   #  changed from 6080.0630 for 450 Torr pressure shift
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
CH4TH = 10000
ETOTH = 15000

for i in range(-170,-154,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1, ETOTH))
for i in range(-154,-143,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1, ETOTH))
for i in range(-143,-136,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1,CH4TH))
for i in range(-136,-132,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1,CH4TH))
for i in range(-132,-128,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1,CH4TH))
for i in range(-128,-40,2):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1, ETOTH))
for i in range(-40,-10,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1, ETOTH))
for i in range(-10,-3,1):
    schemeRows.append(Row(f_eto+i*fsr,5,ETO,vLaser1, ETOTH))
for i in range(-3,4,1):
    schemeRows.append(Row(f_eto+i*fsr,5,ETO,vLaser1, ETOTH))
for i in range(4,10,1):
    schemeRows.append(Row(f_eto+i*fsr,5,ETO,vLaser1, ETOTH))
for i in range(10,50,2):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1, ETOTH))
for i in range(50,100,1):
    schemeRows.append(Row(f_eto+i*fsr,1,ETO,vLaser1, ETOTH))
schemeRows += schemeRows[::-1]
schemeRows.append(Row(f_eto - 170*fsr, 1, ETO|fit, vLaser1, ETOTH))

$$$
