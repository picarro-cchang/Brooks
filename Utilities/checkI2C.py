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
    print "I2C0 MUX status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x55]))
    print "I2C1 MUX status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,0,0x71]))
    print "Power board I2C DIO status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,4,0x71]))

    print "Logic board temperature sensor status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x4E]))
    print "Logic board EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x55]))
    print "Logic board laser TEC monitor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,0,0x14]))
    
    print "Laser 1 thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x26]))
    print "Laser 1 current ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x14]))
    print "Laser 1 EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x50]))
    print "Laser 2 thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,1,0x26]))
    print "Laser 2 current ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,1,0x14]))
    print "Laser 2 EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,1,0x50]))
    print "Laser 3 thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,2,0x26]))
    print "Laser 3 current ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,2,0x14]))
    print "Laser 3 EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,1,0x50]))
    print "Laser 4 thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,3,0x26]))
    print "Laser 4 current ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,3,0x14]))
    print "Laser 4 EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,1,0x50]))
 
    print "Logic board EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,0,0x55]))
    print "WLM board EEPROM status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,0,0x50]))
    print "Warm box thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,0,0x15]))
    print "Etalon thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,0,0x27]))
    print "Warm box heatsink thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[1,0,0x26]))

    print "Cavity thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,7,0x26]))
    print "Hot box heatsink thermistor ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,7,0x27]))
    print "Cavity pressure ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,7,0x24]))
    print "Ambient pressure ADC status: %d"  % Driver.doOperation(Operation("ACTION_I2C_CHECK",[0,7,0x17]))
