# Sample program to get data from ActiveFileManager

from numpy import *
from pylab import *
import socket
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.timestamp import getTimestamp

class ActiveFileManagerProxy(SharedTypes.Singleton):
    """Encapsulates access to the ActiveFileManager via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_ACTIVE_FILE_MANAGER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="getData")
            self.initialized = True

if __name__ == "__main__":
    AFM = ActiveFileManagerProxy().rpc
    now = getTimestamp()
#    result = AFM.getRdData(now-300000, now, ['timestamp', 'waveNumber', 'uncorrectedAbsorbance'])
#    result = AFM.getSensorData(now-300000, now, 'STREAM_Laser1Temp')
#    result = AFM.getDmData('pressure_cal_mode','analyze_PressureCal',now-300000, now, ['unixTime','y_parameter','cavity_pressure'])
    result = AFM.getDmData('pressure_cal_mode','analyze_PressureCal',now+10000, now+20000, ['unixTime','y_parameter','cavity_pressure'])
    print "Time to fetch: %f" % (0.001*(getTimestamp()-now))
    if result is not None:
        subplot(2,1,1)
        plot(result['unixTime'],result['y_parameter'])
        gca().yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter(useOffset=False))
        subplot(2,1,2)
        plot(result['unixTime'],result['cavity_pressure'])
        show()
    else:
        print "Null result"
    