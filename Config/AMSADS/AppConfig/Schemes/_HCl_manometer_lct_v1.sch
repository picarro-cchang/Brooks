$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

repeat = 5
fH2O = 5732.47312
H2O = 63

cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4
vLaser6 = 5
vLaser7 = 6
vLaser8 = 7
vLaser = vLaser3

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result
    
#  Version 1 of a scheme for spectroscopic pressure measurement with SADS, using width of strong water line in dried air

#######################################################################
# H2O section
#######################################################################
H2O_up = makeScan(fH2O,fsr,[(-10,2),(-9,2),(-8,2),(-7,2),(-6,2),(-5,2),(-4,2),(-3,2),(-2,14),(-1,6),(0,45),(1,6),(2,14),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),(9,2),(10,2)],H2O,vLaser)
H2O_dn = makeScan(fH2O,fsr,[(10,2),(9,2),(8,2),(7,2),(6,2),(5,2),(4,2),(3,2),(2,14),(1,6),(0,45),(-1,6),(-2,14),(-3,2),(-4,2),(-5,2),(-6,2),(-7,2),(-8,2),(-9,2),(-10,1),(-10,1)],H2O|cal,vLaser)
H2O_dn[-1].subschemeId |= fit

schemeRows = H2O_up + H2O_dn
$$$
