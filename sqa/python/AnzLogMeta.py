#!/usr/bin/python

'''
Created on Jan 22, 2014

@author: zlu
'''

from P3RestApi import P3RestApi
import P3RestAPITestHelper

class AnzLogMeta():
    
    resource = "AnzLogMeta"
    qryList = ["AnzLogMeta:byEpoch", "AnzLogMeta:resource"]
    
    res = {}
    qryobj = {}
    params = {}
    
    def __init__(self, *args, **kvargs):

        self.anz = kvargs['anz']
        self.alog = kvargs['alog']
        self.fnm = kvargs['fnm']
        
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

        
    def get_byEpoch_alog_startEtm0(self, limit = 10):
        
        print "\n\n\nRunning %s get_byEpoch_alog_startEtm0(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
            
        self.qryobj['qry'] = 'byEpoch'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['alog'] = self.alog
        self.qryobj['startEtm'] = 0
        
        self.qryobj['limit'] = self._get_limit(limit)
                
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj

        self._print_initialization(self.res, self.qryobj, self.params)
             
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        return self._print_rtnData(rtnData)
            
            
    def get_byEpoch_anz_startEtm0(self, limit = 10):
        
        print "\n\n\nRunning %s get_byEpoch_anz_startEtm0(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
            
        self.qryobj['qry'] = 'byEpoch'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['anz'] = self.anz
        self.qryobj['startEtm'] = 0
        
        self.qryobj['limit'] = self._get_limit(limit)
                
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj

        self._print_initialization(self.res, self.qryobj, self.params)
             
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        return self._print_rtnData(rtnData)
    
    
    def get_byEpoch_fnm_startEtm0(self, limit = 10):
        
        print "\n\n\nRunning %s get_byEpoch_fnm_startEtm0(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
            
        self.qryobj['qry'] = 'byEpoch'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['fnm'] = self.fnm
        self.qryobj['startEtm'] = 0
        
        self.qryobj['limit'] = self._get_limit(limit)
                
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj
        
        self._print_initialization(self.res, self.qryobj, self.params)
             
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        return self._print_rtnData(rtnData)    
    
        
    def get_resource(self, limit = 10):
        
        print "\n\n\nRunning %s get_resource(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
                    
        self.qryobj['qry'] = 'resource'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['alog'] = self.alog
        self.qryobj['startEtm'] = 0
        
        self.qryobj['limit'] = self._get_limit(limit)
                
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj

        self._print_initialization(self.res, self.qryobj, self.params)
             
        p3RestApi = P3RestApi(**self.res)
        #rtnData = p3RestApi.get(self.params)
        
        print "\nKnown issue and similar to the bug #589, P3 Rest API, 'AnzMeta:resource' returns 'request failed'"
        
        return False
    
    
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
            if self.doclist is True:
                for key in rtnData[1]['result'].keys():
                    print key, rtnData[1]['result'][key]
                print ""
                print rtnData[1]["result"]["ANALYZER"], rtnData[1]["result"]["LOGNAME"], rtnData[1]["result"]["FILENAME_nint"]
            else:
                for item in rtnData[1][0]:
                    print item, rtnData[1][0][item]
                print ""                
                print rtnData[1][0]["ANALYZER"], rtnData[1][0]["LOGNAME"], rtnData[1][0]["FILENAME_nint"]
            return True
        except Exception, e:
            print "\n\nException (Error) on handling rtnData: ", e.message
        
        return False
    
    
    def _objectCleanUp(self):
        
        if len(self.qryobj) != 0:
            self.qryobj.clear()
            
        if len(self.params) != 0:
            self.params.clear()            
                    
    
    def _get_limit(self, limit = 10):        
        
        try:
            return int(limit)
        except ValueError:
            if limit.lower() == 'all':
                return 'all'
        except Exception, e:
            print "\n\nException (Error) on parsing 'limit': ", e.message            
                        

if __name__ == '__main__':
    
    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzLogMeta = AnzLogMeta(**testProp)
    
    anzLogMeta.get_byEpoch_anz_startEtm0()
    
    anzLogMeta.get_byEpoch_alog_startEtm0()
    
    anzLogMeta.get_byEpoch_fnm_startEtm0()
    
    anzLogMeta.get_resource()