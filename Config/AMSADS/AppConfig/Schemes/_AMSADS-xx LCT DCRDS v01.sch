$$$
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal_lct.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

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

nh3_baseline_offset = 19
hf_baseline_offset = -6
o2_baseline_offset = -37
baseline_interval = 4

th_HF = float(cfg['AUTOCAL']['th_HF'])
th_NH3 = float(cfg['AUTOCAL']['th_NH3'])
th_HCl = float(cfg['AUTOCAL']['th_HCl'])

### merger HCl scheme to AMSADS 
#   2019 0513:  simplified by removing redundant HF and NH3 scans

#schemeVersion = 1
repeat = 5

#cal = 4096
#pztcen = 8192
#ignore = 16384
#fit = 32768

H2O_a = 63
HCl = 64
f_H2O_a = 5738.8599
f_HCl = 5739.2617

HCl_baseline_offset = -6
HCl_baseline_interval = 8

# cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
# fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

HCl_laser = 2
#################################


schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None,extra2=0):
    result = []
    j = 0
    if id%4096 == HF:
        baseline_offset = hf_baseline_offset
    elif id%4096 == O2:
        baseline_offset = o2_baseline_offset
    else:
        baseline_offset = nh3_baseline_offset
    for s,d in stepAndDwell:
        dwell = 0
        for i in range(d):
            if threshold == None:
                if (j % baseline_interval == 0):
                    if dwell > 0:
                        result.append(Row(base+s*incr,dwell,id,vLaser,extra2=0))
                        dwell = 0                
                    result.append(Row(base+baseline_offset*incr,1,id,vLaser,extra2=1))
                dwell += 1
                j += 1
                if i == (d-1):
                    result.append(Row(base+s*incr,dwell,id,vLaser,extra2=0))
            else:
                if (j % baseline_interval == 0):
                    if dwell > 0:
                        result.append(Row(base+s*incr,dwell,id,vLaser,threshold,extra2=0))
                        dwell = 0                
                    result.append(Row(base+baseline_offset*incr,1,id,vLaser,threshold,extra2=1))
                dwell += 1
                j += 1
                if i == (d-1):
                    result.append(Row(base+s*incr,dwell,id,vLaser,threshold,extra2=0))
    return result
    
    
def makeScan_HCl(base,incr,stepAndDwell,id,vLaser,threshold=None,extra2=0):
    result = []
    j = 0
    for s,d in stepAndDwell:
        dwell = 0
        for i in range(d):
            if threshold == None:
                if (j % HCl_baseline_interval == 0):
                    if dwell > 0:
                        result.append(Row(base+s*incr,dwell,id,vLaser,extra2=0))
                        dwell = 0                
                    result.append(Row(base+HCl_baseline_offset*incr,1,id,vLaser,extra2=1))
                dwell += 1
                j += 1
                if i == (d-1):
                    result.append(Row(base+s*incr,dwell,id,vLaser,extra2=0))
            else:
                if (j % HCl_baseline_interval == 0):
                    if dwell > 0:
                        result.append(Row(base+s*incr,dwell,id,vLaser,threshold,extra2=0))
                        dwell = 0                
                    result.append(Row(base+HCl_baseline_offset*incr,1,id,vLaser,threshold,extra2=1))
                dwell += 1
                j += 1
                if i == (d-1):
                    result.append(Row(base+s*incr,dwell,id,vLaser,threshold,extra2=0))
    return result
    
# HF/NH3 schemes
# 2018 0425:  first AMADS DCRDS scheme branched from v06 of the conventional LCT scheme with interleaved 
#             baseline points for differential measurement adapted from SADS scheme _HCl+H2O_DCRDS_v6.sch
# 2018 0710:  Extended H2O region by 1 FSR to higher frequency for better C2H2 determination -- for dirty FOUP application

goto_start_H2O = [ Row(f_NH3+23*fsr,0,ignore|H2O,NH3_laser,th_NH3) ]

scan_H2O = makeScan(f_NH3,fsr,[
(23,4),(24,4),(25,5),(26,10),(27,5),(28,2),(29,2),(30,3),(31,2),(30,3),(29,2),(28,2),(27,5),(26,10),(25,5),(24,4),(23,4)],cal|H2O,NH3_laser,th_NH3)
scan_H2O.append(Row(f_NH3+nh3_baseline_offset*fsr,1,H2O|fit,NH3_laser,th_NH3,extra2=1))

goto_start_NH3 = [ Row(f_NH3+12*fsr,0,ignore|H2O,NH3_laser,th_NH3) ]

NH3_up = makeScan(f_NH3,fsr,[(-3,5),(-2,5),(-1,5),(0,20),(1,5),(2,5),(3,1),(4,1),(5,1),(6,1),(7,5),(8,5),(9,20),
(10,5),(11,5),(12,4)],cal|NH3,NH3_laser,th_NH3)

NH3_dn = deepcopy(NH3_up[::-1])

