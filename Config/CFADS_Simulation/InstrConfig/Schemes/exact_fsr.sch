$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR']) * 0.97
cal = 4096 | 8192
ignore = 16384
fit = 32768
repeat = 5
fCO2 = 6237.408
CO2 = 10
vLaser1 = 0
$$$
#######################################################################
# CO2 section
#######################################################################
fCO2-5*fsr,     5,  cal | CO2, vLaser1
fCO2-4*fsr,     5,  cal | CO2, vLaser1
fCO2-3*fsr,     5,  cal | CO2, vLaser1
fCO2-2*fsr,     5,  cal | CO2, vLaser1
fCO2-1*fsr,     5,  cal | CO2, vLaser1
fCO2-0*fsr,     50,  cal | CO2, vLaser1
fCO2+1*fsr,     5,  cal | CO2, vLaser1
fCO2+2*fsr,     5,  cal | CO2, vLaser1
fCO2+3*fsr,     5,  cal | CO2, vLaser1
fCO2+4*fsr,     5,  cal | CO2, vLaser1
fCO2+5*fsr,     4,  cal | CO2, vLaser1
fCO2+5*fsr,     1,  fit | CO2, vLaser1
