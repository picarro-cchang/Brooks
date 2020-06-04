$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 5
fCO2 = 6058.19127
CO2 = 12
H2O = 11
cal = 4096
pztcen = 8192
fit = 32768
dtop = 0.0003
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
    
#  Version 1 of a scheme for spectroscopic pressure measurement using widely tunable laser.  "Cal" flag turned off.

Nb = round(-0.39840/fsr)      # Physical frequency difference from Hitran 2016 corrected for 140 Torr air shift


#######################################################################
# CO2 section, 30014 P22 line at 6058.2 wvn
#######################################################################
CO2_up = makeScan(fCO2,fsr,[(-5,2),(-4,2),(-3,2),(-2,14),(-1,6),(0,45),(1,6),(2,14),(3,2),(4,2),(5,2),(6,4),(7,4),(8,2),(9,2),(10,4)],CO2,vLaser1)
CO2_dn = makeScan(fCO2,fsr,[(10,4),(9,2),(8,2),(7,4),(6,4),(5,2),(4,2),(3,2),(2,14),(1,6),(0,45),(-1,6),(-2,14),(-3,2),(-4,2),(-5,1),(-5,1)],CO2,vLaser1)
#CO2aux_dn[-1].subschemeId |= fit  no longer necessary with single, agile laser

#######################################################################
# H2O section relative to 6058 line
#######################################################################
H2Ob_up = makeScan(fCO2+Nb*fsr,fsr,[(-5,4),(-4,4),(-3,4),(-2,4),(-1,4),(0,4),(1,4),(2,4),(3,4),(4,4),(5,3),(5,1)],CO2,vLaser1)
H2Ob_dn = makeScan(fCO2+Nb*fsr,fsr,[(5,4),(4,4),(3,4),(2,4),(1,4),(0,4),(-1,4),(-2,4),(-3,4),(-4,4),(-5,4)],CO2,vLaser1)
H2Ob_up[-1].subschemeId |= fit

schemeRows = CO2_up + CO2_dn + H2Ob_dn + H2Ob_up
$$$