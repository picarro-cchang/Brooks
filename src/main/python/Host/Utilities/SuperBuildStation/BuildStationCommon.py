APP_NAME = "BuildStation"

import types
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR
from Host.autogen import interface

Driver = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,APP_NAME, IsDontCareConnection = False)
FreqConverter = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,APP_NAME, IsDontCareConnection = False)
SpectrumCollector = CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,APP_NAME, IsDontCareConnection = False)

def _value(valueOrName):
    if isinstance(valueOrName,types.StringType):
        try:
            valueOrName = getattr(interface,valueOrName)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % valueOrName)
    return valueOrName

def setFPGAbits(FPGAblockName,FPGAregName,optList):
    optMask = 0
    optNew = 0
    for opt,val in optList:
        bitpos = 1<<_value("%s_%s_B" % (FPGAregName,opt))
        fieldMask = (1<<_value("%s_%s_W" % (FPGAregName,opt)))-1
        optMask |= bitpos*fieldMask
        optNew  |= bitpos*val
    oldVal = Driver.rdFPGA(FPGAblockName,FPGAregName)
    newVal = ((~optMask) & oldVal) | optNew
    Driver.wrFPGA(FPGAblockName,FPGAregName,newVal)