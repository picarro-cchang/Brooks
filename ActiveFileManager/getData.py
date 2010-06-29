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
    result = AFM.getDmData('pressure_cal_mode','analyze_CO2_only',now-300000, now, ['unixTime','co2_y','cavity_pressure'])
    print "Time to fetch: %f" % (0.001*(getTimestamp()-now))
    if result is not None:
        t,v,p = result
        subplot(2,1,1)
        plot(t,v)
        subplot(2,1,2)
        plot(t,p)
        show()
    else:
        print "Null result"
    