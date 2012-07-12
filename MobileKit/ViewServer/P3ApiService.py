'''
P3ApiService - Get/Set Analyzer data logs (and metadata) via REST API
'''
import os
import sys
from optparse import OptionParser
import time
import datetime
import traceback

import urllib2
import urllib
import socket
try:
    import simplejson as json
except:
    import json

NaN = 1e1000/1e1000

class P3ApiService(object):
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self.anzlog_url = None    
        if 'anzlog_url' in kwargs:
            self.anzlog_url = kwargs['anzlog_url']
            
        self.csp_url = None    
        if 'csp_url' in kwargs:
            self.csp_url = kwargs['csp_url']

        self.ticket_url = None    
        if 'ticket_url' in kwargs:
            self.ticket_url = kwargs['ticket_url']
        
        self.identity = None
        if 'identity' in kwargs:
            self.identity = kwargs['identity']

        self.psys = None
        if 'psys' in kwargs:
            self.psys = kwargs['psys']

        self.sleep_seconds = None
        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds']:
                self.sleep_seconds = float(kwargs['sleep_seconds'])
        if self.sleep_seconds == None:
            self.sleep_seconds = 1.0

        self.timeout = None
        if 'timeout' in kwargs:
            if kwargs['timeout']:
                self.timeout = int(kwargs['timeout'])
        if self.timeout == None:
            self.timeout = 5

        self.debug = None
        if 'debug' in kwargs:
            self.debug = kwargs['debug']

        self.rprocs = None
        if 'rprocs' in kwargs:
            self.rprocs = kwargs['rprocs']

        self.qryparms = None
        if 'qryparms' in kwargs:
            self.qryparms = kwargs['qryparms']

        self.ticket = "NONE"
        self.sockettimeout = 10

            
    def getTicket(self):
        self.ticket = None
        ticket = None
        qry = "issueTicket"
        params = {
                  "qry": qry
                  , "sys": self.psys
                  , "identity": self.identity
                  , "rprocs": self.rprocs
                  }
        try:
            if self.debug:
                print "ticket_url", self.ticket_url
                
            resp = urllib2.urlopen(self.ticket_url, data=urllib.urlencode(params))
            rtndata_str = resp.read()
            rtndata = json.loads(rtndata_str)
            if "ticket" in rtndata:
                ticket = rtndata["ticket"]

        except urllib2.HTTPError, e:
            err_str = e.read()
            if self.debug:
                print '\nissueTicket failed \n%s\n' % err_str
                
        except Exception, e:
            if self.debug:
                print '\nissueTicket failed \n%s\n' % e

        if ticket:
            self.ticket = ticket;
            if self.debug:
                print "new ticket: ", self.ticket
        
    def get(self, svc, ver, rsc, qryparms_obj):
        
        #qryparms = ""
        #sep = ""
        #for prm,vlu in qryparms_obj.iteritems():
        #    qryparms = "%s%s%s=%s" %(qryparms,sep,prm,vlu)
        #    sep = "&"
            
        #if self.debug:
        #    print qryparms
            
        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            rtn_data = None
            rslt = None
            err_str = None
            try:
                #qry_with_ticket = '%s/rest/%s/%s/%s/%s?%s' % (self.csp_url, svc, self.ticket, ver, rsc, qryparms)
                qry_url = '%s/rest/%s/%s/%s/%s' % (self.csp_url, svc, self.ticket, ver, rsc)
                #qry_with_ticket = '%s?%s' % (self.csp_url.replace("<TICKET>", self.ticket), qryparms)
                if self.debug == True:
                    #print "qry_with_ticket: %s" %(qry_with_ticket)
                    print "qry_url: %s" %(qry_url)
                
                socket.setdefaulttimeout(self.sockettimeout)
                resp = urllib2.urlopen(qry_url, data=urllib.urlencode(qryparms_obj))
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
                        print 'EXCEPTION in P3ApiService - get.\n%s\n' % err_str
                    break
                
            except Exception, e:
                if self.debug:
                    print 'EXCEPTION in P3ApiService - get failed \n%s\n' % e
                
                time.sleep(self.sleep_seconds)
                continue
           
            if (rtn_data):
                rslt = json.loads(rtn_data)
                if self.debug == True:
                    print "rslt: ", rslt
                
                break
                
            if waitForRetry:
                time.sleep(self.timeout)
                
            waitForRetry = True
            
        return {
                "error": err_str
                , "return": rslt
                }
            
    def run(self):
        # Assemble the chain of generators which process the data from the logs in a file or in the database 
        # self.getTicket()
        result = self.get()
        return result



