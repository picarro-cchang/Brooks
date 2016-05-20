$$$
schemeVersion = 1
repeat = 1
_12CO2 = 105
H2O = 665
CH4 = 150
pztcen = 8192
cal = 4096
ignore = 16384
fit = 32768
f_13CH4 = 6059.1757
f_12CO2 = 6251.758
f_H2O = 6254.96913

cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

def transition(a,b,dwells,id,vLaser):
    incr = (b-a)/(len(dwells)+1)
    stepAndDwell = [(i+1,d) for i,d in enumerate(dwells)]
    return makeScan(a,incr,stepAndDwell,id,vLaser)

scan_12CO2 =  makeScan(f_12CO2,fsr,[(6,5),(5,1),(4,2),(3,1),(2,2),(1,3),(0,12),(-1,3),(-2,2),(-3,1),(-4,2),(-5,1),(-6,2)],cal|_12CO2,vLaser1)
scan_12CO2[0].subschemeId |= ignore
scan_12CO2[1].subschemeId  |= ignore
scan_12CO2[-1].subschemeId |= ignore

schemeRows += scan_12CO2
schemeRows.append(Row(f_H2O-8*fsr,0,H2O,vLaser2))

step = 0.001
scanCH4  = makeScan(f_13CH4-3*fsr-6*step,step,[(7,2),(6,3),(5,5),(4,5),(3,9),(2,9),(1,30),(0,30),(-1,30),(-2,9),(-3,9),(-4,5),(-5,5),(-6,3),(-7,3),(-8,3)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4-3*fsr-6*step,step,[(-7,3),(-6,3),(-5,5),(-4,5),(-3,9),(-2,9),(-1,30),(0,30),(1,30),(2,9),(3,9),(4,5),(5,5),(6,2)],CH4,vLaser3)

scanCH4 += makeScan(f_13CH4,fsr,[(-2,3),(-1,2),(0,6),(1,2),(2,3),(3,2),(4,7)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4,fsr,[(3,2),(2,3),(1,2),(0,5),(-1,2),(-2,3),(-3,2),(-4,9),(-5,9),(-6,9)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4,fsr,[(-6,9),(-5,9),(-4,9),(-3,2),(-2,3),(-1,2),(0,5),(1,2),(2,3),(3,2),(4,7)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4,fsr,[(3,2),(2,3),(1,2),(0,6),(-1,2),(-2,3),(-3,2)],CH4,vLaser3)

scanCH4 += makeScan(f_13CH4-3*fsr-6*step,step,[(5,5),(4,5),(3,9),(2,9),(1,30),(0,30),(-1,30),(-2,9),(-3,9),(-4,5),(-5,5),(-6,3),(-7,3),(-8,3)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4-3*fsr-6*step,step,[(-7,3),(-6,3),(-5,5),(-4,5),(-3,9),(-2,9),(-1,30),(0,30),(1,30),(2,9),(3,9),(4,5),(5,5),(6,3)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4-3*fsr-6*step,step,[(7,2),(8,3),(9,2),(10,3),(11,2),(12,3),(11,2),(10,3),(9,2),(8,3),(7,2),(6,3)],CH4,vLaser3)

scanCH4 += makeScan(f_13CH4,fsr,[(-4,6),(-5,6),(-6,6)],CH4,vLaser3)
scanCH4 += makeScan(f_13CH4,fsr,[(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,2),(1,2),(2,2),(3,2),(4,2),(5,2)],cal|CH4,vLaser3)
scanCH4 += makeScan(f_13CH4,fsr,[(4,2),(3,2),(2,2),(1,2),(0,2),(-1,2),(-2,2),(-3,2),(-4,2),(-5,2),(-6,2),(-7,2),(-7,1)],cal|CH4,vLaser3)

scanCH4[-1].subschemeId |= fit

schemeRows += scanCH4

scanH2O = makeScan(f_H2O+13*fsr,fsr,[(-21,1),(-20,1),(-19,2),(-18,1),(-17,2),(-16,2),(-15,2),(-14,3),(-13,8),(-12,3),(-11,2),(-10,2),(-9,2),(-8,1),(-7,2),(-6,1),(-5,2),(-4,1),(-3,2),(-2,1),(-1,2),(0,1)],H2O,vLaser2)
scanH2O += makeScan(f_H2O+13*fsr,fsr,[(-1,2),(-2,2),(-3,2),(-4,2),(-5,2),(-6,2),(-7,2),(-8,2),(-9,2),(-10,2),(-11,2),(-12,2),(-13,2),(-14,2),(-15,2),(-16,2),(-17,2),(-18,2),(-19,2),(-20,2),(-21,2)],cal|H2O,vLaser2)
scanH2O[0].subschemeId |= ignore

schemeRows += scanH2O
schemeRows.append(Row(f_12CO2+6*fsr,0,_12CO2,vLaser1))

schemeRows += scanCH4
$$$
