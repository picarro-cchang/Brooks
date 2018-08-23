$$$
schemeVersion = 1
repeat = 1

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
 
 
scanO2 = makeScan(f_O2,fsr,[(-5,3),(-4,2),(-3,2),(-2,5),(-1,5),(0,16),(1,5),(2,2),(3,2),(4,4)],cal|pztcen|O2,vLaser1)
scanO2 += makeScan(f_O2,fsr,[(3,2),(2,2),(1,5),(0,16),(-1,5),(-2,5),(-3,2),(-4,2),(-5,2)],pztcen|O2,vLaser1)
scanO2 += [Row(f_O2-5*fsr,1,fit|O2,vLaser1)]

schemeRows = scanO2

$$$
