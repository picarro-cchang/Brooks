# Build pressure calibration scheme

def makePressureScheme(peak,fsr,peakDwell,restDwell,fineSteps,subschemeId,nFineFsr,nCoarseFsr,vLaserNum):
    #
    # Scheme runs from peak-(nCoarseFsr+nFineFsr)*fsr through peak+(nCoarseFsr+nFineFsr)*fsr
    #
    wList = []
    dList = []
    iList = []
    vList = []

    for i in range(0,nCoarseFsr):
        wList.append(peak+(i-nCoarseFsr-nFineFsr)*fsr)
        dList.append(restDwell)
        iList.append(subschemeId)
        vList.append(vLaserNum-1)
    for i in range(nFineFsr*fineSteps):
        wList.append(peak+(i-nFineFsr*fineSteps)*fsr/fineSteps)
        dList.append(restDwell)
        iList.append(subschemeId)
        vList.append(vLaserNum-1)
    wList.append(peak)
    dList.append(peakDwell)
    iList.append(subschemeId)
    vList.append(vLaserNum-1)
    for i in range(1,nFineFsr*fineSteps+1):
        wList.append(peak+i*fsr/fineSteps)
        dList.append(restDwell)
        iList.append(subschemeId)
        vList.append(vLaserNum-1)
    for i in range(0,nCoarseFsr):
        wList.append(peak+(i+nFineFsr)*fsr)
        dList.append(restDwell)
        iList.append(subschemeId)
        vList.append(vLaserNum-1)
    wList.append(peak+(nCoarseFsr+nFineFsr)*fsr)
    dList.append(restDwell)
    iList.append(subschemeId)
    vList.append(vLaserNum-1)
    return wList, dList, iList, vList
#
wList = []
dList = []
iList = []
vList = []
#
fsr = 0.0206
peakDwell = 5
restDwell = 2
fineSteps = 20
#
nFineFsr = 1
nCoarseFsr = 3
#
vLaserNum = 1
peak = 6251.758
subschemeId = 0
w1, d1, i1, v1 = makePressureScheme(peak,fsr,peakDwell,restDwell,fineSteps,subschemeId,nFineFsr,nCoarseFsr,vLaserNum)
wList += w1
dList += d1
iList += i1
vList += v1
iList[-1] += 32768
wList += w1[::-1]
dList += d1[::-1]
iList += i1[::-1]
vList += v1[::-1]
iList[-1] += 32768

fname = "PressureCalSchemeiCO2.sch"
lp = file(fname,"w")
print >>lp, 10 # nrepeat
print >>lp, len(wList)
for w,d,i,v in zip(wList,dList,iList,vList):
    print >>lp, "%.5f %d %d %d 0 0" % (w,d,i,v)
lp.close()
print "Written file %s" % (fname,)