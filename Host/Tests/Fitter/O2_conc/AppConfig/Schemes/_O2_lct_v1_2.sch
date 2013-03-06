$$$
schemeVersion = 1
repeat = 30

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

O2 = 61
f_O2 = 7822.9835

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
 
 
scanO2 = makeScan(f_O2,fsr,[(-5,6),(-4,7),(-3,8),(-2,9),(-1,10),(0,12),(1,10),(2,9),(3,8),(4,7),(5,6)],cal|O2,vLaser1)
scanO2 += makeScan(f_O2,fsr,[(5,6),(4,7),(3,8),(2,9),(1,10),(0,12),(-1,10),(-2,9),(-3,8),(-4,7),(-5,6)],O2,vLaser1)
scanO2 += [Row(f_O2-5*fsr,1,fit|O2,vLaser1)]

schemeRows = scanO2

$$$
