$$$
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

schemeVersion = 1
repeat = 1
schemeRows = []
fmax = 6056
fincr = fsr
nfreq = 122
cal = 4096
pztcen = 8192
vLaser = 6
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmax+i*fincr,15,cal,vLaser))


$$$
