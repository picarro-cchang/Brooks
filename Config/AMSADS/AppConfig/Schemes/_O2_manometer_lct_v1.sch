$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 5
fO2 = 7822.9838
O2 = 62
cal = 4096
pztcen = 8192
fit = 32768

vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4
vLaser6 = 5
vLaser7 = 6
vLaser8 = 7

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result
    
#  Version 1 of a scheme specifically for spectroscopic pressure measurement using MADS O2 line width in dried air

#######################################################################
# O2 section
#######################################################################
O2_up = makeScan(fO2,fsr,[(-5,2),(-4,2),(-3,2),(-2,14),(-1,6),(0,45),(1,6),(2,14),(3,2),(4,2),(5,2)],O2,vLaser1)
O2_dn = makeScan(fO2,fsr,[(5,2),(4,2),(3,2),(2,14),(1,6),(0,45),(-1,6),(-2,14),(-3,2),(-4,2),(-5,1),(-5,1)],O2|cal,vLaser1)
O2_dn[-1].subschemeId |= fit

schemeRows = O2_up + O2_dn
$$$