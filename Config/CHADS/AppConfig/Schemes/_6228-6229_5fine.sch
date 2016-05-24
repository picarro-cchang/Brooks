$$$
# iCO2 baseline scheme for alternative spectroscopy at 6228 wvn (experimental CHADS)
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6228.0
fincr = 0.0005
nfreq = 3001
vLaser = 0
fit = 32768
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
cal = 4096

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
f = fmin+i*fincr
while f > fmin:
    schemeRows.append(Row(f,4,cal,vLaser))
    f -= fsr
schemeRows[-1].subschemeId |= fit
$$$
