$$$
schemeVersion = 1
repeat = 1
schemeRows = []
HF = 60
#fmin = 6547.5
fmin = 7821.2
fincr = 0.001
#nfreq = 2501
nfreq = 1000
vLaser = 0
fit = 32768

cfg = getConfig(r'../../InstrConfig/Calibration/InstrCal/Beta2000_HotBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])

def makeScan(base,incr,stepAndDwell,id,vLaser,threshold=None):
    result = []
    for s,d in stepAndDwell:
        if threshold == None:
            result.append(Row(base+s*incr,d,id,vLaser))
        else:
            result.append(Row(base+s*incr,d,id,vLaser,threshold))
    return result

#scanHFup = makeScan(fmin,fsr,[(s,20) for s in range(0,48)],HF,vLaser)

#schemeRows += scanHFup

#scanHFdn = makeScan(fmin+48*fsr,fsr,[(s,20) for s in range(0,-48,-1)],HF,vLaser)

#schemeRows += scanHFdn

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
    
for i in range(nfreq, -1, -1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
    
schemeRows[-1].subschemeId |= fit


    



$$$
