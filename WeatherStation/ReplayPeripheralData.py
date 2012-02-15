from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.LineCacheMmap import getSlice, getSliceIter
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER
from Host.Common import StringPickler

import cPickle
import time
# Dummy address for debugging
BROADCAST_PORT_DATA_MANAGER = 40500

def Log(str):
    print str
    
def line2Dict(line,header):
    result = {}
    if line:
        vals = line.split()
        if len(vals) == len(header): 
            for col,val in zip(header,vals):
                result[col] = float(val)
    return result

#gpsFile = r"R:\crd_G2000\CFADS\932-CFADS2204\GPS_WS_Data\GPS_Raw\2012\01\10\CFADS2204-20120110-021012Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\CFADS\932-CFADS2204\GPS_WS_Data\WS_Raw\2012\01\10\CFADS2204-20120110-021013Z-DataLog_WS_Raw.dat"

#gpsFile = r"C:\Picarro\TestData\GPS_Raw\2012\01\10\CFADS2204-20120110-021012Z-DataLog_GPS_Raw.dat"
#wsFile  = r"C:\Picarro\TestData\WS_Raw\2012\01\10\CFADS2204-20120110-021013Z-DataLog_WS_Raw.dat"

#gpsFile = r"C:\Picarro\TestData\Livermore_20120113\GPS_Raw\2012\01\13\FCDS2003-20120113-213552Z-DataLog_GPS_Raw.dat"
#wsFile  = r"C:\Picarro\TestData\Livermore_20120113\WS_Raw\2012\01\13\FCDS2003-20120113-213552Z-DataLog_WS_Raw.dat"

#gpsFile = r"C:\Picarro\TestData\GPS_Raw\2012\01\10\CFADS2204-20120110-021012Z-DataLog_GPS_Raw.dat"
#wsFile  = r"C:\Picarro\TestData\WS_Raw\2012\01\10\CFADS2204-20120110-021013Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Friday 1_13_12 data\GPS_Raw\2012\01\13\FCDS2003-20120113-213552Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Friday 1_13_12 data\WS_Raw\2012\01\13\FCDS2003-20120113-213552Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Tuesday 1_17_12 data\GPS_Raw\2012\01\17\FCDS2003-20120117-165607Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Tuesday 1_17_12 data\WS_Raw\2012\01\17\FCDS2003-20120117-165607Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Tuesday 1_17_12 data\GPS_Raw\2012\01\17\FCDS2003-20120117-205610Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Tuesday 1_17_12 data\WS_Raw\2012\01\17\FCDS2003-20120117-205609Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Wednesday 1_18_12\GPS_Raw\2012\01\18\FCDS2003-20120118-164701Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Wednesday 1_18_12\WS_Raw\2012\01\18\FCDS2003-20120118-164701Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Wednesday 1_18_12\GPS_Raw\2012\01\18\FCDS2003-20120118-173257Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Wednesday 1_18_12\WS_Raw\2012\01\18\FCDS2003-20120118-173256Z-DataLog_WS_Raw.dat"

#BAD MAGNETOMETER DATA
#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Wednesday 1_18_12\GPS_Raw\2012\01\18\FCDS2003-20120118-213300Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Wednesday 1_18_12\WS_Raw\2012\01\18\FCDS2003-20120118-213259Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Thursday 1_19_12 data\GPS_Raw\2012\01\19\FCDS2003-20120119-151325Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Thursday 1_19_12 data\WS_Raw\2012\01\19\FCDS2003-20120119-151319Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Thursday 1_19_12 data\GPS_Raw\2012\01\19\FCDS2003-20120119-191329Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Thursday 1_19_12 data\WS_Raw\2012\01\19\FCDS2003-20120119-191321Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Thursday 1_19_12 data\GPS_Raw\2012\01\19\FCDS2003-20120119-231331Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Thursday 1_19_12 data\WS_Raw\2012\01\19\FCDS2003-20120119-231324Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Friday 1_19_12 data\GPS_Raw\2012\01\20\FCDS2003-20120120-163430Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\PG&E Phase I experiment Jan 2012\Friday 1_19_12 data\WS_Raw\2012\01\20\FCDS2003-20120120-163431Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120203\GPSWS\FCDS2003-20120203-194800Z-DataLog_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120203\GPSWS\FCDS2003-20120203-194759Z-DataLog_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\MountainViewDrivearound_20120208\GPSWS\Composite_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\MountainViewDrivearound_20120208\GPSWS\Composite_WS_Raw.dat"

#gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\GPSWS\Composite_GPS_Raw.dat"
#wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120213\GPSWS\Composite_WS_Raw.dat"

gpsFile = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120214\GPSWS\FCDS2003-20120214-214802Z-DataLog_GPS_Raw.dat"
wsFile  = r"R:\crd_G2000\FCDS\1061-FCDS2003\Survey_20120214\GPSWS\FCDS2003-20120214-200418Z-DataLog_WS_Raw.dat"

#gpsFile = "gps.dat"
#wsFile  = "ws.dat"

h1 = getSlice(gpsFile,0,1)[0].line.split()
h2  = getSlice(wsFile,0,1)[0].line.split()

it1 = getSliceIter(gpsFile,1)
it2 = getSliceIter(wsFile,1)

dataBroadcaster = Broadcaster(BROADCAST_PORT_DATA_MANAGER, "ReplayPeriphData", logFunc=Log)
time.sleep(2.0)

while True:
    try:
        l1 = it1.next()
        d1 = line2Dict(l1.line,h1)
        u1 = d1['EPOCH_TIME']
        measData = MeasData('parseGPS', u1, d1, True, 0)
        dataBroadcaster.send(measData.dumps())
        l2 = it2.next()
        d2 = line2Dict(l2.line,h2)
        u2 = d2['EPOCH_TIME']
        measData = MeasData('parseWeatherStation', u2, d2, True, 0)
        dataBroadcaster.send(measData.dumps())
        time.sleep(0.01)
    except StopIteration,e:
        print "Out of data"
        dataBroadcaster.send(StringPickler.PackArbitraryObject(e))
        break
        
time.sleep(2.0)