$$$
schemeVersion = 1
repeat = 3

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

scan_CO2 = makeScan(f_CO2,fsr,[(-4,4),(0,12),(4,4)],pztcen|CO2,vLaserCO2)
scan_CO2[-1].subschemeId |= fit

scan_CH4 = makeScan(f_CH4,fsr,[(-5,2),(0,6),(4,2)],pztcen|CH4,vLaserCH4)
scan_CH4[-1].subschemeId |= fit

scan_H2O = makeScan(f_H2O,fsr,[(-3,1),(0,4),(3,1)],pztcen|H2O,vLaserH2O)
scan_H2O[-1].subschemeId |= fit

scan_CO2pzt = makeScan(f_CO2,fsr,[(-4,2),(-3,2),(-2,2),(-1,2),(0,12),(1,2),(2,2),(3,2),(4,2)],pztcen|CO2,vLaserCO2)
scan_CO2pzt[-1].subschemeId |= fit
scan_CO2pzt[-1].extra1 = 1

scan_CH4pzt = makeScan(f_CH4,fsr,[(-5,1),(-4,1),(-3,1),(-2,1),(-1,1),(0,5),(1,1),(2,1),(3,1),(4,1)],pztcen|CH4,vLaserCH4)
scan_CH4pzt[-1].subschemeId |= fit
scan_CH4pzt[-1].extra1 = 1

scan_H2Opzt = makeScan(f_H2O,fsr,[(-4,1),(-3,1),(-2,1),(-1,1),(0,6),(1,1),(2,1),(3,1),(4,1)],pztcen|H2O,vLaserH2O)
scan_H2Opzt[-1].subschemeId |= fit
scan_H2Opzt[-1].extra1 = 1

special1 = (scan_CO2pzt + scan_H2O)
special2 = (scan_CO2 + scan_CH4pzt + scan_H2O)
special3 = (scan_CO2 + scan_H2Opzt)
normal = (scan_CO2 + scan_H2O)

scan_packet = []
for i in range (4):
    scan_packet += normal

for loops in range(1):
    schemeRows += (special1 + scan_packet + special3 + scan_packet)

$$$
