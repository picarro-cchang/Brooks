import time
import datetime
from Host.Common import timestamp
from Host.Common.jsonRpc import Proxy
from numpy import *
from cPickle import loads, dumps, HIGHEST_PROTOCOL
from base64 import b64decode

if __name__ == "__main__":
    running = [True]
    timeTaken = [0]
    pickle = [False]
    def onResult(result):
        print 'Time taken = %.3f' % (time.clock() - timeTaken[0],)
        if pickle[0]:
            print '%r' % loads(b64decode(result))
        else:
            print '%r' % result
        running[0] = False
    def onError(error):
        print 'failure :-( : %s' % error
        running[0] = False
    service = Proxy('http://localhost:5000/jsonrpc')
    tstop = timestamp.getTimestamp()
    tstart = tstop - 60*1000
    range = dict(start=tstart,stop=tstop)

    option = input("Option? ")
    if option == 0:
        mode = "CFADS_mode"
        source = "analyze_CFADS"
        varList = ["timestamp","CO2","CH4","H2O"]
        pickle[0] = False
        params = dict(mode=mode,source=source,varList=varList,range=range,pickle=0)
        timeTaken[0] = time.clock()
        service.call('getDmData',[params],onResult,onError)
    elif option == 1:
        mode = "CFADS_mode"
        source = "analyze_CFADS"
        varList = ["timestamp","CO2","CH4","H2O"]
        pickle[0] = True
        params = dict(mode=mode,source=source,varList=varList,range=range,pickle=1)
        timeTaken[0] = time.clock()
        service.call('getDmData',[params],onResult,onError)
    elif option == 2:
        sensorList = ["Laser1Temp","Laser2Temp","HotBoxHeater"]
        pickle[0] = False
        params = dict(sensorList=sensorList,range=range,pickle=0)
        timeTaken[0] = time.clock()
        service.call('getSensorData',[params],onResult,onError)
    elif option == 3:
        sensorList = ["Laser1Temp","Laser2Temp","HotBoxHeater"]
        pickle[0] = True
        params = dict(sensorList=sensorList,range=range,pickle=1)
        timeTaken[0] = time.clock()
        service.call('getSensorData',[params],onResult,onError)
    elif option == 4:
        varList = ["timestamp","waveNumber","uncorrectedAbsorbance"]
        pickle[0] = False
        params = dict(varList=varList,range=range,pickle=0)
        timeTaken[0] = time.clock()
        service.call('getRdData',[params],onResult,onError)
    elif option == 5:
        varList = ["timestamp","waveNumber","uncorrectedAbsorbance"]
        pickle[0] = True
        params = dict(varList=varList,range=range,pickle=1)
        timeTaken[0] = time.clock()
        service.call('getRdData',[params],onResult,onError)
    elif option == 6:
        pickle[0] = False
        params = dict(range=range,pickle=0)
        timeTaken[0] = time.clock()
        service.call('getRdDataStruct',[params],onResult,onError)
    elif option == 7:
        pickle[0] = True
        params = dict(range=range,pickle=1)
        timeTaken[0] = time.clock()
        service.call('getRdDataStruct',[params],onResult,onError)
    elif option == 8:
        pickle[0] = False
        params = dict(range=range,pickle=0)
        timeTaken[0] = time.clock()
        service.call('getDmDataStruct',[params],onResult,onError)
    elif option == 9:
        pickle[0] = True
        params = dict(range=range,pickle=1)
        timeTaken[0] = time.clock()
        service.call('getDmDataStruct',[params],onResult,onError)
    
    while running[0]:
        time.sleep(0.05)
