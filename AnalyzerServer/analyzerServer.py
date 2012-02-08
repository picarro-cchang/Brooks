from flask import Flask
from flask import make_response, render_template, request
from jsonrpc import JSONRPCHandler, Fault
try:
    import simplejson as json
except:
    import json
from functools import wraps
import fnmatch
import itertools
from LineCacheMmap import getSlice, getSliceIter
import os
import sys
from threading import Thread
import time
import traceback
import CmdFIFO
from SharedTypes import RPC_PORT_DATALOGGER, RPC_PORT_DRIVER, RPC_PORT_INSTR_MANAGER

NaN = 1e1000/1e1000
def pFloat(x):
    try:
        return float(x)
    except:
        return NaN

def genLatestFiles(baseDir,pattern):
    # Generate files in baseDir and its subdirectories which match pattern
    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=True)
        fileNames.sort(reverse=True)
        for name in fileNames:
            if fnmatch.fnmatch(name,pattern):
                yield os.path.join(dirPath,name)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppDir = os.path.split(AppPath)[0]

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# The following are split into a path and a filename with unix style wildcards. 
#  We search for the filename in the specified path and its subdirectories.
USERLOGFILES = 'C:/UserData/AnalyzerServer/*.dat'
PEAKFILES = 'C:/UserData/AnalyzerServer/*.peaks'
ANALYSISFILES = 'C:/UserData/AnalyzerServer/*.analysis'
MAX_DATA_POINTS = 500

app = Flask(__name__)
app.config.from_object(__name__)
handler = JSONRPCHandler('jsonrpc')
handler.connect(app,'/jsonrpc')


class DataLoggerInterface(object):
    """Interface to the data logger and archiver RPC"""
    def __init__(self):
        self.dataLoggerRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATALOGGER, ClientName = "AnalyzerServer")
        self.exception = None
        self.rpcInProgress = False

    def startUserLogs(self,userLogList,restart=False):
        """Start a list of user logs by making a non-blocking RPC call"""
        while self.rpcInProgress: time.sleep(0.5)
        # if self.rpcInProgress: return False
        self.exception = None
        self.rpcInProgress = True
        th = Thread(target=self._startUserLogs,args=(userLogList,restart))
        th.setDaemon(True)
        th.start()
        return True
        
    def _startUserLogs(self,userLogList,restart):
        try:
            for i in userLogList:
                self.dataLoggerRpc.DATALOGGER_startLogRpc(i,restart)
        except Exception,e:
            self.exception = e
        self.rpcInProgress = False

class JSON_Remote_Procedure_Error(RuntimeError):
    pass

def rpcWrapper(func):
    """This decorator wraps a remote procedure call so that any exceptions from the procedure
    raise a JSON_Remote_Procedure_Error and has a traceback."""
    @wraps(func)
    def JSON_RPC_wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except:
            type,value = sys.exc_info()[:2]
            raise JSON_Remote_Procedure_Error, "\n%s" % (traceback.format_exc(),)
    return JSON_RPC_wrapper
    
def _getAnalysis(name,startRow):
    #
    # Gets data from the analyzer analysis file "name" starting  at the specified 
    #  "startRow" within the file. The result dictionary has keys:
    #
    header = getSlice(name,0,1)[0].line.split()
    result = {}
    for h in header: result[h] = []
    for l in getSliceIter(name,startRow,startRow+50):
        line = l.line
        if not line: break
        vals = line.split()
        if len(vals) != len(header): break
        for col,val in zip(header,vals):
            result[col].append(pFloat(val))
        startRow += 1
    result['nextRow'] = startRow
    return result
    
def _getPeaks(name,startRow,minAmp):
    #
    # Gets data from the analyzer peak parameters file "name" starting  at the specified 
    #  "startRow" within the file. Only peaks of amplitude no less than "minAmp" are 
    #  reported. The result dictionary has keys:
    #
    header = getSlice(name,0,1)[0].line.split()
    amplCol = header.index("AMPLITUDE")
    result = {}
    for h in header: result[h] = []
    if amplCol<0:
        print "Cannot find AMPLITUDE column in peak file"
        result['nextRow'] = startRow
        return result
    nresults = 0
    for l in getSliceIter(name,startRow):
        line = l.line
        if not line: break
        vals = line.split()
        if len(vals) != len(header): break
        if pFloat(vals[amplCol]) >= minAmp:
            nresults += 1
            for col,val in zip(header,vals):
                result[col].append(pFloat(val))
            if nresults >= 50: break
        startRow += 1
    result['nextRow'] = startRow
    return result
        