NH3_first = makeScan(f_NH3,fsr,[(12,4),(11,5),(10,5),(9,20),(8,5),(7,5),(6,1),(5,1),(4,1),(3,1),(2,5),(1,5),(0,20),
(-1,5),(-2,5),(-3,5)],cal|NH3,NH3_laser,th_NH3)

NH3_last = makeScan(f_NH3,fsr,[(-3,5),(-2,5),(-1,5),(0,20),(1,5),(2,5),(3,1),(4,1),(5,1),(6,1),(7,5),(8,5),(9,20),
(10,5),(11,5),(12,4)],cal|NH3,NH3_laser,th_NH3)

scan_NH3 = NH3_first + NH3_up + NH3_dn + NH3_last
scan_NH3.append(Row(f_NH3+nh3_baseline_offset*fsr,1,NH3|fit,NH3_laser,th_NH3,extra2=1))

goto_start_O2 = [ Row(f_HF-38*fsr,0,ignore|O2,HF_laser,th_HF) ]

scan_O2 = makeScan(f_HF,fsr,[(-38,5),(-39,2),(-40,2),(-41,5),(-42,10),(-43,5),(-44,2),(-45,2),(-46,2),(-47,10),
(-46,2),(-45,2),(-44,2),(-43,5),(-42,10),(-41,5),(-40,2),(-39,2),(-38,5)],cal|O2,HF_laser,th_HF)
scan_O2.append(Row(f_HF+o2_baseline_offset*fsr,1,O2|fit,HF_laser,th_HF,extra2=1))

goto_start_HF = [ Row(f_HF-5*fsr,0,ignore|O2,HF_laser,th_HF) ]

scan_HF = makeScan(f_HF,fsr,[(-5,5),(-4,1),(-3,1),(-2,1),(-1,5),(0,20),(1,5),(2,1),(3,1),(4,5)],cal|HF,HF_laser,th_HF)
scan_HF += makeScan(f_HF,fsr,[(4,5),(3,1),(2,1),(1,5),(0,20),(-1,5),(-2,1),(-3,1),(-4,1),(-5,5)],cal|HF,HF_laser,th_HF)
scan_HF.append(Row(f_HF+hf_baseline_offset*fsr,1,HF|fit,HF_laser,th_HF,extra2=1))
    
#schemeRows = scan_H2O + goto_start_NH3 + scan_HF + goto_start_O2 + scan_NH3 + scan_O2 + goto_start_HF + scan_NH3 + goto_start_H2O + scan_HF

# HCl scheme
#   Version 2 increases number of RDs on methane peaks
#   Version 3 merges the old "HCL" and "H2O+CH4" scans to try to smooth the Allan Variance
#   Version 4 breaks the HCl scan into shorter pieces and adds up/down flag to H2O sweep -- try to handle solvent interference

#   Version 1 of DCRDS series is a new approach to managing shifting baseline:  Differential CRDS
#   Versions 2-4 of DCRDS explored the idea of putting "baseline" on the HCl peak and reducing frequency of baseline points
#   Version 5 reverts to baseline removed from strong absorption features, retains idea of reduced baseline frequency
#             with baseline_offset = -2 and baseline_interval = 1 it is essentially same as V1 (jah)
#   Version 6 attempts to write lines with dwell > 1 when the baseline interval and scheme permit (may be too clever) (jah)
 
scanHCl = makeScan_HCl(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O_a,HCl_laser,th_HCl)
scanHCl += makeScan_HCl(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],H2O_a,HCl_laser,th_HCl)

scanHCl_first = makeScan_HCl(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O_a,HCl_laser,th_HCl)
scanHCl_first += makeScan_HCl(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],H2O_a,HCl_laser,th_HCl)

scanHCl_last = makeScan_HCl(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O_a,HCl_laser,th_HCl)
scanHCl_last += makeScan_HCl(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],cal|H2O_a,HCl_laser,th_HCl)

scanH2O_a = makeScan_HCl(f_HCl,fsr,[(-4,8),(-5,4),(-6,8),(-7,2),(-8,2),(-9,2),(-10,2),(-11,2),(-12,2),(-13,2),(-14,2),(-15,2),(-16,2),(-17,2),(-18,4),(-19,4),(-20,4),(-21,4),(-22,4),(-23,8),(-24,8)],cal|H2O_a,HCl_laser,th_HCl)
scanH2O_a += makeScan_HCl(f_HCl,fsr,[(-23,8),(-22,4),(-21,4),(-20,4),(-19,4),(-18,4),(-17,2),(-16,2),(-15,2),(-14,2),(-13,2),(-12,2),(-11,2),(-10,2),(-9,2),(-8,2),(-7,2),(-6,8),(-5,4),(-4,7),(-4,1)],H2O_a,HCl_laser,th_HCl)

scanH2O_a.append(Row(f_HCl+HCl_baseline_offset*fsr,1,H2O_a|fit,HCl_laser,th_HCl,extra2=1))

schemeRows = scan_H2O + goto_start_NH3 + scan_HF + goto_start_O2 + scan_NH3 + goto_start_H2O + scan_O2 + goto_start_HF + scanHCl_first + scanHCl + scanHCl + scanHCl + scanHCl_last + scanH2O_a

$$$
