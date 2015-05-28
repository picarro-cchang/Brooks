def parseGPS(rawStr):
    retList = []
    try:
        atomsGPS = rawStr.split(",")
        #print rawStr
        if atomsGPS[0] == "$GPGGA":
            print atomsGPS
            timeSinceMidnight = 60*(60*int(atomsGPS[1][:2])+int(atomsGPS[1][2:4]))+int(atomsGPS[1][4:6])
            degLat  = int(atomsGPS[2][:2]) if atomsGPS[3]=="N" else -int(atomsGPS[2][:2])
            degLong = int(atomsGPS[4][:3]) if atomsGPS[5]=="E" else -int(atomsGPS[4][:3])
            minLat  = float(atomsGPS[2][2:])
            minLong = float(atomsGPS[4][3:])
            degLat  += minLat/60.0  if atomsGPS[3]=="N" else -minLat/60.0
            degLong += minLong/60.0 if atomsGPS[5]=="E" else -minLong/60.0
            fit = int(atomsGPS[6])
            #retList = [timeSinceMidnight, degLat, degLat-int(degLat), degLong, degLong-int(degLong), fit]
            retList = [degLat, degLong, fit]
            print retList
    except Exception, err:
        print "%r" % err
    #print ["%10.6f" % ret for ret in retList]
    return retList
