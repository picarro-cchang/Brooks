$$$
schemeVersion = 1
repeat = 1
_12CO2 = 105
_13CO2 = 106
_12CO2_alt = 155
_13CO2_alt = 156
_13CH4 = 151
_12CH4 = 150
H2O = 152
pztcen = 8192
cal = 4096
ignore = 16384
fit = 32768
f_12CO2 = 6251.758
f_13CO2 = 6251.315
f_H2O = 6028.78038
f_13CH4 = 6029.1031
f_12CH4 = 6028.55298
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
cal_12CO2 += makeScan(f_12CO2,fsr,[(5,4),(4,4),(3,4),(2,4),(1,4),(0,4),(-1,4),(-2,4),(-3,4),(-4,4),(-5,4),(-5,1)],pztcen|_12CO2_alt,vLaser1)
cal_12CO2[-1].subschemeId |= fit

cal_13CO2 =  makeScan(f_13CO2,fsr,[(5,2),(5,2),(4,2),(3,2),(2,2),(1,2),(0,2),(-1,2),(-2,2),(-3,2),(-4,2)],_13CO2_alt,vLaser2)
cal_13CO2 += makeScan(f_13CO2,fsr,[(-5,4),(-4,4),(-3,4),(-2,4),(-1,4),(0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(5,1)],pztcen|_13CO2_alt,vLaser2)
cal_13CO2[-1].subschemeId |= fit

scan_12CO2 = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,7),(1,2),(3,1),(4,3),(3,2),(1,1),(0,7),(-1,2),(-3,1),(-4,1),(-4,1)],_12CO2,vLaser1)
scan_12CO2[-1].subschemeId |= fit

scan_13CO2 = makeScan(f_13CO2,fsr,[(4,30),(3,1),(2,2),(1,5),(0,60),(-1,5),(-2,1),(-3,2),(-4,60),(-3,1),(-2,2),(-1,5),(0,60),(1,5),(2,1),(3,2),(4,30),(4,1)],_13CO2,vLaser2)
scan_13CO2[-1].subschemeId |= fit

cal_13CH4 =  makeScan(f_13CH4,fsr,[(-3,14),(-2,4),(-1,2),(0,32),(1,4),(2,14)],_13CH4,vLaser3)
cal_13CH4 += makeScan(f_13CH4,fsr,[(2,14),(1,4),(0,32),(-1,2),(-2,4),(-3,14)],pztcen|_13CH4,vLaser3)
cal_13CH4[-1].subschemeId |= fit

cal_12CH4 =  makeScan(f_12CH4,fsr,[(4,6),(3,4),(2,2),(1,4),(0,8),(-1,4),(-2,2),(-3,4),(-4,6)],_12CH4,vLaser4)
cal_12CH4 += makeScan(f_12CH4,fsr,[(-4,6),(-3,4),(-2,2),(-1,4),(0,8),(1,4),(2,2),(3,4),(4,6)],pztcen|_12CH4,vLaser4)
cal_12CH4[-1].subschemeId |= fit

#cal_H2O =  makeScan(f_H2O,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,6),(1,2),(2,2),(3,2),(4,2),(5,2)],H2O,vLaser5)
#cal_H2O += makeScan(f_H2O,fsr,[(5,2),(4,2),(3,2),(2,2),(1,2),(0,6),(-1,2),(-2,2),(-3,2),(-4,2),(-5,2)],pztcen|H2O,vLaser5)
cal_H2O =  makeScan(f_H2O,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,6),(1,2),(2,2),(3,2),(4,2),(5,2)],pztcen|H2O,vLaser5)
cal_H2O[-1].subschemeId |= fit

#scan_13CH4 = makeScan(f_13CH4,fsr,[(-3,14),(-2,4),(-1,2),(0,32),(1,4),(2,14),(2,14),(1,4),(0,32),(-1,2),(-2,4),(-3,14)],_13CH4,vLaser3)
scan_13CH4 = makeScan(f_13CH4,fsr,[(-3,42),(-2,12),(-1,6),(0,94),(1,12),(2,42),(2,42),(1,12),(0,94),(-1,6),(-2,12),(-3,42)],_13CH4,vLaser3)
scan_13CH4[-1].subschemeId |= fit

scan_12CH4 = makeScan(f_12CH4,fsr,[(4,6),(3,4),(2,2),(1,4),(0,8),(-1,4),(-2,2),(-3,4),(-4,6),(-4,6),(-3,4),(-2,2),(-1,4),(0,8),(1,4),(2,2),(3,4),(4,6)],_12CH4,vLaser4)
scan_12CH4[-1].subschemeId |= fit

#scan_H2O = makeScan(f_H2O,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,6),(1,2),(2,2),(3,2),(4,2),(5,2),(5,2),(4,2),(3,2),(2,2),(1,2),(0,6),(-1,2),(-2,2),(-3,2),(-4,2),(-5,2)],H2O,vLaser5)
scan_H2O = makeScan(f_H2O,fsr,[(5,2),(4,2),(3,2),(2,2),(1,2),(0,6),(-1,2),(-2,2),(-3,2),(-4,2),(-5,2)],H2O,vLaser5)
scan_H2O[-1].subschemeId |= fit

#schemeRows += cal_13CH4 + cal_12CH4 + cal_H2O
#schemeRows += scan_13CH4 + scan_12CH4 + scan_H2O
schemeRows += cal_13CH4 + scan_H2O + cal_12CH4 + cal_H2O
schemeRows += scan_13CH4 + scan_H2O + scan_12CH4 + cal_H2O

$$$
