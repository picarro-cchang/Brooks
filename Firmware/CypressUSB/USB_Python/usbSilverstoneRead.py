# Program large serial EEPROM for Cypress FX2 from a 0xC2 mode file

from ctypes import byref, c_ubyte, create_string_buffer
from usb import LibUSB
from hexfile import HexFile
from time import sleep
from cStringIO import StringIO
from array import array
from sys import stdout

if __name__ == "__main__":
    # Initially expect to have Cypress chip without EEPROM
    myVid = 0x4B4
    myPid = 0x1002
    
    usb = LibUSB()
    usb.usbInit()
    #print "usbFindBusses returns %d"  % usb.usbFindBusses()
    #print "usbFindDevices returns %d" % usb.usbFindDevices()
    handle = None
    for bus in usb.usbBusses():
        #print bus.dirname
        for pDev in usb.usbDevices(bus):
            dev = pDev.contents
            #print "%s,%x,%x" % (dev.filename, dev.descriptor.idVendor, dev.descriptor.idProduct)
            if dev.descriptor.idVendor == myVid and dev.descriptor.idProduct == myPid:
                handle = usb.usbOpen(pDev)
    if handle == None:
        raise ValueError("Device with VID: 0x%x, PID: 0x%x not found" % (myVid,myPid))
    if usb.usbSetConfiguration(handle,1) < 0:
        usb.usbClose(handle)
        raise ValueError("Setting config 1 failed")
    if usb.usbClaimInterface(handle,0) < 0:
        usb.usbClose(handle)
        raise ValueError("Claiming interface 0 failed")

    # Perform vendor command 

    version = c_ubyte()
    usb.usbControlMsg(handle,0xC0,0xB0,0x0000,0x00,byref(version),1,5000)
    print "Firmware version %d" % version.value

    resets = c_ubyte()
    usb.usbControlMsg(handle,0xC0,0xB3,0x0000,0x00,byref(resets),1,5000)
    print "CPLD reset count %d" % resets.value

    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
