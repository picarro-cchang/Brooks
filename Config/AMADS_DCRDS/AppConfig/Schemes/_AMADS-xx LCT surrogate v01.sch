$$$
schemeVersion = 1
repeat = 10

H2O = 2
NH3 = 4
N2O = 5
HF = 60
O2 = 61
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

HF_laser = 0
NH3_laser = 1

f_NH3 = 6548.618
f_N2O = 6548.85160
f_H2O = 6549.13061
f_HF = 7823.84945
f_O2 = 7822.9835

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
    
# Scheme to measure "surrogate" gases N2O and O2 to confirm proper operation of analyzer
# 2016 1108:  adapted from existing AMADS scheme

goto_start_H2O = [ Row(f_NH3+24*fsr,0,ignore|H2O,NH3_laser) ]

scan_H2O = makeScan(f_NH3,fsr,[
(24,4),(25,5),(26,10),(27,5),(28,2),(29,2),(30,5),(29,2),(28,2),(27,5),(26,10),(25,5),(24,4),(24,1)],H2O,NH3_laser)
scan_H2O[-1].subschemeId |= fit

scan_N2O = makeScan(f_N2O,fsr,[
(-5,10),(-4,2),(-3,2),(-2,2),(-1,5),(0,20),(1,5),(2,2),(3,2),(4,2),(5,20),
(4,2),(3,2),(2,2),(1,5),(0,20),(-1,5),(-2,2),(-3,2),(-4,2),(-5,9),(-5,1)],N2O,NH3_laser)
scan_N2O[-1].subschemeId |= fit

goto_start_NH3 = [ Row(f_NH3+12*fsr,0,ignore|H2O,NH3_laser) ]

NH3_up = makeScan(f_NH3,fsr,[(-3,5),(-2,5),(-1,5),(0,20),(1,5),(2,5),(3,1),(4,1),(5,1),(6,1),(7,5),(8,5),(9,20),
(10,5),(11,5),(12,4)],NH3,NH3_laser)

NH3_dn = deepcopy(NH3_up[::-1])

scan_NH3 = NH3_dn + NH3_up + NH3_dn + NH3_up
scan_NH3.append(Row(f_NH3+12*fsr,1,NH3|fit,NH3_laser))

goto_start_O2 = [ Row(f_HF-38*fsr,0,ignore|O2,HF_laser) ]

scan_O2 = makeScan(f_HF,fsr,[(-38,10),(-39,2),(-40,2),(-41,5),(-42,20),(-43,5),(-44,2),(-45,2),(-46,2),(-47,20),
(-46,2),(-45,2),(-44,2),(-43,5),(-42,20),(-41,5),(-40,2),(-39,2),(-38,9),(-38,1)],O2,HF_laser)
scan_O2[-1].subschemeId |= fit

goto_start_HF = [ Row(f_HF-5*fsr,0,ignore|O2,HF_laser) ]

scan_HF = makeScan(f_HF,fsr,[(-5,5),(-4,1),(-3,1),(-2,1),(-1,5),(0,20),(1,5),(2,1),(3,1),(4,10),
(3,1),(2,1),(1,5),(0,20),(-1,5),(-2,1),(-3,1),(-4,1),(-5,4),(-5,1)],HF,HF_laser)
scan_HF[-1].subschemeId |= fit
    
schemeRows = scan_N2O + scan_O2


$$$