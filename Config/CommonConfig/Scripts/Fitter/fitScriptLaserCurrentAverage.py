from numpy import mean, median

if INIT:
    delay = 0
    INIT = False

delay += 1
if delay > 5:
    delay -= 1
    d = DATA
    whichVirtual = d.laserUsed >> 2
    virtualLasersUsed = set(whichVirtual)

    meanFineLaserCurrentByVirtualLaser = {}
    RESULT = {}

    for v in virtualLasersUsed:
        meanFineLaserCurrentByVirtualLaser[v] = mean(d.fineLaserCurrent[whichVirtual == v])
        RESULT["fineLaserCurrent_%d_mean" % (v+1,)] = meanFineLaserCurrentByVirtualLaser[v]
    print RESULT

ANALYSIS = {}

