from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.LineCacheMmap import getSlice, getSliceIter
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER
import time

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

# gpsFile = r"R:\crd_G2000\CFADS\932-CFADS2204\GPS_WS_Data\GPS_Raw\2012\01\10\CFADS2204-20120110-021012Z-DataLog_GPS_Raw.dat"
# wsFile  = r"R:\crd_G2000\CFADS\932-CFADS2204\GPS_WS_Data\WS_Raw\2012\01\10\CFADS2204-20120110-021013Z-DataLog_WS_Raw.dat"

gpsFile = r"C:\Picarro\TestData\GPS_Raw\2012\01\10\CFADS2204-20120110-021012Z-DataLog_GPS_Raw.dat"
wsFile  = r"C:\Picarro\TestData\WS_Raw\2012\01\10\CFADS2204-20120110-021013Z-DataLog_WS_Raw.dat"

#gpsFile = r"C:\Picarro\TestData\Livermore_20120113\GPS_Raw\2012\01\13\FCDS2003-20120113-213552Z-DataLog_GPS_Raw.dat"
#wsFile  = r"C:\Picarro\TestData\Livermore_20120113\WS_Raw\2012\01\13\FCDS2003-20120113-213552Z-DataLog_WS_Raw.dat"

h1 = getSlice(gpsFile,0,1)[0].line.split()
h2  = getSlice(wsFile,0,1)[0].line.split()

it1 = getSliceIter(gpsFile,1)
it2 = getSliceIter(wsFile,1)

dataBroadcaster = Broadcaster(BROADCAST_PORT_DATA_MANAGER, "ReplayPeriphData", logFunc=Log)


while True:
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
    time.sleep(0.05)