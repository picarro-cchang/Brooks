from numpy import *

fp = file("sample2.sch","w")
wList = linspace(6056.5,6057.5,1001)
wList = concatenate((wList,wList[::-1]))
dwell = 3
subschemeId = 26
laserNum = 1

rep = 1
print >> fp, rep
print >> fp, len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
fp.close()