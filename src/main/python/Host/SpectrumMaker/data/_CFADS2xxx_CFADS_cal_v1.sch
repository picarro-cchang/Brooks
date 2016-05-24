$$$
schemeVersion = 1
cfg = getConfig('Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 2
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
# CO2 section
#######################################################################
fCO2-5*fsr,     6,  CO2, vLaser1
fCO2-4*fsr,     4,  CO2, vLaser1
fCO2-3*fsr,     6,  CO2, vLaser1
fCO2-2*fsr,     4,  CO2, vLaser1
fCO2-fsr,       4,  CO2, vLaser1
fCO2-2*dtop,    4,  CO2, vLaser1
fCO2-dtop,      4,  CO2, vLaser1
fCO2,           29, CO2, vLaser1
fCO2+dtop,      4,  CO2, vLaser1
fCO2+2*dtop,    4,  CO2, vLaser1
fCO2+fsr,       4,  CO2, vLaser1
fCO2+2*fsr,     4,  CO2, vLaser1
fCO2+3*fsr,     6,  CO2, vLaser1
fCO2+4*fsr,     4,  CO2, vLaser1
fCO2+5*fsr,     6,  cal | CO2, vLaser1
fCO2+4*fsr,     4,  cal | CO2, vLaser1
fCO2+3*fsr,     6,  cal | CO2, vLaser1
fCO2+2*fsr,     4,  cal | CO2, vLaser1
fCO2+fsr,       4,  cal | CO2, vLaser1
fCO2+2*dtop,    4,  CO2, vLaser1
fCO2+dtop,      4,  CO2, vLaser1
fCO2,           29, cal | CO2, vLaser1
fCO2-dtop,      4,  CO2, vLaser1
fCO2-2*dtop,    4,  CO2, vLaser1
fCO2-fsr,       4,  cal | CO2, vLaser1
fCO2-2*fsr,     4,  cal | CO2, vLaser1
fCO2-3*fsr,     6,  cal | CO2, vLaser1
fCO2-4*fsr,     4,  cal | CO2, vLaser1
fCO2-5*fsr,     6,  cal | CO2, vLaser1
fCO2-5*fsr,     1,  fit | cal | CO2, vLaser1
#######################################################################
# CH4 section
#######################################################################
fCH4-6*fsr,     4,  CH4, vLaser2
fCH4-5*fsr,     4,  CH4, vLaser2
fCH4-4*fsr,     4,  CH4, vLaser2
fCH4-3*fsr,     4,  CH4, vLaser2
fCH4-2*fsr,     4,  CH4, vLaser2
fCH4-fsr,       6,  CH4, vLaser2
fCH4,           35, CH4, vLaser2
fCH4+fsr,       6,  CH4, vLaser2
fCH4+2*fsr,     4,  CH4, vLaser2
fCH4+3*fsr,     4,  CH4, vLaser2
fCH4+4*fsr,     4,  CH4, vLaser2
fCH4+5*fsr,     4,  CH4, vLaser2
fCH4+6*fsr,     4,  CH4, vLaser2
fCH4+7*fsr,     4,  CH4, vLaser2
fCH4+8*fsr,     4,  cal | CH4, vLaser2
fCH4+7*fsr,     4,  cal | CH4, vLaser2
fCH4+6*fsr,     4,  cal | CH4, vLaser2
fCH4+5*fsr,     4,  cal | CH4, vLaser2
fCH4+4*fsr,     4,  cal | CH4, vLaser2
fCH4+3*fsr,     4,  cal | CH4, vLaser2
fCH4+2*fsr,     6,  cal | CH4, vLaser2
fCH4+fsr,       6,  cal | CH4, vLaser2
fCH4,           35, cal | CH4, vLaser2
fCH4-fsr,       6,  cal | CH4, vLaser2
fCH4-2*fsr,     4,  cal | CH4, vLaser2
fCH4-3*fsr,     4,  cal | CH4, vLaser2
fCH4-4*fsr,     4,  cal | CH4, vLaser2
fCH4-5*fsr,     4,  cal | CH4, vLaser2
fCH4-6*fsr,     4,  cal | CH4, vLaser2
fCH4-6*fsr,     1,  fit | cal | CH4, vLaser2
#######################################################################
# Zero-dwell step towards H2O
#######################################################################
fH2O+5*fsr,     0,  ignore | H2O, vLaser4
#######################################################################
# CO2 section
#######################################################################
fCO2-5*fsr,     6,  CO2_aux, vLaser1
fCO2-4*fsr,     4,  CO2_aux, vLaser1
fCO2-3*fsr,     6,  CO2_aux, vLaser1
fCO2-2*fsr,     4,  CO2_aux, vLaser1
fCO2-fsr,       4,  CO2_aux, vLaser1
fCO2-2*dtop,    4,  CO2_aux, vLaser1
fCO2-dtop,      4,  CO2_aux, vLaser1
fCO2,           29, CO2_aux, vLaser1
fCO2+dtop,      4,  CO2_aux, vLaser1
fCO2+2*dtop,    4,  CO2_aux, vLaser1
fCO2+fsr,       4,  CO2_aux, vLaser1
fCO2+2*fsr,     4,  CO2_aux, vLaser1
fCO2+3*fsr,     6,  CO2_aux, vLaser1
fCO2+4*fsr,     4,  CO2_aux, vLaser1
fCO2+5*fsr,     6,  cal | CO2_aux, vLaser1
fCO2+4*fsr,     4,  cal | CO2_aux, vLaser1
fCO2+3*fsr,     6,  cal | CO2_aux, vLaser1
fCO2+2*fsr,     4,  cal | CO2_aux, vLaser1
fCO2+fsr,       4,  cal | CO2_aux, vLaser1
fCO2+2*dtop,    4,  CO2_aux, vLaser1
fCO2+dtop,      4,  CO2_aux, vLaser1
fCO2,           29, cal | CO2_aux, vLaser1
fCO2-dtop,      4,  CO2_aux, vLaser1
fCO2-2*dtop,    4,  CO2_aux, vLaser1
fCO2-fsr,       4,  cal | CO2_aux, vLaser1
fCO2-2*fsr,     4,  cal | CO2_aux, vLaser1
fCO2-3*fsr,     6,  cal | CO2_aux, vLaser1
fCO2-4*fsr,     4,  cal | CO2_aux, vLaser1
fCO2-5*fsr,     4,  cal | CO2_aux, vLaser1
fCO2-5*fsr,     1,  fit | cal | CO2_aux, vLaser1
#######################################################################
# H2O section
#######################################################################
fH2O+5*fsr,     2,  cal | H2O, vLaser4
fH2O+4*fsr,     2,  cal | H2O, vLaser4
fH2O+3*fsr,     2,  cal | H2O, vLaser4
fH2O+2*fsr,     2,  cal | H2O, vLaser4
fH2O+fsr,       2,  cal | H2O, vLaser4
fH2O,           5,  cal | H2O, vLaser4
fH2O-fsr,       2,  cal | H2O, vLaser4
fH2O-2*fsr,     2,  cal | H2O, vLaser4
fH2O-3*fsr,     2,  cal | H2O, vLaser4
fH2O-4*fsr,     2,  cal | H2O, vLaser4
fH2O-5*fsr,     2,  cal | H2O, vLaser4
fH2O-5*fsr,     1,  fit | cal | H2O, vLaser4
#######################################################################
# Zero-dwell step towards CH4
#######################################################################
fCH4-6*fsr,     0,  ignore | CH4, vLaser2
