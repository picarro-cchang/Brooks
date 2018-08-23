$$$
schemeVersion = 1
repeat = 1
_12CO2 = 105
_13CO2 = 106
H2O = 109
_12CO2_alt = 155
_13CO2_alt = 156
H2O_alt = 159
cal = 4096
fit = 32768
f_12CO2 = 6251.758
f_13CO2 = 6251.315
f_H2O = 6250.421
f_CO2a = 6250.726
f_CH4 = 6250.944
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2

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

schemeRows += makeScan(f_12CO2,fsr,[(s,1) for s in [-5,-5,-4,-3,-2,-1,0,1,2,3,4,3,2,1,0,-1,-2,-3,-4,-5,-5]],0,vLaser1)
schemeRows[-1].subschemeId |= fit

cal_12CO2 =  makeScan(f_12CO2,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,4),(0,6),(1,4),(2,2),(3,2),(4,2),(5,2)],cal|_12CO2_alt,vLaser1)
cal_12CO2 += makeScan(f_12CO2,fsr,[(4,6),(3,2),(2,2),(1,4),(0,6),(-1,4),(-2,2),(-3,2),(-4,3),(-5,2),(-5,1)],cal|_12CO2_alt,vLaser1)
cal_12CO2[-1].subschemeId = fit|_12CO2_alt

scan_12CO2 = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,7),(1,2),(3,1),(4,3),(3,2),(1,1),(0,7),(-1,2),(-3,1),(-4,1),(-4,1)],_12CO2,vLaser1)
scan_12CO2[-1].subschemeId |= fit

scan_13CO2 = makeScan(f_13CO2,fsr,[(4,10),(3,1),(2,2),(1,5),(0,22),(-1,5),(-2,1),(-3,2),(-4,20),(-3,1),(-2,2),(-1,5),(0,22),(1,5),(2,1),(3,2),(4,9),(4,1)],_13CO2,vLaser2)
scan_13CO2[-1].subschemeId |= fit

schemeRows += cal_12CO2 

for loops in range(26):
    schemeRows += scan_12CO2 + scan_13CO2

cal_13CO2 =  makeScan(f_13CO2,fsr,[(5,2),(5,2),(4,2),(3,2),(2,2),(1,2),(0,2),(-1,2),(-2,2),(-3,2),(-4,2)],_13CO2_alt,vLaser2)
cal_13CO2 += makeScan(f_13CO2,fsr,[(-5,4),(-4,4),(-3,4),(-2,4),(-1,4),(0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(5,1)],cal|_13CO2_alt,vLaser2)
cal_13CO2[-1].subschemeId = fit|_13CO2_alt

schemeRows += cal_13CO2 

# Scan over the water spectrum using FSR spacing

cal_H2O =  makeScan(f_H2O,fsr,[(5,2),(4,2),(3,2),(2,2),(1,5),(0,15),(-1,5),(-2,2),(-3,2),(-4,2),(-5,10),(-6,2),(-7,4),(-8,2),(-9,2),(-10,2),(-11,10)],H2O,vLaser3)
cal_H2O += makeScan(f_H2O,fsr,[(-10,2),(-9,2),(-8,2),(-7,4),(-6,2),(-5,10),(-4,2),(-3,2),(-2,2),(-1,5),(0,15),(1,5),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2)],cal|H2O,vLaser3)

# Scan the auxiliary CO2 line and the CH4 line using points on the FSR grid
stepAndDwell = []
step = 10
while True:
    freq = f_H2O + step*fsr
    if freq > f_CH4+28*fsr: break
    dwell = 6 if step-(f_CH4 - f_H2O)//fsr < 10 else 2
    if step-(f_CO2a - f_H2O)//fsr in [0,1]:
        dwell = 10
    if step-(f_CH4 - f_H2O)//fsr in [0,1]:
        dwell = 40
    stepAndDwell.append((step,dwell))
    step += 1
cal_H2O += makeScan(f_H2O,fsr,stepAndDwell,cal|H2O,vLaser3)
cal_H2O.append(deepcopy(cal_H2O[-1]))
cal_H2O[-1].dwell = 1
cal_H2O[-1].subschemeId = fit|H2O
schemeRows += cal_H2O
$$$