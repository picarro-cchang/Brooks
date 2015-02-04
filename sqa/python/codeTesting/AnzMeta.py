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

res['resource'] = 'AnzMeta'
res['rprocs'] = ["AnzMeta:byAnz", "AnzMeta:resource"]
#res['rprocs'] = ["AnzMeta:resource"]

p3RestApiObj = P3RestApi(**res)

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'anz':'FDDS2008', 'doclist':True}}) #working
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'doclist':True}}) #working

rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'anz':'FDDS2038', 'doclist':True, 'limit':'all'}}) #working

print rtn

rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'doclist':True, 'limit':'all'}}) #working

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'resource', 'doclist':True, 'anz':"FDDS2008", 'limit': 10}}) #bug #589, P3 Rest API, 'AnzMeta:resource' returns 'request failed

print rtn