def main(argv=None):
    if argv is None:
        argv = sys.argv
        
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("--qryparms", dest="qryparms",
                      help="REST query parms (JSON String).", metavar="<QRYPARMS>")
    parser.add_option("--timeout", dest="timeout",
                      help="timeout value for response from server.", metavar="<TIMEOUT>")
    parser.add_option("--sleep-seconds", dest="sleep_seconds",
                      help="sleep seconds value. Time to pause between repetitive server requests.", metavar="<SLEEP>")
    parser.add_option("--svc", dest="svc",
                      help="Rest svc (service).", metavar="<SVC>")
    parser.add_option("--resource", dest="resource",
                      help="Rest Resource.", metavar="<RESOURCE>")
    parser.add_option("--resource-ver", dest="resource_ver",
                      help="Rest Resource Version.", metavar="<RSC_VER>")
    parser.add_option("--csp-url", dest="csp_url",
                      help="rest CSP url.", metavar="<LOG_URL>")
    parser.add_option("--ticket-url", dest="ticket_url",
                      help="rest url for authentication ticket. Use the string 'dummy' as the place-holder for the authentication ticket.",  metavar="<TICKET_URL>")
    parser.add_option("--identity", dest="identity",
                      help="Authentication identity string.", metavar="<IDENTITY>")
    parser.add_option("--sys", dest="psys",
                      help="Authentication sys.", metavar="<SYS>")
    parser.add_option("--rprocs", dest="rprocs",
                      help="Authentication rprocs.", metavar="<RPROCS>")
    parser.add_option("--debug", dest="debug", action="store_true",
                      help="Debug mode")
    
    (options, args) = parser.parse_args()

    if not options.csp_url:
        parser.error("Resource URL is required.")
    if not options.ticket_url:
        parser.error("Authentication ticket Resource URL is required.")
    if not options.identity:
        parser.error("Authentication identity string is required.")
    if not options.psys:
        parser.error("Authentication sys name is required.")
        
    class_opts = {}
    
    for copt in [
                 "qryparms"         #REST parameters (as string)
                 , "svc"            #REST service
                 , "resource"       #resource
                 , "resource_ver"   #resource version
                 , "csp_url"        #URL for resource
                 , "ticket_url"     #URL for Admin (issueTicket) resource
                 , "identity"       #identity (authentication)
                 , "psys"           #picarro sys (authentication)
                 , "rprocs"         #security rprocs string
                 , "sleep_seconds"  #override default sleep_seconds value
                 , "timeout"        #override default REST timeout value
                 , "debug"          #True/False show debug print (in stdout)
                 ]:
        if copt in dir(options):
            if copt in ["qryparms", "svc", "resource", "resource_ver"]:
                if copt == "qryparms":
                    qryparmstr = getattr(options, copt)
                    qryparms = eval(qryparmstr,{"__builtins__":None},{})
                else:
                    if copt == "resource":
                        resource = getattr(options, copt)
                    else:
                        if copt == "resource_ver":
                            resource_ver = getattr(options, copt)
                        else:
                            svc = getattr(options, copt)
            else:
                class_opts[copt] = getattr(options, copt)
        else:
            class_opts[copt] = None
    
    if "debug" in class_opts:
        if class_opts["debug"]:
            print "run options"
            for copt in class_opts:
                print "   ", copt, class_opts[copt]
            
            print "qryparms"
            for qopt in qryparms:
                print "  ", qopt, qryparms[qopt]
                
            print "query request"
            print "   resource: ", resource
            print "   resource_ver: ", resource_ver
            print "   service: ", svc
    
    pf = P3ApiService(**class_opts)
    print pf.get(svc, resource_ver, resource, qryparms)


if __name__ == "__main__":
    sys.exit(main())

