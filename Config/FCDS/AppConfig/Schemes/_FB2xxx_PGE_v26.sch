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
common = 150
CH4_high_precision = 25    #high precision 6057.09
H2O_CFADS = 11
_12CO2_CFADS = 153
pztcen = 8192
cal = 4096
ignore = 16384
fit = 32768
f_12CO2 = 6251.758
f_13CO2 = 6251.315
f_H2O = 6028.78616  #  2011 0714:  Changed from 6028.78038 to 6028.78616 cm-1 based on new finescans
f_13CH4 = 6029.1031
f_12CH4 = 6028.55288
f_H2O_CFADS = 6057.800
f_CH4_high_precision = 6057.090
f_12CO2_CFADS = 6056.50781
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4
vLaser6 = 5
vLaser7 = 6
vLaser8 = 7

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

cal_12CO2 = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,7),(1,2),(3,1),(4,3),(3,2),(1,1),(0,7),(-1,2),(-3,1),(-4,1),(-4,1)],pztcen|cal|_12CO2,vLaser1)
cal_12CO2[-1].subschemeId |= fit

cal_13CO2 = makeScan(f_13CO2,fsr,[(4,30),(3,1),(2,2),(1,5),(0,60),(-1,5),(-2,1),(-3,2),(-4,60),(-3,1),(-2,2),(-1,5),(0,60),(1,5),(2,1),(3,2),(4,30),(4,1)],pztcen|cal|_13CO2,vLaser2)
cal_13CO2[-1].subschemeId |= fit

cal_13CH4_up =  makeScan(f_13CH4,fsr,[(-3,12),(-2,3),(-1,8),(0,30),(1,3),(2,8),(3,3),(4,3)],pztcen|cal|common,vLaser3)
cal_13CH4_down = makeScan(f_13CH4,fsr,[(4,3),(3,3),(2,8),(1,3),(0,30),(-1,8),(-2,3),(-3,12)],pztcen|cal|common,vLaser3)

cal_12CH4_down =  makeScan(f_12CH4,fsr,[(4,3),(3,2),(2,2),(1,2),(0,4),(-1,2),(-2,2),(-3,2),(-4,3)],pztcen|cal|common,vLaser4,extra1=0)
cal_12CH4_down[-1].subschemeId |= fit
cal_12CH4_up = makeScan(f_12CH4,fsr,[(-4,3),(-3,2),(-2,2),(-1,2),(0,4),(1,2),(2,2),(3,2),(4,3)],pztcen|cal|common,vLaser4,extra1=1)

cal_H2O_up =  makeScan(f_H2O,fsr,[(-7,1),(-6,1),(-5,1),(-4,1),(-3,1),(-2,1),(-1,1),(0,3),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),(10,1),(11,1),(12,1)],pztcen|cal|common,vLaser5)
cal_H2O_up[0].subschemeId &= ~cal

cal_H2O_down = makeScan(f_H2O,fsr,[(12,1),(11,1),(10,1),(9,1),(8,1),(7,1),(6,1),(5,1),(4,1),(3,1),(2,1),(1,1),(0,3),(-1,1),(-2,1),(-3,1),(-4,1),(-5,1),(-6,1),(-7,1)],pztcen|cal|common,vLaser5)
cal_H2O_down[0].subschemeId &= ~cal

goto_start_CH4_high_precision = [ Row(f_CH4_high_precision-6*fsr,0,ignore|common,vLaser8) ]
scan_CH4_high_precision =  makeScan(f_CH4_high_precision,fsr,[(-6,2),(-5,1),(-4,2),(-3,1),(-2,2),(-1,2),(0,3),(1,2),(2,2),(3,1),(4,2),(5,1),(6,2),(7,1)],common,vLaser8)
scan_CH4_high_precision += makeScan(f_CH4_high_precision,fsr,[(8,2),(7,1),(6,2),(5,1),(4,2),(3,1),(2,2),(1,2),(0,3),(-1,2),(-2,2),(-3,1),(-4,2),(-5,1),(-6,2)],pztcen|cal|common,vLaser8)

# Mark rows for processed loss calculation
for r in scan_CH4_high_precision:
    if abs(r.setpoint - f_CH4_high_precision) < 0.001*fsr : r.pzt |= 2
    if abs(r.setpoint - (f_CH4_high_precision-6*fsr)) < 0.001*fsr: r.pzt |= 1

#scan_CH4_high_precision[-1].subschemeId |= fit

goto_start_H2O = [ Row(f_H2O_CFADS-5*fsr,0,ignore|H2O_CFADS,vLaser7) ]
scan_H2O =  makeScan(f_H2O_CFADS,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,5),(1,2),(2,2),(3,2),(4,2),(5,2)],pztcen|cal|H2O_CFADS,vLaser7)
scan_H2O[-1].subschemeId |= fit

goto_start_12CO2_CFADS = [ Row(f_12CO2_CFADS-4*fsr,0,ignore|H2O_CFADS,vLaser6) ]
scan_12CO2_CFADS =  makeScan(f_12CO2_CFADS,fsr,[(-4,1),(-3,1),(-2,1),(-1,1),(0,3),(1,1),(2,1),(3,1),(4,1)],pztcen|cal|_12CO2_CFADS,vLaser6)
scan_12CO2_CFADS[-1].subschemeId |= fit

schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + scan_CH4_high_precision + cal_13CH4_down + cal_H2O_down + cal_12CH4_down
schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + scan_CH4_high_precision + cal_13CH4_down + cal_H2O_down + cal_12CH4_down
schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + scan_CH4_high_precision + cal_13CH4_down + cal_H2O_down + cal_12CH4_down
schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + scan_CH4_high_precision + cal_13CH4_down + cal_H2O_down + cal_12CH4_down
schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + scan_CH4_high_precision + cal_13CH4_down + cal_H2O_down + cal_12CH4_down
schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + scan_CH4_high_precision + goto_start_12CO2_CFADS + cal_13CH4_down + cal_H2O_down + cal_12CH4_down + scan_12CO2_CFADS + goto_start_CH4_high_precision

$$$
