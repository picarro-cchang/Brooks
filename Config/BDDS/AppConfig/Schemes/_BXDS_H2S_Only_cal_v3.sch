$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 2
fH2S = 6351.0
H2S = 125
H2S_aux = 126
fCH4 = 6057.090
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
$$$
#  Version 1 is the first translation from G1000 series
#  Version 2 add baseline points for better balance without baseline averaging
#  Version 3 removes superfluous spectrum id 126
#######################################################################
# H2S section
#######################################################################
fH2S-5*fsr,     2,  H2S, vLaser1
fH2S-4*fsr,     2,  H2S, vLaser1
fH2S-3*fsr,     6,  H2S, vLaser1
fH2S-2*fsr,     2,  H2S, vLaser1
fH2S-fsr,       4,  H2S, vLaser1
fH2S,           20, H2S, vLaser1
fH2S+fsr,       4,  H2S, vLaser1
fH2S+2*fsr,     2,  H2S, vLaser1
fH2S+3*fsr,     6,  H2S, vLaser1
fH2S+4*fsr,     2,  H2S, vLaser1
fH2S+5*fsr,     2,  H2S, vLaser1
fH2S+6*fsr,     2,  H2S, vLaser1
fH2S+7*fsr,     2,  H2S, vLaser1
fH2S+8*fsr,     2,  H2S, vLaser1
fH2S+9*fsr,     4,  H2S, vLaser1
fH2S+10*fsr,    4,  H2S, vLaser1
fH2S+11*fsr,    4,  H2S, vLaser1
fH2S+12*fsr,    5,  H2S, vLaser1
fH2S+13*fsr,    5,  H2S, vLaser1
fH2S+14*fsr,    5,  H2S, vLaser1
fH2S+15*fsr,    5,  H2S, vLaser1
fH2S+16*fsr,    5,  H2S, vLaser1
fH2S+17*fsr,    5,  H2S, vLaser1
fH2S+18*fsr,    10, H2S, vLaser1
fH2S+19*fsr,    5,  H2S, vLaser1
fH2S+20*fsr,    4,  cal | H2S, vLaser1
fH2S+19*fsr,    5,  cal | H2S, vLaser1
fH2S+18*fsr,    10, cal | H2S, vLaser1
fH2S+17*fsr,    5,  cal | H2S, vLaser1
fH2S+16*fsr,    5,  cal | H2S, vLaser1
fH2S+15*fsr,    5,  cal | H2S, vLaser1
fH2S+14*fsr,    5,  cal | H2S, vLaser1
fH2S+13*fsr,    5,  cal | H2S, vLaser1
fH2S+12*fsr,    5,  cal | H2S, vLaser1
fH2S+11*fsr,    4,  cal | H2S, vLaser1
fH2S+10*fsr,    4,  cal | H2S, vLaser1
fH2S+9*fsr,     4,  cal | H2S, vLaser1
fH2S+8*fsr,     2,  cal | H2S, vLaser1
fH2S+7*fsr,     2,  cal | H2S, vLaser1
fH2S+6*fsr,     2,  cal | H2S, vLaser1
fH2S+5*fsr,     2,  cal | H2S, vLaser1
fH2S+4*fsr,     2,  cal | H2S, vLaser1
fH2S+3*fsr,     6,  cal | H2S, vLaser1
fH2S+2*fsr,     2,  cal | H2S, vLaser1
fH2S+1*fsr,     4,  cal | H2S, vLaser1
fH2S,           20, cal | H2S, vLaser1
fH2S-1*fsr,     4,  cal | H2S, vLaser1
fH2S-2*fsr,     2,  cal | H2S, vLaser1
fH2S-3*fsr,     6,  cal | H2S, vLaser1
fH2S-4*fsr,     2,  cal | H2S, vLaser1
fH2S-5*fsr,     1,  cal | H2S, vLaser1
fH2S-5*fsr,     1,  cal | H2S, vLaser1
#######################################################################
# was called H2S_aux section
#######################################################################
fH2S-5*fsr,     2,  H2S, vLaser1
fH2S-4*fsr,     2,  H2S, vLaser1
fH2S-3*fsr,     6,  H2S, vLaser1
fH2S-2*fsr,     2,  H2S, vLaser1
fH2S-fsr,       4,  H2S, vLaser1
fH2S,           20, H2S, vLaser1
fH2S+fsr,       4,  H2S, vLaser1
fH2S+2*fsr,     2,  H2S, vLaser1
fH2S+3*fsr,     6,  H2S, vLaser1
fH2S+4*fsr,     2,  H2S, vLaser1
fH2S+5*fsr,     2,  H2S, vLaser1
fH2S+6*fsr,     2,  H2S, vLaser1
fH2S+7*fsr,     2,  H2S, vLaser1
fH2S+8*fsr,     2,  H2S, vLaser1
fH2S+9*fsr,     4,  H2S, vLaser1
fH2S+10*fsr,    4,  H2S, vLaser1
fH2S+11*fsr,    4,  H2S, vLaser1
fH2S+12*fsr,    5,  H2S, vLaser1
fH2S+13*fsr,    5,  H2S, vLaser1
fH2S+14*fsr,    5,  H2S, vLaser1
fH2S+15*fsr,    5,  H2S, vLaser1
fH2S+16*fsr,    5,  H2S, vLaser1
fH2S+17*fsr,    5,  H2S, vLaser1
fH2S+18*fsr,    10, H2S, vLaser1
fH2S+19*fsr,    5,  H2S, vLaser1
fH2S+20*fsr,    4,  cal | H2S, vLaser1
fH2S+19*fsr,    5,  cal | H2S, vLaser1
fH2S+18*fsr,    10, cal | H2S, vLaser1
fH2S+17*fsr,    5,  cal | H2S, vLaser1
fH2S+16*fsr,    5,  cal | H2S, vLaser1
fH2S+15*fsr,    5,  cal | H2S, vLaser1
fH2S+14*fsr,    5,  cal | H2S, vLaser1
fH2S+13*fsr,    5,  cal | H2S, vLaser1
fH2S+12*fsr,    5,  cal | H2S, vLaser1
fH2S+11*fsr,    4,  cal | H2S, vLaser1
fH2S+10*fsr,    4,  cal | H2S, vLaser1
fH2S+9*fsr,     4,  cal | H2S, vLaser1
fH2S+8*fsr,     2,  cal | H2S, vLaser1
fH2S+7*fsr,     2,  cal | H2S, vLaser1
fH2S+6*fsr,     2,  cal | H2S, vLaser1
fH2S+5*fsr,     2,  cal | H2S, vLaser1
fH2S+4*fsr,     2,  cal | H2S, vLaser1
fH2S+3*fsr,     6,  cal | H2S, vLaser1
fH2S+2*fsr,     2,  cal | H2S, vLaser1
fH2S+1*fsr,     4,  cal | H2S, vLaser1
fH2S,           20, cal | H2S, vLaser1
fH2S-1*fsr,     4,  cal | H2S, vLaser1
fH2S-2*fsr,     2,  cal | H2S, vLaser1
fH2S-3*fsr,     6,  cal | H2S, vLaser1
fH2S-4*fsr,     2,  cal | H2S, vLaser1
fH2S-5*fsr,     1,  cal | H2S, vLaser1
fH2S-5*fsr,     1,  fit | cal | H2S, vLaser1

