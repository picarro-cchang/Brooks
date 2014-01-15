import os
import sys
import threading

from PeakFinder import PeakFinder
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_PEAK_FINDER
from Host.Common import CmdFIFO

DEBUG = {'level': 0}

def getLocalAnalyzerId():
    try:
        CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "RunPeakFinder")
        curValDict = CRDS_Driver.fetchLogicEEPROM()[0]
        localAnalyzerId = curValDict["Analyzer"]+curValDict["AnalyzerNum"]
        if DEBUG['level']>0: print "Local analyzer id found: %s" % localAnalyzerId 
    except:
        localAnalyzerId = None
    return localAnalyzerId
    
def appMain():
    localAnalyzerId = getLocalAnalyzerId()
    if localAnalyzerId:
        # Local
        analyzer = localAnalyzerId
        data_dir = 'C:/UserData/AnalyzerServer' # local Analyzer data location
        debug = False
    else:
        # P3
        if 1 < len(sys.argv):
            analyzer = sys.argv[1]
        else:
            analyzer = 'ZZZ'
            
        if 2 < len(sys.argv):
            debug = sys.argv[2]
        else:
            debug = None
            
        data_dir = os.path.join('/data/mdudata/datalogAdd', analyzer) # P3 Server data location
        
        pidpath = os.path.join(data_dir, 'peakFinderMain.pid') 
        try:
            open(pidpath, 'r').close()
            raise RuntimeError('pidfile exists. Verify that there is not another peakFinderMain task for the directory. path: %s.' % data_dir)
        except:
            try:
                pidf = open(pidpath, 'wb+', 0) #open file with NO buffering
            except:
                raise RuntimeError('Cannot open pidfile for output. path: %s.' % pidpath)
        
        pid = os.getpid()
        pidf.write("%s" % (pid))
        pidf.close()
        
    ulog = os.path.join(data_dir, '*DataLog_User_Minimal.dat')
    pf = PeakFinder(analyzerId=analyzer)
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()

    if not localAnalyzerId:
        os.remove(pidpath)
 
def main():
    th = threading.Thread(target=appMain)
    th.setDaemon(True)
    th.start()
    rpcServer = CmdFIFO.CmdFIFOServer(("",RPC_PORT_PEAK_FINDER),
                                       ServerName="PeakFinder",
                                       ServerDescription="PeakFinder",
                                       ServerVersion="1.0",
                                       threaded=True)
    try:
        while True:
            rpcServer.daemon.handleRequests(0.5)
            if not th.isAlive(): break
        if DEBUG['level']>0: print "Supervised PeakFinder died"
    except:
        if DEBUG['level']>0: print "CmdFIFO stopped"
        
if __name__ == '__main__':
    main()
    