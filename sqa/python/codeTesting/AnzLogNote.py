'''
Created on Dec 11, 2013

@author: zlu
'''

#not implemented yet

from P3RestApi import P3RestApi
import calendar

res = {}
res['host'] = "p3.picarro.com"
res['port'] = 443

res['site'] = 'stage'
res['identity'] = 'zYa8P106vCc8IfpYGv4qcy2z8YNeVjHJw1zaBDth'
res['psys'] = 'stage'

res['svc'] = 'gdu'
res['debug'] = True
res['version'] = '1.0'

res['resource'] = 'AnzLogNote'
res['rprocs'] = ['AnzLogNote:byEpoch']

p3RestApiObj = P3RestApi(**res)

alog = 'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat'
#alog = 'FDDS2027-20130611-200359Z-DataLog_User_Minimal.dat'

analyzer = 'DEMO2000'

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'alog':log, 'doclist':True}})

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'alog':alog, 'startEtm':0, 'doclist':True, 'limit':1}})
rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'anz':'FDDS2021', 'startEtm':0, 'doclist':True, 'limit':1}})

print rtn