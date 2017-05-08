$$$
schemeVersion = 1
repeat = 10

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

H2O = 63
HCl = 64
f_H2O = 5723.18457
f_HCl = 5723.29933

cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

vLaser1 = 1


def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None):
    result = []
    for s,d in stepAndDwell:
        if threshold == None:
            result.append(Row(base+s*incr,d,id,vLaser))
        else:
            result.append(Row(base+s*incr,d,id,vLaser,threshold))
    return result

#   Scheme to use with "big water" reference line
 
scanHCl = makeScan(f_HCl,fsr,[(-10,4),(-9,2),(-8,2),(-7,2),(-6,8),(-5,8),(-4,2),(-3,25),(-2,2),(-1,4),(0,50),(1,4),(2,2),(3,25)],H2O,vLaser1)
scanHCl += makeScan(f_HCl,fsr,[(3,25),(2,2),(1,4),(0,50),(-1,4),(-2,2),(-3,25),(-4,2),(-5,8),(-6,8),(-7,2),(-8,2),(-9,2),(-10,3),(-10,1)],H2O|cal|pztcen,vLaser1)
scanHCl[-1].subschemeId |= fit

schemeRows = scanHCl

$$$
