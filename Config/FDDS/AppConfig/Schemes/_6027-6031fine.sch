$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6027.1
fincr = 0.0005
nfreq = 7500
vLaser = 3
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
