$$$
schemeVersion = 1
repeat = 10

CO2 = 10
CH4 = 25
H2O = 28

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

f_CO2 = 6237.4214
f_CH4 = 6057.0882
f_H2O = 6053.2139

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

vLaserCO2 = 0
vLaserCH4 = 2
vLaserH2O = 1


schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result


scan_CO2 = makeScan(f_CO2,fsr,[(-4,2),(0,6),(4,2)],CO2,vLaserCO2)
scan_CO2[-1].subschemeId |= fit


scan_CO2pzt = makeScan(f_CO2,fsr,[(-4,1),(-3,1),(-2,1),(-1,1),(0,6),(1,1),(2,1),(3,1),(4,1)],pztcen|CO2,vLaserCO2)
scan_CO2pzt[-1].subschemeId |= fit

scan_packet = []
for i in range (15):
    scan_packet += scan_CO2

for loops in range(1):
    schemeRows += (scan_CO2pzt + scan_packet)


$$$
