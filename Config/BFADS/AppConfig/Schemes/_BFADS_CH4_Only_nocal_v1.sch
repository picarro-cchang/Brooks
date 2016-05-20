$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 5
fCO2 = 6237.408
CO2 = 10
CO2_aux = 12
fCH4 = 6057.090
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
$$$
#######################################################################
# CH4 section
#######################################################################
fCH4-6*fsr,     2,  pztcen | CH4, vLaser2
fCH4-5*fsr,     2,  pztcen | CH4, vLaser2
fCH4-4*fsr,     2,  pztcen | CH4, vLaser2
fCH4-3*fsr,     2,  pztcen | CH4, vLaser2
fCH4-2*fsr,     2,  pztcen | CH4, vLaser2
fCH4-fsr,       3,  pztcen | CH4, vLaser2
fCH4,           20, pztcen | CH4, vLaser2
fCH4+fsr,       3,  pztcen | CH4, vLaser2
fCH4+2*fsr,     2,  pztcen | CH4, vLaser2
fCH4+3*fsr,     2,  pztcen | CH4, vLaser2
fCH4+4*fsr,     2,  pztcen | CH4, vLaser2
fCH4+5*fsr,     2,  pztcen | CH4, vLaser2
fCH4+6*fsr,     2,  pztcen | CH4, vLaser2
fCH4+7*fsr,     2,  pztcen | CH4, vLaser2
fCH4+8*fsr,     2,  pztcen | CH4, vLaser2
fCH4+7*fsr,     2,  pztcen | CH4, vLaser2
fCH4+6*fsr,     2,  pztcen | CH4, vLaser2
fCH4+5*fsr,     2,  pztcen | CH4, vLaser2
fCH4+4*fsr,     2,  pztcen | CH4, vLaser2
fCH4+3*fsr,     2,  pztcen | CH4, vLaser2
fCH4+2*fsr,     2,  pztcen | CH4, vLaser2
fCH4+fsr,       3,  pztcen | CH4, vLaser2
fCH4,           20, pztcen | CH4, vLaser2
fCH4-fsr,       3,  pztcen | CH4, vLaser2
fCH4-2*fsr,     2,  pztcen | CH4, vLaser2
fCH4-3*fsr,     2,  pztcen | CH4, vLaser2
fCH4-4*fsr,     2,  pztcen | CH4, vLaser2
fCH4-5*fsr,     2,  pztcen | CH4, vLaser2
fCH4-6*fsr,     1,  pztcen | CH4, vLaser2
fCH4-6*fsr,     1,  fit | pztcen | CH4, vLaser2
#######################################################################
