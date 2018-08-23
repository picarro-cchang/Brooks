from ctypes import create_string_buffer, byref, c_ubyte
from usb import LibUSB

if __name__ == "__main__":
    myVid = 0x3EF
    myPid = 0x1001
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
                print pDev
                handle = usb.usbOpen(pDev)
                break
        if handle != None: break
    
    if handle == None:
        raise ValueError("Device with VID: 0x%x, PID: 0x%x not found" % (myVid,myPid))
    print usb.usbDeviceDict(dev)
    print usb.usbDeviceDescrDict(dev.descriptor)
    print usb.usbDeviceChain(dev)
    
    if usb.usbSetConfiguration(handle,1) < 0:
        usb.usbClose(handle)
        raise ValueError("Setting config 1 failed")
    if usb.usbClaimInterface(handle,0) < 0:
        usb.usbClose(handle)
        raise ValueError("Claiming interface 0 failed")
    while True:
        try:
            d = input("Digit to display: ")
            tmp = c_ubyte(d & 0xF)
            usb.usbBulkWrite(handle,epOut,byref(tmp),1,5000)
        except:
            break
    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
