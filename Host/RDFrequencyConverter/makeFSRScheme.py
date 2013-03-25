from numpy import *

fsr = 0.020605
fp = file("fsrCal.sch","w")
wList1 = [6237.408+i*fsr for i in range(-5,5)]
wList1 = concatenate((wList1,wList1[::-1]))
wList2 = [6057.1+i*fsr for i in range(-6,6)]
wList2 = concatenate((wList2,wList2[::-1]))
dwell = 10
subschemeId = len(wList1)*[4096+25] + len(wList2)*[4096+26]
laserNum = len(wList1)*[0] + len(wList2)*[1]
wList = concatenate((wList1,wList2))

rep = 3
print >> fp, rep
print >> fp, len(wList)
for i,w in enumerate(wList):
    print >> fp, w, dwell, subschemeId[i], laserNum[i]
