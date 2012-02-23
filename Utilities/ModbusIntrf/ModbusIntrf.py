"""
File Name: ModbusIntrf.py

Purpose:
    This is the module responsible for managing Modbus communication with Costech CM remote interface

File History:
    02-13-12 Alex Lee Created file
"""

import os
import sys
import time
import serial
import itertools
import modbus
import utils
import defines as cst
import _winreg as winreg
import modbus_rtu

def scanSerialPorts():
    """ Uses the Win32 registry to return an
        iterator of serial (COM) ports
        existing on this computer.
    """
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
    except WindowsError:
        raise IterationError
    for i in itertools.count():
        try:
            val = winreg.EnumValue(key, i)
            yield str(val[1])
        except EnvironmentError:
            break
            
class ModbusIntrf(object):
    def __init__(self):
        # Search for Modbus interface with CM
        self.ser = None
        self.master = None
        
    def searchSerPort(self):
        for p in scanSerialPorts():
            if self.ser:
                self.ser.close()
                self.ser = None
                self.master = None
            try:
                self.ser = serial.Serial(port=p, baudrate=9600, bytesize=8, parity=serial.PARITY_NONE, stopbits=1, xonxoff=1)
                time.sleep(2)
            except:
                continue
            try:
                print "Testing %s..." % (p)
                self.master = modbus_rtu.RtuMaster(self.ser)
                self.master.set_timeout(5.0)
                self.master.set_verbose(True)
                self.testIntrf()
                break
            except:
                pass
                
        if not self.master:
            if self.ser:
                self.ser.close()
                self.ser = None
            raise Exception, "Costech Modbus interface not found"
        else:
            print "Costech Modbus interface found at %s" % (p)
            return p
            
    def trigger(self):
        try:
            self.master.execute(1, cst.WRITE_SINGLE_REGISTER, 2100, output_value=1)
            print "CM triggered"
        except modbus.ModbusError, e:
            print "%s- Code=%d" % (e, e.get_exception_code())
            self.ser.close()
            self.ser = None
        except Exception, err:
            print "ERROR: %r" % err
            self.ser.close()
            self.ser = None

    def testIntrf(self):
        try:
            ret = self.master.execute(1, cst.READ_HOLDING_REGISTERS, 2014, quantity_of_x=1)
            if ret[0] in [1,2,3]:
                print "Interface test succeeded"
                return
            else:
                raise
        except modbus.ModbusError, e:
            print "%s- Code=%d" % (e, e.get_exception_code())
            self.ser.close()
            self.ser = None
            raise
        except Exception, err:
            print "ERROR: %r" % err
            self.ser.close()
            self.ser = None
            raise
            
if __name__ == "__main__":
    m = ModbusIntrf()
    