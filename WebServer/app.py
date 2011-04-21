from flask import redirect, url_for, abort, render_template, flash, make_response
from flask import Flask, Response, request
from flaskext.jsonrpc import JSONRPCHandler, Fault

from Host.Common import timestamp
from Host.ActiveFileManager.ActiveFileManager import ActiveFile
import Host.ActiveFileManager.ActiveUtils as ActiveUtils
from numpy import *
from base64 import b64encode
from cPickle import loads, dumps, HIGHEST_PROTOCOL

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)
handler = JSONRPCHandler('jsonrpc')
handler.connect(app,'/jsonrpc')

def recArrayToDict(recArray):
    obj = {}
    for n in recArray.dtype.names:
        # N.B. MUST have float since numpy scalars do not JSON 
        #  serialize
        obj[n] = [float(v) for v in recArray[n]]
    return obj

@handler.register
def greet(name='world'):
    """Greet the name passed in as a parameter"""
    return "Hello, %s!" % name

@handler.register
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
    dmData = ActiveUtils.getDmData(mode,source,tstart,tstop,varList)
    if pickle:
        d = b64encode(dumps(dmData,HIGHEST_PROTOCOL))
    else:
        d = recArrayToDict(dmData)
    return d
    
@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) # ,threaded=True)
