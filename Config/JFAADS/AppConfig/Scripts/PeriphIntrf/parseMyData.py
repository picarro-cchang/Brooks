def parseMyData(rawStr):
    retList = []
    try:
        dataLogger8 = rawStr.split()
        #print dataLogger8
        temp1 = float(dataLogger8[0])
        temp2 = float(dataLogger8[1])
        pressure = float(dataLogger8[2])
        switch = float(dataLogger8[3])
        #data_chan5 = float(dataLogger8[4])
        #data_chan6 = float(dataLogger8[5])
        #data_chan7 = float(dataLogger8[6])
        #data_chan8 = float(dataLogger8[7])
        retList = [temp1,temp2,pressure,switch]
    except Exception, err:
        print "%r" % err
    print ["%10.6f" % ret for ret in retList]
    return retList