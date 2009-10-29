from numpy import *

fsr = 0.020691
fp = file("fsr4.sch","w")
wList = [6317.208+i*fsr for i in range(-15,16)]
wList = concatenate((wList,wList[::-1]))
dwell = 10
subschemeId = 4096+26
laserNum = 0

rep = 3
print >> fp, rep
print >> fp, len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
