from P3RestApi import P3RestApi
import calendar
import sys
import time

restP = {}
restP['host'] = "192.168.56.101"
restP['port'] = 443
restP['site'] = 'pfranz'
restP['identity'] = 'n2fv6HxiLEb68XJ8zyG0nWJuRTPU1b'
restP['psys'] = 'pfranz'
restP['svc'] = 'gdu'
restP['debug'] = False
restP['version'] = '1.0'

restP['resource'] = 'AnzMeta'
restP['rprocs'] = ["AnzMeta:byAnz"]
anzMeta = P3RestApi(**restP)

restP['resource'] = 'AnzLogMeta'
restP['rprocs'] = ["AnzLogMeta:byEpoch"]
anzLogMeta = P3RestApi(**restP)

restP['resource'] = 'AnzLog'
restP['rprocs'] = ["AnzLog:byEpoch", "AnzLog:byPos"]
anzLog = P3RestApi(**restP)

restP['resource'] = 'GduService'
restP['rprocs'] = ["GduService:runProcess", "GduService:getProcessStatus"]
gduService = P3RestApi(**restP)

with open('peakUtility.log','a') as fp:
    anz = 'FDDS2038'
    qryparms = {'qry':'byEpoch', 'anz':anz, 'startEtm':0, 'logtype':'dat', 'limit':'all'}
    res = anzLogMeta.get({'existing_tkt':True, 'qryobj':qryparms})
    datFiles = []
    if res[0] == 200 and res[1]:
        datFiles = [r['name'] for r in res[1] if 'User' in r['name']]

    qryparms = {'qry':'byEpoch', 'anz':anz, 'startEtm':0, 'logtype':'peaks', 'limit':'all'}
    res = anzLogMeta.get({'existing_tkt':True, 'qryobj':qryparms})
    peakFiles = []
    if res[0] == 200 and res[1]:
        peakFiles = [r['name'] for r in res[1] if 'User' in r['name']]

    datFiles = set([d[:d.find('.dat')] for d in datFiles])
    peakFiles = set([d[:d.find('.peaks')] for d in peakFiles])
    toDo = datFiles-peakFiles
    print len(datFiles), len(peakFiles), len(toDo)

    for f in toDo:
        print "Processing", f
        qryparms = {'qry':'runProcess', 'proctype':'PeakFinder', 'logtype':'dat', 'logname':'%s.dat' % f}
        res = gduService.get({'existing_tkt':True, 'qryobj':qryparms})
        print res
        handle = res[1]['process_handle']
        res = gduService.get({'existing_tkt':True, 'qryobj':{'qry':'getProcessStatus', 'handle':handle}})
        status = res[1]
        while 'end' not in status[0]:
            sys.stdout.write('.')
            time.sleep(5)
            res = gduService.get({'existing_tkt':True, 'qryobj':{'qry':'getProcessStatus', 'handle':handle}})
            status = res[1]
        qryparms = {'qry':'runProcess', 'proctype':'PeakAnalyzer', 'logtype':'dat', 'logname':'%s.dat' % f}
        res = gduService.get({'existing_tkt':True, 'qryobj':qryparms})
        print res
        handle = res[1]['process_handle']
        res = gduService.get({'existing_tkt':True, 'qryobj':{'qry':'getProcessStatus', 'handle':handle}})
        status = res[1]
        while 'end' not in status[0]:
            sys.stdout.write('.')
            time.sleep(5)
            res = gduService.get({'existing_tkt':True, 'qryobj':{'qry':'getProcessStatus', 'handle':handle}})
            status = res[1]
        print>>fp, f
