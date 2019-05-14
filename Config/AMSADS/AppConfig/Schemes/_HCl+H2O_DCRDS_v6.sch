$$$
schemeVersion = 1
repeat = 5

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

H2O = 63
HCl = 64
f_H2O = 5738.8599
f_HCl = 5739.2617

baseline_offset = -6
baseline_interval = 8

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

vLaser1 = 2


def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None,extra2=0):
    result = []
    j = 0
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


#   Version 2 increases number of RDs on methane peaks
#   Version 3 merges the old "HCL" and "H2O+CH4" scans to try to smooth the Allan Variance
#   Version 4 breaks the HCl scan into shorter pieces and adds up/down flag to H2O sweep -- try to handle solvent interference

#   Version 1 of DCRDS series is a new approach to managing shifting baseline:  Differential CRDS
#   Versions 2-4 of DCRDS explored the idea of putting "baseline" on the HCl peak and reducing frequency of baseline points
#   Version 5 reverts to baseline removed from strong absorption features, retains idea of reduced baseline frequency
#             with baseline_offset = -2 and baseline_interval = 1 it is essentially same as V1 (jah)
#   Version 6 attempts to write lines with dwell > 1 when the baseline interval and scheme permit (may be too clever) (jah)
 
scanHCl = makeScan(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O,vLaser1)
scanHCl += makeScan(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],H2O,vLaser1)

scanHCl_first = makeScan(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O,vLaser1)
scanHCl_first += makeScan(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],H2O,vLaser1)

scanHCl_last = makeScan(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O,vLaser1)
scanHCl_last += makeScan(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],cal|pztcen|H2O,vLaser1)

scanH2O = makeScan(f_HCl,fsr,[(-4,8),(-5,4),(-6,8),(-7,2),(-8,2),(-9,2),(-10,2),(-11,2),(-12,2),(-13,2),(-14,2),(-15,2),(-16,2),(-17,2),(-18,4),(-19,4),(-20,4),(-21,4),(-22,4),(-23,8),(-24,8)],cal|pztcen|H2O,vLaser1)
scanH2O += makeScan(f_HCl,fsr,[(-23,8),(-22,4),(-21,4),(-20,4),(-19,4),(-18,4),(-17,2),(-16,2),(-15,2),(-14,2),(-13,2),(-12,2),(-11,2),(-10,2),(-9,2),(-8,2),(-7,2),(-6,8),(-5,4),(-4,7),(-4,1)],H2O,vLaser1)

scanH2O.append(Row(f_HCl+baseline_offset*fsr,1,H2O|fit,vLaser1,extra2=1))

schemeRows = scanHCl_first + scanHCl + scanHCl + scanHCl + scanHCl_last + scanH2O

$$$
