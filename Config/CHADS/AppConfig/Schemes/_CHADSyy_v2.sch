$$$
schemeVersion = 2
repeat = 10
CO2 = 164
HDO = 160
pztcen = 8192
cal = 4096
fit = 32768
f_12CO2 = 6228.68998
f_13CO2 = 6228.43265
f_H2O = 6434.18738
f_HDO = 6434.31714
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
H2O_Laser = 3
HDO_Laser = 4
th_12C = 11000
th_13C = 11000
th_w = 11000

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,threshold):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser,threshold))
    return result

def transition(a,b,dwells,id,vLaser,threshold):
    incr = (b-a)/(len(dwells)+1)
    stepAndDwell = [(i+1,d) for i,d in enumerate(dwells)]
    return makeScan(a,incr,stepAndDwell,id,vLaser,threshold)

scan_12CO2up = makeScan(f_12CO2,fsr,[(-4,4),(-3,2),(-2,1),(-1,2),(0,8),(1,2),(2,1),(3,2),(4,2),(5,3),(5,1)],cal|pztcen|CO2,vLaser1,th_12C)
scan_12CO2dn = makeScan(f_12CO2,fsr,[(5,4),(4,2),(3,2),(2,1),(1,2),(0,8),(-1,2),(-2,1),(-3,2),(-4,4)],cal|pztcen|CO2,vLaser1,th_12C)
scan_13CO2 = makeScan(f_13CO2,fsr,[(4,12),(3,4),(2,2),(1,4),(0,32),(-1,4),(-2,2),(-3,4),(-4,4),(-5,24),(-4,4),(-3,4),(-2,2),(-1,4),(0,32),(1,4),(2,2),(3,4),(4,12)],cal|pztcen|CO2,vLaser2,th_13C)

schemeRows += scan_12CO2dn + scan_13CO2 + scan_12CO2up
schemeRows[-1].subschemeId |= fit


H2O_scan = makeScan(f_H2O,fsr,[(-4,4),(-3,4),(-2,4),(-1,5),(0,16),(1,5),(2,4),(3,4)],cal|HDO|pztcen,H2O_Laser,th_w)
HDO_scan = makeScan(f_HDO,fsr,[(-3,4),(-2,4),(-1,5),(0,20),(1,5),(2,4),(3,4),(4,4)],cal|HDO|pztcen,HDO_Laser,th_w)

idea1 = H2O_scan + HDO_scan
idea2 = idea1 + deepcopy(idea1[::-1])
idea2[-1].subschemeId |= fit

schemeRows += idea2

$$$
