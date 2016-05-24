$$$
schemeVersion = 1
repeat = 1
H2O = 120
H2Oalt = 121
cal = 4096
fit = 32768
fH_D_16O = 7183.97340
fH2_16O = 7183.6851
fH2_18O = 7183.5855
fcal_min = 7183.43421
vLaser1 = 0
cfg = getConfig(r'..\..\InstrConfig\Calibration\InstrCal\Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser))
    return result

def transition(a,b,dwells,id,vLaser):
    incr = (b-a)/(len(dwells)+1)
    stepAndDwell = [(i+1,d) for i,d in enumerate(dwells)]
    return makeScan(a,incr,stepAndDwell,id,vLaser)

# Make the main scan starting with H_D_16O followed by H2_16O and H2_18O
# The transitions are not quite separated by the cavity fsr, but there are
#  pre and post scans spaced at the cavity fsr

pk3  = makeScan(fH_D_16O,0.0003,[(2,3),(1,3),(0,33),(-1,3),(-2,3)],H2O,vLaser1)
pk2 = [Row(fH2_16O,21,H2O,vLaser1)]
pk1 = [Row(fH2_18O,18,H2O,vLaser1)]
pre3 = makeScan(pk3[0].setpoint,fsr,[(3,2),(2,2),(1,2)],H2O,vLaser1)
from3to2 = transition(pk3[-1].setpoint,pk2[0].setpoint,[2,2,1,1,1,1,2,2,2,2,2,2,2],H2O,vLaser1)
from2to1 = transition(pk2[-1].setpoint,pk1[0].setpoint,[2,2,2,2],H2O,vLaser1)
post1 = makeScan(pk1[0].setpoint,fsr,[(-1,2),(-2,2),(-3,2),(-4,2),(-5,2),(-6,2)],H2O,vLaser1)
idea1 = pre3 + pk3 + from3to2 + pk2 + from2to1 + pk1 + post1

# Append the reverse of the scan followed by a row indicating that a fit is required

rep = idea1 + idea1[::-1] + [Row(idea1[0].setpoint,1,fit|H2O,vLaser1)]

schemeRows += rep + rep + rep

# Make the calibration run with an alternate subscheme ID

idea2 = makeScan(idea1[0].setpoint,fsr,[(-i,4) for i in range(30)],cal|H2Oalt,vLaser1)
schemeRows += idea2 + idea2[::-1] + [Row(idea1[0].setpoint,1,fit|cal|H2Oalt,vLaser1)]

$$$
