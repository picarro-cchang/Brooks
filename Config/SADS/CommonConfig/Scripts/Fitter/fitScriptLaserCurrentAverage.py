from numpy import mean, median

if INIT:
    delay = 0
    delayEnd = 5
    INIT = False

    # override delay if set
    from os import listdir
    from os.path import isfile, join

    calDir = "C:/Picarro/G2000/InstrConfig/Calibration/InstrCal"
    fnames = listdir(calDir)
    la_fname = None
    for fn in fnames:
        if fn.startswith("LaserTempOffsets") and fn.endswith(".ini"):
            la_fname = join(calDir, fn)
            break

    if la_fname is not None:
        laDict = getInstrParams(la_fname)
        try:
            delayEnd = laDict["Data"]["la_StartDelayEnd"]
        except:
            delayEnd = 5

        #print "delayEnd=", delayEnd

delay += 1
if delay > delayEnd:
    delay -= 1
    d = DATA
    whichVirtual = d.laserUsed >> 2
    virtualLasersUsed = set(whichVirtual)

    meanFineLaserCurrentByVirtualLaser = {}
    RESULT = {}

    for v in virtualLasersUsed:
        meanFineLaserCurrentByVirtualLaser[v] = mean(d.fineLaserCurrent[whichVirtual == v])
        RESULT["fineLaserCurrent_%d_mean" % (v+1,)] = meanFineLaserCurrentByVirtualLaser[v]
    #print RESULT

ANALYSIS = {}

