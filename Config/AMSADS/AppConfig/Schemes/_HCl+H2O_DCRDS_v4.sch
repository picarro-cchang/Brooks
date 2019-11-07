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

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

vLaser1 = 0


def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None,extra2=0):
    #result0=[]
    result=[]
    for s,d in stepAndDwell:
        for i in range(d):
            if threshold == None:
                result.append(Row(base+s*incr,1,id,vLaser,extra2=0))
                #if(i%5 ==0): result.append(Row(base-0.0*incr,1,id,vLaser,extra2=1)) # reduce the numbers of the reference point 
            else:
                result.append(Row(base+s*incr,1,id,vLaser,threshold,extra2=0))
                #if(i%5 ==0): result.append(Row(base-0.0*incr,1,id,vLaser,threshold,extra2=1)) # reduce the numbers of the reference point

    return result


#   Version 2 increases number of RDs on methane peaks
#   Version 3 merges the old "HCL" and "H2O+CH4" scans to try to smooth the Allan Variance
#   Version 4 breaks the HCl scan into shorter pieces and adds up/down flag to H2O sweep -- try to handle solvent interference

#   Version 1 of DCRDS series is a new approach to managing shifting baseline:  Differential CRDS

scanHCl = makeScan(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O,vLaser1)
scanHCl += makeScan(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],H2O,vLaser1)

scanHCl_first = makeScan(f_HCl,fsr,[(-2,1),(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O,vLaser1)
scanHCl_first += makeScan(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],H2O,vLaser1)
#scanHCl_first[0].extra2 = 1

scanHCl_last = makeScan(f_HCl,fsr,[(-3,5),(-2,1),(-1,1),(0,10),(1,1),(2,1),(3,5)],H2O,vLaser1)
scanHCl_last += makeScan(f_HCl,fsr,[(3,5),(2,1),(1,1),(0,10),(-1,1),(-2,1),(-3,5)],cal|pztcen|H2O,vLaser1)

scanH2O = makeScan(f_HCl,fsr,[(-4,8),(-5,4),(-6,8),(-7,2),(-8,2),(-9,2),(-10,2),(-11,2),(-12,2),(-13,2),(-14,2),(-15,2),(-16,2),(-17,2),(-18,4),(-19,4),(-20,4),(-21,4),(-22,4),(-23,8),(-24,8)],cal|pztcen|H2O,vLaser1)
scanH2O += makeScan(f_HCl,fsr,[(-23,8),(-22,4),(-21,4),(-20,4),(-19,4),(-18,4),(-17,2),(-16,2),(-15,2),(-14,2),(-13,2),(-12,2),(-11,2),(-10,2),(-9,2),(-8,2),(-7,2),(-6,8),(-5,4),(-4,7),(-4,1)],H2O,vLaser1)
scanH2O[-1].subschemeId |= fit
#schemeRows = scanHCl
scantotal = scanHCl_first + scanHCl + scanHCl + scanHCl + scanHCl_last + scanH2O
res_len=len(scantotal)
scans=[]
for k in range(res_len):
        scans.append(scantotal[k])
        if (k%9==0): # reduce the numbers of the reference points by the factor of 5, 4, 3, 2, and 1
            scantotal[k].extra2 = 1
            scantotal[k].setpoint = f_HCl
            scans.append(scantotal[k])
schemeRows = scans

$$$
