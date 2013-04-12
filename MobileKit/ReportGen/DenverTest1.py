'''
Make a request to P3 to get some data from a log
Created on Jun 20, 2012

@author: stan
'''
from P3ApiService import P3ApiService
import pprint
import sys
import time

P3Api = P3ApiService()

P3Api.csp_url = "https://dev.picarro.com/dev"
P3Api.identity = "dc1563a216f25ef8a20081668bb6201e"
P3Api.psys = "APITEST2"

P3Api.ticket_url = P3Api.csp_url + "/rest/sec/dummy/1.0/Admin/"
P3Api.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath","AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov"]'
P3Api.debug = True

pp = pprint.PrettyPrinter(indent=4)

# qryparms = {'qry': 'byEpoch', 'anz': 'CFADS2274', 'startEtm': 1354838400, 'endEtm': 1354924740, 'logtype': 'peaks',
qryparms = {'qry': 'byEpoch', 'anz': 'CFADS2274', 'startEtm': 1343800800, 'endEtm': 1362121140, 'logtype': 'peaks',
            'minLng': -105.04715, 'minLat': 39.67958, 'maxLng': -105.01814, 'maxLat': 39.71366,
            'forceLrt': False, 'resolveLogname': True, 'doclist': False, 'limit': 'all', 'rtnFmt': 'lrt'}

result = P3Api.get("gdu", "1.0", "AnzLog", qryparms)
if 'error' in result and result['error'] is not None:
    raise RuntimeError("%s" % result)
ret = result['return']
if ret["lrt_start_ts"] == ret["request_ts"]:
    print "This is a new request, made at %s" % ret["lrt_start_ts"]
else:
    print "This is a duplicate of a request made at %s" % ret["lrt_start_ts"]
print "INITIAL QUERY"
print pp.pprint(ret)

lrt_parms_hash = ret["lrt_parms_hash"]
lrt_start_ts  = ret["lrt_start_ts"]
done = False

while not done:       # Loop until status is successful
    print "Waiting"
    time.sleep(5.0)
    qryparms = {'prmsHash': lrt_parms_hash, 'startTs': lrt_start_ts, 'qry': 'getStatus'}
    result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
    if 'error' in result and result['error'] is not None:
        raise RuntimeError("%s" % result)
    ret = result['return']
    print "GET STATUS"
    print pp.pprint(ret)
    done = ret['status'] == 16

print ret
count = ret["count"]    # Number of result rows
print "Result rows:", count

qryparms = {'prmsHash':lrt_parms_hash, 'startTs':lrt_start_ts, 'qry':'firstSet', 'limit': 'all' }
result = P3Api.get("gdu", "1.0", "AnzLrt", qryparms)
if 'error' in result and result['error'] is not None:
    raise RuntimeError("%s" % result)
ret = result['return']
print pp.pprint(ret)
