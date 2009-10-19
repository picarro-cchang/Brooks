from numpy import *

fsr = 0.026
fp = file("fsr4.sch","w")
wList = [6316.425+i*fsr for i in range(-8,9)]
wList = concatenate((wList,wList[::-1]))
dwell = 3
subschemeId = 4096+26
laserNum = 0

rep = 3
print >> fp, rep
print >> fp, len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
