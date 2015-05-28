$$$
schemeVersion = 1
repeat = 1
cal = 4096
pztcen = 8192
fit = 32768

vLaserH2_16O = 2

fmin = 7199.75000
fincr = 0.001
vLaser = vLaserH2_16O
nfreq = 750

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

def transition(a,b,dwells,id,vLaser):
    incr = (b-a)/(len(dwells)+1)
    stepAndDwell = [(i+1,d) for i,d in enumerate(dwells)]
    return makeScan(a,incr,stepAndDwell,id,vLaser)

finescan = []

for i in range(nfreq+1):
    finescan.append(Row(fmin+i*fincr,2,0,vLaser))

schemeRows += finescan + finescan[::-1]

fsrscan = []
i = -1
while fmin+i*fsr < finescan[-1].setpoint+0.5*fsr:
    fsrscan.append(Row(fmin+i*fsr,6,cal,vLaser))
    i += 1
schemeRows += fsrscan + deepcopy(fsrscan[::-1])
schemeRows[-1].subschemeId |= fit
$$$
