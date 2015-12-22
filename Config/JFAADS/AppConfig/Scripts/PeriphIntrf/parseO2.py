def parseO2(rawStr):
    retList = []
    try:
        dataLogger8 = rawStr.split(",")
        #print dataLogger8
        jdate = int(dataLogger8[1])
        year = int(dataLogger8[2])
        month = int(dataLogger8[3])
        day = int(dataLogger8[4])
        hour = int(dataLogger8[5])
        min = int(dataLogger8[6])
        second = int(dataLogger8[7])
        msecond = int(dataLogger8[8])
        BATT_V = float(dataLogger8[9])
        PANEL_TEMP = float(dataLogger8[10])
        WSPEED_N = float(dataLogger8[11])
        WSPEED_E = float(dataLogger8[12])
        SOLAR_RAD = float(dataLogger8[13])
        SURFACE_TEMP = float(dataLogger8[14])
        AIR_TEMP = float(dataLogger8[15])
        SOIL_O2 = float(dataLogger8[16])
        SOIL_SENSOR_TEMP = float(dataLogger8[17])
        retList = [jdate,year,month,day,hour,min,second,msecond,BATT_V,PANEL_TEMP,WSPEED_N,WSPEED_E,SOLAR_RAD,SURFACE_TEMP,AIR_TEMP,SOIL_O2,SOIL_SENSOR_TEMP]
    except Exception, err:
        print "%r" % err
    print ["%10.6f" % ret for ret in retList]
    return retList