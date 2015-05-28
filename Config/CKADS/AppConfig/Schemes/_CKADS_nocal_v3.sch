$$$
schemeVersion = 1
repeat = 2
fit = 32768
ignore = 16384
pzt = 8192
cal = 4096

fCO  = 6380.3227
fCO2 = 6237.408

cfg = getConfig("..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini")
fsr1  = float(cfg["AUTOCAL"]["CAVITY_FSR_VLASER_1"])
fsr2  = float(cfg["AUTOCAL"]["CAVITY_FSR_VLASER_2_NOCHANGE"])
dtop = 0.0003

CO  = 145
CO2 = 10
CH4 = 25
H2O = 11

CO2Threshold = 13500


vlaser1 = 0
vlaser2 = 1


#####################################################################
#####                   CO2 Section                             #####
#####################################################################

fsrlist = [-5,-4,-3,-2,-1,0,0,0,0,0,1,2,3,4]
dtoplist = [0,0,0,0,0,-2,-1,0,1,2,0,0,0,0]
dwell = [5,4,5,3,3,3,3,19,3,3,3,3,5,3]

schemeRows = []
for i in range(len(fsrlist)):
    schemeRows.append(Row(fCO2 + fsrlist[i]*fsr1 + dtoplist[i]*dtop, dwell[i], CO2, vlaser1, CO2Threshold))

fsrlist = [5,4,3,2,1,0,0,0,0,0,-1,-2,-3,-4,-5,-5]
dwell = [5,3,5,3,3,3,3,19,3,3,3,3,5,3,4,1]
dtoplist = [0,0,0,0,0,2,1,0,-1,-2,0,0,0,0,0,0]

for i in range(len(fsrlist)):
    c = pzt if (dtoplist[i] == 0) else 0
    schemeRows.append(Row(fCO2 + fsrlist[i]*fsr1 + dtoplist[i]*dtop, dwell[i], CO2 | c, vlaser1, CO2Threshold))

schemeRows[-1].subschemeId |= fit




#####################################################################
#####                   CO Section                              #####
#####################################################################


fsrlist = [0,1,2,3,4,5,6,7,8,7,6,5,4,3,2,1,0,-1,-2,-3,-4,-5,-6,-7,-8,-7,-6,-5,-4,-3,-2,-1,0]
dwell = [60,3,3,3,3,6,3,3,6,3,3,4,3,3,3,3,60,3,3,3,3,4,3,3,4,3,3,4,3,3,3,3,60]

for i in range(len(fsrlist)):
    schemeRows.append(Row(fCO + fsrlist[i]*fsr2, dwell[i], CO | pzt, vlaser2))


fsrlist = [1,2,3,4,3,2,1,0,-1,-2,-3,-4,-3,-2,-1,0]
dwell = [3,2,1,1,1,2,3,60,3,2,1,1,1,2,3,60]

for x in range(4):
    for i in range(len(fsrlist)):
        schemeRows.append(Row(fCO + fsrlist[i]*fsr2, dwell[i], CO | pzt, vlaser2))


schemeRows.append(Row(fCO, 1, CO | fit, vlaser2))

$$$
