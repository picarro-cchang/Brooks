from flask import Flask
from flask import make_response, render_template, request
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
from timestamp import getTimestamp
from SharedTypes import RPC_PORT_DATALOGGER, RPC_PORT_DRIVER, RPC_PORT_INSTR_MANAGER, RPC_PORT_DATA_MANAGER
import SwathProcessor as sp
import math

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
    appPath = sys.executable
else:
    appPath = sys.argv[0]
appDir = os.path.split(appPath)[0]

# configuration
DEBUG = False
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# The following are split into a path and a filename with unix style wildcards. 
#  We search for the filename in the specified path and its subdirectories.
USERLOGFILES = 'C:/UserData/AnalyzerServer/*.dat'
PEAKFILES = 'C:/UserData/AnalyzerServer/*.peaks'
ANALYSISFILES = 'C:/UserData/AnalyzerServer/*.analysis'
SWATHFILES = 'C:/UserData/AnalyzerServer/*.swath'
MAX_DATA_POINTS = 500

STATICROOT = os.path.join(appDir,'static')

app = Flask(__name__)
app.config.from_object(__name__)

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
    
def _getSwath(name,startRow,limit):
    #
    # Gets data from the analyzer peak parameters file "name" starting  at the specified 
    #  "startRow" within the file:
    #
    header = getSlice(name,0,1)[0].line.split()
    result = {}
    for h in header: result[h] = []
    nresults = 0
    for l in getSliceIter(name,startRow):
        line = l.line
        if not line: break
        vals = line.split()
        if len(vals) != len(header): break
        nresults += 1
        for col,val in zip(header,vals):
            result[col].append(pFloat(val))
        if nresults >= limit: break
        startRow += 1
    result['nextRow'] = startRow
    return result

def _makeSwath(name,startRow,limit,nWindow,stabClass,minLeak,minAmp,astdParams):
    # Making a swath requires 2*nWindow+1 points centered about
    #  each position, so to produce the swath at startRow, we need
    #  to fetch rows startRow-nWindow through startRow+nWindow.
    # We need to keep track of the rows that will have their swaths
    #  calculated by this call, so that result['nextRow'] can be 
    #  filled up.
    header = getSlice(name,0,1)[0].line.split()
    result = {}
    source = []     # This is the collection of rows to be processed
    nresults = 0
    firstRow = max(1,startRow-nWindow)
    row = firstRow  
    for l in getSliceIter(name,firstRow):
        line = l.line
        if not line: break
        vals = line.split()
        if len(vals) != len(header): break
        row += 1
        if row >= firstRow+limit+2*nWindow: break
        # source is a list of dictionaries, one for
        #  each row of the data file
        rowDict = {}
        for col,val in zip(header,vals):
            rowDict[col] = pFloat(val)
        source.append(rowDict)            
    result = sp.process(source,nWindow,stabClass,minLeak,minAmp,astdParams)
    result['nextRow'] = row-nWindow
    return result
    
def _getData(name,startPos=None,varList=None,limit=MAX_DATA_POINTS):    
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
            endPos = startPos + limit
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
        limit = int(params.get('limit',MAX_DATA_POINTS))
    except:
        limit = MAX_DATA_POINTS
        
    try:
        result,lastPos = _getData(name,startPos,varList,limit)
    except:
        return {'lastPos':"null", 'filename':''}
    
    result['filename'] = os.path.basename(name)
    result['lastPos'] = lastPos
    return result
   
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

@app.route('/rest/getSwath')
def rest_getSwath():
    result = getSwathEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def getSwathEx(params):
    try:
        startRow = int(params.get('startRow',1))
    except:
        startRow = 1
    try:
        limit = int(params.get('limit',MAX_DATA_POINTS))
    except:
        limit = MAX_DATA_POINTS
    try:
        name = genLatestFiles(*os.path.split(SWATHFILES)).next()
    except:
        return {'filename':''}
    result = _getSwath(name,startRow,limit)
    result["filename"]=os.path.basename(name)
    return result

@app.route('/rest/makeSwath')
def rest_makeSwath():
    result = makeSwathEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def makeSwathEx(params):
    astdParams = dict(a=0.15*math.pi,b=0.25,c=0.0)
    try:
        startRow = int(params.get('startRow',1))
    except:
        startRow = 1
    try:
        limit = int(params.get('limit',MAX_DATA_POINTS))
    except:
        limit = MAX_DATA_POINTS
    try:
        nWindow = int(params.get('nWindow',10))
    except:
        nWindow = 10
    try:
        stabClass = params.get('stabClass','D')
    except:
        stabClass = 'D'
    try:
        minLeak = float(params.get('minLeak',1.0))
    except:
        minLeak = 1.0
    try:
        minAmp = float(params.get('minAmp',0.05))
    except:
        minAmp = 0.05
    try:
        astdParams['a'] = float(params.get('astd_a',0.15*math.pi))
    except:
        astdParams['a'] = 0.15*math.pi
    try:
        astdParams['b'] = float(params.get('astd_b',0.25))
    except:
        astdParams['b'] = 0.25
    try:
        astdParams['c'] = float(params.get('astd_c',0.0))
    except:
        astdParams['c'] = 0.0
    try:
        name = genLatestFiles(*os.path.split(USERLOGFILES)).next()
    except:
        return {'filename':''}
    result = _makeSwath(name,startRow,limit,nWindow,stabClass,minLeak,minAmp,astdParams)
    result["filename"]=os.path.basename(name)
    return result
    
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

@app.route('/rest/getLastPeriphUpdate')
def rest_getLastPeriphUpdate():
    result = getLastPeriphUpdateEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))

def getLastPeriphUpdateEx(params):
    # Get the last timestamps of peripheral data
    DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = "AnalyzerServer")
    try:
        lastTimestamps = DataManager.Periph_GetLastTimestamps()
        currentTimestamp = getTimestamp()
        if len(lastTimestamps) > 0:
            for port in lastTimestamps:
                lastTimestamps[port] = currentTimestamp - lastTimestamps[port]
            return lastTimestamps
        else:
            return {}
    except:
        return dict(error=traceback.format_exc())

@app.route('/rest/ping')
def ping():
    return 'ping'
    
@app.route('/rest/admin')
def issueTicket():
    print "Ticket:", request.values
    ticket = 'abcdefghijkl'
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"ticket":ticket}) + ')')
    else:
        return make_response(json.dumps({"ticket":ticket}))
        
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
    app.run(host='0.0.0.0',port=5000,debug=DEBUG)
    