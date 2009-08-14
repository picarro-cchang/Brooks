from Host.Common import CmdFIFO, SharedTypes
from Host.autogen import interface
from numpy import *
from pylab import *

if __name__ == "__main__":
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="uploadTestScheme")
    thList = linspace(0,1000,8001)
    dwell = ones(thList.shape)
    repeats = 2
    driver.wrScheme(0,repeats,zip(thList,dwell))
    