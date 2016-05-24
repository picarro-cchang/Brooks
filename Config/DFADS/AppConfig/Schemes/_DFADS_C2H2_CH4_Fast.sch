$$$
schemeVersion = 1
repeat = 10
C2H2a = 200
C2H2b = 201
CH4 = 25
H2Ob = 11
cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768
f_C2H2 = 6574.3832
f_CH4 = 6057.09
f_H2O = 6574.8535
f_H2Ob = 6057.800

CH4_th = 8000
H2Ob_th = 8000

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2

def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None):
    result = []
    for s,d in stepAndDwell:
        if threshold == None:
            result.append(Row(base+s*incr,d,id,vLaser))
        else:
            result.append(Row(base+s*incr,d,id,vLaser,threshold))
    return result

scanH2O = [Row(f_H2O-21*fsr,1,ignore|C2H2a,vLaser1)]
scanH2O += makeScan(f_H2O,fsr,[(s,2) for s in range(-21,6)],C2H2a,vLaser1)
scanH2O += makeScan(f_H2O,fsr,[(s,2) for s in range(5,-28,-1)],C2H2a|cal|pztcen,vLaser1)
scanH2O += makeScan(f_H2O,fsr,[(s,2) for s in range(-27,-21)],C2H2a|cal|pztcen,vLaser1)
scanH2O += [Row(f_H2O-22*fsr,1,C2H2a|cal|pztcen|fit,vLaser1)]

scanCH4dn = makeScan(f_CH4,fsr,[(s,1) for s in range(8,1,-1)],CH4,vLaser2, CH4_th)
scanCH4dn += [Row(f_CH4+fsr,2,CH4,vLaser2, CH4_th)]
scanCH4dn += [Row(f_CH4,5,CH4,vLaser2, CH4_th)]
scanCH4dn += [Row(f_CH4-fsr,2,CH4,vLaser2, CH4_th)]
scanCH4dn += makeScan(f_CH4,fsr,[(s,1) for s in range(-2,-7,-1)],CH4,vLaser2, CH4_th)

scanCH4up = deepcopy(scanCH4dn[::-1])
for row in scanCH4up: row.subschemeId |= cal + pztcen

scanCH4 = [Row(f_CH4+8*fsr,5,ignore|CH4,vLaser2, CH4_th)]
scanCH4 += scanCH4dn + [Row(f_CH4-6*fsr,1,CH4,vLaser2, CH4_th)] + scanCH4up
scanCH4 += [Row(f_CH4+8*fsr,1,CH4|fit,vLaser2, CH4_th)]
scanCH4 += [Row(f_H2Ob-6*fsr,0,CH4|ignore,vLaser3, H2Ob_th)]

scanH2Ob = [Row(f_H2Ob-6*fsr,5,ignore|H2Ob,vLaser3)]
scanH2Ob += makeScan(f_H2Ob,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,5),(1,2),(2,2),(3,2),(4,2),(5,2)],H2Ob|cal|pztcen,vLaser3, H2Ob_th)
scanH2Ob[-1].subschemeId |= fit
scanH2Ob += [Row(f_CH4+8*fsr,0,ignore|CH4,vLaser2, CH4_th)]

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

schemeRows = scanCH4 + scanH2O
for i in range(5): schemeRows += scanCH4 + scanC2H2 + scanH2Ob + scanC2H2
$$$
