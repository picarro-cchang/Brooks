$$$
schemeVersion = 1
repeat = 1

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

HF = 60
O2 = 61
f_HF = 7823.8505
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
 
 
scanO2 = makeScan(f_O2,fsr,[(s,7) for s in range(60,-9,-1)],cal|O2,vLaser1)
scanO2 += makeScan(f_O2,fsr,[(s,7) for s in range(-8,61)],cal|O2,vLaser1)
scanO2 += [Row(f_O2+60*fsr,1,fit|O2,vLaser1)]

#scanO2 = makeScan(f_HF,fsr,[(s,7) for s in range(18,-51,-1)],cal|O2,vLaser1)
#scanO2 += makeScan(f_HF,fsr,[(s,7) for s in range(-50,19)],cal|O2,vLaser1)
#scanO2 += [Row(f_HF+18*fsr,1,fit|O2,vLaser1)]

scanHFdn = makeScan(f_HF,fsr,[(s,5) for s in range(18,1,-1)],HF,vLaser1)
scanHFdn += [Row(f_HF+fsr,10,HF,vLaser1)]
scanHFdn += [Row(f_HF,80,HF,vLaser1)]
scanHFdn += [Row(f_HF-fsr,10,HF,vLaser1)]
scanHFdn += makeScan(f_HF,fsr,[(s,5) for s in range(-2,-8,-1)],HF,vLaser1)

scanHFup = makeScan(f_HF,fsr,[(s,5) for s in range(-7,-1)],HF,vLaser1)
scanHFup += [Row(f_HF-fsr,10,HF,vLaser1)]
scanHFup += [Row(f_HF,80,HF,vLaser1)]
scanHFup += [Row(f_HF+fsr,10,HF,vLaser1)]
scanHFup += makeScan(f_HF,fsr,[(s,5) for s in range(2,19)],HF,vLaser1)
scanHFup += [Row(f_HF+18*fsr,1,fit|HF,vLaser1)]

scanHF = scanHFdn + scanHFup

schemeRows = scanO2 + scanHF + scanHF + scanHF + scanHF + scanHF

$$$
