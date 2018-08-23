# Program large serial EEPROM for Cypress FX2 from a 0xC2 mode file

from ctypes import byref, c_ubyte, c_int, create_string_buffer
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

    # Perform bulk write
    epOut = 2
    i = 0
    while True:
        nBytes = input("Number of bytes to write? ")
        if nBytes == 0: break
        tmp = (c_ubyte*nBytes)()
        for k in range(nBytes): 
            tmp[k] = i
            i += 1
        usb.usbBulkWrite(handle,epOut,byref(tmp),nBytes,5000)
        print "Error string: %s" % usb.usbStrerror()

    # tmp = (c_int*32)()
    # for i in range(32): tmp[i] = 0xAA55AA55
    # tmp[0] = 0x01234567
    # tmp[1] = 0x89ABCDEF
    # usb.usbResetep(handle,epOut)
    # usb.usbBulkWrite(handle,epOut,byref(tmp),64,5000)
    # print "Error string: %s" % usb.usbStrerror()
    
    # Perform bulk read
    #epIn = 0x86
    #tmp = (c_int*2)()
    #usb.usbResetep(handle,epIn)
    #usb.usbBulkRead(handle,epIn,byref(tmp),8,5000)
    #print "Error string: %s" % usb.usbStrerror()
    
    version = c_ubyte()
    usb.usbControlMsg(handle,0xC0,0xB0,0x0000,0x00,byref(version),1,5000)
    print "Firmware version %d" % version.value
    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
