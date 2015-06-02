from flask import Flask
from flask import make_response, render_template, request
from Host.Utilities.BackpackServer.jsonrpc import JSONRPCHandler, Fault
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
USERLOGFILES = 'C:/UserData/Minimal/*.dat'

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

def _getData(fp,startRow):
    fp.seek(0,0)
    header = fp.readline().split()
    result = dict(CH4=[])
    lineLength = fp.tell()
    fp.seek(0,2)
    if fp.tell() < startRow*lineLength:
        startRow = 1
    fp.seek(startRow*lineLength,0)
    for line in fp:
        if len(line) != lineLength:
            break
        vals = line.split()
        if len(vals)!=len(header):
            break
        for col,val in zip(header,vals):
            if col in result: result[col].append(float(val))
        startRow += 1
    result['NEXT_ROW'] = startRow
    return result

@handler.register
@rpcWrapper
def getData(params):
    startRow = int(params.get('startRow',1))
    names = sorted(glob.glob(USERLOGFILES))
    try:
        name = names[-1]
        fp = file(name,'rb')
    except:
        return {'filename':''}
    result = _getData(fp,startRow)
    fp.close();
    ch4 = result["CH4"]
    nextRow = result["NEXT_ROW"]
    print nextRow
    return(dict(filename=name,ch4=ch4,nextRow=nextRow))

@app.route('/methane')
def data():
    return render_template('methane.html')

@app.route('/')
def hello():
    return render_template('methane.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)