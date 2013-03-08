'''
Created on Jun 20, 2012

@author: stan
'''
from P3ApiService import P3ApiService
try:
    import simplejson as json
except:
    import json
import datetime
import re

class SecureRestProxy(object):
    # Proxy to make rest calls to a secure Pcubed server
    def __init__(self,csp_url,svc,ticket_url,identity,psys):
        self.P3Api = P3ApiService()
        self.P3Api.csp_url = csp_url
        self.P3Api.ticket_url = ticket_url
        self.P3Api.identity = identity
        self.P3Api.psys = psys
        self.P3Api.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzMeta:byAnz"]'
        self.P3Api.debug = False
        self.svc = svc
   
    def getAnalyzerList(self,parms):
        qryparms = {'qry':'byAnz','limit':'all','doclist':True}
        try:
            analyzerList = self.P3Api.get("gdu", "1.0", "AnzMeta", qryparms)['return']['result']['ANALYZER_NAME']
        except:
            analyzerList = []
        return {"analyzerList":analyzerList}
    
    def getLatestLog(self,parms):
        # Get the latest log which is of the form DataLog_User_Minimal.dat.
        chunk = 10
        dateTimeRe = re.compile("^.*?\-(\d{8})\-(\d{6})Z.*?DataLog_User_Minimal\.dat$")
        anz = parms["analyzer"]
        endEtm = 2000000000
        # Go back in time to find the log matching the regular expression
        while True:
            qryparms = {'qry':'byEpoch','limit':chunk,'anz':anz,'reverse':True,'startEtm':0,'endEtm':endEtm}
            rList = self.P3Api.get("gdu", "1.0", "AnzLogMeta", qryparms)['return']
            r = None # So that if rList is empty, we leave with r set to None
            for r in rList:
                if dateTimeRe.match(r["LOGNAME"]): break
            else:
                if not rList: break
                endEtm = r["etmname"]
                continue
        # At this point, r is the desired log, or is None, if such a log does not exist                
        logname = r['LOGNAME'] if r else ""
        return {"latestLog":logname}

    def getDatLogList(self,parms):
        dateTimeRe = re.compile("^.*?\-(\d{8})\-(\d{6})Z.*?DataLog_User_Minimal\.dat$")
        anz = parms["analyzer"]
        endEtm = 2000000000
        fList = [{'alog':"@@Live:%s"%anz, 'name':"Live"}]
        qryparms = {'qry':'byEpoch','limit':'all','anz':anz,'reverse':True,'startEtm':0,'endEtm':endEtm}
        rList = self.P3Api.get("gdu", "1.0", "AnzLogMeta", qryparms)['return']
        for r in rList:
            m = dateTimeRe.match(r['LOGNAME'])
            if m:
                when = datetime.datetime.strptime("%sT%s" % (m.group(1),m.group(2)),"%Y%m%dT%H%M%S")
                fmtDate = when.strftime("%d %b %Y, %H:%M GMT")
                duration = r.get('durr',None)
                r['name'] = fmtDate + ('(%dh,%dm)' % (duration//3600,round((duration%3600)/60.0))) if duration is not None else ''
                r['alog'] = r['LOGNAME']
                fList.append(r)
        return {"logList":fList}
    
    def getData(self,parms):
        retVal = {'filename':''}    
        if 'alog' in parms:
            alog = parms['alog']
            #if alog.startswith('@@Live:'):
            #    anz = alog[7:]
            #    parms['alog'] = self.getLatestLog({"analyzer":anz})
            if parms['alog']:
                qryparms = parms.copy()
                qryparms.update(dict(qry='byPos',limit=2000,doclist=True,insFilename=True,insNextLastPos=True))
                if 'startPos' in qryparms and qryparms['startPos']<0:
                    qryparms['limit'] = -qryparms['startPos']
                    qryparms['reverse'] = True
                    qryparms['startPos'] = 0
                try:
                    retVal = self.P3Api.get("gdu", "1.0", "AnzLog", qryparms)['return']['result']
                except:
                    pass
        return retVal
        
    def __getattr__(self,attrName):
        def dispatch(argsDict):
            print "Calling %s" % attrName
            print "Arguments: %s" % argsDict
            print "Not yet implemented"
            return None
        return dispatch
