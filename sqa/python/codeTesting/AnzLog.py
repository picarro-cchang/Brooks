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

res['resource'] = 'AnzLog'
#res['rprocs'] = ['AnzLog:byPos', 'AnzLog:byEpoch', 'AnzLog:byGeo', 'AnzLog:makeSwath', 'AnzLog:makeFov', 'AnzLog:makePeaks', 'AnzLog:makeAnalyses', 'AnzLog;makeRflt']
#res['rprocs'] = ['AnzLog:byEpoch', 'AnzLog:byPos', 'AnzLog:byGeo', 'AnzLog:makeSwath', 'AnzLog:makeFov', 'AnzLog:makePeaks', 'AnzLog:makeAnalyses', 'AnzLog:makeRflt']
res['rprocs'] = ['AnzLog:byEpoch', 'AnzLog:byPos', 'AnzLog:byGeo']

p3RestApiObj = P3RestApi(**res)

#===============================================================================
# 
#         #qry: byPos
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byPos','doclist':True, 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat', 'startPos':0, 'limit':1}}) #working
# print "\n\n\nRunning p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byPos','doclist':True, 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat', 'startPos':0, 'limit':1}})"
# print "\nrtn: ", rtn
# 
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byPos','doclist':True, 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat', 'limit':1}})
# print "\n\n\nRunning p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byPos','doclist':True, 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat', 'limit':1}})"
# print "\nrtn: ", rtn
# 
# #rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byPos','doclist':True, 'fnm':96, 'startPos':0, 'limit':1}}) #working
# #rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byPos','doclist':True, 'fnm':2000, 'startPos':0, 'limit':1}}) #working
# 
#         #qry: byEpoch
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'anz':'DEMO2000', 'doclist':True, 'startEtm':0, 'limit':10}}) #working
# print "\nrtn: ", rtn
#===============================================================================

rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'anz':'FCDS2008', 'doclist':True, 'startEtm':0, 'limit':100}}) #working
print "\nrtn: ", rtn

rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'anz':'DEMO2000', 'doclist':True, 'startEtm':0, 'limit':100}}) #working
print "\nrtn: ", rtn

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat', 'doclist':True, 'startEtm':0, 'limit':10}}) #working
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':True, 'startEtm':0, 'limit':10}}) #not working: one and only one of alog, anz or fnm is required\     
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'varList':'["WIND_N","WIND_E"]', 'anz':'DEMO2000', 'doclist':True, 'startEtm':0, 'logtype':'dat', 'limit':10}}) #working

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'alog':'DEMO2000-20120610-131326Z-DataLog_User_Minimal.dat'}}) #empty result
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'anz':'DEMO2000'}}) #empty result
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'fnm':96}}) #empty result
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'fnm':96, 'startEtm':0, 'limit':10}}) #working
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'fnm':2000, 'startEtm':0, 'limit':10}})
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'fnm':150, 'startEtm':0, 'limit':10}}) #same result when fnm = 2000 or ...
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':True, 'fnm':301, 'startEtm':0, 'limit':10}}) #same result as fnm = 150

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch', 'doclist':False, 'startEtm':0, 'logtype':'dat', 'limit':'all'}})

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':doclist, 'fnm':fnm,'startEtm':0, 'limit':1}}) #Bug #489

#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':doclist, 'anz':anz, 'startEtm':0, 'limit':1}})
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byEpoch','doclist':doclist, 'alog':alog, 'startEtm':0, 'limit':1}})

            #qry: byGeo
#rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'qry':'byGeo','doclist':True, 'startEtm':0, 'anz':'FDDS2030', 'box':[-121.89494445, 36.600532566, -121.89494445+.01, 36.600532566+.01], 'limit':1}}) #not working
#===============================================================================
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'anz':'CFADS2276', 'startEtm':1354641132, 'endEtm':1355011140,
#                   'box':'[-105.31494,39.4892,-104.65576,39.98343]', 'qry':'byGeo',
#                   'resolveLogname':True, 'doclist':True, 'limit':1}})
#===============================================================================

#    'center' and 'radius' not working
#===============================================================================
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'anz':'CFADS2276', 'startEtm':1354641132, 'endEtm':1355011140,
#                   'center':'[-105.31494,39.4892]', 'radius':0.15, 'qry':'byGeo',
#                   'resolveLogname':True, 'doclist':True, 'limit':10}})
#===============================================================================

#===============================================================================
# #'box' works 
# ###rtn['rprocs'] = ['AnzLog:byEpoch', 'AnzLog:byPos', 'AnzLog:byGeo'] ###otherwise complains about the invalid ticket
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'anz':'CFADS2276', 'startEtm':0,
#                   'box':'[-105.31494,39.4892,-104.65576,39.98343]', 'qry':'byGeo',
#                   'resolveLogname':True, 'doclist':True, 'limit':10}})
#===============================================================================

#'polygon' not working, try to see why always "502 Bad Gateway" when parameters are wrong.
# rtn = p3RestApiObj.get({'existing_tkt':True, 'qryobj':{'anz':'CFADS2276', 'startEtm':0,
#                   'polygon':'[-105.31494,39.4892, -105.31494, 39.98343, -104.65576,39.98343]', 'qry':'byGeo',
#                   'resolveLogname':True, 'doclist':True, 'limit':10}})