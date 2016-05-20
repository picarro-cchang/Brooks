$$$
schemeVersion = 1
repeat = 2
fit = 32768
ignore = 16384
pzt = 8192
cal = 4096

fC2H4 = 6181.66391

cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr  = float(cfg["AUTOCAL"]["CAVITY_FSR"])

C2H4 = 30
C2H4_H2O = 31


vlaser = 5


#####################################################################
#####                 Spectrum ID = 30                          #####
#####################################################################

fsrlist = [-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5]
dwell = [4,4,12,12,4,4,4,4,4,4,4,4,4,4,4,4,40,4,4,4,4,4]

SID30 = []
for i in range(len(fsrlist)):
    SID30.append(Row(fC2H4 + fsrlist[i]*fsr, dwell[i], C2H4 | pzt | cal, vlaser))

fsrlist = [5,4,3,2,1,0,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16]
dwell = [4,4,4,4,4,40,4,4,4,4,4,4,4,4,4,4,4,4,12,12,4,1]

for i in range(len(fsrlist)):
    SID30.append(Row(fC2H4 + fsrlist[i]*fsr, dwell[i], C2H4, vlaser))

SID30.append(Row(fC2H4 - 16*fsr, 1, C2H4 | fit, vlaser))


#####################################################################
#####                   Spectrum ID = 31                        #####
#####################################################################

SID31 = []
for i in range(-16,22):
    SID31.append(Row(fC2H4 + i*fsr, 5, C2H4_H2O | pzt | cal, vlaser))

for i in range(21,-17,-1):
    SID31.append(Row(fC2H4 + i*fsr, 5, C2H4_H2O, vlaser))

SID31.append(Row(fC2H4 - 16*fsr, 1, C2H4_H2O | fit, vlaser))


schemeRows = SID31 + SID30 + SID30 + SID30 + SID30 + SID30

$$$
