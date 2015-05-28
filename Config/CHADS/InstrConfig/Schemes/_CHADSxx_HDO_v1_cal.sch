$$$
schemeVersion = 1
repeat = 1
HDO = 160
HDO_cal = 161
pztcen = 8192
cal = 4096
fit = 32768
f_H2O = 6434.18738
f_HDO = 6434.31778
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
H2O_Laser = 3
HDO_Laser = 4

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

H2O_scan = makeScan(f_H2O,fsr,[(-4,2),(-3,2),(-2,2),(-1,3),(0,8),(1,3),(2,2),(3,2)],HDO|cal,H2O_Laser)
HDO_scan = makeScan(f_HDO,fsr,[(-3,2),(-2,2),(-1,3),(0,10),(1,3),(2,2),(3,2),(4,2)],HDO|cal,HDO_Laser)

idea1 = H2O_scan + HDO_scan
idea2 = idea1 + deepcopy(idea1[::-1])
idea2[-1].subschemeId |= fit

schemeRows += idea2

$$$
