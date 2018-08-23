$$$
schemeVersion = 1
#repeat = 1
repeat = 0
schemeRows = []
fmin = 7009.0
fincr = 0.001
nfreq = 3501
vLaser = 0
fit = 32768

for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,1,0,vLaser))
schemeRows[-1].subschemeId |= fit
$$$
