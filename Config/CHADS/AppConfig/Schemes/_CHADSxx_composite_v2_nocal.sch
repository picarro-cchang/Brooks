$$$
schemeVersion = 2
repeat = 1
_12CO2a = 105
_13CO2 = 106
_12CO2b = 107
H2O = 109
HDO = 160
HDO_cal = 161
pztcen = 8192
cal = 4096
fit = 32768
f_12CO2 = 6251.758
f_13CO2 = 6251.315
f_H2O_CO2 = 6250.421
f_H2O = 6434.18738
f_HDO = 6434.31778
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
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

scan_12CO2a = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,5),(1,2),(3,1),(4,2),(3,2),(1,1),(0,5),(-1,2),(-3,1),(-4,1),(-4,1)],pztcen|_12CO2a,vLaser1)
scan_12CO2a[-1].subschemeId |= fit

scan_13CO2 = makeScan(f_13CO2,fsr,[(4,20),(3,1),(2,2),(1,4),(0,40),(-1,4),(-2,1),(-3,2),(-4,40),(-3,1),(-2,2),(-1,4),(0,40),(1,4),(2,1),(3,2),(4,20),(4,1)],pztcen|_13CO2,vLaser2)
scan_13CO2[-1].subschemeId |= fit

scan_12CO2b = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,5),(1,2),(3,1),(4,2),(3,2),(1,1),(0,5),(-1,2),(-3,1),(-4,1),(-4,1)],pztcen|_12CO2b,vLaser1)
scan_12CO2b[-1].subschemeId |= fit

schemeRows += scan_12CO2a + scan_13CO2 + scan_12CO2b

H2O_scan = makeScan(f_H2O,fsr,[(-4,4),(-3,4),(-2,4),(-1,5),(0,16),(1,5),(2,4),(3,4)],HDO|pztcen,H2O_Laser)
HDO_scan = makeScan(f_HDO,fsr,[(-3,4),(-2,4),(-1,5),(0,20),(1,5),(2,4),(3,4),(4,4)],HDO|pztcen,HDO_Laser)

idea1 = H2O_scan + HDO_scan
idea2 = idea1 + deepcopy(idea1[::-1])
idea2[-1].subschemeId |= fit

schemeRows += idea2

$$$
