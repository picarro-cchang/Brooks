import os
import sys
from PeakFinder import PeakFinder

def getLocalAnalyzerId():
    try:
        import CmdFIFO
        RPC_PORT_DRIVER = 50010
        CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "RunPeakFinder")
        curValDict = CRDS_Driver.fetchLogicEEPROM()[0]
        localAnalyzerId = curValDict["Analyzer"]+curValDict["AnalyzerNum"]
        print "Local analyzer id found: %s" % localAnalyzerId 
    except:
        localAnalyzerId = None
    return localAnalyzerId
    
if __name__ == "__main__":
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    localAnalyzerId = getLocalAnalyzerId()
    if localAnalyzerId:
        # Local
        analyzer = localAnalyzerId
        data_dir = os.path.join(AppDir,'static/datalog') # local Analyzer data location
        debug = True
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
        
        pidpath = os.path.join(data_dir, 'peakFinder.pid') 
        try:
            testf = open(pidpath, 'r')
            raise RuntimeError('pidfile exists. Verify that there is not another peakFinderMain task for the directory. path: %s.' % data_dir)
        except:
            try:
                pidf = open(pidpath, 'wb+', 0) #open file with NO buffering
            except:
                raise RuntimeError('Cannot open pidfile for output. path: %s.' % pidpath)
        
        pid = os.getpid()
        pidf.write("%s" % (pid))
        pidf.close()
        
    ulog = os.path.join(data_dir, '*.dat')
    pf = PeakFinder(analyzerId=analyzer)
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()

    if not localAnalyzerId:
        os.remove(pidpath)