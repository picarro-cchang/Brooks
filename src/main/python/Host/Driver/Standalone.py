import sys
import os
from Host.Common.hostDasInterface import DasInterface, HostToDspSender
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.autogen import interface

# Stand-alone to start communicating with a running system

if __name__ == "__main__":
    configFile = "../../AppConfig/Config/Driver/Driver.ini"
    config = CustomConfigObj(configFile)
    basePath = os.path.split(configFile)[0]
    stateDbFile = os.path.join(basePath, config["Files"]["instrStateFileName"])
    instrConfigFile = os.path.join(basePath, config["Files"]["instrConfigFileName"])
    usbFile  = os.path.join(basePath, config["Files"]["usbFileName"])
    dspFile  = os.path.join(basePath, config["Files"]["dspFileName"])
    fpgaFile = os.path.join(basePath, config["Files"]["fpgaFileName"])
    dasInterface = DasInterface(stateDbFile,usbFile,dspFile,fpgaFile,False)
    usbSpeed = dasInterface.startUsb()
    print "USB enumerated at %s speed" % (("full","high")[usbSpeed])
    timeout = 5
    sender = HostToDspSender(dasInterface.analyzerUsb,timeout)
    print "HostToDspSender id is: ", id(sender)
    # Try to read from DSP host area
    noop_original = sender.rdRegUint(interface.NOOP_REGISTER)
    print "NOOP_REGISTER: %x" % noop_original
    print "VERIFY_INIT_REGISTER: %x" % sender.rdRegUint(interface.VERIFY_INIT_REGISTER)
    # Try to write to a DSP register
    seqNum = sender.getSequenceNumber()
    print "Sequence number: %s, %s" % (seqNum, sender.seqNum)
    sender.wrRegUint(interface.NOOP_REGISTER,0xA5A5A5A5)
    print "After write, NOOP_REGISTER: %x" % sender.rdRegUint(interface.NOOP_REGISTER)
    sender.wrRegUint(interface.NOOP_REGISTER,noop_original)
    print "After second write, NOOP_REGISTER: %x" % sender.rdRegUint(interface.NOOP_REGISTER)
    print "HostToDspSender id is: ", id(HostToDspSender())