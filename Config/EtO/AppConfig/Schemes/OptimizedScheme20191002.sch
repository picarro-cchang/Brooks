$$$
schemeVersion = 1
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
ignore = 16384
repeat = 2
f_eto = 6080.0630
f_ref = 6079.563376
ETO = 181
cal = 4096
pztcen = 8192
fit = 32768
vLaser1 = 0
vLaser2 = 1
vLaser3 = 2
vLaser4 = 3
vLaser5 = 4
vLaser6 = 5
vLaser7 = 6
vLaser8 = 7

    
#  Version 1 of a scheme to measurement ethylene oxide with the widely tunable laser.  "Cal" flag turned off.
#  Version 2 tries to use RDs better, starting with more on the ETO peak
#  Version 3 -- automatic optimization (rella 20191002_1753)

schemeRows = []
schemeRows.append(Row(f_eto - 170*fsr, 15, ETO, vLaser1))
schemeRows.append(Row(f_eto - 168*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 167*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 166*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 165*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 164*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 163*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 162*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 161*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 160*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 159*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 158*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 157*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 156*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 155*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 154*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 153*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 152*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 151*fsr, 4, ETO, vLaser1))
schemeRows.append(Row(f_eto - 150*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 149*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 148*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 147*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 146*fsr, 4, ETO, vLaser1))
schemeRows.append(Row(f_eto - 145*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 144*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 143*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 142*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 141*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 140*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 139*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 138*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 137*fsr, 5, ETO, vLaser1))
schemeRows.append(Row(f_eto - 136*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 135*fsr, 5, ETO, vLaser1))
schemeRows.append(Row(f_eto - 134*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 133*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 132*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 131*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 130*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 129*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 122*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 117*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 108*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 103*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 93*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 87*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 77*fsr, 4, ETO, vLaser1))
schemeRows.append(Row(f_eto - 72*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 67*fsr, 4, ETO, vLaser1))
schemeRows.append(Row(f_eto - 53*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 49*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 39*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 31*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 30*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 29*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 28*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 27*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 26*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 25*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 24*fsr, 5, ETO, vLaser1))
schemeRows.append(Row(f_eto - 23*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 22*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 21*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 20*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 15*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto - 7*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto, 68, ETO, vLaser1))
schemeRows.append(Row(f_eto + 10*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 14*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 25*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 34*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 41*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 42*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 55*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 56*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 57*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 58*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 59*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 60*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 61*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 62*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 63*fsr, 5, ETO, vLaser1))
schemeRows.append(Row(f_eto + 64*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 65*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 66*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 67*fsr, 23, ETO, vLaser1))
schemeRows.append(Row(f_eto + 68*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 69*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 70*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 74*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 81*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 92*fsr, 1, ETO, vLaser1))
schemeRows.append(Row(f_eto + 93*fsr, 18, ETO, vLaser1))
schemeRows.append(Row(f_eto + 94*fsr, 8, ETO, vLaser1))
schemeRows += schemeRows[::-1]
schemeRows.append(Row(f_eto - 170*fsr, 1, ETO|fit, vLaser1))


$$$