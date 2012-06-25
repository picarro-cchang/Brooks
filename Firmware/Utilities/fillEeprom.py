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
    ident = "LASER1_EEPROM"
    print "%s status: %d"  % (ident,Driver.doOperation(Operation("ACTION_I2C_CHECK",i2cByIdent[ident][1:4])))
    #
    myEnv = Byte64EnvType()
    raw_input("Press return to write...")
    for addr in range(0,4096,32):
        for i in range(8):
            myEnv.buffer[i] = addr//4 + i
        Driver.wrEnvFromString("BYTE64_ENV",Byte64EnvType,ObjAsString(myEnv))
        op = Operation("ACTION_EEPROM_WRITE",[i2cByIdent[ident][0],addr,32],"BYTE64_ENV")
        Driver.doOperation(op)
        print addr
        while not Driver.doOperation(Operation("ACTION_EEPROM_READY",[i2cByIdent[ident][0]])):
            time.sleep(0.01)
    raw_input("Press return to read...")
    for addr in range(0,4096,32):
        op = Operation("ACTION_EEPROM_READ",[i2cByIdent[ident][0],addr,32],"BYTE64_ENV")
        Driver.doOperation(op)
        result = StringAsObject(Driver.rdEnvToString("BYTE64_ENV",Byte64EnvType),Byte64EnvType)
        print "%04x:"  % addr,["%08x" % result.buffer[i] for i in range(8)]
        raw_input()