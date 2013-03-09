from collections import namedtuple
import hashlib
try:
    import json
except:
    import simplejson as json
import socket
import socket
import time
import urllib
import urllib2

PROJECT_SUBMISSION_PORT = 5201
JOB_DISTRIBUTION_PORT = 5202
JOB_COMPLETE_PORT = 5203
PROJECT_MANAGER_CMD_PORT = 5204
STOP_WORKERS_PORT = 5205
RESOURCE_MANAGER_PORT = 5221

ResourceTuple = namedtuple("ResourceTuple",["ticket","type","region"])        
ResponseTuple = namedtuple("ResponseTuple",["type","data"])
MapRect = namedtuple("MapRect",["swCorner","neCorner"])
LatLng  = namedtuple("LatLng", ["lat","lng"])

def getTicket(contents):
    return hashlib.md5(contents).hexdigest()

class ReportApiService(object):
    def __init__(self, *args, **kwargs):
        self.sockettimeout = 10
        self.csp_url = None    
        if 'csp_url' in kwargs: self.csp_url = kwargs['csp_url']
        self.sleep_seconds = None
        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds']:
                self.sleep_seconds = float(kwargs['sleep_seconds'])
        if self.sleep_seconds == None: self.sleep_seconds = 1.0
        self.ticket = 'None'
        self.debug = False
    def getTicket(self):
        print "Not implemented"
    def get(self, svc, ver, rsc, qryparms_obj):
        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            rtn_data = None
            rslt = None
            err_str = None
            try:
                assert 'qry' in qryparms_obj
                qry = qryparms_obj['qry']
                del qryparms_obj['qry']
                data = urllib.urlencode(qryparms_obj)
                qry_url = '%s/rest/%s?%s' % (self.csp_url,qry,data)
                if self.debug == True: print "qry_url: %s" %(qry_url)
                socket.setdefaulttimeout(self.sockettimeout)
                resp = urllib2.urlopen(qry_url)
                info = resp.info()
                rtn_data = resp.read()
                
            except urllib2.HTTPError, e:
                err_str = e.read()
                if "invalid ticket" in err_str:
                    if self.debug == True:
                        print "We Have an invalid or expired ticket"
                    self.getTicket()
                    waitForRetryCtr += 1
                    if waitForRetryCtr < 100:
                        waitForRetry = None
                else:
                    if self.debug == True:
                        print 'EXCEPTION in ReportApiService - get.\n%s\n' % err_str
                    info = {}
                    break
                
            except Exception, e:
                if self.debug:
                    print 'EXCEPTION in ReportApiService - get failed \n%s\n' % e
                
                time.sleep(self.sleep_seconds)
                continue
           
            if (rtn_data):
                if 'json' in info['content-type']:
                    rslt = json.loads(rtn_data)
                    if self.debug == True:
                        print "rslt: ", rslt
                else:
                    print "rslt of type: ", info['content-type']
                    rslt = rtn_data
                break
                
            if waitForRetry: 
                time.sleep(self.timeout)
                print "Looping"
            waitForRetry = True
            
        return { "error": err_str, "return": rslt, "info": dict(info.items()) }
