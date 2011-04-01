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
    print ["%10.3f" % ret for ret in retList]
    return retList
        
def parseDefault(rawStr):
    retList = []
    for data in rawStr.split(","):
        data = data.replace("\r","")
        data = data.replace("\n","")
        retList.append(eval("0x"+data))
    print ["%10.3f" % ret for ret in retList]
    return retList