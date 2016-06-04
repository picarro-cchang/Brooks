PARSER_VERSION = 1.0

def parseGPS(rawStr):
    retList = []
    try:
        atomsGPS = rawStr.split(",")
        sentence = atomsGPS[0]
        if sentence == "$GPGGA":
            timeSinceMidnight = 60*(60*int(atomsGPS[1][:2])+int(atomsGPS[1][2:4]))+float(atomsGPS[1][4:])
            degLat  = int(atomsGPS[2][:2]) if atomsGPS[3]=="N" else -int(atomsGPS[2][:2])
            degLong = int(atomsGPS[4][:3]) if atomsGPS[5]=="E" else -int(atomsGPS[4][:3])
            minLat  = float(atomsGPS[2][2:])
            minLong = float(atomsGPS[4][3:])
            degLat  += minLat/60.0  if atomsGPS[3]=="N" else -minLat/60.0
            degLong += minLong/60.0 if atomsGPS[5]=="E" else -minLong/60.0
            fit = int(atomsGPS[6])
            retList = [sentence, degLat, degLong, fit, timeSinceMidnight]
        elif sentence == "$GPGST":
            timeSinceMidnight = 60*(60*int(atomsGPS[1][:2])+int(atomsGPS[1][2:4]))+float(atomsGPS[1][4:])
            try:
                sigmaLat = float(atomsGPS[6])
            except:
                sigmaLat = -1
            try:
                sigmaLong = float(atomsGPS[7])
            except:
                sigmaLong = -1
            retList = [sentence, sigmaLat, sigmaLong, 1, timeSinceMidnight]
    except Exception, err:
        pass
        #print "%r" % err, " from parseGPS"
    return retList
    
def syncData(oldData, newData):
    try:
        dataLabels = _DATALABELS_.split(',')
        if len(dataLabels) == 4:  # regular GPS
            if newData[0] == "$GPGGA":
                return [newData[1], newData[2], newData[3], newData[4]]
        elif len(dataLabels) == 6: # iGPS
            if oldData[0] == "$GPGGA" and newData[0] == "$GPGST":
                GGAdata, GSTdata = oldData, newData
            elif oldData[0] == "$GPGST" and newData[0] == "$GPGGA":
                GGAdata, GSTdata = newData, oldData
            elif oldData[0] == "$GPGGA" and newData[0] == "$GPGGA":
                return [newData[1], newData[2], -1, -1, newData[3], newData[4]]
                
            if oldData[4] != newData[4]:
                print "timestemp of old data (%s, %f) does not match new data (%s, %f)" % (oldData[0], oldData[4], newData[0], newData[4])
                return []
            else:
                return [GGAdata[1], GGAdata[2], GSTdata[1], GSTdata[2], GGAdata[3], GGAdata[4]]
    except:
        pass
    return []

if "_RAWSTRING_" in dir():
    data = parseGPS(_RAWSTRING_)
    _OUTPUT_ = syncData(_PERSISTENT_, data)
    if data:
        _PERSISTENT_ = data if not _OUTPUT_ else None