$$$
schemeVersion = 1
repeat = 10
CO2 = 47
N2O = 45
cal = 4096
pztcen = 8192
fit = 32768

f_N2O = 6562.59891
f_CO2 = 6562.50002

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

# Scans go up and down over N2O (schemeID 128) peak only.
# Each is an FSR scan about that peak.

CO2_up  = makeScan(f_CO2,fsr,[(-2,3),(-1,5),(0,5),(1,5),(2,3)],CO2,0)
N2O_up  = makeScan(f_N2O,fsr,[(-2,10),(-1,10),(0,40),(1,10),(2,10)],N2O,0)
CO2_down = deepcopy(CO2_up[::-1])
N2O_down = deepcopy(N2O_up[::-1])
schemeRows = N2O_up + N2O_down
schemeRows[-1].subschemeId |= fit
$$$
