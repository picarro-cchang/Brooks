$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6547.5
vLaser = 1
fit = 32768
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
fincr = fsr
nfreq = 121

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,12,0,vLaser))

for i in range(nfreq, -1, -1):
    schemeRows.append(Row(fmin+0.5*fsr+i*fincr,12,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
