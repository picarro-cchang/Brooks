'''
Make a request to P3 to get some data from a log
Created on Jun 20, 2012

@author: stan
'''
from P3ApiService import P3ApiService
import sys

P3Api = P3ApiService()

def main():
    P3Api.csp_url = "https://dev.picarro.com/node"
    P3Api.ticket_url = "https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
    P3Api.identity = "85490338d7412a6d31e99ef58bce5de6"
    P3Api.psys = "APITEST"
    P3Api.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzMeta:byAnz"]'
    P3Api.debug = True
    qnum = 5
    if qnum == 1:
        qryparms = {'alog':'FCDS2006-20120323-020431Z-DataLog_User_Minimal.dat','logtype':'dat',
                          'limit':10,'qry':'byPos','startPos':0,'reverse':True,'doclist':True,'varList':'["CH4"]'}
        print P3Api.get("gdu", "1.0", "AnzLog", qryparms)['return']['result']
    elif qnum == 2:
        qryparms = {'qry':'byAnz','doclist':True}
        print P3Api.get("gdu", "1.0", "AnzMeta", qryparms)['return']['result']['ANALYZER_NAME']
    elif qnum == 3:
        qryparms = {'qry':'byEpoch','anz':'FCDS2008','startEtm':'1340220784','reverse':True,'limit':5,'endEtm':1340225112}
        result = P3Api.get("gdu", "1.0", "AnzLogMeta", qryparms)['return']
        print len(result)
        print [r["etmname"] for r in result]
    elif qnum == 4:
        qryparms = {'qry':'byEpoch','alog':'FCDS2006-20120323-020431Z-DataLog_User_Minimal.dat',
                    'startEtm':0,'limit':10,'doclist':True,'reverse':True}
        print P3Api.get("gdu", "1.0", "AnzLog", qryparms)['return']['result']
    elif qnum == 5:
        qryparms = {'qry':'byEpoch','anz':'FCDS2010','reverse':True,'limit':10}
        result = P3Api.get("gdu", "1.0", "AnzLogMeta", qryparms)['return']
        print result
    if qnum == 6:
        qryparms = {'alog':'FCDS2006-20120323-020431Z-DataLog_User_Minimal.dat','logtype':'dat',
                          'limit':10,'qry':'byPos','startPos':0,'reverse':True,'doclist':True,'varList':'["INST_STATUS"]'}
        print P3Api.get("gdu", "1.0", "AnzLog", qryparms)['return']['result']
        
if __name__ == '__main__':
    sys.exit(main())
    