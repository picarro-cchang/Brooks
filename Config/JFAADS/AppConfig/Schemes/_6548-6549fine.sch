$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6548.5
#fincr = 0.0005
fincr = 0.001
nfreq = 500
vLaser = 5
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
