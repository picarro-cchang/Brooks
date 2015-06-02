from flask import Flask
from flask import make_response, render_template, request
from Host.Utilities.MobileKit.AnalyzerServer.jsonrpc import JSONRPCHandler, Fault
from functools import wraps
import glob
import os
import sys
import time
import traceback

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# Default shift between GPS and concentration data
#  This is a property of the analyzer and should not
#  be changed by the viewers. Later we should read this
#  from an InstrConfig variable
SHIFT = -7
USERLOGFILES = 'static/datalog/*.dat'
app = Flask(__name__)
app.config.from_object(__name__)
handler = JSONRPCHandler('jsonrpc')
handler.connect(app,'/jsonrpc')

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
        while True:
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
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'lastPos':0, 'filename':''}

    if 'startPos' in params:
        startPos = int(params['startPos'])
    else:
        startPos = None
    shift = int(params.get('shift',SHIFT))
    result,lastPos = _getData(fp,startPos,shift)
    result['filename'] = os.path.basename(name)
    result['lastPos'] = lastPos
    return result

@handler.register
@rpcWrapper
def getPos():
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
def getLastDataRows(params):
    numRows = int(params.get('numRows',1))
    shift = int(params.get('shift',SHIFT))
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'filename':''}
    result = _getLastDataRows(fp,numRows,shift)
    result['filename'] = os.path.basename(name)
    return result

@handler.register
@rpcWrapper
def getPath(params):
    numRows = int(params.get('numRows',1))
    shift = int(params.get('shift',SHIFT))
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'filename':''}
    result = _getLastDataRows(fp,numRows,shift)
    epochTime, long, lat, ch4 = result["EPOCH_TIME"], result["GPS_ABS_LONG"], result["GPS_ABS_LAT"], result["CH4"]
    peakPos = ch4.index(max(ch4))
    timeStrings = [time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(t)) for t in epochTime]
    return(dict(long=long,lat=lat,ch4=ch4,timeStrings=timeStrings,peakPos=peakPos))

@handler.register
@rpcWrapper
def restartDatalog(params):
    print "<------------------ Restarting data log ------------------>"
    return {}

@handler.register
@rpcWrapper
def getDateTime(params):
    print time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    return(dict(dateTime=time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())))

@app.route('/maps')
def maps():
    threshold = float(request.values.get('threshold',2.5))
    return render_template('maps.html',threshold=threshold)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)