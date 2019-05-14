$$$
schemeVersion = 1
repeat = 0
schemeRows = []
fmin = 5737.8
fincr = 0.001
nfreq = 2001
vLaser = 2
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
    
for i in range(nfreq, -1, -1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
