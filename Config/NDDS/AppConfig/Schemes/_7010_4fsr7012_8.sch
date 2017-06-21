$$$
schemeVersion = 1
repeat = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
schemeRows = []
fmin = 7010.4
fmax = 7012.8
fincr = 0.001
nfreq = 2401
vLaser = 0
cal = 4096
pztcen = 8192
fit = 32768

f = fmin
while f < fmax:
    schemeRows.append(Row(f,16,cal,vLaser))
    f += fsr

while f > fmin:
    schemeRows.append(Row(f,16,0,vLaser))
    f -= fsr

schemeRows[-1].subschemeId |= fit
$$$
