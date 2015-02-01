'''
Created on Dec 5, 2013

@author: zlu
'''

from P3RestApi import P3RestApi
import calendar
import sys

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
res['rprocs'] = ['AnzMeta:byAnz']

"AnzMeta:data",
anzMeta = P3RestApi(**res)

rtn = anzMeta.get({'existing_tkt':True, 'qryobj':{'qry':'byAnz', 'doclist':True}})

print rtn