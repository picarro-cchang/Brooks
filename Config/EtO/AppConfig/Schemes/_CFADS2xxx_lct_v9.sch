$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 5
fCO2 = 6237.408
fCO2aux = 6058.19255
CO2 = 10
CO2_aux = 12
# fCH4 = 6057.090   # for spline
fCH4 = 6057.0863   # for Galatry
CH4 = 25
fH2O = 6057.800
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
    
#  Version 9 of the LCT scheme for CFADS is designed to eliminate pzt creep by referencing all frequencies to 6237.4 CO2

Na = round(-179.62761/fsr)     # These are physical frequency differences from Hitran 2016 corrected for 140 Torr air shift
Nb = round(-180.33418/fsr)

Picarro_offset_a = 0.01961     # Offset of Picarro spectral library (WLM setpoints) from Hitran
Picarro_offset_b = 0.01403

#######################################################################
# CO2 section
#######################################################################
CO2_up = makeScan(fCO2,fsr,[(-5,2),(-4,2),(-3,2),(-2,14),(-1,6),(0,45),(1,6),(2,14),(3,2),(4,2),(5,2)],CO2,vLaser1)
CO2_dn = makeScan(fCO2,fsr,[(5,2),(4,2),(3,2),(2,14),(1,6),(0,45),(-1,6),(-2,14),(-3,2),(-4,2),(-5,1),(-5,1)],CO2|cal,vLaser1)
CO2_dn[-1].subschemeId |= fit

#######################################################################
# H2O section relative to 6237 line
#######################################################################
H2O_up = makeScan(fCO2+Na*fsr+Picarro_offset_a,fsr,[(-5,4),(-4,4),(-3,4),(-2,4),(-1,4),(0,4),(1,4),(2,4),(3,4),(4,4),(5,4)],H2O,vLaser4)
H2O_dn = makeScan(fCO2+Na*fsr+Picarro_offset_a,fsr,[(5,4),(4,4),(3,4),(2,4),(1,4),(0,4),(-1,4),(-2,4),(-3,4),(-4,4),(-5,3),(-5,1)],H2O|cal,vLaser4)
H2O_dn[-1].subschemeId |= fit
H2O_dn.append(Row(fCO2+(Nb+5)*fsr+Picarro_offset_b,0,CH4|ignore,vLaser2))

#######################################################################
# Auxiliary CO2 section
#######################################################################
CO2aux_up = makeScan(fCO2,fsr,[(-5,2),(-4,2),(-3,2),(-2,14),(-1,6),(0,45),(1,6),(2,14),(3,2),(4,2),(5,2)],CO2_aux,vLaser1)
CO2aux_dn = makeScan(fCO2,fsr,[(5,2),(4,2),(3,2),(2,14),(1,6),(0,45),(-1,6),(-2,14),(-3,2),(-4,2),(-5,1),(-5,1)],CO2_aux|cal,vLaser1)
CO2aux_dn[-1].subschemeId |= fit

#######################################################################
# CH4 section
#######################################################################
CH4_up = makeScan(fCO2+Nb*fsr+Picarro_offset_b,fsr,[(-5,7),(-4,2),(-3,2),(-2,21),(-1,2),(0,37),(1,32),(2,2),(3,2),(4,2),(5,6),(5,1)],CH4,vLaser2)
CH4_dn = makeScan(fCO2+Nb*fsr+Picarro_offset_b,fsr,[(5,7),(4,2),(3,2),(2,2),(1,32),(0,37),(-1,2),(-2,21),(-3,2),(-4,2),(-5,6),(-5,1)],CH4|cal,vLaser2)
CH4_up[-1].subschemeId |= fit
CH4_up.append(Row(fCO2+(Na-5)*fsr+Picarro_offset_a,0,H2O|ignore,vLaser4))

schemeRows = H2O_up + H2O_dn + CO2_up + CO2_dn + CH4_dn + CH4_up + CO2_up + CO2_dn
$$$