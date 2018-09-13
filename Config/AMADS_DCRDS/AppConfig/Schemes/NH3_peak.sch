$$$
schemeVersion = 1
repeat = 10
schemeRows = []
fmin = 6548.804
fincr = 0
nfreq = 0
vLaser = 1
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))

for i in range(nfreq, -1, -1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
