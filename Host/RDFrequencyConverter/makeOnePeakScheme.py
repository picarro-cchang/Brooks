from numpy import *

fp = file("onePeak.sch","w")
wList = linspace(6316.225,6316.625,401)
wList = concatenate((wList,wList[::-1]))
dwell = 3
subschemeId = 20
laserNum = 0

rep = 1
print >> fp, rep
print >> fp, len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
fp.close()