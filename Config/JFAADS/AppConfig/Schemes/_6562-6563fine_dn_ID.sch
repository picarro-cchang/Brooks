$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmax = 6562.8
fincr = -0.0005
nfreq = 800
vLaser = 0
fit = 32768
N2O = 45


for i in range(nfreq+1):
    schemeRows.append(Row(fmax+i*fincr,1,N2O,vLaser))

    
schemeRows[-1].subschemeId |= fit
$$$