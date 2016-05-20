$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6433.0
fincr = 0.0005
nfreq = 4000
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser = 4
cal = 4096
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
f = 6435.0
while f > fmin:
    schemeRows.append(Row(f,4,cal,vLaser))
    f -= fsr
schemeRows[-1].subschemeId |= fit
$$$
