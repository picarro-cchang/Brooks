import os
import sys
import threading
import optparse

from PeakAnalyzer import PeakAnalyzer
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_PEAK_ANALYZER
from Host.Common import CmdFIFO


UNIX_EPOCH_BEGIN = 0.0
HEAT_DEATH_OF_UNIVERSE = 1300000000.0


def getLocalAnalyzerId():
    try:
        CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "RunPeakAnalyzer")
        curValDict = CRDS_Driver.fetchLogicEEPROM()[0]
        localAnalyzerId = curValDict["Analyzer"]+curValDict["AnalyzerNum"]
        print "Local analyzer id found: %s" % localAnalyzerId
    except:
        localAnalyzerId = None
    return localAnalyzerId

def appMain(checkForCancellation):
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

        pidpath = os.path.join(data_dir, 'peakAnalyzerMain.pid')
        try:
            testf = open(pidpath, 'r')
            testf.close()
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

    valveCheckTime = UNIX_EPOCH_BEGIN

    if not checkForCancellation:
        valveCheckTime = HEAT_DEATH_OF_UNIVERSE


    pf = PeakAnalyzer(analyzerId=analyzer,
                      legacyValveStop=valveCheckTime)
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()

    if not localAnalyzerId:
        os.remove(pidpath)


def main(checkForCancellation):
    th = threading.Thread(target=appMain, args=[checkForCancellation])
    th.setDaemon(True)
    th.start()
    rpcServer = CmdFIFO.CmdFIFOServer(("",RPC_PORT_PEAK_ANALYZER),
                                       ServerName="PeakAnalyzer",
                                       ServerDescription="PeakAnalyzer",
                                       ServerVersion="1.0",
                                       threaded=True)
    try:
        while True:
            rpcServer.daemon.handleRequests(0.5)
            if not th.isAlive(): break
        print "Supervised PeakAnalyzer died"
    except:
        print "CmdFIFO stopped"

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--without-cancellation', dest='checkForCancellation',
                      default=True, action='store_false')
    options, _ = parser.parse_args()

    main(options.checkForCancellation)
