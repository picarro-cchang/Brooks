$$$
schemeVersion = 1
repeat = 10
CO2 = 10
CH4 = 25
H2Oa = 26
H2Ob = 11
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768
f_CO2 = 6237.408
f_CH4 = 6057.09
f_H2Oa = 6234.3135
f_H2Ob = 6057.80
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

scan_CO2 = makeScan(f_CO2,fsr,[(4,1),(3,1),(2,1),(1,1),(0,6),(-1,1),(-2,1),(-3,1),(-4,1)],pztcen|CO2,vLaser1)
scan_CO2[-1].subschemeId |= fit

scan_H2Ob = makeScan(f_H2Ob,fsr,[(4,1),(3,1),(2,1),(1,1),(0,9),(-1,1),(-4,1),(-4,1)],pztcen|H2Ob,vLaser4)
scan_H2Ob[-1].subschemeId = fit | ignore | H2Ob

for loops in range(10):
    schemeRows += (scan_CO2 + scan_H2Ob)
$$$
