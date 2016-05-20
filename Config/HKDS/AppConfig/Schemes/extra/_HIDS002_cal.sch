$$$
schemeVersion = 1
repeat = 10
H2O = 123
cal = 4096
pztcen = 8192
fit = 32768

fH_D_16O = 7200.30265
fH2_16O = 7200.13384
fH2_18O = 7199.96047

vLaser1 = 0
vLaser2 = 1
vLaserH2_16O = 2
vLaserH2_18O = 3
vLaserH_D_16O = 4

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
    
# Scan consists of up (schemeID 123) and down (schemeID 124) which are identical except for scan direction.
# Each of up and down consists of 3 sub scans, one for each main peak.  Each is an FSR scan about that peak.
# Each sub scan uses its own virtual laser.
# Version 2 scheme (9 May 2011) merges up & down scans to reduce systematic error when concentration changes

pkH2_18O  = makeScan(fH2_18O,fsr,[(-6,2),(-5,1),(-4,1),(-3,1),(-2,1),(-1,2),(0,14),(1,2),(2,1),(3,1),(4,2)],H2O|cal,vLaserH2_18O)
pkH2_16O  = makeScan(fH2_16O,fsr,[(-4,2),(-3,1),(-2,1),(-1,2),(0,10),(1,2),(2,1),(3,1),(4,2)],H2O|cal,vLaserH2_16O)
pkH_D_16O  = makeScan(fH_D_16O,fsr,[(-4,2),(-3,1),(-2,1),(-1,2),(0,12),(1,2),(2,1),(3,1),(4,1),(5,2)],H2O|cal,vLaserH_D_16O)
idea1 = pkH2_18O + pkH2_16O + pkH_D_16O
idea2 = deepcopy(idea1[::-1])
schemeRows = idea1 + idea2
schemeRows[-1].subschemeId |= fit
$$$
