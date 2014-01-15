from ctypes import byref, c_ubyte, create_string_buffer
from usb import LibUSB
from hexfile import HexFile
from time import sleep
from cStringIO import StringIO
from array import array

if __name__ == "__main__":
#    myVid = 0x4B4
#    myPid = 0x81
    myVid = 0x4B4
    myPid = 0x1002
    
    epOut = 0x02
        
    usb = LibUSB()
    usb.usbInit()
    print "usbFindBusses returns %d"  % usb.usbFindBusses()
    print "usbFindDevices returns %d" % usb.usbFindDevices()
    handle = None
    for bus in usb.usbBusses():
        print bus.dirname
        for pDev in usb.usbDevices(bus):
            dev = pDev.contents
            print "%s,%x,%x" % (dev.filename, dev.descriptor.idVendor, dev.descriptor.idProduct)
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

    # Try to reset the 8051 by sending it a vendor command
    #usb.usbControlMsg(handle,0x40,0xA0,0xE600,0x00,byref(c_ubyte(0x1)),1,5000)
    #usb.usbControlMsg(handle,0x40,0xA0,0xE600,0x00,byref(c_ubyte(0x0)),1,5000)

    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
