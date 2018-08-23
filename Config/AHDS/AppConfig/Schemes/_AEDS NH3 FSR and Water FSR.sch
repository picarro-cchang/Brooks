$$$
schemeVersion = 1
repeat = 1

NH3 = 4
H2O = 2

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

f_NH3 = 6548.8046

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

vLaser = 0

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

scan_H2O = makeScan(f_NH3,fsr,[
(-14,2),(-13,2),(-12,2),(-11,2),(-10,2),
(-9,2),(-8,2),(-7,2),(-6,2),(-5,2),
(-4,2),(-3,2),(-2,2),(-1,2),(0,2),
(1,2),(2,2),(3,2),(4,2),(5,2),
(6,2),(7,2),(8,2),(9,2),(10,2),
(11,2),(12,2),(13,2),(14,2),(15,5),
(16,10),(17,5),(18,2),(19,2),(20,2),(21,2)],cal | H2O,vLaser)

scan_H2O += deepcopy(scan_H2O[::-1])
scan_H2O[-1].subschemeId |= fit

scan_NH3 = makeScan(f_NH3,fsr,[
(-14,2),(-13,2),(-12,2),(-11,10),(-10,10),
(-9,40),(-8,10),(-7,10),(-6,2),(-5,2),
(-4,2),(-3,2),(-2,10),(-1,10),(0,40),
(1,10),(2,10),(3,2),(4,2),(5,2),(6,2)],cal | NH3,vLaser)

scan_NH3 += deepcopy(scan_NH3[::-1])
scan_NH3[-1].subschemeId |= fit


scan_packet_NH3 = []
for i in range (11):
    scan_packet_NH3 += scan_NH3
    
for loops in range(1):
    schemeRows += scan_H2O + scan_packet_NH3

$$$