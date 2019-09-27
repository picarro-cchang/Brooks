$$$
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
schemeVersion = 1
repeat = 1
schemeRows = []
fmax = 5724.71
fmin = 5722.71
fincr = 0.0005
nfreq = 4001
vLaser = 1
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

f = fmax
while f > fmin:
    schemeRows.append(Row(f,16,cal|pztcen,vLaser))
    f -= fsr
schemeRows[-1].subschemeId |= fit
$$$
