#!/usr/bin/python

'''
Created on Jan 23, 2014

@author: zlu
'''

from P3RestApi import P3RestApi
import P3RestAPITestHelper

class AnzMeta():
    
    resource = "AnzMeta"
    qryList = ["AnzMeta:byAnz", "AnzMeta:resource"]
    
    res = {}
    qryobj = {}
    params = {}
    
    def __init__(self, *args, **kvargs):
        
        self.anz = kvargs['anz']
        self.alog = kvargs['alog']
        
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
        
        
    def get_byAnz_anz(self, limit = 10):
        
        print "\n\n\nRunning %s get_byAnz_anz(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
        
        self.qryobj['qry'] = 'byAnz'
        self.qryobj['doclist'] = self.doclist
        
        self.qryobj['anz'] = self.anz
        
        self.qryobj['limit'] = self._get_limit(limit)
        
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj
        
        
        
        self._print_initialization(self.res, self.qryobj, self.params)
        
        
        p3RestApi = P3RestApi(**self.res)
        rtnData = p3RestApi.get(self.params)
        
        return self._print_rtnData(rtnData)
        
        
    def get_byAnz(self, limit = 10):
        
        print "\n\n\nRunning %s get_byAnz(self, limit = 10)..." % (self.resource)
        
        self._objectCleanUp()
        
        self.qryobj['qry'] = 'byAnz'
        self.qryobj['doclist'] = self.doclist
        
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
        
        self.qryobj['anz'] = self.anz
        
        self.qryobj['limit'] = self._get_limit(limit)
                     
        self.params['existing_tkt'] = self.existing_tkt
        self.params['qryobj'] = self.qryobj
        
        self._print_initialization(self.res, self.qryobj, self.params)
            
        p3RestApi = P3RestApi(**self.res)
        #rtnData = p3RestApi.get(self.params)
        
        print "\nKnown issue: bug #589, P3 Rest API, 'AnzMeta:resource' returns 'request failed'"
        
        return False
    
    
    def _print_initialization(self, res, qryobj, params):
        
        print ''
        print 'res: ', res
        print 'qryobj: ', qryobj
        print 'params: ', params

        
    def _print_rtnData(self, rtnData):        
        
        anzList = []
        
        try:
            print "\ndoclist is %r" % (self.doclist)  
            print "\nrtnData: ", rtnData
            print ""
            if self.doclist is True:
                anzList = rtnData[1]["result"]["ANALYZER_NAME"]
            else:
                for item in rtnData[1]:
                    anzList.append(item["ANALYZER_NAME"])
            print "The Analyzer (list):"
            for anzName in anzList:
                print anzName
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
                                
    
if __name__ == '__main__':

    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzMeta = AnzMeta(**testProp)
    
    anzMeta.get_byAnz_anz()
    
    anzMeta.get_byAnz()
    anzMeta.get_resource()