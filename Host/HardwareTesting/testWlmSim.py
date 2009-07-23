from Host.Common import CmdFIFO, SharedTypes
from Host.autogen import interface
from numpy import *
from pylab import *

if __name__ == "__main__":
    serverURI = "http://localhost:%d" % (SharedTypes.RPC_PORT_DRIVER,)
    driver = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="testWlmSim")
    eta1 = []
    ref1 = []
    eta2 = []
    ref2 = []
    thList = arange(0,2*pi,pi/180.0)
    for th in thList:
        driver.wrFPGA("FPGA_WLMSIM","WLMSIM_Z0",int(65536*th/(2*pi)))
        eta1.append(driver.rdFPGA("FPGA_WLMSIM","WLMSIM_ETA1"))
        ref1.append(driver.rdFPGA("FPGA_WLMSIM","WLMSIM_REF1"))
        eta2.append(driver.rdFPGA("FPGA_WLMSIM","WLMSIM_ETA2"))
        ref2.append(driver.rdFPGA("FPGA_WLMSIM","WLMSIM_REF2"))
    eta1 = array(eta1,dtype=float)
    eta2 = array(eta2,dtype=float) 
    ref1 = array(ref1,dtype=float)
    ref2 = array(ref2,dtype=float)
    figure(1)
    plot(thList,eta1,thList,ref1,thList,eta2,thList,ref2)
    grid(True)
    figure(2)
    plot(thList,eta1/ref1,thList,eta2/ref2)
    grid(True)
    show()
    