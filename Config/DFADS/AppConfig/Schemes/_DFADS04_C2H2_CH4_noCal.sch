$$$
schemeVersion = 1
repeat = 2
C2H2a = 200
C2H2b = 201
CH4 = 25
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768
f_C2H2 = 6574.3832
f_CH4 = 6057.09
f_H2O = 6574.833

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

scanH2O = [Row(f_H2O-21*fsr,1,ignore|C2H2a,vLaser1)]
scanH2O += makeScan(f_H2O,fsr,[(s,2) for s in range(-21,6)],C2H2a,vLaser1)
scanH2O += makeScan(f_H2O,fsr,[(s,2) for s in range(5,-28,-1)],C2H2a|pztcen,vLaser1)
scanH2O += makeScan(f_H2O,fsr,[(s,2) for s in range(-27,-21)],C2H2a|pztcen,vLaser1)
scanH2O += [Row(f_H2O-22*fsr,1,C2H2a|pztcen|fit,vLaser1)]

scanCH4up = makeScan(f_CH4,fsr,[(s,1) for s in range(-6,-1)],CH4,vLaser2)
scanCH4up += [Row(f_CH4-fsr,2,CH4,vLaser2)]
scanCH4up += [Row(f_CH4,5,CH4,vLaser2)]
scanCH4up += [Row(f_CH4+fsr,2,CH4,vLaser2)]
scanCH4up += makeScan(f_CH4,fsr,[(s,1) for s in range(2,8)],CH4,vLaser2)

scanCH4dn = deepcopy(scanCH4up[::-1])
for row in scanCH4dn: row.subschemeId |= pztcen

scanCH4 = [Row(f_CH4-6*fsr,1,ignore|CH4,vLaser2)]
scanCH4 += scanCH4up + [Row(f_CH4+8*fsr,1,CH4,vLaser2)] + scanCH4dn
scanCH4 += [Row(f_CH4-6*fsr,1,CH4|fit,vLaser2)]

scanC2H2 = [Row(f_C2H2-fsr,1,ignore|C2H2b,vLaser1)]
scanC2H2 += [Row(f_C2H2-fsr,5,C2H2b,vLaser1)]
scanC2H2 += [Row(f_C2H2,15,C2H2b,vLaser1)]
scanC2H2 += makeScan(f_C2H2,fsr,[(s,1) for s in range(1,6)],C2H2b,vLaser1)
scanC2H2 += makeScan(f_C2H2,fsr,[(s,1) for s in range(5,0,-1)],C2H2b,vLaser1)
scanC2H2 += [Row(f_C2H2,15,C2H2b,vLaser1)]
scanC2H2 += [Row(f_C2H2-fsr,5,C2H2b,vLaser1)]
scanC2H2 += makeScan(f_C2H2,fsr,[(s,1) for s in range(-2,-6,-1)],C2H2b,vLaser1)
scanC2H2 += makeScan(f_C2H2,fsr,[(s,1) for s in range(-5,-1)],C2H2b,vLaser1)
scanC2H2 += [Row(f_C2H2-fsr,5,C2H2b,vLaser1)]
scanC2H2 += [Row(f_C2H2,15,C2H2b,vLaser1)]
scanC2H2 += [Row(f_C2H2,1,C2H2b|fit,vLaser1)]

schemeRows = scanH2O
for i in range(10): schemeRows += scanCH4 + scanC2H2
$$$
