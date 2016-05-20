$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6056.6
fincr = 0.002
nfreq = 1400
vLaser = 1
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))

schemeRows += deepcopy(schemeRows[::-1])
schemeRows[-1].subschemeId |= fit
$$$
