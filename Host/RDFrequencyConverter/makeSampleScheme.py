from numpy import *

fp = file("sample1.sch","w")
wList = linspace(6316,6318,2001)
wList = concatenate((wList,wList[::-1]))
dwell = 3
subschemeId = 25
laserNum = 0

rep = 1
print >> fp, rep
print >> fp, len(wList)
for w in wList:
    print >> fp, w, dwell, subschemeId, laserNum
fp.close()