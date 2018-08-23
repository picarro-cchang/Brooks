from ctypes import sizeof, byref, c_ubyte
from usb import LibUSB
from time import clock

if __name__ == "__main__":
    myVid = 0x547
    myPid = 0x1002
    epOut = 0x02
    epIn = 0x86
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
    if handle == None:
        raise ValueError("Device with VID: 0x%x, PID: 0x%x not found" % (myVid,myPid))
    if usb.usbSetConfiguration(handle,1) < 0:
        usb.usbClose(handle)
        raise ValueError("Setting config 1 failed")
    if usb.usbClaimInterface(handle,0) < 0:
        usb.usbClose(handle)
        raise ValueError("Claiming interface 0 failed")
    buf1 = (c_ubyte*4096)()
    buf2 = (c_ubyte*4096)()
    print sizeof(buf1)
    for i in range(sizeof(buf1)): buf1[i] = i
    niter = 1000
    tStart = time()
    for i in range(niter):
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        usb.usbBulkRead(handle,epIn,buf2,sizeof(buf2),1000)
        # for j in range(sizeof(buf1)): assert(buf1[j] == buf2[j])
    tStop = time()
    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
    print "Time per iteration: %s" % ((tStop-tStart)/(10*niter),)
    