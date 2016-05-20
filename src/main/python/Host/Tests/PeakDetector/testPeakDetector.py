# Program to test operation of peak detector

from Host.autogen import interface
from Host.Common import CmdFIFO
from Host.Common import SharedTypes
from Host.Common.SharedTypes import RPC_PORT_DRIVER
import sys
import time

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "TestPeakDetector")

# Ensure that the methane tank is not connected
Driver.openValves(0x4)
Driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER","PEAK_DETECT_CNTRL_IdleState")
while True:
    print "Flowing air for 10s..."
    time.sleep(10.0)

    # Place peak detector in the armed state
    Driver.wrDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER","PEAK_DETECT_CNTRL_ArmedState")
    print "Introducing methane pulse..."

    Driver.closeValves(0x4)
    time.sleep(2.0)
    Driver.openValves(0x4)
    while Driver.rdDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER") != 0:
        time.sleep(5.0)
        sys.stdout.write('.')
    print