'''
Make a request to P3 to get some data from a log
Created on Jun 20, 2012

@author: stan
'''
from P3ApiService import P3ApiService
import sys
import time

P3Api = P3ApiService()

def main():
    #P3Api.csp_url = "https://localhost:8081/node"
    #P3Api.identity = "85490338d7412a6d31e99ef58bce5dPM"
    #P3Api.psys = "SUPERADMIN"

    P3Api.csp_url = "https://dev.picarro.com/dev"
    P3Api.identity = "dc1563a216f25ef8a20081668bb6201e"
    P3Api.psys = "APITEST2"

    P3Api.ticket_url = P3Api.csp_url + "/rest/sec/dummy/1.0/Admin/"
    P3Api.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath","AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov"]'
    P3Api.debug = True
    qnum = 8
    if qnum == 1:
        #qryparms = {'alog':'CFADS2274-20130107-170017Z-DataLog_User_Minimal.dat','logtype':'dat',
        #                  'limit':10,'qry':'byPos','startPos':0,'reverse':True,'doclist':True,'varList':'["CH4"]'}
        qryparms = {'alog':'CFADS2274-20130107-170017Z-DataLog_User_Minimal.dat', 'logtype':'dat', 'varList':'["CH4"]',
                          'limit':100, 'qry':'byPos', 'startPos':0, 'doclist':True, 'rtnFmt':'lrt'}
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

        while ret["status"] == 0:       # Loop until status is successful
            print "Waiting"
            time.sleep(5.0)
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'getStatus'}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print "Request status: %d" % ret["status"]

        count = ret["count"]    # Number of result rows
        print "Result rows:", count

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'byRow', 'startRow':0, 'limit':'all', 'doclist':True }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print ret
    elif qnum == 2:
        qryparms = {'anz':'CFADS2276', 'startEtm':1354641132, 'endEtm':1355011140,
                    'box':[-105.31494,39.4892,-104.65576,39.98343], 'qry':'byGeo',
                    'resolveLogname':True, 'doclist':True, 'limit':30000, 'rtnFmt':'lrt' }
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

        while ret["status"] == 0:       # Loop until status is successful
            print "Waiting"
            time.sleep(5.0)
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'getStatus'}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print "Request status: %d" % ret["status"]

        count = ret["count"]    # Number of result rows
        print "Result rows:", count

        #qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'byRow', 'startRow':0, 'limit':'all', 'doclist':True }
        #result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        #if 'error' in result and result['error'] is not None:
        #    raise RuntimeError("%s" % result)
        #ret = result['return']
        #print ret
    elif qnum == 3:
        qryparms = {'anz':'CFADS2276', 'startEtm':1354300086, 'endEtm':1354732086,
                    'box':[-105.31494,39.4892,-104.65576,39.98343], 'qry':'byGeo', 'forceLrt':False,
                    'resolveLogname':True, 'doclist':True, 'limit':5000, 'rtnFmt':'lrt', 'lrtSortList':'["EPOCH_TIME"]' }
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

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit':1000 }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print len(ret)
        print ret[-1]['lrt_sortpos']

        while len(ret)>0:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':1000,
                        'sortPos': ret[-1]['lrt_sortpos']}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print len(ret)
            print ret[-1]['lrt_sortpos']
    elif qnum == 4:
        qryparms = {'anz':'CFADS2276', 'startEtm':1354300086, 'endEtm':1355011140,
                    'box':[-105.31494,39.4892,-104.65576,39.98343], 'qry':'byGeo', 'logtype':'peaks',
                    'resolveLogname':True, 'doclist':True, 'limit':'all', 'rtnFmt':'lrt', 'lrtSortList':'["EPOCH_TIME"]'}
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

        count = ret["count"]    # Number of result rows
        print "Result rows:", count

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit':200 }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print len(ret)
        print ret[-1]['lrt_sortpos']

        while len(ret)>0:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':200,
                        'sortPos': ret[-1]['lrt_sortpos']}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print len(ret)
            print ret[-1]['lrt_sortpos']
    elif qnum == 5:
        qryparms = {'anz':'CFADS2276', 'startEtm':1354300086, 'endEtm':1354732086,
                    'minLng':-105.31494, 'minLat':39.4892, 'maxLng':-104.65576, 'maxLat':39.98343, 'qry':'byEpoch',
                    'forceLrt':False, 'resolveLogname':True, 'doclist':True, 'limit':1000, 'rtnFmt':'lrt',
                    'lrtSortList':'["EPOCH_TIME"]' }
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

        count = ret["count"]    # Number of result rows
        print "Result rows:", count

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit':200 }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print len(ret)
        print ret[-1]['lrt_sortpos']

        while len(ret)>0:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':200,
                        'sortPos': ret[-1]['lrt_sortpos']}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print len(ret)
            print ret[-1]['lrt_sortpos']
    elif qnum == 6:
        qryparms = {'anz':'CFADS2276', 'startEtm':1354300086, 'endEtm':1354732086,
                    'minLng':-105.31494, 'minLat':39.4892, 'maxLng':-104.65576, 'maxLat':39.98343, 'qry':'byEpoch',
                    'forceLrt':False, 'resolveLogname':True, 'doclist':True, 'limit':5000, 'rtnFmt':'lrt' }
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

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit':1000, 'doclist':True }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print len(ret)

        while len(ret)>0:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':1000, 'doclist':True,
                        'sortPos': ret['result']['lrt_sortpos'][-1]}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print len(ret)

    elif qnum == 7:
        qryparms = {'qry': 'makeSwath', 'alog': 'CFADS2274-20121205-170312Z-DataLog_User_Minimal.dat',
                    'startPos': 0, 'limit': 5000, 'stabClass': 'D', 'nWindow': 10, 'minLeak': 1,
                    'minAmp': 0.05, 'rtnFmt': 'lrt'}
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
            qryparms = {'prmsHash': lrt_parms_hash, 'startTs': lrt_start_ts, 'qry': 'getStatus'}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            print "Request status: %d" % ret["status"]

        print ret
        count = ret["count"]    # Number of result rows
        print "Result rows:", count

    elif qnum == 8:
        # Sorting by LOGNAME and then by Epoch Time
        qryparms = {'anz':'FCDS2008', 'startEtm':1339333980, 'endEtm':1339372740,
                    'minLng':-121.93108, 'minLat':36.58838, 'maxLng':-121.88112, 'maxLat':36.62807, 'qry':'byEpoch',
                    'forceLrt':True, 'resolveLogname':True, 'doclist':True, 'limit':'all', 'rtnFmt':'lrt',
                    'lrtSortList':'["LOGNAME"]' }
        #qryparms = {'anz':'FCDS2008', 'startEtm':1339333980, 'endEtm':1339372740,
        #            'box':[-121.93108,36.58838,-121.88112,36.62807], 'qry':'byGeo',
        #            'forceLrt':True, 'resolveLogname':True, 'doclist':True, 'limit':'all',
        #            'rtnFmt':'lrt','lrtSortList':'["LOGNAME", "EPOCH_TIME"]' }
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
        logs = []
        times = []
        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit':5000, 'doclist':True }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        logs.extend(ret['result']['LOGNAME'])
        times.extend(ret['result']['EPOCH_TIME'])
        print len(ret)

        while len(ret)>0:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':5000, 'doclist':True,
                        'sortPos': ret['result']['lrt_sortpos'][-1]}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] and '404 resource error' in result['error']:
                break
            ret = result['return']
            logs.extend(ret['result']['LOGNAME'])
            times.extend(ret['result']['EPOCH_TIME'])
            print len(ret)

        lastName = None
        lastTime = None
        for name,t in zip(logs,times):
            if lastName != name:
                print name
                lastName = name
                # lastTime = t
            if t < lastTime: print "Time is out of sequence"
            lastTime = t
    elif qnum == 9: # Check how an LRT returns values if we do not set doclis to true
        qryparms = {'anz':'CFADS2276', 'startEtm':1354300086, 'endEtm':1354732086,
                    'box':[-105.31494,39.4892,-104.65576,39.98343], 'qry':'byGeo', 'forceLrt':False,
                    'resolveLogname':True, 'doclist':False, 'limit':500, 'rtnFmt':'lrt', 'lrtSortList':'["EPOCH_TIME"]' }
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
        print len(ret)
        raw_input("%s" % result)

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':5,
                    'sortPos': ret[-1]['lrt_sortpos'], 'doclist': True}
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        raw_input("%s" % result)

        while True:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':5,
                        'sortPos': ret['lrt_sortpos'][-1], 'doclist': True}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            raw_input("%s" % result)
    elif qnum == 10: # Check how an LRT returns values if we do not set doclist to true
        qryparms = {'alog':"DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat",
                    'stabClass':"D", 'forceLrt':True, 'qry':'makeFov'}
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

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'lrttype':'lrtfov', 'limit': 5 }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print len(ret)
        raw_input("%s" % result)

        while True:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet', 'lrttype':'lrtfov', 'limit':5,
                        'sortPos': ret[-1]['lrt_sortpos'], 'doclist': False}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            raw_input("%s" % result)

    elif qnum == 11: # Check long running task on local server
        qryparms = {'anz':'DEMO2000', 'startEtm':1339333980, 'endEtm':1339372740,
                    'qry':'byEpoch', 'forceLrt':False,
                    'resolveLogname':True, 'doclist':False, 
                    'limit':'all', 'rtnFmt':'lrt' }
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

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit': 10 }
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        print len(ret)
        raw_input("%s" % result)

        qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':10,
                    'sortPos': ret[-1]['lrt_sortpos'], 'doclist': True}
        result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
        if 'error' in result and result['error'] is not None:
            raise RuntimeError("%s" % result)
        ret = result['return']
        raw_input("%s" % result)

        while True:
            qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'nextSet','limit':10,
                        'sortPos': ret['lrt_sortpos'][-1], 'doclist': True}
            result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
            if 'error' in result and result['error'] is not None:
                raise RuntimeError("%s" % result)
            ret = result['return']
            raw_input("%s" % result)



if __name__ == '__main__':
    sys.exit(main())
