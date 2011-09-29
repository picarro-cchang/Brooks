from flask import Flask
from flask import make_response, render_template, request
from jsonrpc import JSONRPCHandler, Fault
from functools import wraps
from collections import deque
import glob
import os
from Queue import Queue
import sys
from threading import Thread
import time
import traceback
import types
from Host.Common import CmdFIFO, SharedTypes
from Host.autogen import interface
from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, Singleton
from Host.Common.StringPickler import ArbitraryObject
from Host.Common.timestamp import getTimestamp, timestampToUtcDatetime

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
USERLOGFILES = os.path.join(AppDir,'static/datalog/*.dat')

app = Flask(__name__)
app.config.from_object(__name__)
handler = JSONRPCHandler('jsonrpc')
handler.connect(app,'/jsonrpc')

class DataManagerInterface(Singleton):
    initialized = False
    maxHistory = 100
    def __init__(self, configPath=None):        
        if not self.initialized:
            self.dmQueue = Queue(0)
            self.dmListener = Listener.Listener(self.dmQueue,
                                                BROADCAST_PORT_DATA_MANAGER,
                                                ArbitraryObject,
                                                retry = True,
                                                name = "Display server listener")
        self.recentData = deque()
        self.collectThread = Thread(target = self.saveLatest)
        self.collectThread.setDaemon(True)
        self.collectThread.start()
        
    def saveLatest(self):
        while True:
            d = self.dmQueue.get()
            ts, mode, source = d['data']['timestamp'], d['mode'], d['source']
            status_fields = []
            if source == 'analyze_CH4nowlm': 
                tsAsString = timestampToUtcDatetime(ts).strftime('%Y%m%dT%H%M%S') + '.%03d' % (ts % 1000,)
                status_fields.append(tsAsString)
                status_fields.append('DATA')
                dd = d['data']
                self.recentData.append(dd.copy())
                if len(self.recentData) > self.maxHistory:
                    self.recentData.popleft()

dataManager = DataManagerInterface()
                    
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

@handler.register
@rpcWrapper
def getLatestData(params):
    if len(dataManager.recentData):
        return dataManager.recentData[-1]
    else:
        return {}

@app.route('/data')
def data():
    return render_template('data.html')

@app.route('/')
def hello():
    return 'Hello world'
   
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
