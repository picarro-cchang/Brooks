#! /usr/bin/python
'''
LogExportImport.py

Export P3 Analyzer Log (dat, peaks, analysis, or other) from source site,
and Import that log into destination site)

instruction-obj JSON

  {"surl": <SOURCE SITE URL STRING Example: "https://p3b.picarro.com/mfg">, 
   "ssys": <SOURCE SECURITY SYS STRING Example: "mfg">, 
   "sid": <SOURCE SECURITY IDENTITY STRING Example: "blah1234567">, 
   "durl": <DESTINATION SITE URL STRING Example: "https://p3b.picarro.com/google">, 
   "dsys": <DESTINATION SECURITY SYS STRING Example: "google">, 
   "did": <DESTINATION SECURITY IDENTITY STRING Example: "blah1234567">, 
   "anz": <ANALYZER STRING Example: "FDDS2008">,
   "logs": [
              {"alog": <LOGNAME STRING Example: "FDDS2008-20121214-213345Z-DataLog_Sensor_Minimal.dat">
               , "ltype": <LOGTYPE STRING Example: "dat">}
              , {"alog": <LOGNAME STRING Example: FDDS2008-20121214-213825Z-DataLog_Sensor_Minimal.dat">
               , "ltype": <LOGTYPE STRING Example: "dat">}
              , ...
           ]
  }
]

'''
import os
import sys
import subprocess
import glob
import shutil

from optparse import OptionParser

import time
import datetime

try:
    import simplejson as json
except:
    import json

import math
from P3ApiService import P3ApiService

LogExportImportOPTS = [
               ("instruction-obj", "inst_obj", "Path to instruction JSON file ", "<PATH-TO-INST-JSON-FILE>", None, True), 
               ("log-path", "log_path", "Path for process logs", "./logs", "./logs"),
               ("debug", "debug", "Debug mode", "<DEBUG>", False),
               ("skip-mkdir", "skip_mkdir", "Skip creating the log_path (they must already exists and be writable)", "<SKIPMKDIR>", False)
         ]


