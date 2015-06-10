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
# CO2 section
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
