import struct 

def parseAnemometer(rawStr):
    retList = []
    try:
        reading = struct.unpack("hhhhH", rawStr[:-2])
        counter = reading[4] & 0x3F
        uz_range = (reading[4] >> 6) & 0x3
        uy_range = (reading[4] >> 8) & 0x3
        ux_range = (reading[4] >> 10) & 0x3
        flags =  (reading[4] >> 12) & 0xF
        ux = 0.002*reading[0]/(1<<ux_range)
        uy = 0.002*reading[1]/(1<<uy_range)
        uz = 0.002*reading[2]/(1<<uz_range)
        c = 340.0+0.001*reading[3]
        retList = [ux, uy, uz, c]
    except Exception, err:
        print "%r" % err
    #print ["%10.3f" % ret for ret in retList]
    return retList
     
def parseGPS(rawStr):
    retList = []
    try:
        atomsGPS = rawStr.split(",")
        #print rawStr
        if atomsGPS[0] == "$GPGGA":
            #print atomsGPS
            timeSinceMidnight = 60*(60*int(atomsGPS[1][:2])+int(atomsGPS[1][2:4]))+int(atomsGPS[1][4:6])
            degLat  = int(atomsGPS[2][:2]) if atomsGPS[3]=="N" else -int(atomsGPS[2][:2])
            degLong = int(atomsGPS[4][:3]) if atomsGPS[5]=="E" else -int(atomsGPS[4][:3])
            minLat  = float(atomsGPS[2][2:])
            minLong = float(atomsGPS[4][3:])
            degLat  += minLat/60.0  if atomsGPS[3]=="N" else -minLat/60.0
            degLong += minLong/60.0 if atomsGPS[5]=="E" else -minLong/60.0
            fit = int(atomsGPS[6])
            if fit:
                retList = [timeSinceMidnight, degLat, degLat-int(degLat), degLong, degLong-int(degLong), fit]
    except Exception, err:
        print "%r" % err
    #print ["%10.6f" % ret for ret in retList]
    return retList
    
def parseDefault(rawStr):
    retList = []
    for data in rawStr.split(","):
        data = data.replace("\r","")
        data = data.replace("\n","")
        retList.append(eval("0x"+data))
    #print ["%10.3f" % ret for ret in retList]
    return retList