import sys
import time
from P3ApiService import P3ApiService

P3Api = P3ApiService()
P3Api.csp_url = "https://localhost:8081/node"
P3Api.ticket_url = P3Api.csp_url + "/rest/sec/dummy/1.0/Admin/"
P3Api.identity = "85490338d7412a6d31e99ef58bce5dPM"
P3Api.psys = "SUPERADMIN"
P3Api.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath",' +\
               '"AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet",' +\
               '"AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov","GduService:runProcess","GduService:getProcessStatus"]'
P3Api.debug = False
P3Api.timeout = 15
P3Api.sockettimeout = 15

anz = raw_input('Analyzer for which to generate peaks? ')
qryparms = {'qry':'byEpoch','anz':anz,'startEtm':0, 'logtype':'dat'}
result = P3Api.get("gdu", "1.0", "AnzLogMeta", qryparms)['return']
datFiles = [r['name'] for r in result] if result else []

qryparms = {'qry':'byEpoch','anz':anz,'startEtm':0, 'logtype':'peaks'}
result = P3Api.get("gdu", "1.0", "AnzLogMeta", qryparms)['return']
peakFiles = [r['name'] for r in result] if result else []

datFiles = set([d[:d.find('.dat')] for d in datFiles])
peakFiles = set([d[:d.find('.peaks')] for d in peakFiles])
toDo = datFiles-peakFiles

for f in toDo:
    print "Processing", f
    qryparms = {'qry':'runProcess', 'proctype':'PeakFinder', 'logtype':'dat', 'logname':'%s.dat' % f}
    result = P3Api.get("gdu", "1.0", "GduService", qryparms)['return']
    qryparms = {'qry':'getProcessStatus', 'handle':result['process_handle']}
    status = P3Api.get("gdu", "1.0", "GduService", qryparms)['return']
    while 'end' not in status[0]:
        sys.stdout.write('.')
        time.sleep(10)
        status = P3Api.get("gdu", "1.0", "GduService", qryparms)['return']
    sys.stdout.write('\n')
