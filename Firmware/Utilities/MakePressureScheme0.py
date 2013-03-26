# Build pressure calibration scheme

peak = 6237.408
fsr = 0.0206
peakDwell = 5
restDwell = 2
fineSteps = 20
subschemeId = 10
#
nFineFsr = 1
nCoarseFsr = 3
#
# Scheme runs from peak-(nCoarseFsr+nFineFsr)*fsr through peak+(nCoarseFsr+nFineFsr)*fsr
#
wList = []
dList = []
iList = []
vLaserNum = 1

for i in range(0,nCoarseFsr):
    wList.append(peak+(i-nCoarseFsr-nFineFsr)*fsr)
    dList.append(restDwell)
    iList.append(subschemeId)
for i in range(nFineFsr*fineSteps):
    wList.append(peak+(i-nFineFsr*fineSteps)*fsr/fineSteps)
    dList.append(restDwell)
    iList.append(subschemeId)
wList.append(peak)
dList.append(peakDwell)
iList.append(subschemeId)
for i in range(1,nFineFsr*fineSteps+1):
    wList.append(peak+i*fsr/fineSteps)
    dList.append(restDwell)
    iList.append(subschemeId)
for i in range(0,nCoarseFsr):
    wList.append(peak+(i+nFineFsr)*fsr)
    dList.append(restDwell)
    iList.append(subschemeId)
wList.append(peak+(nCoarseFsr+nFineFsr)*fsr)
dList.append(restDwell)
iList.append(32768+subschemeId)
#
fname = "PressureCalScheme.sch"
lp = file(fname,"w")
print >>lp, 10 # nrepeat
print >>lp, 2*len(wList)
for w,d,i in zip(wList,dList,iList):
    print >>lp, "%.5f %d %d %d 0 0" % (w,d,i,vLaserNum-1)
for w,d,i in zip(wList[:0:-1],dList[:0:-1],iList[:0:-1]):
    print >>lp, "%.5f %d %d %d 0 0" % (w,d,(i & 0x7FFF),vLaserNum-1)
print >>lp, "%.5f %d %d %d 0 0" % (wList[0],dList[0],iList[0] | 0x8000,vLaserNum-1)
lp.close()
print "Written file %s" % (fname,)
