$$$
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal_lct.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

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


th_NH3 = float(cfg['AUTOCAL']['th_NH3'])

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None,extra1=0):
    result = []
    for s,d in stepAndDwell:
        if threshold == None:
            result.append(Row(base+s*incr,d,id,vLaser,extra1=extra1))
        else:
            result.append(Row(base+s*incr,d,id,vLaser,threshold,extra1=extra1))
    return result
    
def transition(a,b,dwells,id,vLaser,threshold):
    incr = (b-a)/(len(dwells)+1)
    stepAndDwell = [(i+1,d) for i,d in enumerate(dwells)]
    return makeScan(a,incr,stepAndDwell,id,vLaser,threshold)
    
# 2016 0628:  adapted from existing AEDS and MADS schemes
# 2016 0708:  modified for LCT
# 2016 0718:  V2 shortened HF and NH3 scans for faster response
# 2017 0526:  Removed Cal from schemes.
# 2017 0905:  Added Cal to schemes
# 2018 0206:  Added flags for first and last ring-downs so that fitter can monitor baseline shift
# 2018 0313:  Extended H2O region by 1 FSR to lower frequency for better CO2 determination

goto_start_H2O = [ Row(f_NH3+23*fsr,0,ignore|H2O,NH3_laser,th_NH3) ]

scan_H2O = makeScan(f_NH3,fsr,[
(23,4),(24,4),(25,5),(26,10),(27,5),(28,2),(29,2),(30,5),(29,2),(28,2),(27,5),(26,10),(25,5),(24,4),(23,3),(23,1)],cal|H2O,NH3_laser,th_NH3)
scan_H2O[-1].subschemeId |= fit

goto_start_NH3 = [ Row(f_NH3+12*fsr,0,ignore|H2O,NH3_laser,th_NH3) ]

NH3_up = makeScan(f_NH3,fsr,[(-3,5),(-2,5),(-1,5),(0,20),(1,5),(2,5),(3,1),(4,1),(5,1),(6,1),(7,5),(8,5),(9,20),
(10,5),(11,5),(12,4)],cal|NH3,NH3_laser,th_NH3,extra1=0)

NH3_dn = deepcopy(NH3_up[::-1])

NH3_first = makeScan(f_NH3,fsr,[(12,4),(11,5),(10,5),(9,20),(8,5),(7,5),(6,1),(5,1),(4,1),(3,1),(2,5),(1,5),(0,20),
(-1,5),(-2,5),(-3,4),(-3,1)],cal|NH3,NH3_laser,th_NH3,extra1=1)

NH3_last = makeScan(f_NH3,fsr,[(-3,5),(-2,5),(-1,5),(0,20),(1,5),(2,5),(3,1),(4,1),(5,1),(6,1),(7,5),(8,5),(9,20),
(10,5),(11,5),(12,4)],cal|NH3,NH3_laser,th_NH3,extra1=2)

scan_NH3 = NH3_first + NH3_up + NH3_dn + NH3_last
scan_NH3.append(Row(f_NH3+12*fsr,1,NH3|fit,NH3_laser,th_NH3))

schemeRows = scan_H2O + goto_start_NH3  + scan_NH3 + goto_start_NH3  + scan_NH3 + goto_start_H2O
$$$
