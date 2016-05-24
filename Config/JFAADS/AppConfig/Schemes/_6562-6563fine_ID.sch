$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6562.4
fincr = 0.0005
nfreq = 800
vLaser = 0
fit = 32768
N2O = 45


for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,N2O,vLaser))

    
schemeRows[-1].subschemeId |= fit
$$$