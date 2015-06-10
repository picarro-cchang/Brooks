$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6562.4
#fincr = 0.0005
fincr = 0.001
nfreq = 300
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
