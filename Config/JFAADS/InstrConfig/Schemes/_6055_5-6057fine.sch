$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6055.5
fincr = 0.0005
nfreq = 3000
vLaser = 6
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
