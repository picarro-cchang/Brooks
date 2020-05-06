$$$
schemeVersion = 1
repeat = 10
schemeRows = []
fmin = 5739.1892
fincr = 0.0
nfreq = 0
vLaser = 2
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,20,0,vLaser))

schemeRows[-1].subschemeId |= fit
$$$
