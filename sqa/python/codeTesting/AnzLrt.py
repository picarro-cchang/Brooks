'''
Created on Dec 11, 2013

@author: zlu
'''

from P3RestApi import P3RestApi
import calendar

res = {}
res['host'] = "p3.picarro.com"
res['port'] = 443
res['site'] = 'stage'
res['identity'] = 'zYa8P106vCc8IfpYGv4qcy2z8YNeVjHJw1zaBDth'
res['psys'] = 'stage'
res['svc'] = 'gdu'
res['debug'] = False
res['version'] = '1.0'

res['resource'] = 'AnzLrt'
res['rprocs'] = ['AnzLrt:getStatus', 'AnzLrt:byRow', 'AnzLrt:byRowFov']

p3RestApiObj = P3RestApi(**res)

        #qry: getStatus
rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'getStatus', 'doclist':True, 'prmsHash': 'b0e8ffa76a5ff56246b6e871c2d7d548', 'startTs': '2014-02-10T19:29:23.768Z'}})

print "\ngetStatus: ", rtn


        #qry: byRow
rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byRow', 'doclist':True, 'prmsHash': 'b0e8ffa76a5ff56246b6e871c2d7d548', 'startTs': '2014-02-10T19:29:23.768Z', 'startRow': 0}})

print "\nbyRow: ", rtn

        #qry: byRowFov
rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byRowFov', 'doclist':False, 'prmsHash': 'b0e8ffa76a5ff56246b6e871c2d7d548', 'startTs': '2014-02-10T19:29:23.768Z', 'startRow': 0}})

print "\nbyRowFov with doclist set to False", rtn #bug 608

rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byRowFov', 'doclist':True, 'prmsHash': 'b0e8ffa76a5ff56246b6e871c2d7d548', 'startTs': '2014-02-10T19:29:23.768Z', 'startRow': 0}})

print "\nbyRowFov with doclist set to True ", rtn
