from numpy import *

fsr = 0.026
fp = file("fsr2.sch","w")
wList = [6316.26+i*fsr for i in range(20)]
wList = concatenate((wList,wList[::-1]))
dwell = 3
subschemeId = 4096+26
laserNum = 1

rep = 3
print >> fp, rep
print >> fp, len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
fp.close()
