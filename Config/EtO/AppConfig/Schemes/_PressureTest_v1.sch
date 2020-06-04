$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal_lct.ini')
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
    
#  Branched from CFADS LCT Version 8 scheme for spectroscopic pressure, removing short wavelength piece

#######################################################################
# H2O section   
#######################################################################
H2O_up = makeScan(fH2O,fsr,[(-5,2),(-4,2),(-3,2),(-2,2),(-1,2),(0,2),(1,2),(2,2),(3,2),(4,2),(5,1),(5,1)],H2O,vLaser1)
H2O_dn = makeScan(fH2O,fsr,[(5,2),(4,2),(3,2),(2,2),(1,2),(0,2),(-1,2),(-2,2),(-3,2),(-4,2),(-5,1),(-5,1)],H2O,vLaser1)
H2O_up[-1].subschemeId |= fit

#######################################################################
# Auxiliary CO2 section
#######################################################################
CO2aux_up = makeScan(fCO2aux,fsr,[(-5,2),(-4,2),(-3,2),(-2,14),(-1,6),(0,45),(1,6),(2,14),(3,2),(4,2),(5,2),(6,4),(7,4),(8,2),(9,2),(10,4)],CO2_aux,vLaser1)
CO2aux_dn = makeScan(fCO2aux,fsr,[(10,4),(9,2),(8,2),(7,4),(6,4),(5,2),(4,2),(3,2),(2,14),(1,6),(0,45),(-1,6),(-2,14),(-3,2),(-4,2),(-5,1),(-5,1)],CO2_aux,vLaser1)
CO2aux_dn[-1].subschemeId |= fit

schemeRows = H2O_dn + H2O_up + CO2aux_up + CO2aux_dn

# Following line tests if we can pass arbitrary 'schemeInfo' dictionary to the fitter
schemeInfo = {'name': 'Pressure Test v1'}
$$$