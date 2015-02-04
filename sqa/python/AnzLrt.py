#!/usr/bin/python

'''
Created on Jan 29, 2014

@author: zlu
'''

from P3RestApi import P3RestApi
import P3RestAPITestHelper

class AnzLrt():
    
    resource = "AnzLrt"
    qryList = ["AnzLrt:getStatus", "AnzLrt:byRow", "AnzLrt:byRowFov"]
    
    res = {}
    qryobj = {}
    params = {}
    
    
    def __init__(self, *args, **kvargs):
        
        self.anz = kvargs['anz']
        self.alog = kvargs['alog']
        self.prmsHash = kvargs['prmsHash']
        self.startTs = kvargs['startTs']
        
        self.existing_tkt = kvargs['existing_tkt']
        self.doclist = kvargs['doclist']
        
        self.res['host'] = kvargs['host']
        self.res['port'] = kvargs['port']
        self.res['site'] = kvargs['site']
        self.res['identity'] = kvargs['identity']
        self.res['psys'] = kvargs['psys']
        self.res['svc'] = kvargs['svc']
        self.res['debug'] = kvargs['debug']
        self.res['version'] = kvargs['version']
        
        self.res['resource'] = self.resource
        self.res['rprocs'] = self.qryList
        
        self.row = kvargs['row']
        
        
    def get_getStatus(self, limit = 10):
        
        print "\n\n\nRunning %s get_getStatus(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
        
        self.qryobj['qry'] = 'getStatus'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['prmsHash'] = self.prmsHash
        self.qryobj['startTs'] = self.startTs
        
        self.qryobj['limit'] = self._get_limit(limit)
                
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj
        
        self._print_initialization(self.res, self.qryobj, self.params)
            
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        return self._print_rtnData(rtnData)
    
    
    def get_byRow_startRow0(self, limit = 10):
        
        print "\n\n\nRunning %s get_byRow_startRow0(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
            
        self.qryobj['qry'] = 'byRow'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['prmsHash'] = self.prmsHash
        self.qryobj['startTs'] = self.startTs
        self.qryobj['startRow'] = 0
        
        self.qryobj['limit'] = self._get_limit(limit)
                
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj
        
        self._print_initialization(self.res, self.qryobj, self.params)
            
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        return self._print_rtnData(rtnData)
    
        
    def get_byRowFov_startRow0(self, limit = 10):
        
        print "\n\n\nRunning %s get_byRowFov_startRow0(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
            
        self.qryobj['qry'] = 'byRowFov'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['prmsHash'] = self.prmsHash
        self.qryobj['startTs'] = self.startTs
        self.qryobj['startRow'] = 0
        
        self.qryobj['limit'] = self._get_limit(limit)

        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj
        
        self._print_initialization(self.res, self.qryobj, self.params)
        
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        if self.doclist == False:
            print '\nBug #608, P3 Rest API, "AnzLrt:byRowFov" returns "404 resource error" if set "doclist" to "False"'
             
        return self._print_rtnData(rtnData)
    
          
    def _print_initialization(self, res, qryobj, params):
        
        print ''
        print 'res: ', res
        print 'qryobj: ', qryobj
        print 'params: ', params

        
    def _print_rtnData(self, rtnData):        
        
        try:
            print "\ndoclist is %r" % (self.doclist)  
            print "\nrtnData: ", rtnData
            print ""
            return True
        except Exception, e:
            print "\n\nException (Error) on handling rtnData: ", e.message
        
        return False
    
    
    def _objectCleanUp(self):
        
        if len(self.qryobj) != 0:
            self.qryobj.clear()
            
        if len(self.params) != 0:
            self.params.clear()
                    
    
    def _get_limit(self, limit):        
        
        try:
            return int(limit)
        except ValueError:
            if limit.lower() == 'all':
                return 'all'
        except Exception, e:
            print "\n\nException (Error) on parsing 'limit': ", e.message
            
     
if __name__ == "__main__":
    
    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzLrt = AnzLrt(**testProp)
    
    anzLrt.get_getStatus()
    
    anzLrt.get_byRow_startRow0()
    
    anzLrt.get_byRowFov_startRow0()