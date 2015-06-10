$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

repeat = 2

CO2 = 10
CO2_aux = 12
CH4 = 25
H2O = 28

fCO2 = 6237.4214
fCH4 = 6057.0882
fH2O = 6053.2139


cal = 4096
pztcen = 8192
ignore = 16384
fit = 32768

dtop = 0.0003

vLaser1 = 0
vLaser2 = 2
vLaser3 = 1

$$$
#######################################################################
# CO2 section
#######################################################################
fCO2-5*fsr,     5,  CO2, vLaser1
fCO2-4*fsr,     3,  CO2, vLaser1
fCO2-3*fsr,     5,  CO2, vLaser1
fCO2-2*fsr,     3,  CO2, vLaser1
fCO2-fsr,       3,  CO2, vLaser1
fCO2-2*dtop,    3,  CO2, vLaser1
fCO2-dtop,      3,  CO2, vLaser1
fCO2,           19, CO2, vLaser1
fCO2+dtop,      3,  CO2, vLaser1
fCO2+2*dtop,    3,  CO2, vLaser1
fCO2+fsr,       3,  CO2, vLaser1
fCO2+2*fsr,     3,  CO2, vLaser1
fCO2+3*fsr,     5,  CO2, vLaser1
fCO2+4*fsr,     3,  CO2, vLaser1
fCO2+5*fsr,     5,  cal | CO2, vLaser1
fCO2+4*fsr,     3,  cal | CO2, vLaser1
fCO2+3*fsr,     5,  cal | CO2, vLaser1
fCO2+2*fsr,     3,  cal | CO2, vLaser1
fCO2+fsr,       3,  cal | CO2, vLaser1
fCO2+2*dtop,    3,  CO2, vLaser1
fCO2+dtop,      3,  CO2, vLaser1
fCO2,           19, cal | CO2, vLaser1
fCO2-dtop,      3,  CO2, vLaser1
fCO2-2*dtop,    3,  CO2, vLaser1
fCO2-fsr,       3,  cal | CO2, vLaser1
fCO2-2*fsr,     3,  cal | CO2, vLaser1
fCO2-3*fsr,     5,  cal | CO2, vLaser1
fCO2-4*fsr,     3,  cal | CO2, vLaser1
fCO2-5*fsr,     5,  cal | CO2, vLaser1
fCO2-5*fsr,     1,  fit | cal | CO2, vLaser1
#######################################################################
# CH4 section
#######################################################################
fCH4-6*fsr,     3,  CH4, vLaser2
fCH4-5*fsr,     3,  CH4, vLaser2
fCH4-4*fsr,     3,  CH4, vLaser2
fCH4-3*fsr,     3,  CH4, vLaser2
fCH4-2*fsr,     3,  CH4, vLaser2
fCH4-fsr,       5,  CH4, vLaser2
fCH4,           25, CH4, vLaser2
fCH4+fsr,       5,  CH4, vLaser2
fCH4+2*fsr,     5,  CH4, vLaser2
fCH4+3*fsr,     3,  CH4, vLaser2
fCH4+4*fsr,     3,  CH4, vLaser2
fCH4+5*fsr,     3,  CH4, vLaser2
fCH4+6*fsr,     3,  CH4, vLaser2
fCH4+7*fsr,     3,  CH4, vLaser2
fCH4+8*fsr,     3,  cal | CH4, vLaser2
fCH4+7*fsr,     3,  cal | CH4, vLaser2
fCH4+6*fsr,     3,  cal | CH4, vLaser2
fCH4+5*fsr,     3,  cal | CH4, vLaser2
fCH4+4*fsr,     3,  cal | CH4, vLaser2
fCH4+3*fsr,     3,  cal | CH4, vLaser2
fCH4+2*fsr,     5,  cal | CH4, vLaser2
fCH4+fsr,       5,  cal | CH4, vLaser2
fCH4,           25, cal | CH4, vLaser2
fCH4-fsr,       5,  cal | CH4, vLaser2
fCH4-2*fsr,     3,  cal | CH4, vLaser2
fCH4-3*fsr,     3,  cal | CH4, vLaser2
fCH4-4*fsr,     3,  cal | CH4, vLaser2
fCH4-5*fsr,     3,  cal | CH4, vLaser2
fCH4-6*fsr,     3,  cal | CH4, vLaser2
fCH4-6*fsr,     1,  fit | cal | CH4, vLaser2
#######################################################################
# CO2_alt section
#######################################################################
fCO2-5*fsr,     5,  CO2_aux, vLaser1
fCO2-4*fsr,     3,  CO2_aux, vLaser1
fCO2-3*fsr,     5,  CO2_aux, vLaser1
fCO2-2*fsr,     3,  CO2_aux, vLaser1
fCO2-fsr,       3,  CO2_aux, vLaser1
fCO2-2*dtop,    3,  CO2_aux, vLaser1
fCO2-dtop,      3,  CO2_aux, vLaser1
fCO2,           19, CO2_aux, vLaser1
fCO2+dtop,      3,  CO2_aux, vLaser1
fCO2+2*dtop,    3,  CO2_aux, vLaser1
fCO2+fsr,       3,  CO2_aux, vLaser1
fCO2+2*fsr,     3,  CO2_aux, vLaser1
fCO2+3*fsr,     5,  CO2_aux, vLaser1
fCO2+4*fsr,     3,  CO2_aux, vLaser1
fCO2+5*fsr,     5,  cal | CO2_aux, vLaser1
fCO2+4*fsr,     3,  cal | CO2_aux, vLaser1
fCO2+3*fsr,     5,  cal | CO2_aux, vLaser1
fCO2+2*fsr,     3,  cal | CO2_aux, vLaser1
fCO2+fsr,       3,  cal | CO2_aux, vLaser1
fCO2+2*dtop,    3,  CO2_aux, vLaser1
fCO2+dtop,      3,  CO2_aux, vLaser1
fCO2,           19, cal | CO2_aux, vLaser1
fCO2-dtop,      3,  CO2_aux, vLaser1
fCO2-2*dtop,    3,  CO2_aux, vLaser1
fCO2-fsr,       3,  cal | CO2_aux, vLaser1
fCO2-2*fsr,     3,  cal | CO2_aux, vLaser1
fCO2-3*fsr,     5,  cal | CO2_aux, vLaser1
fCO2-4*fsr,     3,  cal | CO2_aux, vLaser1
fCO2-5*fsr,     5,  cal | CO2_aux, vLaser1
fCO2-5*fsr,     1,  fit | cal | CO2_aux, vLaser1
#######################################################################
# H2O section
#######################################################################
fH2O+6*fsr,     2,  cal | H2O, vLaser3
fH2O+5*fsr,     2,  cal | H2O, vLaser3
fH2O+4*fsr,     2,  cal | H2O, vLaser3
fH2O+3*fsr,     2,  cal | H2O, vLaser3
fH2O+2*fsr,     2,  cal | H2O, vLaser3
fH2O+fsr,       2,  cal | H2O, vLaser3
fH2O,           10,  cal | H2O, vLaser3
fH2O-fsr,       2,  cal | H2O, vLaser3
fH2O-2*fsr,     2,  cal | H2O, vLaser3
fH2O-3*fsr,     2,  cal | H2O, vLaser3
fH2O-4*fsr,     2,  cal | H2O, vLaser3
fH2O-5*fsr,     2,  cal | H2O, vLaser3
fH2O-6*fsr,     2,  cal | H2O, vLaser3
fH2O-5*fsr,     2,  cal | H2O, vLaser3
fH2O-4*fsr,     2,  cal | H2O, vLaser3
fH2O-3*fsr,     2,  cal | H2O, vLaser3
fH2O-2*fsr,     2,  cal | H2O, vLaser3
fH2O-fsr,       2,  cal | H2O, vLaser3
fH2O,           10,  cal | H2O, vLaser3
fH2O+fsr,       2,  cal | H2O, vLaser3
fH2O+2*fsr,     2,  cal | H2O, vLaser3
fH2O+3*fsr,     2,  cal | H2O, vLaser3
fH2O+4*fsr,     2,  cal | H2O, vLaser3
fH2O+5*fsr,     2,  cal | H2O, vLaser3
fH2O+6*fsr,     1,  cal | H2O, vLaser3
fH2O+6*fsr,     1,  fit | cal | H2O, vLaser3
#######################################################################

