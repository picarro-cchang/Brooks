from flask import redirect, url_for, abort, render_template, flash, make_response
from flask import Flask, Response, request
from jsonrpc import JSONRPCHandler, Fault

from Host.Common import timestamp
from Host.ActiveFileManager.ActiveFileManager import ActiveFile
import Host.ActiveFileManager.ActiveUtils as ActiveUtils
from numpy import *
from base64 import b64encode
from cPickle import loads, dumps, HIGHEST_PROTOCOL

import sys
import traceback
from functools import wraps



# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

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

def recArrayToDict(recArray):
    obj = {}
    for n in recArray.dtype.names:
        # N.B. MUST have float since numpy scalars do not JSON 
        #  serialize
        obj[n] = [float(v) for v in recArray[n]]
    return obj

@handler.register
@rpcWrapper
def getSensorData(params):
    # Get selected sensor outputs within a specified timestamp range
    # Keyword parameters are:
    # range:  A dictionary of start and stop timestamps
    # sensorList: A list of variable names to extract
    # pickle: If present and True, return a base64 encoded pickle rather
    #          than a plain JSON result
    # Result is a dictionary keyed by the sensor name. Values are record arrays 
    #  consisting of timestamps and values
    pickle = ('pickle' in params) and params['pickle']
    range = params['range']
    sensorList = [str(v) for v in params['sensorList']]
    tstart, tstop = range['start'], range['stop']
    d = {}
    for s in sensorList:
        data = ActiveUtils.getSensorData(tstart,tstop,s)
        d[s] = data if pickle else recArrayToDict(data)
    return b64encode(dumps(d,HIGHEST_PROTOCOL)) if pickle else d

@handler.register
@rpcWrapper
def getRdData(params):
    # Get selected ringdown outputs within a specified timestamp range
    # Keyword parameters are:
    # range:  A dictionary of start and stop timestamps
    # varList: A list of variable names to extract
    # pickle: If present and True, return a base64 encoded pickle rather
    #          than a plain JSON result
    # Result is a record array of selected columns
    pickle = ('pickle' in params) and params['pickle']
    range = params['range']
    varList = [str(v) for v in params['varList']]
    tstart, tstop = range['start'], range['stop']
    data = ActiveUtils.getRdData(tstart,tstop,varList)
    return b64encode(dumps(data,HIGHEST_PROTOCOL)) if pickle else recArrayToDict(data)
    
@handler.register
@rpcWrapper
def getDmData(params):
    # Get selected data manager outputs within a specified timestamp range
    # Keyword parameters are:
    # mode:   Analyzer mode
    # source: Source name to extract
    # range:  A dictionary of start and stop timestamps
    # varList: A list of variable names to extract
    # pickle: If present and True, return a base64 encoded pickle rather
    #          than a plain JSON result
    pickle = ('pickle' in params) and params['pickle']
    mode = params['mode']
    source = params['source']
    range = params['range']
    varList = [str(v) for v in params['varList']]
    tstart, tstop = range['start'], range['stop']
    data = ActiveUtils.getDmData(mode,source,tstart,tstop,varList)
    return b64encode(dumps(data,HIGHEST_PROTOCOL)) if pickle else recArrayToDict(data)

@handler.register
@rpcWrapper
def getLatestDmData(params):
    # Get selected data manager outputs within a specified timestamp range
    # Keyword parameters are:
    # mode:   Analyzer mode
    # source: Source name to extract
    # varList: A list of variable names to extract
    # pickle: If present and True, return a base64 encoded pickle rather
    #          than a plain JSON result
    pickle = ('pickle' in params) and params['pickle']
    mode = params['mode']
    source = params['source']
    varList = [str(v) for v in params['varList']]
    data = ActiveUtils.getLatestDmData(mode,source,varList)
    return b64encode(dumps(data,HIGHEST_PROTOCOL)) if pickle else recArrayToDict(data)
    
@handler.register
@rpcWrapper
def getRdDataStruct(params):
    # Get structure of ringdown data within a specified timestamp range
    # Keyword parameters are:
    # range:  A dictionary of start and stop timestamps
    # pickle: If present and True, return a base64 encoded pickle rather
    #          than a plain JSON result
    pickle = ('pickle' in params) and params['pickle']
    range = params['range']
    tstart, tstop = range['start'], range['stop']
    data = ActiveUtils.getRdDataStruct(tstart,tstop)
    return b64encode(dumps(data,HIGHEST_PROTOCOL)) if pickle else data

@handler.register
@rpcWrapper
def getDmDataStruct(params):
    # Get structure of data manager outputs within a specified timestamp range
    # Keyword parameters are:
    # range:  A dictionary of start and stop timestamps
    # pickle: If present and True, return a base64 encoded pickle rather
    #          than a plain JSON result
    pickle = ('pickle' in params) and params['pickle']
    range = params['range']
    tstart, tstop = range['start'], range['stop']
    data = ActiveUtils.getDmDataStruct(tstart,tstop)
    return b64encode(dumps(data,HIGHEST_PROTOCOL)) if pickle else data
    
@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) # ,threaded=True)
