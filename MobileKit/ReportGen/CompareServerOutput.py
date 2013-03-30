'''
Make a request to P3 to get some data from a log
Created on Jun 20, 2012

@author: stan
'''
from P3ApiService import P3ApiService
import sys
import time

P3Api1 = P3ApiService()
P3Api2 = P3ApiService()

def main():
    P3Api1.csp_url = "https://localhost:8081/node"
    P3Api1.identity = "85490338d7412a6d31e99ef58bce5dPM"
    P3Api1.psys = "SUPERADMIN"

    P3Api2.csp_url = "https://dev.picarro.com/dev"
    P3Api2.identity = "dc1563a216f25ef8a20081668bb6201e"
    P3Api2.psys = "APITEST2"

    P3Api1.ticket_url = P3Api1.csp_url + "/rest/sec/dummy/1.0/Admin/"
    P3Api1.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath","AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov"]'
    P3Api1.debug = True

    P3Api2.ticket_url = P3Api2.csp_url + "/rest/sec/dummy/1.0/Admin/"
    P3Api2.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath","AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov"]'
    P3Api2.debug = True

    def getData(P3Api):
        qryparms = {'anz':'DEMO2000', 'startEtm':1339333980, 'endEtm':1339372740,
                    'qry':'byEpoch', 'forceLrt':False,
                    'resolveLogname':True, 'doclist':False, 
                    'limit':10, 'rtnFmt':'lrt' }
        result = P3Api.get("gdu", "1.0", "AnzLog", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        if ret["lrt_start_ts"] == ret["request_ts"]:
            print "This is a new request, made at %s" % ret["lrt_start_ts"]
        else:
            print "This is a duplicate of a request made at %s" % ret["lrt_start_ts"]
        print "Request status: %d" % ret["status"]
        lrt_parms_hash = ret["lrt_parms_hash"]
        lrt_start_ts  = ret["lrt_start_ts"]

        while ret["status"] != 16:       # Loop until status is successful
            print "Waiting"
            time.sleep(5.0)
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'getStatus'}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print "Request status: %d" % ret["status"]

        print ret
        count = ret["count"]    # Number of result rows
        print "Result rows:", count

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit': 5 }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print result

    print "+++++++++++ LOCAL SERVER +++++++++++"
    getData(P3Api1)
    
    print "+++++++++++ P3 SERVER +++++++++++"
    getData(P3Api2)
        
if __name__ == '__main__':
    sys.exit(main())
