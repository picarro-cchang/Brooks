$$$
cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
schemeVersion = 1
repeat = 1
schemeRows = []
fmax = 5739.8
fmin = 5738.3
fincr = 0.0005
nfreq = 3001
vLaser = 0
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
