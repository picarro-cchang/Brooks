$$$
schemeVersion = 1
repeat = 2
fit = 32768
ignore = 16384
pzt = 8192
cal = 4096

fC2H4 = 6181.66391
fCH4 = 6057.090
fH2O = 6057.800

cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr  = float(cfg["AUTOCAL"]["CAVITY_FSR"])

H2O = 11
CH4 = 25
C2H4 = 30
C2H4_H2O = 31


C2H4laser = 5
CH4laser = 1
H2Olaser = 3

#####################################################################
#####                   Methane scan                            #####
#####################################################################

fsrlist = [-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7]
dwell = [4,4,4,4,4,6,35,6,4,4,4,4,4,4]

CH4_scan = []
for i in range(len(fsrlist)):
    CH4_scan.append(Row(fCH4 + fsrlist[i]*fsr, dwell[i], CH4, CH4laser))

fsrlist = [8,7,6,5,4,3,2,1,0,-1,-2,-3,-4,-5,-6]
dwell = [4,4,4,4,4,4,4,6,35,6,4,4,4,4,3]

for i in range(len(fsrlist)):
    CH4_scan.append(Row(fCH4 + fsrlist[i]*fsr, dwell[i], CH4 | cal | pzt, CH4laser))
CH4_scan.append(Row(fCH4 - 6*fsr, 1, CH4 | fit | cal | pzt, CH4laser))
CH4_scan.append(Row(fH2O + 5*fsr, 0, H2O | ignore, H2Olaser))

#####################################################################
#####                  Water vapor scan                         #####
#####################################################################

fsrlist = [5,4,3,2,1,0,-1,-2,-3,-4,-5]
dwell = [2,2,2,2,2,5,2,2,2,2,1]

H2O_scan = []

for i in range(len(fsrlist)):
    H2O_scan.append(Row(fH2O + fsrlist[i]*fsr, dwell[i], H2O | cal | pzt, H2Olaser))
H2O_scan.append(Row(fH2O - 5*fsr, 1, H2O | fit | cal | pzt, H2Olaser))
H2O_scan.append(Row(fCH4 - 6*fsr, 0, CH4 | ignore, CH4laser))

#####################################################################
#####                 Spectrum ID = 30                          #####
#####################################################################

fsrlist = [-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5]
dwell = [2,2,8,8,2,2,2,2,2,2,2,2,2,2,2,2,20,2,2,2,2,2]

SID30 = []
for i in range(len(fsrlist)):
    SID30.append(Row(fC2H4 + fsrlist[i]*fsr, dwell[i], C2H4 | pzt | cal, C2H4laser))

fsrlist = [5,4,3,2,1,0,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16]
dwell = [2,2,2,2,2,20,2,2,2,2,2,2,2,2,2,2,2,2,8,8,2,1]

for i in range(len(fsrlist)):
    SID30.append(Row(fC2H4 + fsrlist[i]*fsr, dwell[i], C2H4, C2H4laser))

SID30.append(Row(fC2H4 - 16*fsr, 1, C2H4 | fit, C2H4laser))


#####################################################################
#####                   Spectrum ID = 31                        #####
#####################################################################

SID31 = []
for i in range(-16,22):
    SID31.append(Row(fC2H4 + i*fsr, 5, C2H4_H2O | pzt | cal, C2H4laser))

for i in range(21,-17,-1):
    SID31.append(Row(fC2H4 + i*fsr, 5, C2H4_H2O, C2H4laser))

SID31.append(Row(fC2H4 - 16*fsr, 1, C2H4_H2O | fit, C2H4laser))


schemeRows = H2O_scan + SID31 + SID30 + SID30 + SID30 + SID30 + SID30 + CH4_scan + SID31 + SID30 + SID30 + SID30 + SID30 + SID30

$$$
