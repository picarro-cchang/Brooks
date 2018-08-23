$$$
schemeVersion = 1
repeat = 3
H2O2_only = 65
H2O2_wide = 66
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

VL = 0

fH2O = 7011.192
fH2O2a = 7011.567
fH2O2b = 7011.605
df = 0.5*(fH2O2b - fH2O2a)

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

H2O2_pass = makeScan(fH2O2b,fsr,[(4,5),(3,5),(2,5),(1,5),(0,5),(-1,5),(-2,5),(-3,5),(-4,5),(-5,5),(-4,5),(-3,5),(-2,5),(-1,5),(0,5),(1,5),(2,5),(3,5),(4,5),(5,5)],H2O2_only,VL)

H2O2_scan = H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass + H2O2_pass

wide_down = makeScan(fH2O,fsr,[(26,3),(25,3),(24,3),(23,3),(22,3),(21,3),(20,3),(19,3),(18,3),(17,3),(16,3),(15,3),(14,3),(13,3),(12,3),(11,3),(10,3),(9,3),(8,3),(7,3),(6,3),(5,3),(4,3),(3,3),(2,3),(1,3),(0,12),(-1,3),(-2,3),(-3,3),(-4,3),(-5,3),(-6,3),(-7,3),(-8,3),(-9,3),(-10,3),(-11,2)],H2O2_wide|cal,VL)
wide_up = deepcopy(wide_down[::-1])
wide_scan = wide_down + wide_up
transition1 = []
transition1.append(Row(fH2O+25*fsr,1,H2O2_wide|fit,VL))
transition1.append(Row(fH2O2b+5*fsr,1,H2O2_only|ignore,VL))
transition2 = []
transition2.append(Row(0.5*(fH2O+fH2O2b+25*fsr+5*fsr),1,H2O2_only|ignore|fit,VL))
transition2.append(Row(0.5*(fH2O+fH2O2b+25*fsr+5*fsr),1,H2O2_only|ignore,VL))
schemeRows = wide_scan + transition1 + H2O2_scan + transition2
$$$
