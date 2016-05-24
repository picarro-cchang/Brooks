$$$
schemeVersion = 1
repeat = 80
H2O = 123
cal = 4096
pztcen = 8192
cc = 12288
fit = 32768

f_17O = 7193.1288
f_18O = 7192.8388
fH_D_16O = 7200.30265
fH2_16O = 7200.13384
fH2_18O = 7199.96047

vLaser_18O = 0
vLaser_17O = 1
vLaserH2_16O = 2
vLaserH2_18O = 3
vLaserH_D_16O = 4

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal_lct.ini')
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

# Merger of earlier schemes from 7193 and 7200 wvn regions

pk_18O_up  = makeScan(f_18O,fsr,[(-3,1),(-3,3),(-2,2),(-1,4),(0,5),(1,4),(2,2),(3,4)],H2O|cal,vLaser_18O)
pk_17O_up  = makeScan(f_17O,fsr,[(-6,2),(-5,1),(-4,1),(-3,2),(-2,6),(-1,10),(0,16),(1,10),(2,6),(3,2),(4,4)],H2O|cal,vLaser_17O)
transition_up = makeScan(f_18O,fsr,[(4,1),(5,1),(6,1),(7,1)],H2O|cal,vLaser_18O)
pk_18O_down = deepcopy(pk_18O_up[::-1])
pk_17O_down = deepcopy(pk_17O_up[::-1])
transition_down = deepcopy(transition_up[::-1])
pkH2_18O  = makeScan(fH2_18O,fsr,[(-6,2),(-5,1),(-4,1),(-3,1),(-2,2),(-1,3),(0,5),(1,3),(2,2),(3,1),(4,2)],H2O|cal,vLaserH2_18O)
pkH2_16O  = makeScan(fH2_16O,fsr,[(-4,2),(-3,1),(-2,3),(-1,4),(0,6),(1,4),(2,3),(3,1),(4,2)],H2O|cal,vLaserH2_16O)
pkH_D_16O  = makeScan(fH_D_16O,fsr,[(-4,2),(-3,1),(-2,2),(-1,3),(0,5),(1,3),(2,2),(3,1),(4,1),(5,2)],H2O|cal,vLaserH_D_16O)
idea1 = pk_18O_up + transition_up + pk_17O_up + pkH2_18O + pkH2_16O + pkH_D_16O
idea2 = deepcopy(idea1[::-1])
schemeRows = idea1 + idea2
schemeRows[-1].subschemeId |= fit
$$$
