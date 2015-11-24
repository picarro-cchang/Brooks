$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6566.5
#fincr = 0.005
fincr = 0.01
nfreq = 2000
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
