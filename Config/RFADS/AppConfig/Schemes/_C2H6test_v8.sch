$$$
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

schemeVersion = 1
repeat = 100
C2H6 = 170
f_C2H6 = 5946.5285
f_H2O = 5946.8296
f_CH4 = 6057.090
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768
C2H6_Laser = 1
CH4_Laser = 7

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

schemeRows = makeScan(f_C2H6,fsr,[(-4,5),(-3,1),(-2,1),(-1,1),(0,5),(1,1),(2,1),(3,1),(5,1),(7,1),(9,1),(11,1)],cal|pztcen|C2H6,C2H6_Laser)
schemeRows.append(Row(f_C2H6+12*fsr,0,C2H6|ignore,C2H6_Laser))
schemeRows += makeScan(f_CH4,fsr,[(-6,1),(-5,1),(-4,1),(-3,1),(-2,1),(-1,1),(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1)],cal|pztcen|C2H6,CH4_Laser)
schemeRows += makeScan(f_C2H6,fsr,[(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,2),(17,1),(16,1),(15,1),(14,1),(13,1),(12,1)],cal|pztcen|C2H6,C2H6_Laser)
schemeRows.append(Row(f_C2H6+3*fsr,0,C2H6|ignore,C2H6_Laser))
schemeRows += makeScan(f_CH4,fsr,[(8,1),(7,1),(6,1),(5,1),(4,1),(3,1),(2,1),(1,1),(0,1),(-1,1),(-2,1),(-3,1),(-4,1),(-5,1),(-6,1)],cal|pztcen|C2H6,CH4_Laser)
schemeRows += makeScan(f_C2H6,fsr,[(10,1),(8,1),(6,1),(4,1),(3,1),(2,1),(1,1),(0,5),(-1,1),(-2,1),(-3,1),(-4,4),(-4,1)],cal|pztcen|C2H6,C2H6_Laser)
schemeRows[-1].subschemeId |= fit

# Mark rows for processed loss calculation
for r in schemeRows:
    if abs(r.setpoint - f_CH4) < 0.001*fsr : r.pzt |= 2
    if abs(r.setpoint - (f_CH4-6*fsr)) < 0.001*fsr: r.pzt |= 1

$$$
