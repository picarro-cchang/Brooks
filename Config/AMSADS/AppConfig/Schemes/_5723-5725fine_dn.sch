$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmax = 5724.71
fincr = 0.0005
nfreq = 4001
vLaser = 1
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmax-i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
