'''
P3RestApi - Get/Set Analyzer data logs (and metadata) via REST API
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
NONE = "NONE"
ERROR = "ERROR"

class P3RestApi(object):
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self.host = None
        if 'host' in kwargs:
            self.host = kwargs['host']
            
        self.port = None
        if 'port' in kwargs:
            if kwargs['port']:
                self.port = int(kwargs['port'])
        #if self.port == None:
        #    self.port = 80
            
        self.site = None
        if 'site' in kwargs:
            self.site = kwargs['site']
            
        self.identity = None
        if 'identity' in kwargs:
            self.identity = kwargs['identity']

        self.psys = None
        if 'psys' in kwargs:
            self.psys = kwargs['psys']

        self.rprocs = None
        if 'rprocs' in kwargs:
            if kwargs['rprocs']:
                self.rprocs = kwargs['rprocs']
        if type(self.rprocs) == "str":
            self.rprocs = json.loads(self.rprocs)
            
        self.svc = None
        if 'svc' in kwargs:
            self.svc = kwargs['svc']
            
        self.version = None
        if 'version' in kwargs:
            self.version = kwargs['version']
        if self.version == None:
            self.version = '1.0'
            
        self.resource = None
        if 'resource' in kwargs:
            self.resource = kwargs['resource']
            
        self.max_auth_attempts = None
        if 'max_auth_attempts' in kwargs:
            if kwargs['max_auth_attempts']:
                self.max_auth_attempts = int(kwargs['max_auth_attempts'])
        if self.max_auth_attempts == None:
            self.max_auth_attempts = 5
            
        self.sleep_seconds = None
        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds']:
                self.sleep_seconds = float(kwargs['sleep_seconds'])
        if self.sleep_seconds == None:
            self.sleep_seconds = 1.0

        self.api_timeout = None
        if 'api_timeout' in kwargs:
            if kwargs['api_timeout']:
                self.api_timeout = int(kwargs['api_timeout'])
        if self.api_timeout == None:
            self.api_timeout = 5

        self.debug = None
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
            
        self.api_ticket = NONE;

        missing_required = False
        emsg = ""
        esep = ""
        if not self.host:
            emsg += esep + "host is required."
            esep = "\n"
            missing_required = True
        if not self.site:
            emsg += esep + "site is required."
            esep = "\n"
            missing_required = True
        if not self.identity:
            emsg += esep + "identity is required."
            esep = "\n"
            missing_required = True
        if not self.psys:
            emsg += esep + "psys is required."
            esep = "\n"
            missing_required = True
        if not self.rprocs:
            emsg += esep + "rprocs is required."
            esep = "\n"
            missing_required = True
        if not self.svc:
            emsg += esep + "svc is required."
            esep = "\n"
            missing_required = True
        if not self.resource:
            emsg += esep + "resource is required."
            esep = "\n"
            missing_required = True
            
        if missing_required == True:
            raise RuntimeError, "%s" % (emsg)   
        

    def _httpRequestFn(self, request_obj):
        
        if self.debug == True:
            print "\nP3RestApi.py _httpRequestFn\n"
            
        my_url = ""
        if (self.port == 443):
            my_url += "https://"
            my_url += self.host
        else:
            my_url += "http://"
            my_url += self.host
            
            if self.port:
                my_url += ":%s" % (self.port)
            
        my_url += request_obj["path"]        
        
        if self.debug == True:
            print "P3RestApi.py my_url: ", my_url

        try:
            if "data" in request_obj:
                jdata = {"data": json.dumps(request_obj["data"])}
                enc_data = urllib.urlencode(jdata)
                
                if self.debug:
                    print "P3RestApi.py urlencode data: ", enc_data
                    
                resp = urllib2.urlopen(my_url, data=enc_data)
            else:
                resp = urllib2.urlopen(my_url)
            
            rtndata_str = resp.read()
            rtndata = json.loads(rtndata_str)
            return (200, rtndata)

        except urllib2.HTTPError, e:
            err_str = e.read()
            rcode = e.code
            if self.debug:
                print '\nP3RestApi.py HTTP request failed \n%s\n' % err_str
                
        except Exception, e:
            err_str = e
            rcode = 999
            if self.debug:
                print '\nP3RestApi.py HTTP request failed \n%s\n' % e

        return (rcode, "%s" %(err_str))
    
    def _getTicket(self):
        
        if self.debug == True:
            print "\nP3RestApi.py _getTicket\n"
            
        self.api_ticket = NONE
        
        path = "/%s/rest/%s/%s/%s/%s" % (self.site
                                         , "sec"
                                         , self.api_ticket
                                         , self.version
                                         , "Admin")

        params = {
            "qry": "issueTicket",
            "sys": self.psys,
            "identity": self.identity,
            "rprocs": json.dumps(self.rprocs)
        }
        
        path += "?%s" % urllib.urlencode(params)
                
        eobj = {}
        rtndata = self._httpRequestFn({"path": path})

        if rtndata[0] == 200:
            self.api_ticket = rtndata[1]["ticket"]
            
            if self.debug:
                print "P3RestApi.py new ticket: ", self.api_ticket
            
            return True
        else:
            self.api_ticket = ERROR
            eobj["rtn"] = rtndata
            
        eobj["msg"] = "ERROR No Ticket Returned"
        
        return eobj
    
    def get(self, params, resourcePath = None):
        
        if self.debug == True:
            print "\nP3RestApi.py get\n"
            

        tkt_cntl_max = self.max_auth_attempts
        tkt_cntl_err = None;
        tkt_cntl_acount = 0;
        tkt_cntl_ecount = 0;
        tkt_cntl_OK = False;
        
        if "existing_tkt" in params:
            use_existing_tkt = params["existing_tkt"]
        else:
            use_existing_tkt = True
        
        while tkt_cntl_acount < tkt_cntl_max:
            if tkt_cntl_ecount >= 1:
                sleep_sec = self.sleep_seconds
            else:
                sleep_sec = 0

            tkt_ok = False
            if use_existing_tkt == True:
                use_existing_tkt = False
                
                if (not self.api_ticket == NONE) and (not self.api_ticket == ERROR):
                    #Try with the existing ticket
                    
                    if not resourcePath:
                        path = "/%s/rest/%s/%s/%s/%s" % (self.site
                                                     , self.svc
                                                     , self.api_ticket
                                                     , self.version
                                                     , self.resource)
                    else:
                        path = "/%s/rest/%s/%s/%s/%s/%s" % (self.site
                                                     , self.svc
                                                     , self.api_ticket
                                                     , self.version
                                                     , self.resource
                                                     , resourcePath)
                  
                    if "qryobj" in params:
                        sep = "?"
                        for ky in params["qryobj"]:
                            path += sep + ky + "=" + "%s" % params["qryobj"][ky]
                            sep = "&"
                    
                    getrsp = self._httpRequestFn({"path": path})
                    
                    if getrsp[0] == 200:
                        ## Good data so return
                        return getrsp
                    
                    else:
                        if type(getrsp[1] == "str"):
                            if "invalid ticket" in getrsp[1]:
                                tktrsp = {"msg": getrsp[1]}
                                
                            else:
                                ## error, but not a ticket error, so return
                                return getrsp
                                
                else:
                    # try to get a ticket
                    
                    tkt_cntl_acount += 1
                    tktrsp = self._getTicket()
                    if tktrsp == True:
                        tkt_ok = True;
                        
            else:
                # try to get a ticket
                    
                tkt_cntl_acount += 1
                tktrsp = self._getTicket()
                if tktrsp == True:
                    tkt_ok = True;
            
            if tkt_ok == True:
                if not resourcePath:
                    path = "/%s/rest/%s/%s/%s/%s" % (self.site
                                                 , self.svc
                                                 , self.api_ticket
                                                 , self.version
                                                 , self.resource)
                else:
                    path = "/%s/rest/%s/%s/%s/%s/%s" % (self.site
                                                 , self.svc
                                                 , self.api_ticket
                                                 , self.version
                                                 , self.resource
                                                 , resourcePath)
                
                if "qryobj" in params:
                    sep = "?"
                    for ky in params["qryobj"]:
                        path += sep + ky + "=" + "%s" % params["qryobj"][ky]
                        sep = "&"
                
                getrsp = self._httpRequestFn({"path": path})
                
                return getrsp
            
            else:
                # bad ticket attempt.  wait a bit and try again
                
                tkt_cntl_err = tktrsp
                tkt_cntl_ecount += 1
            
            time.sleep(sleep_sec)
        
        return tkt_cntl_err
            
    def post(self, params):
        
        if self.debug == True:
            print "\nP3RestApi.py post\n"
            
        tkt_cntl_max = self.max_auth_attempts
        tkt_cntl_err = None;
        tkt_cntl_acount = 0;
        tkt_cntl_ecount = 0;
        tkt_cntl_OK = False;
        
        if "existing_tkt" in params:
            use_existing_tkt = params["existing_tkt"]
        else:
            use_existing_tkt = True
        
        while tkt_cntl_acount < tkt_cntl_max:
            if tkt_cntl_ecount >= 1:
                sleep_sec = self.sleep_seconds
            else:
                sleep_sec = 0

            tkt_ok = False
            if use_existing_tkt == True:
                use_existing_tkt = False
                
                if (not self.api_ticket == NONE) and (not self.api_ticket == ERROR):
                    
                    #Try with the existing ticket
                    path = "/%s/rest/%s/%s/%s/%s" % (self.site
                                                     , self.svc
                                                     , self.api_ticket
                                                     , self.version
                                                     , self.resource)
                    
                    if "dataobj" in params:
                        data = params["dataobj"] #json.dumps(params["dataobj"])
                        if self.debug:
                            print "P3RestApi.py dataobj: ", data
                    
                    getrsp = self._httpRequestFn({"path": path, "data": data})
                    
                    if getrsp[0] == 200:
                        ## Good data so return
                        return getrsp
                    
                    else:
                        if type(getrsp[1] == "str"):
                            if "invalid ticket" in getrsp[1]:
                                tktrsp = {"msg": getrsp[1]}
                                
                            else:
                                ## error, but not a ticket error, so return
                                return getrsp
                                
                else:
                    # try to get a ticket
                    
                    tkt_cntl_acount += 1
                    tktrsp = self._getTicket()
                    if tktrsp == True:
                        tkt_ok = True;
                        
            else:
                # try to get a ticket
                
                tkt_cntl_acount += 1
                tktrsp = self._getTicket()
                if tktrsp == True:
                    tkt_ok = True;
            
            if tkt_ok == True:
                path = "/%s/rest/%s/%s/%s/%s" % (self.site
                                                 , self.svc
                                                 , self.api_ticket
                                                 , self.version
                                                 , self.resource)
                
                if "dataobj" in params:
                    data = params["dataobj"]
                
                getrsp = self._httpRequestFn({"path": path, "data": data})
                
                return getrsp
            
            else:
                # bad ticket attempt.  wait a bit and try again
                
                tkt_cntl_err = tktrsp
                tkt_cntl_ecount += 1
            
            time.sleep(sleep_sec)
        
        return tkt_cntl_err
