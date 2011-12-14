from flask import Flask
from flask import make_response, render_template, request
from jsonrpc import JSONRPCHandler, Fault
try:
    import simplejson as json
except:
    import json
from functools import wraps
import glob
import itertools
import linecacheCopy as linecache
import os
import sys
from threading import Thread
import time
import traceback
import CmdFIFO
from SharedTypes import RPC_PORT_DATALOGGER, RPC_PORT_DRIVER, RPC_PORT_INSTR_MANAGER
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

# Default shift between GPS and concentration data
#  This is a property of the analyzer and should not
#  be changed by the viewers. Later we should read this
#  from an InstrConfig variable
SHIFT = -4
USERLOGFILES = 'C:/UserData/AnalyzerServer/*.dat'
PEAKFILES = 'C:/UserData/AnalyzerServer/*.peaks'
ANALYSISFILES = 'C:/UserData/AnalyzerServer/*.analysis'

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
    # DISTANCE        Distance along path at which maxima are located
    # GPS_ABS_LONG    Longitude of maxima
    # GPS_ABS_LAT     Latitude of maxima
    # CONC            Methane concentration at peak
    # DELTA           Isotopic ratio value
    # UNCERTAINTY     Uncertainty in delta
    # NEXT_ROW        Next row in file which has yet to be processed
    #
    # N.B. Rows start at zero, whereas linecache starts lines at 1
    header = linecache.getline(name,1).split()
    result = dict(DISTANCE=[],GPS_ABS_LONG=[],GPS_ABS_LAT=[],CONC=[],DELTA=[],UNCERTAINTY=[])
    for lineNum in range(startRow+1,startRow+20):
        line = linecache.getline(name,lineNum)
        if not line: break
        vals = line.split()
        if len(vals) != len(header): break
        for col,val in zip(header,vals):
            if col in result: result[col].append(float(val))
        startRow += 1
    result['NEXT_ROW'] = startRow
    return result
    
def _getPeaks(name,startRow,minAmp):
    #
    # Gets data from the analyzer peak parameters file "name" starting  at the specified 
    #  "startRow" within the file. Only peaks of amplitude no less than "minAmp" are 
    #  reported. The result dictionary has keys:
    # DISTANCE        Distance along path at which maxima are located
    # GPS_ABS_LONG    Longitude of maxima
    # GPS_ABS_LAT    Latitude of maxima
    # CH4            Methane concentration of maxima
    # AMPLITUDE     Amplitudes calculated from space-scale representation
    # SIGMA            Half-widths calculated from space-scale representation
    # NEXT_ROW        Next row in file which has yet to be processed
    #
    # N.B. Rows start at zero, whereas linecache starts lines at 1
    header = linecache.getline(name,1).split()
    amplCol = header.index("AMPLITUDE")
    result = dict(DISTANCE=[],GPS_ABS_LONG=[],GPS_ABS_LAT=[],CH4=[],AMPLITUDE=[],SIGMA=[])
    if amplCol<0:
        print "Cannot find AMPLITUDE column in peak file"
        result['NEXT_ROW'] = startRow
        return result
    for lineNum in range(startRow+1,startRow+20):
        line = linecache.getline(name,lineNum)
        if not line: break
        vals = line.split()
        if len(vals) != len(header): break
        if float(vals[amplCol]) >= minAmp:
            for col,val in zip(header,vals):
                if col in result: result[col].append(float(val))
        startRow += 1
    result['NEXT_ROW'] = startRow
    return result
        
def _getData(fp,startPos=None,shift=0):    
    #
    # Gets data from the analyzer live archive file "fp" starting  at the specified 
    #  position "startPos" within the file. It is also possible to specify a 
    #  "shift" for aligning the GPS data with the concentration data. By convention
    #  a NEGATIVE shift associates concentration data with EARLIER GPS data. Any
    #  columns whose names start with "GPS" are shifted in this way.
    #
    # If shift is negative, "startPos" is the position in the file of the GPS data
    # If shift is positive, "startPos" is the position in the file of the concentration data
    #
    # We collect "posList" which indicates the position in the file of the start of
    #  each row of data. There are corresponding lists for GPS variables and non-GPS
    #  variables. If we read nRows of data from the file, we can only report 
    #  nRows-abs(shift) rows back to the caller. If nRows<abs(shift), we return nothing.
    #
    # For shift>0, we report GPS[shift:] and nonGPS[:-shift] and return lastPos = posList[-shift-1]
    # For shift<0, we report GPS[:shift] and nonGPS[-shift:] and return lastPos = posList[shift-1]
    # For shift==0, we report GPS[:] and nonGPS[:] and return lastPos = posList[-1]
    #
    try:
        fp.seek(0,0)
        header = fp.readline().split()
        columns = [[] for i in range(len(header))]
        if startPos is not None:
            fp.seek(startPos,0)
        startPos = fp.tell()
        posList = [startPos]
        for l in range(100):
            line = fp.readline()
            if not line: break
            vals = line.split()
            if len(vals)!=len(header): break
            posList.append(fp.tell())
            for col,val in zip(columns,vals):
                col.append(float(val))
        posList = posList[:-1]
        nRows = len(columns[0])
        result = {}
        if nRows>=abs(shift):
            if shift>0:
                for col,h in zip(columns,header):
                    if h.startswith('GPS'):
                        result[h] = col[shift:]
                    else:
                        result[h] = col[:-shift]
                lastPos = posList[-shift-1]
            elif shift<0:
                for col,h in zip(columns,header):
                    if h.startswith('GPS'):
                        result[h] = col[:shift]
                    else:
                        result[h] = col[-shift:]
                lastPos = posList[shift-1]
            else:
                for col,h in zip(columns,header):
                    result[h] = col
                lastPos = posList[-1]
        else:
            for col,h in zip(columns,header):
                result[h] = []
            lastPos = startPos
        epochTime = result['EPOCH_TIME']
        result['timeStrings'] = [time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) for t in epochTime]
        return result, lastPos
    except:
        print traceback.format_exc()
    finally:
        fp.close()

