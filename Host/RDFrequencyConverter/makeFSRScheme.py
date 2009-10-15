from numpy import *

fsr = 0.026
fp = file("fsr3.sch","w")
wList = [6316.25+i*fsr for i in range(20)]
wList = concatenate((wList,wList[::-1]))
dwell = 3
subschemeId = 4096+26
laserNum = 0

rep = 3
print >> fp, rep
print >> fp, 2*len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum

wList = [6316.26+i*fsr for i in range(20)]
wList = concatenate((wList,wList[::-1]))
laserNum = 1
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
fp.close()
