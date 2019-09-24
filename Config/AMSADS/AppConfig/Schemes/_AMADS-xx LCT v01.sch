$$$
schemeVersion = 1
repeat = 3

H2O = 2
NH3 = 4
HF = 60
O2 = 61
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

HF_laser = 0
NH3_laser = 1

f_NH3 = 6548.618
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
    
# 2016 0628:  adapted from existing AEDS and MADS schemes
# 2016 0708:  modified for LCT

goto_start_H2O = [ Row(f_NH3+24*fsr,0,ignore|H2O,NH3_laser) ]

scan_H2O = makeScan(f_NH3,fsr,[
(24,4),(25,5),(26,10),(27,5),(28,2),(29,2),(30,5),(29,2),(28,2),(27,5),(26,10),(25,5),(24,4),(24,1)],H2O,NH3_laser)
scan_H2O[-1].subschemeId |= fit

goto_start_NH3 = [ Row(f_NH3+12*fsr,0,ignore|H2O,NH3_laser) ]

NH3_up = makeScan(f_NH3,fsr,[(-3,10),(-2,10),(-1,10),(0,40),(1,10),(2,10),(3,2),(4,2),(5,2),(6,2),(7,10),(8,10),(9,40),
(10,10),(11,10),(12,10)],NH3,NH3_laser)

NH3_dn = deepcopy(NH3_up[::-1])

scan_NH3 = NH3_dn + NH3_up + NH3_dn + NH3_up
scan_NH3.append(Row(f_NH3+12*fsr,1,NH3|fit,NH3_laser))

goto_start_O2 = [ Row(f_HF-38*fsr,0,ignore|O2,HF_laser) ]

scan_O2 = makeScan(f_HF,fsr,[(-38,5),(-39,2),(-40,2),(-41,5),(-42,10),(-43,5),(-44,2),(-45,2),(-46,2),(-47,10),
(-46,2),(-45,2),(-44,2),(-43,5),(-42,10),(-41,5),(-40,2),(-39,2),(-38,4),(-38,1)],O2,HF_laser)
scan_O2[-1].subschemeId |= fit

goto_start_HF = [ Row(f_HF-5*fsr,0,ignore|O2,HF_laser) ]

scan_HF = makeScan(f_HF,fsr,[(-5,10),(-4,2),(-3,2),(-2,2),(-1,10),(0,40),(1,10),(2,2),(3,2),(4,20),
(3,2),(2,2),(1,10),(0,40),(-1,10),(-2,2),(-3,2),(-4,2),(-5,9),(-5,1)],HF,HF_laser)
scan_HF[-1].subschemeId |= fit
    
schemeRows = scan_H2O + goto_start_NH3 + scan_HF + goto_start_O2 + scan_NH3 + scan_O2 + goto_start_HF + scan_NH3 + goto_start_H2O + scan_HF


$$$