class LogExportImport(object):
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self.nowtm = datetime.datetime.now()
        self.nowtm_str = self.nowtm.strftime("%Y-%m-%dT%H%M%S")

        self.kwargs = {}
        for myopts in LogExportImportOPTS:
            ky = myopts[1]
            df = myopts[4]

            self.kwargs[ky] = None
            if ky in kwargs:
                self.kwargs[ky] = kwargs[ky]

            if not self.kwargs[ky]:
                self.kwargs[ky] = df

        self.debug = self.kwargs["debug"]
        self.logf = None

        self.logname = "LogExportImport_%s.log" %(self.nowtm_str)

        if not self.kwargs["log_path"]:
            self.kwargs["log_path"] = "./logs/LogExportImport"

        self.logloc = "%s" %(self.kwargs["log_path"])

        if not self.kwargs["skip_mkdir"]:
            if not os.path.isdir(self.logloc):
                os.makedirs(self.logloc)
        
        log =  os.path.join(self.logloc, self.logname) #"%s/%s" %(self.logloc, self.logname)
        
        try:
            self.logf = open(log, 'wb+', 0) #open file with NO buffering
        except:
            raise RuntimeError('Cannot open logf for output. path: %s.' % log)
        
        if self.debug == True:
            for ky, val in self.kwargs.iteritems():
                self.logger("%s: %s" %(ky, val))

    def logger(self, txt):
        if self.logf:
            self.logf.write("%s\n" %(txt))
        
        print txt
        
    def getMatrix(self, path):
        if not os.path.isfile(path):
            open(path, 'w').close()
        sname = os.path.basename(path)
        pnp = open(path,"r")
        matrix_str = pnp.read().strip()
        pnp.close()
        
        print "matrix_str"
        print matrix_str
        print
        
        build_instructions = json.loads(matrix_str)
        return build_instructions
    
    def doInst(self, exp_instructions):
        for inst_obj in exp_instructions:
            surl = None
            ssys = None
            sid = None
            durl = None
            dsys = None
            did = None
            anz = None
            loglist = None
            
            for inst, val in inst_obj.iteritems():
                if inst == "surl":
                    surl = val
                elif inst == "ssys":
                    ssys = val
                elif inst == "sid":
                    sid = val
                elif inst == "durl":
                    durl = val
                elif inst == "dsys":
                    dsys = val
                elif inst == "did":
                    did = val
                elif inst == "anz":
                    anz = val
                elif inst == 'logs':
                    loglist = val

            if surl and ssys and sid and durl and dsys and did and anz and loglist:
                print surl, ssys, sid, durl, dsys, did, anz
                print loglist
                
                SrcP3Api = P3ApiService()
                SrcP3Api.csp_url = surl  #URL for resource
                SrcP3Api.ticket_url = "%s/rest/sec/dummy/1.0/Admin" % SrcP3Api.csp_url #"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin"  #URL for Admin (issueTicket) resource
                SrcP3Api.identity = sid #identity (authentication)
                SrcP3Api.psys = ssys              #picarro sys (authentication)
                SrcP3Api.rprocs = '["AnzLog:byPos"]'          #security rprocs string
                SrcP3Api.debug = self.debug
                print "Source: ", SrcP3Api
                DestP3Api = P3ApiService()
                DestP3Api.csp_url = durl  #URL for resource
                DestP3Api.ticket_url = "%s/rest/sec/dummy/1.0/Admin" % DestP3Api.csp_url #"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin"  #URL for Admin (issueTicket) resource
                DestP3Api.identity = did #identity (authentication)
                DestP3Api.psys = dsys              #picarro sys (authentication)
                DestP3Api.rprocs = '["AnzLog:byPos", "AnzLog:data", "AnzMeta:data", "GduService:runProcess"]'          #security rprocs string
                DestP3Api.debug = self.debug
                print "Dest: ", DestP3Api
                
                dqryparams = {}
                dqryparams["data"] = json.dumps([{'ANALYZER': anz}])
                
                tryAgain = True
                while tryAgain: 
                    rtn_obj = DestP3Api.get('gdu', '1.0', 'AnzMeta', dqryparams)
                    print "AnzMeta output", rtn_obj
                    if 'return' in rtn_obj:
                        if rtn_obj['return'] == "OK":
                            tryAgain = None
                        else:
                            print rtn_obj
                    
                    if tryAgain:
                        print rtn_obj
                        time.sleep(3)
                
                for logid in loglist:
                    alog = logid["alog"]
                    ltype = logid["ltype"]
                    
                    startPos = 0
                    
                    goodData = True
                    while goodData:
                        qryparams = {}
                        qryparams["qry"] = "byPos"
                        qryparams["alog"] = alog
                        qryparams["logtype"] = ltype
                        qryparams["startPos"] = startPos
                        qryparams["limit"] = 500
                        
                        rtn_obj = SrcP3Api.get('gdu', '1.0', 'AnzLog', qryparams)
                        if "error" in rtn_obj and rtn_obj["error"] != None:
                            print "Done with ", alog
                            print rtn_obj
                            goodData = None
                            
                        else:
                            #ltype = None
                            print "Source file read", rtn_obj
                            doclist = []
                            
                            for rdoc in rtn_obj["return"]:
                                # filter fields that must be generated
                                if 'shash' in rdoc:
                                    del rdoc['shash']
                                if 'SERVER_HASH' in rdoc:
                                    del rdoc['SERVER_HASH']
                                if 'FILENAME_nint' in rdoc:
                                    del rdoc['FILENAME_nint']
                                if 'ANALYZER' in rdoc:
                                    del rdoc['ANALYZER']
                                if 'ltype' in rdoc:
                                    if ltype == None:
                                        ltype = rdoc['ltype']
                                    del rdoc['ltype']
                                
                                ndoc = {}
                                for col in rdoc:
                                    ndoc[col] = rdoc[col]
                                    try:
                                        if ndoc[col] == None:
                                            ndoc[col] = "NaN"
                                        
                                        elif math.isnan(ndoc[col]):
                                            ndoc[col] = "NaN"
                
                                    except Exception:
                                        print 'col: ', col, ndoc[col]
                                
                                startPos = rdoc["row"] + 1
                                print alog, rdoc["row"]
                                
                                doclist.append(ndoc)
                        
                            if len(doclist) > 0:
                                if ltype:
                                    dqryparams = {}
                                    dqryparams["data"] = json.dumps(
                                                        [{
                                                          'logname': alog,
                                                          'replace': 0,
                                                          'logtype': ltype,
                                                          'logdata': doclist
                                                          }]
                                    )
                                    
                                    tryAgain = True
                                    while tryAgain: 
                                        rtn_obj = DestP3Api.get('gdu', '1.0', 'AnzLog', dqryparams)
                                        if 'return' in rtn_obj:
                                            if rtn_obj['return'] == "OK":
                                                tryAgain = None
                                                
                                        if tryAgain:
                                            print rtn_obj
                                            time.sleep(3)


                                else:                                    
                                    print "missing ltype"
                    tryAgain = True
                    # mqueryparams = {}
                    mqueryparams=dict(qry="runProcess",logname=alog,proctype="RefreshMetaData")
                    # https://dev.picarro.com/investigator/rest/gdu/
                    # 80199022bb80a5907ed1af3417eebbd3/1.0/GduService?callback=_jqjsp&
                    # qry=runProcess&
                    # logname=CFADS2206-20130129-001712Z-DataLog_User_Minimal.dat&
                    # proctype=RefreshMetaData
                    # &_1363906817324=
                    # mqueryparams["debug"] = True
                    # https://localhost:8081/node/rest/gdu/50a160d8f014d1b50b14c2932bfcf218/1.0/AnzLogMeta?proctype=RefreshMetaData&qry=runProcess&logname=CFADS2206-20130129-001712Z-DataLog_User_Minimal.dat
                    while tryAgain:
                        print "running refresh metadata"
                        rtn_obj = DestP3Api.get('gdu', '1.0', 'GduService', mqueryparams)                                        
                        print rtn_obj
                        if 'return' in rtn_obj:
                            if rtn_obj['error'] == None:
                                tryAgain = None
                                
                        if tryAgain:
                            print rtn_obj
                            time.sleep(3)
                
                
    def run(self):
        msg = "LogExportImport log: %s/%s" % (self.logloc, self.logname)
        self.logger(msg)

        self.doInst(self.getMatrix(self.kwargs['inst_obj']))
        
        sys.exit()
    
def main(argv=None):
    if argv is None:
        argv = sys.argv
            
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    for myopts in LogExportImportOPTS:
        if ((myopts[4] == True) or (myopts[4] == False)):
            parser.add_option("--%s" %(myopts[0]), dest=myopts[1], help=myopts[2], metavar=myopts[3], action="store_true")
        else:
            parser.add_option("--%s" %(myopts[0]), dest=myopts[1], help=myopts[2], metavar=myopts[3])
    
    (options, args) = parser.parse_args()

    emsg = ""
    emsg_sep = ""
    perror = None
    for myopts in LogExportImportOPTS:
        if len(myopts) >= 6:
            if myopts[5] == True:
                vl = getattr(options, myopts[1])
                if not vl:
                    emsg += "%s--%s is required" % (emsg_sep, myopts[0])
                    emsg_sep = "\n"
                    perror = True
                
    if perror == True:
        parser.error(emsg)

    class_opts = {}
    for myopts in LogExportImportOPTS:
        vl = getattr(options, myopts[1])
        if vl:
            class_opts[myopts[1]] = vl
    
    pf = LogExportImport(**class_opts)
    pf.run()


if __name__ == "__main__":
    sys.exit(main())

