$$$
schemeVersion = 1
repeat = 10

H2O = 2
NH3 = 4
CH4 = 25
CO2 = 47
CO2_HP = 46
N2O = 45
WLMcal = 48
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

N2O_laser = 0
NH3_laser = 4
CH4_laser = 6
CO2_laser = 7


f_N2O = 6562.59881
f_CO2 = 6562.50002
f_NH3 = 6548.8046
f_H2O = 6549.76902
f_CH4 = 6057.090
f_CO2_HP = 6058.1985

th_6562 = 12000
th_6057 = 14000

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
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
    
# Scans go up and down over CO2 (schemeID 127) and N2O (schemeID 128) peaks.
# Each is an FSR scan about that peak.
# There is only one virtual laser, which is flattened with a single long fsr scan
# In addition we now have scans over the AADS ammonia region and the CFADS methane region
# Version 5 of the scheme adds a new CO2 "high-precision" scan at 6058.2 wavenumbers
# Version 7 adds variable threshold.

CH4_up = makeScan(f_CH4,fsr,[(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,3),(0,17),(1,3),(2,3),(3,2),(4,2),(5,2),(6,2),(7,2)],CH4|pztcen,CH4_laser,th_6057)
CH4_down = makeScan(f_CH4,fsr,[(8,2),(7,2),(6,2),(5,2),(4,2),(3,2),(2,3),(1,3),(0,17),(-1,3),(-2,2),(-3,2),(-4,2),(-5,2),(-6,2),(-6,1)],CH4|pztcen|cal,CH4_laser,th_6057)
CH4_up[-1].subschemeId |= fit
scan_CH4 = CH4_down + CH4_up
scan_CH4.append(Row(f_CO2_HP-4*fsr,0,CO2 | ignore,CO2_laser,th_6057))

CO2_HP = makeScan(f_CO2_HP,fsr,[(-4,6),(-3,2),(-2,4),(-1,10),(0,20),(1,10),(2,4),(3,2),(4,12),(3,2),(2,2),(1,4),(0,20),(-1,4),(-2,2),(-3,2),(-4,6)],CO2_HP|pztcen|cal,CO2_laser,th_6057)
CO2_HP[-1].subschemeId |= fit
CO2_HP.append(Row(f_CH4+8*fsr,0,CH4 | ignore,CH4_laser,th_6057))

CO2_up  = makeScan(f_CO2,fsr,[(-2,3),(-1,5),(0,5),(1,5),(2,5)],CO2,N2O_laser,th_6562)
N2O_up_45  = makeScan(f_N2O,fsr,[(-2,10),(-1,10),(0,40),(1,10),(2,10)],N2O,N2O_laser,th_6562)
N2O_up_47  = makeScan(f_N2O,fsr,[(-2,10),(-1,10),(0,40),(1,10),(2,10)],CO2,N2O_laser,th_6562)
transition1 = makeScan(f_N2O,fsr,[(-3,2),(-4,2),(-5,2),(-6,2),(-7,2),(-8,2)],WLMcal,N2O_laser,th_6562)
WLMcal_up = makeScan(f_N2O,fsr,[(-8,2),(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,2),(1,2),(2,2)],WLMcal|cal|pztcen,N2O_laser,th_6562)
transition2 = makeScan(f_N2O,fsr,[(1,2),(0,2),(-1,2),(-2,1),(-2,1)],WLMcal,N2O_laser,th_6562)
CO2_down = deepcopy(CO2_up[::-1])
N2O_down_45 = deepcopy(N2O_up_45[::-1])
N2O_down_47 = deepcopy(N2O_up_47[::-1])
scan45 = N2O_up_45 + N2O_down_45
scan45.append(Row(f_N2O-2*fsr,1,N2O | fit,N2O_laser,th_6562))
scan47 = CO2_down + CO2_up + N2O_up_47 + N2O_down_47 + CO2_down + CO2_up + N2O_up_47 + N2O_down_47
scan47.append(Row(f_N2O-2*fsr,1,CO2 | fit,N2O_laser,th_6562))
N2Ocal = transition1 + WLMcal_up + transition2
N2Ocal[-1].subschemeId |= fit

scan_N2O = scan47 + N2Ocal

scan_H2O = makeScan(f_NH3,fsr,[
(21,1),(21,1),(20,2),(19,2),(18,2),(17,5),(16,10),
(15,5),(14,2),(13,2),(12,2),(11,2),
(10,2),(9,2),(8,2),(7,2),(6,2),
(5,2),(4,2),(3,2),(2,5),(1,5),
(0,20),(-1,5),(-2,5),(-3,2),(-4,2),
(-5,2),(-6,2),(-7,5),(-8,5),(-9,20),
(-10,5),(-11,5),(-12,2),(-13,2),(-14,2)],cal|pztcen|H2O,NH3_laser,th_6562)

#scan_H2O = makeScan(f_NH3,fsr,[
#(-14,1),(-14,1),(-13,2),(-12,2),(-11,5),(-10,5),
#(-9,20),(-8,5),(-7,5),(-6,2),(-5,2),
#(-4,2),(-3,2),(-2,5),(-1,5),(0,20),
#(1,5),(2,5),(3,2),(4,2),(5,2),
#(6,2),(7,2),(8,2),(9,2),(10,2),
#(11,2),(12,2),(13,2),(14,2),(15,5),
#(16,10),(17,5),(18,2),(19,2),(20,2),(21,2)],cal|pztcen|H2O,NH3_laser,th_6562)

scan_H2O += deepcopy(scan_H2O[::-1])
scan_H2O[-1].subschemeId |= fit
scan_NH3 = deepcopy(scan_H2O[::1])
#scan_H2O.append(Row(f_NH3+6*fsr,0,NH3 | ignore,NH3_laser))

# NH3_up = makeScan(f_NH3,fsr,[(-14,2),(-13,2),(-12,2),(-11,10),(-10,10),
# (-9,40),(-8,10),(-7,10),(-6,2),(-5,2),(-4,2),(-3,2),(-2,10),(-1,10),(0,40),
# (1,10),(2,10),(3,2),(4,2),(5,2),(6,2)],cal | NH3,NH3_laser)

# NH3_down = deepcopy(NH3_up[::-1])

# scan_NH3 = []
# scan_NH3 = NH3_down + NH3_up
# scan_NH3.append(Row(f_NH3+6*fsr,1,NH3 | fit,NH3_laser))
# scan_NH3.append(Row(f_NH3-14*fsr,0,H2O | ignore,NH3_laser))
    
#schemeRows = scan_CH4 + scan_N2O + scan_H2O + CO2_HP + scan_N2O + scan_NH3 
schemeRows = scan_CH4 + scan_CH4 + scan_CH4 + scan_CH4 
$$$