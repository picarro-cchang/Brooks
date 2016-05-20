$$$
schemeVersion = 4
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
fCH4 = 6056.82000
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
CO2TH = float(cfg['AUTOCAL']['CO2TH'])
CH4TH = float(cfg['AUTOCAL']['CH4TH'])
COTH = float(cfg['AUTOCAL']['COTH'])
H2OTH = float(cfg['AUTOCAL']['H2OTH'])
$$$
#######################################################################
# CO2 section
#######################################################################
fCO2-5*fsr,     5,  CO2, vLaser1, threshold = CO2TH
fCO2-4*fsr,     4,  CO2, vLaser1, threshold = CO2TH
fCO2-3*fsr,     5,  CO2, vLaser1, threshold = CO2TH
fCO2-2*fsr,     3,  CO2, vLaser1, threshold = CO2TH
fCO2-fsr,       3,  CO2, vLaser1, threshold = CO2TH
fCO2-2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2-dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2,           19, CO2, vLaser1, threshold = CO2TH
fCO2+dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2+2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2+fsr,       3,  CO2, vLaser1, threshold = CO2TH
fCO2+2*fsr,     3,  CO2, vLaser1, threshold = CO2TH
fCO2+3*fsr,     5,  CO2, vLaser1, threshold = CO2TH
fCO2+4*fsr,     3,  CO2, vLaser1, threshold = CO2TH
fCO2+5*fsr,     5,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+4*fsr,     3,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+3*fsr,     5,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+2*fsr,     3,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+fsr,       3,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2+2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2+dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2,           19, cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-dtop,      3,  CO2, vLaser1, threshold = CO2TH
fCO2-2*dtop,    3,  CO2, vLaser1, threshold = CO2TH
fCO2-fsr,       3,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-2*fsr,     3,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-3*fsr,     5,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-4*fsr,     3,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-5*fsr,     4,  cal | pztcen | CO2, vLaser1, threshold = CO2TH
fCO2-5*fsr,     1,  fit | cal | pztcen | CO2, vLaser1, threshold = CO2TH
#######################################################################
# CH4 section
#######################################################################
fCH4+3*fsr,     4,  CH4, vLaser2, threshold = CH4TH
fCH4+2*fsr,     4,  CH4, vLaser2, threshold = CH4TH
fCH4+fsr,       6,  CH4, vLaser2, threshold = CH4TH
fCH4,           35, CH4, vLaser2, threshold = CH4TH
fCH4-fsr,       6,  CH4, vLaser2, threshold = CH4TH
fCH4-2*fsr,     4,  CH4, vLaser2, threshold = CH4TH
fCH4-3*fsr,     4,  CH4, vLaser2, threshold = CH4TH
fCH4-4*fsr,     4,  CH4, vLaser2, threshold = CH4TH
fCH4-4*fsr,     4,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-3*fsr,     4,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-2*fsr,     4,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4-fsr,       6,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4,           35, cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+fsr,       6,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+2*fsr,     4,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+3*fsr,     4,  cal | pztcen | CH4, vLaser2, threshold = CH4TH
fCH4+3*fsr,     1,  fit | cal | pztcen | CH4, vLaser2, threshold = CH4TH
#######################################################################
# Zero-dwell step towards H2O
#######################################################################
fH2O-5*fsr,     0,  ignore | H2O, vLaser4, threshold = H2OTH
#######################################################################
# CO section
#######################################################################
fCO-2*fsr5,     15, CO, vLaser5, threshold = COTH
fCO-fsr5,        1, CO, vLaser5, threshold = COTH
fCO,            30, CO, vLaser5, threshold = COTH
fCO+fsr5,        1, CO, vLaser5, threshold = COTH
fCO+2*fsr5,     15, CO, vLaser5, threshold = COTH
#
fCO+2*fsr5,     15, CO, vLaser5, threshold = COTH
fCO+fsr5,        1, CO, vLaser5, threshold = COTH
fCO,            30, CO, vLaser5, threshold = COTH
fCO-fsr5,        1, CO, vLaser5, threshold = COTH
fCO-2*fsr5,     15, CO, vLaser5, threshold = COTH
#
fCO-2*fsr5,     15, CO, vLaser5, threshold = COTH
fCO-fsr5,        1, CO, vLaser5, threshold = COTH
fCO,            30, CO, vLaser5, threshold = COTH
fCO+fsr5,        1, CO, vLaser5, threshold = COTH
fCO+2*fsr5,     15, CO, vLaser5, threshold = COTH
#
fCO+2*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+5*fsr5,      4, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+6*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+7*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+8*fsr5,      4, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+7*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+6*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+5*fsr5,      4, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+4*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+3*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+2*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO+fsr5,        3, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO,            10, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-fsr5,        2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-5*fsr5,      4, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-6*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-7*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-8*fsr5,      4, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-7*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-6*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-5*fsr5,      4, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-4*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-3*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      2, cal | pztcen | pztcen | CO, vLaser5, threshold = COTH
#
fCO-2*fsr5,     15, CO, vLaser5, threshold = COTH
fCO-fsr5,        1, CO, vLaser5, threshold = COTH
fCO,            30, CO, vLaser5, threshold = COTH
fCO+fsr5,        1, CO, vLaser5, threshold = COTH
fCO+2*fsr5,     15, CO, vLaser5, threshold = COTH
#
fCO+2*fsr5,     15, CO, vLaser5, threshold = COTH
fCO+fsr5,        1, CO, vLaser5, threshold = COTH
fCO,            30, CO, vLaser5, threshold = COTH
fCO-fsr5,        1, CO, vLaser5, threshold = COTH
fCO-2*fsr5,     15, CO, vLaser5, threshold = COTH
#
fCO-2*fsr5,     15, CO, vLaser5, threshold = COTH
fCO-fsr5,        1, CO, vLaser5, threshold = COTH
fCO,            30, CO, vLaser5, threshold = COTH
fCO+fsr5,        1, CO, vLaser5, threshold = COTH
fCO+2*fsr5,     14, CO, vLaser5, threshold = COTH
#
fCO+2*fsr5,      1, fit | CO, vLaser5, threshold = COTH
fCO-2*fsr5,      0, ignore | CO, vLaser5, threshold = COTH
#######################################################################
# H2O section
#######################################################################
fH2O-5*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O-4*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O-3*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O-2*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O-fsr,       2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O,           5,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O+fsr,       2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O+2*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O+3*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O+4*fsr,     2,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O+5*fsr,     1,  cal | pztcen | H2O, vLaser4, threshold = H2OTH
fH2O+5*fsr,     1,  fit | cal | pztcen | H2O, vLaser4, threshold = H2OTH
#######################################################################
# Zero-dwell step towards CH4
#######################################################################
fCH4+3*fsr,     0,  ignore | CH4, vLaser2, threshold = CH4TH