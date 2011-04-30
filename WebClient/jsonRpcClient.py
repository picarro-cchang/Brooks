import urllib2,uuid,thread,base64
import simplejson as json
import time
from numpy import array, asarray
import pylab
import datetime
import matplotlib
from Host.Common import timestamp
from numpy import *
from cPickle import loads, dumps, HIGHEST_PROTOCOL
from base64 import b64decode

class _Method(object):
    # from jsonrpclib
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
        return self.__send(self.__name, args)

class Proxy():
    def __init__(self, service_url, auth_user = None, auth_password = None):
        self.service_url = service_url
        self.auth_user = auth_user
        self.auth_password = auth_password
    def call(self, method, params=None, success=None, failure=None):
        if success != None or failure != None:
            thread.start_new_thread(self.__call,(method, params, success, failure))
        else:
            result = self.__call(method,params)
            if ('error' in result) and result['error'] != None:
                raise Exception(result['error'])
                return None
            else:
                return result['result']
    def __call(self, method, params=None, success=None, failure=None):
        try:
            id = str(uuid.uuid1())
            data = json.dumps({'method':method, 'params':params, 'id':id})
            req = urllib2.Request(self.service_url)
            if self.auth_user != None and self.auth_password != None:
                authString = base64.encodestring('%s:%s' % (self.auth_user, self.auth_password))[:-1]
                req.add_header("Authorization", "Basic %s" % authString)
            req.add_header("Content-type", "application/json")
            f = urllib2.urlopen(req, data)
            response = f.read()
            data = json.loads(response)
        except IOError, (strerror):
            data = dict(result=None,error=dict(message='Network error. ' + str(strerror),code=None,data=None), id=id)
        except ValueError, (strerror):
            data = dict(result=None,error=dict(message='JSON format error. ' + str(strerror),code=None,data=None), id=id)

        if ("error" in data) and data["error"] != None:
            if failure != None:
                failure(data['error'])
        else:
            if success != None:
                success(data['result'])
        return data
    def __getattr__(self, name):
        return _Method(self.call, name)

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
        sensorList = ["Laser1Temp","Laser2Temp"]
        pickle[0] = False
        params = dict(sensorList=sensorList,range=range,pickle=0)
        timeTaken[0] = time.clock()
        service.call('getSensorData',[params],onResult,onError)
    elif option == 3:
        sensorList = ["Laser1Temp","Laser2Temp"]
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