def _getLastDataRows(fp,numRows=1,shift=0):        
    # Gets the last numRows of data from 
    fp.seek(0,0)
    header = fp.readline()
    linelen = len(header)
    firstData = fp.tell()
    fp.seek(0,2)
    endData = fp.tell()
    startPos = max(firstData,endData-(numRows+abs(shift)+1)*linelen)
    result,lastPos = _getData(fp,startPos,shift)
    for h in result:
        result[h] = (result[h])[-numRows:]
    return result
    
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
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'lastPos':0, 'filename':''}
        
    if 'startPos' in params and (params['startPos'] is not None) and (params['startPos'] != "null"):
        try:
            startPos = int(params['startPos'])
        except:
            startPos = None
    else:
        startPos = None
    shift = int(params.get('shift',SHIFT))

    try:
        result,lastPos = _getData(fp,startPos,shift)
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
    result = getPosEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
    
def getPosEx():
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'filename':''}
    try:
        header = fp.readline()
        linelen = len(header)
        header = header.split()
        result = {'filename':os.path.basename(name)}
        fp.seek(-3*linelen,2)
        fp.readline()
        for line in fp.readlines():
            vals = line.split()
            if len(vals)!=len(header): break
            for h,val in zip(header,vals):
                result[h] = float(val)
        return result
    finally:
        fp.close()
    
@handler.register
@rpcWrapper
def getPath(params):
    return getPathEx(params)
    
@app.route('/rest/getPath')
def rest_getPath():
    result = getPathEx(request.values)
    if 'callback' in request.values:
        return make_response(request.values['callback'] + '(' + json.dumps({"result":result}) + ')')
    else:
        return make_response(json.dumps({"result":result}))
        
def getPathEx(params):
    numRows = int(params.get('numRows',1))
    shift = int(params.get('shift',SHIFT))
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'filename':''}

    try:
        result = _getLastDataRows(fp,numRows,shift)
    except:
        result = _getLastDataRows(fp,numRows,shift)
    
    epochTime, long, lat, ch4 = result["EPOCH_TIME"], result["GPS_ABS_LONG"], result["GPS_ABS_LAT"], result["CH4"]
    peakPos = ch4.index(max(ch4))
    timeStrings = [time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) for t in epochTime]
    return(dict(long=long,lat=lat,ch4=ch4,timeStrings=timeStrings,peakPos=peakPos))

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
    names = sorted(glob.glob(PEAKFILES))
    try:
        name = names[-1]
    except:
        return {'filename':''}
    linecache.checkcache(name)
    result = _getPeaks(name,startRow,minAmp)
    dist, long, lat = result["DISTANCE"], result["GPS_ABS_LONG"], result["GPS_ABS_LAT"] 
    ch4, amp, sigma = result["CH4"], result["AMPLITUDE"], result["SIGMA"]
    nextRow = result["NEXT_ROW"]
    return(dict(filename=name,dist=dist,long=long,lat=lat,ch4=ch4,amp=amp,sigma=sigma,nextRow=nextRow))

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
    names = sorted(glob.glob(ANALYSISFILES))
    try:
        name = names[-1]
    except:
        return {'filename':''}
    linecache.checkcache(name)
    result = _getAnalysis(name,startRow)
    dist, long, lat = result["DISTANCE"], result["GPS_ABS_LONG"], result["GPS_ABS_LAT"] 
    conc, delta, uncertainty = result["CONC"], result["DELTA"], result["UNCERTAINTY"]
    nextRow = result["NEXT_ROW"]
    return(dict(filename=name,dist=dist,long=long,lat=lat,conc=conc,delta=delta,
                uncertainty=uncertainty,nextRow=nextRow))
                
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

def driverRpcEx(params):
    # Call any RPC function on the driver by passing
    #  params['func'] = name of Driver RPC function to call (as a string)
    #  params['args'] = string which evaluates to a list of positional arguments for the RPC function
    #  params['kwargs'] = string which evaluates to a dictionary of keyword arguments for the RPC function
    Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "AnalyzerServer")
    try:
        return dict(value=getattr(Driver,params['func'])(*eval(params.get('args','()'),{}),**eval(params.get('kwargs','{}'))))
    except:
        return dict(error=traceback.format_exc())

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
@app.route('/layout2')
def layout2():
    return render_template('layout2.html')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
    