def _getData(name,startPos=None,varList=None):    
    #
    # Gets data from the analyzer live archive file "name" starting  at the specified 
    #  line "startPos" within the file.
    #
    if varList is not None:
        if "EPOCH_TIME" not in varList:
            varList.append("EPOCH_TIME")
    try:
        header = getSlice(name,0,1)[0].line.split()
        columns = [[] for i in range(len(header))]
        if (startPos==0 or startPos is None): startPos = 1
        if startPos<0: 
            endPos = None
        else:
            endPos = startPos + MAX_DATA_POINTS
        lineNum = -1
        for l in getSliceIter(name,startPos,endPos):
            lineNum = l.lineNumber
            line = l.line
            if not line: break
            vals = line.split()
            if len(vals)!=len(header): break
            for col,val in zip(columns,vals):
                col.append(pFloat(val))
        if lineNum < 0:
            return {},1
        nRows = len(columns[0])
        result = {}
        if nRows>=0:
            for col,h in zip(columns,header):
                if varList is None or h in varList:
                    result[h] = col
            lastPos = lineNum
        else:
            for col,h in zip(columns,header):
                if varList is None or h in varList:
                    result[h] = []
            lastPos = startPos
        epochTime = result['EPOCH_TIME']
        result['timeStrings'] = [time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(epochTime[-1]))]
        return result, lastPos
    except:
        print traceback.format_exc()
    
@handler.register
@rpcWrapper
def getData(params):
    return getDataEx(params)

@app.route('/rest/getData')
def rest_getData():
    result = getDataEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
    
def getDataEx(params):
    try:
        name = genLatestFiles(*os.path.split(USERLOGFILES)).next()
    except:
        return {'lastPos':"null", 'filename':''}
        
    if 'startPos' in params and (params['startPos'] is not None) and (params['startPos'] != "null"):
        try:
            startPos = int(params['startPos'])
        except:
            startPos = None
    else:
        startPos = None

    varList = json.loads(params['varList']) if 'varList' in params else None
        
    try:
        result,lastPos = _getData(name,startPos,varList)
    except:
        return {'lastPos':"null", 'filename':''}
    
    result['filename'] = os.path.basename(name)
    result['lastPos'] = lastPos
    return result
   
@handler.register
@rpcWrapper
def getPos():
    return getPosEx()
    
@app.route('/rest/getPos')
def rest_getPos():
    result = getPosEx()
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
    
def getPosEx():
    result = getDataEx({'startPos':-2,'varList':'["GPS_ABS_LONG","GPS_ABS_LAT"]'})
    long = result['GPS_ABS_LONG'][-1]
    lat = result['GPS_ABS_LAT'][-1]
    return {'result':dict(GPS_ABS_LONG=long,GPS_ABS_LAT=lat)}
        
@handler.register
@rpcWrapper
def getPeaks(params):
    return getPeaksEx(params)

@app.route('/rest/getPeaks')
def rest_getPeaks():
    result = getPeaksEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def getPeaksEx(params):
    try:
        startRow = int(params.get('startRow',1))
    except:
        startRow = 1
    minAmp = float(params.get('minAmp',0))
    try:
        name = genLatestFiles(*os.path.split(PEAKFILES)).next()
    except:
        return {'filename':''}
    result = _getPeaks(name,startRow,minAmp)
    result["filename"]=os.path.basename(name)
    return result

@handler.register
@rpcWrapper
def getAnalysis(params):
    return getAnalysisEx(params)

@app.route('/rest/getAnalysis')
def rest_getAnalysis():
    result = getAnalysisEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def getAnalysisEx(params):
    try:
        startRow = int(params.get('startRow',1))
    except:
        startRow = 1
    try:
        name = genLatestFiles(*os.path.split(ANALYSISFILES)).next()
    except:
        return {'filename':''}
    result = _getAnalysis(name,startRow)
    result["filename"]=os.path.basename(name)
    return result
                
