$$$
schemeVersion = 1
repeat = 3

H2O = 2
NH3 = 4
CO2 = 47
N2O = 45
WLMcal = 48
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

N2O_laser = 0
NH3_laser = 4

f_N2O = 6562.59891
f_CO2 = 6562.50002
f_NH3 = 6548.8046
f_H2O = 6549.76902

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
    
# Scans go up and down over CO2 (schemeID 127) and N2O (schemeID 128) peaks.
# Each is an FSR scan about that peak.
# There is only one virtual laser, which is flattened with a single long fsr scan

CO2_up  = makeScan(f_CO2,fsr,[(-2,3),(-1,5),(0,5),(1,5),(2,3)],CO2,N2O_laser)
N2O_up_45  = makeScan(f_N2O,fsr,[(-2,1),(-2,9),(-1,10),(0,40),(1,10),(2,10)],N2O,N2O_laser)
N2O_up_47  = makeScan(f_N2O,fsr,[(-2,10),(-1,10),(0,40),(1,10),(2,10)],CO2,N2O_laser)
transition1 = makeScan(f_N2O,fsr,[(-3,2),(-4,2),(-5,2),(-6,2),(-7,2),(-8,2)],WLMcal,N2O_laser)
WLMcal_up = makeScan(f_N2O,fsr,[(-8,2),(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,2),(1,2),(2,2)],WLMcal|cal|pztcen,N2O_laser)
transition2 = makeScan(f_N2O,fsr,[(1,2),(0,2),(-1,2),(-2,1),(-2,1)],WLMcal,N2O_laser)
CO2_down = deepcopy(CO2_up[::-1])
N2O_down_45 = deepcopy(N2O_up_45[::-1])
N2O_down_47 = deepcopy(N2O_up_47[::-1])
scan45 = N2O_up_45 + N2O_down_45
scan45[-1].subschemeId |= fit
scan47 = CO2_down + CO2_up + N2O_up_47 + N2O_down_47 + transition1 + WLMcal_up + transition2
scan47[-1].subschemeId |= fit

scan_H2O = makeScan(f_NH3,fsr,[
(-14,1),(-14,1),(-13,2),(-12,2),(-11,2),(-10,2),
(-9,2),(-8,2),(-7,2),(-6,2),(-5,2),
(-4,2),(-3,2),(-2,2),(-1,2),(0,2),
(1,2),(2,2),(3,2),(4,2),(5,2),
(6,2),(7,2),(8,2),(9,2),(10,2),
(11,2),(12,2),(13,2),(14,2),(15,5),
(16,10),(17,5),(18,2),(19,2),(20,2),(21,2)],cal|pztcen|H2O,NH3_laser)

scan_H2O += deepcopy(scan_H2O[::-1])
scan_H2O[-1].subschemeId |= fit
scan_H2O.append(Row(f_NH3+6*fsr,0,NH3 | ignore,NH3_laser))

NH3_up = makeScan(f_NH3,fsr,[(-14,2),(-13,2),(-12,2),(-11,10),(-10,10),
(-9,40),(-8,10),(-7,10),(-6,2),(-5,2),(-4,2),(-3,2),(-2,10),(-1,10),(0,40),
(1,10),(2,10),(3,2),(4,2),(5,2),(6,2)],cal | NH3,NH3_laser)

NH3_down = deepcopy(NH3_up[::-1])

scan_NH3 = []
scan_NH3 = NH3_down + NH3_up + NH3_down + NH3_up + NH3_down + NH3_up
scan_NH3.append(Row(f_NH3+6*fsr,1,NH3 | fit,NH3_laser))
scan_NH3.append(Row(f_NH3-14*fsr,0,H2O | ignore,NH3_laser))
    
scan_N2O = scan47
for i in range(10):
    scan_N2O += scan45

schemeRows = scan_N2O + scan_H2O + scan_N2O + scan_NH3    
$$$