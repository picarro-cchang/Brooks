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
common = 160
CH4_high_precision = 25    #high precision 6057.09
H2O_CFADS = 11
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

cal_12CO2 = makeScan(f_12CO2,fsr,[(-4,1),(-3,2),(-1,1),(0,7),(1,2),(3,1),(4,3),(3,2),(1,1),(0,7),(-1,2),(-3,1),(-4,1),(-4,1)],pztcen|_12CO2,vLaser1)
cal_12CO2[-1].subschemeId |= fit

cal_13CO2 = makeScan(f_13CO2,fsr,[(4,30),(3,1),(2,2),(1,5),(0,60),(-1,5),(-2,1),(-3,2),(-4,60),(-3,1),(-2,2),(-1,5),(0,60),(1,5),(2,1),(3,2),(4,30),(4,1)],pztcen|_13CO2,vLaser2)
cal_13CO2[-1].subschemeId |= fit

cal_13CH4_up =  makeScan(f_13CH4,fsr,[(-3,14),(-2,4),(-1,8),(0,32),(1,4),(2,14),(3,4),(4,4)],pztcen|common,vLaser3,extra1=_13CH4)
cal_13CH4_down = makeScan(f_13CH4,fsr,[(4,4),(3,4),(2,14),(1,4),(0,32),(-1,8),(-2,4),(-3,14)],pztcen|common,vLaser3,extra1=_13CH4)

cal_12CH4_down =  makeScan(f_12CH4,fsr,[(4,6),(3,4),(2,2),(1,4),(0,8),(-1,4),(-2,2),(-3,4),(-4,6)],pztcen|common,vLaser4,extra1=_12CH4)
cal_12CH4_down[-1].subschemeId |= fit
cal_12CH4_up = makeScan(f_12CH4,fsr,[(-4,6),(-3,4),(-2,2),(-1,4),(0,8),(1,4),(2,2),(3,4),(4,6)],pztcen|common,vLaser4,extra1=_12CH4)


cal_H2O_up =  makeScan(f_H2O,fsr,[(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,6),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2),(11,2),(12,2)],pztcen|common,vLaser5,extra1=H2O)
cal_H2O_up[0].subschemeId &= ~cal

cal_H2O_down = makeScan(f_H2O,fsr,[(12,2),(11,2),(10,2),(9,2),(8,2),(7,2),(6,2),(5,2),(4,2),(3,2),(2,2),(1,2),(0,6),(-1,2),(-2,2),(-3,2),(-4,2),(-5,2),(-6,2),(-7,2)],pztcen|common,vLaser5,extra1=H2O)
cal_H2O_down[0].subschemeId &= ~cal

goto_start_CH4_high_precision = [ Row(f_CH4_high_precision-6*fsr,0,ignore|CH4_high_precision,vLaser8) ]
scan_CH4_high_precision =  makeScan(f_CH4_high_precision,fsr,[(-6,2),(-5,1),(-4,2),(-3,1),(-2,2),(-1,3),(0,8),(1,3),(2,2),(3,1),(4,2),(5,1),(6,2),(7,2)],CH4_high_precision,vLaser8)
scan_CH4_high_precision += makeScan(f_CH4_high_precision,fsr,[(8,2),(7,2),(6,2),(5,1),(4,2),(3,1),(2,2),(1,3),(0,8),(-1,3),(-2,2),(-3,1),(-4,2),(-5,1),(-6,2)],pztcen|CH4_high_precision,vLaser8)
scan_CH4_high_precision[-1].subschemeId |= fit

goto_start_H2O = [ Row(f_H2O_CFADS-5*fsr,0,ignore|H2O_CFADS,vLaser7) ]
scan_H2O =  makeScan(f_H2O_CFADS,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,5),(1,2),(2,2),(3,2),(4,2),(5,2)],pztcen|H2O_CFADS,vLaser7)
scan_H2O[-1].subschemeId |= fit

schemeRows += cal_12CH4_up + cal_H2O_up + cal_13CH4_up + cal_13CH4_down + cal_H2O_down + cal_12CH4_down + scan_CH4_high_precision + goto_start_H2O + cal_12CH4_up + cal_H2O_up + cal_13CH4_up + cal_13CH4_down + cal_H2O_down + cal_12CH4_down+ scan_H2O + goto_start_CH4_high_precision



$$$