@handler.register
@rpcWrapper
def restartDatalog(params):
    return restartDatalogEx(params)

@app.route('/rest/restartDatalog')
def rest_restartDatalog():
    result = restartDatalogEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def restartDatalogEx(params):
    print "<------------------ Restarting data log ------------------>"
    dataLogger = DataLoggerInterface()
    dataLogger.startUserLogs(['DataLog_User_Minimal'],restart=True)
    return {}
    
@handler.register
@rpcWrapper
def shutdownAnalyzer(params):
    return shutdownAnalyzerEx(params)

@app.route('/rest/shutdownAnalyzer')
def rest_shutdownAnalyzer():
    result = shutdownAnalyzerEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def shutdownAnalyzerEx(params):
    print "<------------------ Shut down analyzer in current state ------------------>"
    INST_MGR_RPC = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, ClientName = "AnalyzerServer")
    INST_MGR_RPC.INSTMGR_ShutdownRpc(2)
    return {}

@handler.register
@rpcWrapper
def driverRpc(params):
    return driverRpcEx(params)

@app.route('/rest/driverRpc')
def rest_driverRpc():
    result = driverRpcEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))

driverAvailable = True
lastDriverCheck = None

def driverRpcEx(params):
    # Call any RPC function on the driver by passing
    #  params['func'] = name of Driver RPC function to call (as a string)
    #  params['args'] = string which evaluates to a list of positional arguments for the RPC function
    #  params['kwargs'] = string which evaluates to a dictionary of keyword arguments for the RPC function
    global driverAvailable, lastDriverCheck
    
    if driverAvailable:
        Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "AnalyzerServer")
        try:
            return dict(value=getattr(Driver,params['func'])(*eval(params.get('args','()'),{}),**eval(params.get('kwargs','{}'))))
        except:
            driverAvailable = False
            lastDriverCheck = time.clock()
            return dict(error=traceback.format_exc())
    else:
        if time.clock() - lastDriverCheck > 60: driverAvailable = True
        return(dict(error="No Driver"))
        
@handler.register
@rpcWrapper
def injectCal(params):
    return injectCalEx(params)

@app.route('/rest/injectCal')
def rest_injectCal():
    result = injectCalEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))

def injectCalEx(params):
    # Inject calibration gas using "valve" for a duration of length 0.2*samples seconds
    #  An additional "flagValve" is opened for an extra 2s so that we have an indication of the calibration
    #  in the data log
    Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "AnalyzerServer")
    try:
        valve = int(params.get('valve',3))
        valveMask = 1 << (valve-1)
        flagValve = int(params.get('flagValve',4))
        flagValveMask = 1 << (flagValve-1)
        mask = valveMask | flagValveMask
        samples = int(params.get('samples',5))
        Driver.wrValveSequence([[mask,mask,samples],[mask,flagValveMask,10],[mask,0,1],[0,0,0]])
        Driver.wrDasReg("VALVE_CNTRL_SEQUENCE_STEP_REGISTER",0)
        return dict(value='OK')
    except:
        return dict(error=traceback.format_exc())
        
@handler.register
@rpcWrapper
def getDateTime(params):
    return getDateTimeEx(params)
    
@app.route('/rest/getDateTime')
def rest_getDateTime():
    result = getDateTimeEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))

def getDateTimeEx(params):
    print time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    return(dict(dateTime=time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())))

@app.route('/maps')
def maps():
    amplitude = float(request.values.get('amplitude',0.1))
    do_not_follow = int('do_not_follow' in request.values)
    follow = int('follow' in request.values or not do_not_follow)
    center_longitude = float(request.values.get('center_longitude',-121.98432))
    center_latitude = float(request.values.get('center_latitude',37.39604))
    return render_template('maps.html',amplitude=amplitude,follow=follow,do_not_follow=do_not_follow,
                                       center_latitude=center_latitude,center_longitude=center_longitude)
@app.route('/test')
def test():
    return render_template('test.html')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
    