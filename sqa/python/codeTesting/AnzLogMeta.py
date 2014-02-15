'''
Created on Dec 9, 2013

@author: zlu
'''

from P3RestApi import P3RestApi

res = {}
res['host'] = "p3.picarro.com"
res['port'] = 443
res['site'] = 'stage'
res['identity'] = 'zYa8P106vCc8IfpYGv4qcy2z8YNeVjHJw1zaBDth'
res['psys'] = 'stage'
res['svc'] = 'gdu'
res['debug'] = True
res['version'] = '1.0'

res['resource'] = 'AnzLogMeta'
res['rprocs'] = ['AnzLogMeta:byEpoch']

p3RestApiObj = P3RestApi(**res)

#===============================================================================
# anz = 'DEMO2000'
# #anz = 'FDDS2008'
# #anz = 'FDDS2038'
# #anz = 'FDDS2027'
#  
# start = 0
# stop  = 2000000000
#===============================================================================
  
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'anz':'FDDS2008', 'startEtm':0, 'endEtm':2000000000, 'logtype':'dat', 'limit':'all'}}) #working
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'anz':'FDDS2008', 'limit':10}}) #working, but empty result
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'startEtm':0, 'anz':'FDDS2008', 'limit':10}}) #working
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'startEtm':0, 'fnm': 301, 'limit':10}}) #working
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'startEtm':0, 'alog':'FDDS2030-20130506-224905Z-DataLog_Sensor_Minimal.dat', 'limit':10}}) #working

rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'startEtm':0, 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat', 'limit':10}}) #working

print rtn

#===============================================================================
# start = calendar.timegm((2013, 6,  1,  0,  0,  0))
# stop  = calendar.timegm((2013, 6, 30, 23, 59, 59))
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'anz':anz,
#                                                      'startEtm':start, 'endEtm':stop, 
#                                                      'logtype':'dat', 'limit':'all'}})
# 
# if ('name' in res[1]['result']):
#     print "\n".join(res[1]['result']['name'])
# 
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'anz':anz, 'doclist':True, 'startEtm':0, 'logtype':'dat', 'limit':2}})
# print rtn[1]
# 
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'anz':anz, 'doclist':True, 
#                                                      'startEtm':0, 
#                                                      'logtype':'peaks', 'limit':10}})
# print "\n".join(res[1]['result']['name'])
#===============================================================================