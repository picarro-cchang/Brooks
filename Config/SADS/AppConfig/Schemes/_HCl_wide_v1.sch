$$$
schemeVersion = 1
repeat = 10

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

HCl = 64
f_HCl = 5739.26252

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
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
 
 
scanHCl = makeScan(f_HCl,fsr,[(-11,2),(-10,2),(-9,2),(-8,2),(-7,2),(-6,2),(-5,2),(-4,2),(-3,25),(-2,2),(-1,4),(0,50),(1,4),(2,2),(3,25)],cal|pztcen|HCl,vLaser1)
scanHCl += makeScan(f_HCl,fsr,[(3,25),(2,2),(1,4),(0,50),(-1,4),(-2,2),(-3,25),(-4,2),(-5,2),(-6,2),(-7,2),(-8,2),(-9,2),(-10,2),(-11,1)],pztcen|HCl,vLaser1)
scanHCl[-1].subschemeId |= fit

schemeRows = scanHCl

$$$
