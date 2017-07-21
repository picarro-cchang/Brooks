$$$
schemeVersion = 1
repeat = 3

H2O = 2
NH3 = 4
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

NH3_laser = 0

f_NH3 = 6548.618
f_H2O = 6549.13061

cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
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

# Translated from AEDS2039 NH3 FSR and Water FSR.sch


scan_H2O = makeScan(f_H2O,fsr,[
(-30,1),(-30,1),(-29,2),(-28,2),(-27,2),(-26,2),(-25,2),(-24,2),(-23,2),(-22,2),(-21,2),
(-20,2),(-19,2),(-18,2),(-17,2),(-16,2),(-15,2),(-14,2),(-13,2),(-12,2),(-11,2),(-10,2),
(-9,2),(-8,2),(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,10),(1,2),(2,2),(3,2),
(4,2),(5,2)],cal|pztcen|H2O,NH3_laser)

scan_H2O += deepcopy(scan_H2O[::-1])
scan_H2O[-1].subschemeId |= fit

NH3_up = makeScan(f_NH3,fsr,[(-5,2),(-4,2),(-3,2),(-2,10),(-1,10),
(0,40),(1,10),(2,10),(3,2),(4,2),(5,2),(6,2),(7,10),(8,10),(9,40),
(10,10),(11,10),(12,2),(13,2),(14,2),(15,1)],NH3,NH3_laser)

NH3_down = deepcopy(NH3_up[::-1])

scan_NH3 = NH3_up + NH3_down
scan_NH3.append(Row(f_NH3-5*fsr,1,NH3|ignore|fit,NH3_laser))

schemeRows += scan_H2O
for i in range(11):
    schemeRows += scan_NH3


$$$
