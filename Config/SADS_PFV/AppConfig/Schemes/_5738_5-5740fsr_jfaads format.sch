$$$
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
schemeVersion = 1
repeat = 1
schemeRows = []
fmax = 5740.0
fmin = 5738.5
fincr = 0.0005
nfreq = 3001
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmax-i*fincr,15,pztcen,vLaser))
    

$$$
