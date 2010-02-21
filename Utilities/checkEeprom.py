# Test program to interact with logic board EEPROM

import socket
import time
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.hostDasInterface import Operation, OperationGroup
from Host.Common.StringPickler import StringAsObject, ObjAsString

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateSystem")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

if __name__ == "__main__":
    # Check for I2C
    print "Logic board EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x55]))
 #
    myEnv = Byte64EnvType()
    for i in range(16):
        myEnv.buffer[i] = 0x11111111 * (15-i)
    Driver.wrEnvFromString("BYTE64_ENV",Byte64EnvType,ObjAsString(myEnv))
    #print "Eeprom Ready returns: ", Driver.doOperation(Operation("ACTION_EEPROM_READY",[0]))
    op = Operation("ACTION_EEPROM_WRITE",[0,0x12C0,64],"BYTE64_ENV")
    Driver.doOperation(op)
    #print "Eeprom Ready returns: ", Driver.doOperation(Operation("ACTION_EEPROM_READY",[0]))
    myEnv = Byte64EnvType()
    for i in range(16):
        myEnv.buffer[i] = 0
    Driver.wrEnvFromString("BYTE64_ENV",Byte64EnvType,ObjAsString(myEnv))
    raw_input("Press return to read...")
    op = Operation("ACTION_EEPROM_READ",[0,0x12C0,64],"BYTE64_ENV")
    Driver.doOperation(op)
    result = StringAsObject(Driver.rdEnvToString("BYTE64_ENV",Byte64EnvType),Byte64EnvType)
    print ["%08x" % result.buffer[i] for i in range(16)]
    #print "Eeprom Ready returns: ", Driver.doOperation(Operation("ACTION_EEPROM_READY",[0]))
