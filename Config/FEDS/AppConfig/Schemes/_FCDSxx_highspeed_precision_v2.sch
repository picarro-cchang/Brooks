$$$
schemeVersion = 1
repeat = 1

CH4_high_precision = 25
common = 150
_12CH4 = 150
_13CH4 = 151
H2O = 152
CO2 = 153
pztcen = 8192
cal = 4096
ignore = 16384
fit = 32768

f_H2O = 6028.78616 
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

goto_start_CH4_high_precision = [ Row(f_CH4_high_precision-6*fsr,0,ignore|CH4_high_precision,vLaser8) ]
scan_CH4_high_precision =  makeScan(f_CH4_high_precision,fsr,[(-6,2),(-5,1),(-4,2),(-3,1),(-2,2),(-1,2),(0,3),(1,2),(2,2),(3,1),(4,2),(5,1),(6,2),(7,1)],pztcen|CH4_high_precision,vLaser8)
scan_CH4_high_precision += makeScan(f_CH4_high_precision,fsr,[(8,2),(7,1),(6,2),(5,1),(4,2),(3,1),(2,2),(1,2),(0,3),(-1,2),(-2,2),(-3,1),(-4,2),(-5,1),(-6,1),(-6,1)],cal|CH4_high_precision,vLaser8)
scan_CH4_high_precision[-1].subschemeId |= fit

goto_start_12CH4 = [ Row(f_12CH4-3*fsr,0,ignore|_12CH4,vLaser4) ]
scan_12CH4 =  makeScan(f_12CH4,fsr,[(-3,1),(-2,1),(-1,1),(0,3),(1,1),(2,1),(3,1)],cal|pztcen|_12CH4,vLaser4)
scan_12CH4[-1].subschemeId |= fit

goto_start_13CH4 = [ Row(f_13CH4-4*fsr,0,ignore|_13CH4,vLaser3) ]
scan_13CH4 =  makeScan(f_13CH4,fsr,[(-4,1),(-3,1),(-2,1),(-1,1),(0,3),(1,1),(2,1),(3,1)],cal|pztcen|_13CH4,vLaser3)
scan_13CH4[-1].subschemeId |= fit

goto_start_H2O = [ Row(f_H2O-3*fsr,0,ignore|H2O,vLaser5) ]
scan_H2O =  makeScan(f_H2O,fsr,[(-3,1),(-2,1),(-1,2),(0,2),(1,2),(2,1),(3,1)],cal|pztcen|H2O,vLaser5)
scan_H2O[-1].subschemeId |= fit

goto_start_12CH4_dn = [ Row(f_12CH4+3*fsr,0,ignore|_12CH4,vLaser4) ]
scan_12CH4_dn =  makeScan(f_12CH4,fsr,[(3,1),(2,1),(1,1),(0,3),(-1,1),(-2,1),(-3,1)],cal|pztcen|_12CH4,vLaser4)
scan_12CH4_dn[-1].subschemeId |= fit

goto_start_13CH4_dn = [ Row(f_13CH4+3*fsr,0,ignore|_13CH4,vLaser3) ]
scan_13CH4_dn =  makeScan(f_13CH4,fsr,[(3,1),(2,1),(1,1),(0,3),(-1,1),(-2,1),(-3,1),(-4,1)],cal|pztcen|_13CH4,vLaser3)
scan_13CH4_dn[-1].subschemeId |= fit

goto_start_H2O_dn = [ Row(f_H2O+3*fsr,0,ignore|H2O,vLaser5) ]
scan_H2O_dn =  makeScan(f_H2O,fsr,[(3,1),(2,1),(1,2),(0,2),(-1,2),(-2,1),(-3,1)],cal|pztcen|H2O,vLaser5)
scan_H2O_dn[-1].subschemeId |= fit

schemeRows += scan_CH4_high_precision + scan_12CH4 + goto_start_H2O
schemeRows += scan_CH4_high_precision + scan_H2O + goto_start_13CH4
schemeRows += scan_CH4_high_precision + scan_13CH4
schemeRows += scan_CH4_high_precision + scan_13CH4_dn + goto_start_H2O_dn
schemeRows += scan_CH4_high_precision + scan_H2O_dn + goto_start_12CH4_dn
schemeRows += scan_CH4_high_precision + scan_12CH4_dn

$$$
