$$$
schemeVersion = 1
repeat = 10
peak = 6547.825
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
peakDwell = 5
restDwell = 2
fineSteps = 20
nFineFsr = 2
nCoarseFsr = 3
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser = vLaser1
subschemeId = 0
fit = 32768
idea1 = []
#######################################################################
# FSR steps below peak frequency
#######################################################################
for i in range(0,nCoarseFsr):
    idea1.append(Row(peak + (i-nCoarseFsr-nFineFsr)*fsr,restDwell,subschemeId,vLaser))
#######################################################################
# Fine steps below peak frequency
#######################################################################
for i in range(nFineFsr*fineSteps):
    idea1.append(Row(peak+(i-nFineFsr*fineSteps)*fsr/fineSteps,restDwell,subschemeId,vLaser))
#######################################################################
# Peak
#######################################################################
idea1.append(Row(peak,peakDwell,subschemeId,vLaser))
#######################################################################
# Fine steps above peak frequency
#######################################################################
for i in range(1,nFineFsr*fineSteps+1):
    idea1.append(Row(peak + i*fsr/fineSteps,restDwell,subschemeId,vLaser))
#######################################################################
# FSR steps above peak frequency
#######################################################################
for i in range(0,nCoarseFsr):
    idea1.append(Row(peak + (i+nFineFsr)*fsr,restDwell,subschemeId,vLaser))
idea1.append(Row(peak+(nCoarseFsr+nFineFsr)*fsr,restDwell,subschemeId,vLaser))

# Reverse for the second half of the scheme
idea2 = deepcopy(idea1[::-1])

# Set fit flags
idea1[-1].subschemeId |= fit
idea2[-1].subschemeId |= fit

schemeRows = idea1 + idea2
$$$