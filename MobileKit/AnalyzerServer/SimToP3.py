'''
SimToP3.py - Spawns DatEchoP3 to send a collection of files to P3
'''
from glob import glob
import numpy as np
import os
import re
import sys
import time
import subprocess
from P3ApiService import P3ApiService
try:
    import json
except:
    import simplejson as json

from Host.Common.configobj import ConfigObj

VER = "1.0"
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    appPath = sys.executable
else:
    appPath = sys.argv[0]

# Here are the regular expressions for various data types
typeRegex = {"dat" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_User_Minimal\.dat)$"""),
             "peaks" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_User_Minimal\.peaks)$"""),
             "analysis" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_User_Minimal\.peaks)$"""),
             "GPS_Raw" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_GPS_Raw\.dat)$"""),
             "WS_Raw" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_WS_Raw\.dat)$""")}

def getLogtype(logName):
    for dt in typeRegex:
        if typeRegex[dt].search(logName):
            return dt
    else:
        raise ValueError("Unknown logtype: %s" % logName)

if __name__ == "__main__":
    P3Api = P3ApiService()
    callParams = []
    # The configuration filename is the same as the executable, except that it has an 
    #  extension of .ini
    basePath = os.path.split(appPath)[0]
    configFile = os.path.splitext(appPath)[0] + ".ini"
    config = ConfigObj(configFile)
    params = config["SIMTOP3"]
    # Number to lines to send as a block each time to Pcubed
    nlines = int(params.get("nlines",10))
    # Seconds to wait between blocks
    wait = float(params.get("wait",0.1))
    
    baseUrl = params["baseurl"]
    csp = params["csp"]
    # Get the parameters for P3ApiService
    P3Api.csp_url = "https://" + "/".join([baseUrl,csp])
    P3Api.ticket_url = "https://" + "/".join([baseUrl,csp,"rest","sec","dummy",VER,"Admin"])
    P3Api.identity = params["identity"]
    P3Api.psys = params["sys"]
    P3Api.rprocs = '["AnzLog:data"]'
    P3Api.debug = True
    
    fileName = os.path.join(basePath,params["file"])
    fp = file(fileName,"rb")
    if not fp:
        raise ValueError("Cannot open file: %s" % fileName)
    logName = os.path.basename(fileName)
    dt = getLogtype(logName)
    headers = None
    rowctr = 0
    docs = []
    replaceFlag = 1
    for line in fp:
        if not line: continue
        rowctr += 1
        if headers is None:
            headers = line.split()
        else:
            vals = line.split()
            if len(vals) != len(headers):
                print "LEN ERROR", len(vals), len(headers)
                print line
                continue
            doc = {}
            for col,val in zip(headers,vals):
                try:
                    v = float(val)
                    if np.isfinite(v):
                        doc[col] = v
                    else:
                        doc[col] = "NaN"
                except:
                    doc[col] = "NaN"
            doc['row'] = rowctr
            docs.append(doc)
            if rowctr % nlines == 0:
                params = [{"logname": logName, "replace": replaceFlag, "logtype": dt, "logdata": docs}]
                postparms = {'data': json.dumps(params)}
                while True:
                    row, result = rowctr,P3Api.get("gdu", "1.0", "AnzLog", postparms)
                    if result['return'] == 'OK': break
                    time.sleep(1.0)
                print "At row %d" % (row,)
                time.sleep(wait)
                replaceFlag = 0
                docs = []
    fp.close()
