$$$
schemeVersion = 2  #  July 2011:  center frequencies revised based on new spectroscopy with CFIDS2001
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
f_H2O = 6028.7861
f_13CH4 = 6029.1020
f_12CH4 = 6028.55288
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,**kwargs):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser,**kwargs))
    return result
    
def transition(a,b,dwells,id,vLaser,**kwargs):
    incr = (b-a)/(len(dwells)+1)
    stepAndDwell = [(i+1,d) for i,d in enumerate(dwells)]
    return makeScan(a,incr,stepAndDwell,id,vLaser,**kwargs)

cal_12CO2 = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,7),(1,2),(3,1),(4,3),(3,2),(1,1),(0,7),(-1,2),(-3,1),(-4,1),(-4,1)],cal|_12CO2,vLaser1)
cal_12CO2[-1].subschemeId |= fit

cal_13CO2 = makeScan(f_13CO2,fsr,[(4,30),(3,1),(2,2),(1,5),(0,60),(-1,5),(-2,1),(-3,2),(-4,60),(-3,1),(-2,2),(-1,5),(0,60),(1,5),(2,1),(3,2),(4,30),(4,1)],cal|_13CO2,vLaser2)
cal_13CO2[-1].subschemeId |= fit

cal_13CH4 =  makeScan(f_13CH4,fsr,[(-3,14),(-2,4),(-1,8),(0,32),(1,4),(2,14)],_13CH4,vLaser3)
cal_13CH4 += makeScan(f_13CH4,fsr,[(2,14),(1,4),(0,32),(-1,8),(-2,4),(-3,14)],cal|_13CH4,vLaser3)
cal_13CH4[-1].subschemeId |= fit

cal_12CH4 =  makeScan(f_12CH4,fsr,[(4,6),(3,4),(2,2),(1,4),(0,8),(-1,4),(-2,2),(-3,4),(-4,6)],_12CH4,vLaser4)
cal_12CH4 += makeScan(f_12CH4,fsr,[(-4,6),(-3,4),(-2,2),(-1,4),(0,8),(1,4),(2,2),(3,4),(4,6)],cal|_12CH4,vLaser4)
cal_12CH4[-1].subschemeId |= fit

cal_H2O_up =  makeScan(f_H2O,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,6),(1,2),(2,2),(3,2),(4,2),(5,2)],cal|H2O,vLaser5,extra1=1)
#cal_H2O_up[0].subschemeId &= ~cal
cal_H2O_up[-1].subschemeId |= fit

cal_H2O_down = makeScan(f_H2O,fsr,[(5,2),(4,2),(3,2),(2,2),(1,2),(0,6),(-1,2),(-2,2),(-3,2),(-4,2),(-5,2)],cal|H2O,vLaser5,extra1=2)
#cal_H2O_down[0].subschemeId &= ~cal
cal_H2O_down[-1].subschemeId |= fit

schemeRows += cal_13CH4 + cal_H2O_down + cal_12CH4 + cal_H2O_up



$$$
