$$$
schemeVersion = 1
repeat = 1
schemeRows = []
fmin = 6237
fincr = 0.001
nfreq = 1000
vLaser = 0


for i in range(nfreq+1):
    schemeRows.append(Row(fmin+i*fincr,3,0,vLaser))

schemeRows += deepcopy(schemeRows[::-1])

$$$
