$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
fsr5  = float(cfg["AUTOCAL"]["CAVITY_FSR_CO_Fixed"])
ignore = 16384
repeat = 2
fCO = 6380.32270
CO = 145
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
vLaser5 = 4
CO2TH = 12000
CH4TH = 16000
COTH = 14000
$$$
#######################################################################
# CO2 section
#######################################################################
fCO2-5*fsr,     5,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-4*fsr,     4,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-3*fsr,     5,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-2*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-fsr,       3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2-dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2,           19, pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2+2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2+fsr,       3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+2*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+3*fsr,     5,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+4*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+5*fsr,     5,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+4*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+3*fsr,     5,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+2*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+fsr,       3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2+dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2,           19, pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2-2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2-fsr,       3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-2*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-3*fsr,     5,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-4*fsr,     3,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-5*fsr,     4,  pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-5*fsr,     1,  fit | pztcen | CO2, vLaser1, threshold = CO2TH
#######################################################################
# CH4 section
#######################################################################
fCH4+8*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+7*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+6*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+5*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+4*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+3*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+2*fsr,     5,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+fsr,       5,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4,           25, pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-fsr,       5,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-2*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-3*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-4*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-5*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-6*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-5*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-4*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-3*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-2*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-fsr,       5,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4,           25, pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+fsr,       5,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+2*fsr,     5,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+3*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+4*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+5*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+6*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+7*fsr,     3,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+8*fsr,     2,  pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+8*fsr,     1,  fit | pztcen | CH4, vLaser2, threshold = CH4TH
#######################################################################
# Zero-dwell step towards H2O
#######################################################################
fH2O-5*fsr,     0,  ignore | H2O, vLaser4, threshold = CH4TH
#######################################################################
# CO section
#######################################################################
fCO,           40, CO, vLaser5, threshold = COTH
fCO+fsr5,        3, CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, CO, vLaser5, threshold = COTH
fCO+3*fsr5,      2, CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, CO, vLaser5, threshold = COTH
fCO+5*fsr5,      4, CO, vLaser5, threshold = COTH
fCO+6*fsr5,      2, CO, vLaser5, threshold = COTH
fCO+7*fsr5,      2, CO, vLaser5, threshold = COTH
fCO+8*fsr5,      4, pztcen | CO, vLaser5, threshold = COTH
fCO+7*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+6*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+5*fsr5,      4, pztcen | CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        2, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-5*fsr5,      4, pztcen | CO, vLaser5, threshold = COTH
fCO-6*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-7*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-8*fsr5,      4, pztcen | CO, vLaser5, threshold = COTH
fCO-7*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-6*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-5*fsr5,      4, pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
#
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
#
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
#
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO,           40, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      1, pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        3, pztcen | CO, vLaser5, threshold = COTH
#
fCO,           39, pztcen | CO, vLaser5, threshold = COTH
fCO,            1, fit | CO, vLaser5, threshold = COTH
#######################################################################
# H2O section
#######################################################################
fH2O-5*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O-4*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O-3*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O-2*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O-fsr,       2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O,           5,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O+fsr,       2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O+2*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O+3*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O+4*fsr,     2,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O+5*fsr,     1,  pztcen | H2O, vLaser4, threshold = CH4TH
fH2O+6*fsr,     1,  fit | pztcen | H2O, vLaser4, threshold = CH4TH
#######################################################################
# Zero-dwell step towards CH4
#######################################################################
fCH4+8*fsr,     0,  ignore | CH4, vLaser2, threshold = CH4TH
