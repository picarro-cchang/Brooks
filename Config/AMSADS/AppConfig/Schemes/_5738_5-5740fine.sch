$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 5738.3
fincr = 0.0005
nfreq = 3001
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
