$$$
schemeVersion = 1
repeat = 1
_12CO2 = 105
_13CO2 = 106
_12CO2_alt = 155
_13CO2_alt = 156
CH4_high_precision = 25    #high precision 6057.09
CH4 = 29 #sholder 6057.8
H2O = 11
pztcen = 8192
cal = 4096
ignore = 16384
fit = 32768
f_12CO2 = 6251.758
f_13CO2 = 6251.315
f_H2O = 6057.800
f_CH4_high_precision = 6057.090
f_CH4 = 6056.82000
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4

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

cal_12CO2 =  makeScan(f_12CO2,fsr,[(-5,3),(-4,3),(-3,3),(-2,3),(-1,3),(0,3),(1,3),(2,3),(3,3),(4,3)],_12CO2_alt,vLaser1)
cal_12CO2 += makeScan(f_12CO2,fsr,[(5,4),(4,4),(3,4),(2,4),(1,4),(0,4),(-1,4),(-2,4),(-3,4),(-4,4),(-5,4),(-5,1)],cal|_12CO2_alt,vLaser1)
cal_12CO2[-1].subschemeId |= fit

cal_13CO2 =  makeScan(f_13CO2,fsr,[(5,2),(5,2),(4,2),(3,2),(2,2),(1,2),(0,2),(-1,2),(-2,2),(-3,2),(-4,2)],_13CO2_alt,vLaser2)
cal_13CO2 += makeScan(f_13CO2,fsr,[(-5,4),(-4,4),(-3,4),(-2,4),(-1,4),(0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(5,1)],cal|_13CO2_alt,vLaser2)
cal_13CO2[-1].subschemeId |= fit

scan_12CO2 = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,7),(1,2),(3,1),(4,3),(3,2),(1,1),(0,7),(-1,2),(-3,1),(-4,1),(-4,1)],_12CO2,vLaser1)
scan_12CO2[-1].subschemeId |= fit

scan_13CO2 = makeScan(f_13CO2,fsr,[(4,30),(3,1),(2,2),(1,5),(0,60),(-1,5),(-2,1),(-3,2),(-4,60),(-3,1),(-2,2),(-1,5),(0,60),(1,5),(2,1),(3,2),(4,30),(4,1)],_13CO2,vLaser2)
scan_13CO2[-1].subschemeId |= fit

goto_start_CH4_high_precision = [ Row(f_CH4_high_precision-6*fsr,0,ignore|CH4_high_precision,vLaser3) ]
scan_CH4_high_precision =  makeScan(f_CH4_high_precision,fsr,[(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,3),(0,17),(1,3),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2)],CH4_high_precision,vLaser3)
scan_CH4_high_precision += makeScan(f_CH4_high_precision,fsr,[(8,2),(7,2),(6,2),(5,2),(4,2),(3,2),(2,2),(1,3),(0,17),(-1,3),(-2,2),(-3,2),(-4,2),(-5,2),(-6,2)],cal|CH4_high_precision,vLaser3)
scan_CH4_high_precision[-1].subschemeId |= fit

goto_start_CH4 = [ Row(f_CH4-3*fsr,0,ignore|CH4,vLaser4) ]
scan_CH4 =  makeScan(f_CH4,fsr,[(-3,4),(-2,4),(-1,6),(0,35),(1,6),(2,4),(3,4),(4,4)],CH4,vLaser4)
scan_CH4 += makeScan(f_CH4,fsr,[(4,4),(3,4),(2,4),(1,6),(0,35),(-1,6),(-2,4),(-3,4)],cal|CH4,vLaser4)
scan_CH4[-1].subschemeId |= fit

goto_start_H2O = [ Row(f_H2O-5*fsr,0,ignore|H2O,vLaser5) ]
scan_H2O =  makeScan(f_H2O,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,5),(1,2),(2,2),(3,2),(4,2),(5,2)],cal|H2O,vLaser5)
scan_H2O[-1].subschemeId |= fit

schemeRows += cal_12CO2 + cal_13CO2

for i in range(5):
    for loops in range(2):
        schemeRows += scan_13CO2 + scan_12CO2
    schemeRows += scan_13CO2 + scan_CH4 + goto_start_H2O
    for loops in range(2):
        schemeRows += scan_13CO2 + scan_12CO2
    schemeRows += scan_13CO2 + scan_H2O + goto_start_CH4


$$$
