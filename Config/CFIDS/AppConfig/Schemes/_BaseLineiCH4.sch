$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6028.9
fincr = 0.0000
nfreq = 7600
vLaser = 2
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
