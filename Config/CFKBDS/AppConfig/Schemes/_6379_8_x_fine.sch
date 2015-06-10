$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6379.8
fincr = 0.001
nfreq = 2200
vLaser = 4
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))

schemeRows += deepcopy(schemeRows[::-1])
schemeRows[-1].subschemeId |= fit
$$$
