$$$
schemeVersion = 1
repeat = 4
H2O2_only = 65
H2O2_wide = 66
CH4 = 67
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

VL = 0

fH2O = 7011.192
fH2O2a = 7011.567
fH2O2b = 7011.605
df = 0.5*(fH2O2b - fH2O2a)
fCH4 = 7011.0840

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
    
# Scan over water vapor peak

ch4_dn = makeScan(fCH4,fsr,[(8,1),(8,15),(7,4),(6,16),(5,16),(4,4),(3,4),(2,8),(1,8),(0,16),(-1,8),(-2,8),(-3,4),(-4,4),(-5,16)],CH4|cal,VL)
ch4_up = deepcopy(ch4_dn[::-1])
schemeRows = ch4_dn + ch4_up
$$$
