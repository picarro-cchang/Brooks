$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6563.3
fincr = -0.0005
nfreq = 3100
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,47,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
