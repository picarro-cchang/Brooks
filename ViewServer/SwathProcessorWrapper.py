import SwathProcessor as swathp
from P3ApiService import P3ApiService
from gearman import GearmanWorker

try:
    import simplejson as json
except:
    import json

import sys
import datetime
import time

NaN = 1e1000/1e1000

P3Api = P3ApiService()

def stopRun(worker, job):
    print "stopRun requested"
    print "sys.exit() at: ", datetime.datetime.now()
    sys.exit()
    
# The function that will do the work
def makeSwath(worker, job):
    
    params = json.loads("%s" % job.data);
    #print "params: ", params
    source_params = params["sourceParams"];
    #source = params["source"]
    nWindow = params["nWindow"];
    stabClass = params["stabClass"];
    minLeak = params["minLeak"];
    minAmp = params["minAmp"];
    astdParams = params["astdParams"];
    
    #print "request: ", datetime.datetime.now();
    
    rtn_obj = _getData(source_params);
    
    if "error" in rtn_obj:
        return json.dumps(rtn_obj);
    
    else:
        if "source" in rtn_obj:
            #print rtn_obj
            return _makeSwath(rtn_obj,nWindow,stabClass,minLeak,minAmp,astdParams)

    return json.dumps({"error": "unexpected error in SwathProcessorWrapper!!"});
        
def _getData(getparms):
    # Making a swath requires 2*nWindow+1 points centered about
    #  each position, so to produce the swath at startRow, we need
    #  to fetch rows startRow-nWindow through startRow+nWindow.
    # We need to keep track of the rows that will have their swaths
    #  calculated by this call, so that result['nextRow'] can be 
    #  filled up.
    
    P3Api.csp_url = getparms["csp_url"]        #URL for resource
    P3Api.ticket_url = getparms["ticket_url"]  #URL for Admin (issueTicket) resource
    P3Api.identity = getparms["identity"]      #identity (authentication)
    P3Api.psys = getparms["psys"]              #picarro sys (authentication)
    P3Api.rprocs = getparms["rprocs"]          #security rprocs string
    
    source = []
    lastRow = 0

    rtn = P3Api.get(getparms["svc"], getparms["resource_ver"], getparms["resource"], getparms["qryparms"])
    if ("error" in rtn) and (rtn["error"] != None):
        return {"error": rtn["error"]}
    else:
        if "return" in rtn:
            for row in rtn["return"]:
                for  k in row.keys():
                    try:
                        row[k] = float(row[k])
                    except:
                        row[k] = NaN
                
                if "row" in row:
                    lastRow = row["row"]
                    
                source.append(row)
                
    filename = getparms["qryparms"]["alog"]       
    return {"source": source, "lastRow": lastRow, "filename": filename}
    
def _makeSwath(source_obj,nWindow,stabClass,minLeak,minAmp,astdParams):
    source = source_obj["source"]
    lastRow = source_obj["lastRow"]
    sp_result = swathp.process(source,nWindow,stabClass,minLeak,minAmp,astdParams)
    sp_result['nextRow'] = lastRow-nWindow
    sp_result['filename'] = source_obj["filename"]
    result = json.dumps(sp_result)
    #print "result: ", result
    return result
    
    
worker = GearmanWorker(['127.0.0.1'])
worker.register_task('makeSwath', makeSwath)
worker.register_task('stopRun', stopRun)

print 'working...'
worker.work()
