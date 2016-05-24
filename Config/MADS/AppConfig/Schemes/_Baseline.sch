$$$
schemeVersion = 1
repeat = 1
schemeRows = []
#fmin = 6547.5
fmin = 7822.9
fincr = 0.001
nfreq = 2501
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))

for i in range(nfreq, -1, -1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
