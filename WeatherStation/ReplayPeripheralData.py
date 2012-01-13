from Host.Common.MeasData import MeasData
from Host.Common.Broadcaster import Broadcaster
from Host.Common.LineCacheMmap import getSlice, getSliceIter
import time

def line2Dict(line,header):
    result = {}
    if line:
        vals = line.split()
        if len(vals) == len(header): 
            for col,val in zip(header,vals):
                result[col] = float(val)
    return result

gpsFile = r"R:\crd_G2000\CFADS\932-CFADS2204\GPS_WS_Data\GPS_Raw\2012\01\10\CFADS2204-20120110-021012Z-DataLog_GPS_Raw.dat"
wsFile  = r"R:\crd_G2000\CFADS\932-CFADS2204\GPS_WS_Data\WS_Raw\2012\01\10\CFADS2204-20120110-021013Z-DataLog_WS_Raw.dat"

h1 = getSlice(gpsFile,0,1)[0].line.split()
h2  = getSlice(wsFile,0,1)[0].line.split()

it1 = getSliceIter(gpsFile,1)
it2 = getSliceIter(wsFile,1)

while True:
    l1 = it1.next()
    print line2Dict(l1.line,h1)
    
    l2 = it2.next()
    print line2Dict(l2.line,h2)
