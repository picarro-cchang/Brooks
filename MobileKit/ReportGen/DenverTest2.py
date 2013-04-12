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
            'forceLrt': False, 'resolveLogname': True, 'doclist': False, 'limit': 'all', 'rtnFmt': 'json'}

result = P3Api.get("gdu", "1.0", "AnzLog", qryparms)
if 'error' in result and result['error'] is not None:
    raise RuntimeError("%s" % result)
ret = result['return']
print "INITIAL QUERY"
print pp.pprint(ret)
print "Number of records", len(ret)

print "Number above 0.03 amplitude", len([r for r in ret if r['AMPLITUDE']>=0.03])