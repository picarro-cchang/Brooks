import time
import datetime
from Host.Common import timestamp
from Host.Common.jsonRpc import Proxy
from numpy import *
from cPickle import loads, dumps, HIGHEST_PROTOCOL
from base64 import b64decode

if __name__ == "__main__":
    service = Proxy('http://localhost:5000/jsonrpc')
    tstop = timestamp.getTimestamp()
    tstart = tstop - 60*1000
    range = dict(start=tstart,stop=tstop)

    option = input("Option? ")
    if option == 0:
        mode = "CFADS_mode"
        source = "analyze_CFADS"
        varList = ["timestamp","CO2","CH4","H2O"]
        params = dict(mode=mode,source=source,varList=varList,range=range,pickle=0)
        print service.getDmData(params)
    elif option == 1:
        mode = "CFADS_mode"
        source = "analyze_CFADS"
        varList = ["timestamp","CO2","CH4","H2O"]
        params = dict(mode=mode,source=source,varList=varList,range=range,pickle=1)
        print loads(b64decode(service.getDmData(params)))
        result = loads(b64decode(service.getDmData(params)))
    elif option == 2:
        sensorList = ["Laser1Temp","Laser2Temp","HotBoxHeater"]
        params = dict(sensorList=sensorList,range=range,pickle=0)
        print service.getSensorData(params)
    elif option == 3:
        sensorList = ["Laser1Temp","Laser2Temp","HotBoxHeater"]
        params = dict(sensorList=sensorList,range=range,pickle=1)
        print loads(b64decode(service.getSensorData(params)))
    elif option == 4:
        varList = ["timestamp","waveNumber","uncorrectedAbsorbance"]
        params = dict(varList=varList,range=range,pickle=0)
        print service.getRdData(params)
    elif option == 5:
        varList = ["timestamp","waveNumber","uncorrectedAbsorbance"]
        params = dict(varList=varList,range=range,pickle=1)
        print loads(b64decode(service.getRdData(params)))
    elif option == 6:
        params = dict(range=range,pickle=0)
        print service.getRdDataStruct(params)
    elif option == 7:
        params = dict(range=range,pickle=1)
        print loads(b64decode(service.getRdDataStruct(params)))
    elif option == 8:
        params = dict(range=range,pickle=0)
        print service.getDmDataStruct(params)
    elif option == 9:
        params = dict(range=range,pickle=1)
        print loads(b64decode(service.getDmDataStruct(params)))
    elif option == 10:
        # Get meas modes
        params = dict(range=range,pickle=1)
        print loads(b64decode(service.getDmDataStruct(params))).keys()