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

cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

vLaser1 = 0


def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None):
    result = []
    for s,d in stepAndDwell:
        if threshold == None:
            result.append(Row(base+s*incr,d,id,vLaser))
        else:
            result.append(Row(base+s*incr,d,id,vLaser,threshold))
    return result
 
 
scanHCl = makeScan(f_HCl,fsr,[(-3,25),(-2,2),(-1,4),(0,50),(1,4),(2,2),(3,25)],HCl,vLaser1)
scanHCl += makeScan(f_HCl,fsr,[(3,25),(2,2),(1,4),(0,50),(-1,4),(-2,2),(-3,24),(-3,1)],HCl,vLaser1)
scanHCl[-1].subschemeId |= fit

scanH2O = makeScan(f_HCl,fsr,[(-3,2),(-4,2),(-5,2),(-6,2),(-7,2),(-8,2),(-9,2),(-10,2),(-11,2),(-12,2),(-13,2),(-14,2),(-15,2),(-16,2),(-17,2),(-18,4),(-19,4),(-20,4),(-21,4),(-22,2),(-23,2),(-24,2)],H2O,vLaser1)
scanH2O += makeScan(f_HCl,fsr,[(-23,2),(-22,2),(-21,4),(-20,4),(-19,4),(-18,4),(-17,2),(-16,2),(-15,2),(-14,2),(-13,2),(-12,2),(-11,2),(-10,2),(-9,2),(-8,2),(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,4),(0,4),(1,4),(2,2),(3,2),(4,2)],cal|pztcen|H2O,vLaser1)
scanH2O += makeScan(f_HCl,fsr,[(3,2),(2,2),(1,4),(0,4),(-1,4),(-2,2),(-3,1)],H2O,vLaser1)
scanH2O[-1].subschemeId |= fit

schemeRows = scanH2O + scanHCl + scanHCl + scanHCl + scanHCl + scanHCl + scanHCl + scanHCl + scanHCl + scanHCl + scanHCl

$$$
