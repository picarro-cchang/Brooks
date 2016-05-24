from ctypes import create_string_buffer, byref, c_ubyte, c_short, sizeof
from usb import LibUSB

def controlInTransaction(self,var,cmd,value=0,index=0):
    sv = sizeof(var)
    actual = self.usb.usbControlMsg(self.handle,0xC0,cmd,value,index,byref(var),sv,5000)
    if actual != sv:
        raise UsbPacketLengthError("Unexpected packet length %d [%d] in controlIn transaction 0x%2x" % (actual,sv,cmd))
    return

def controlOutTransaction(self,msg,cmd,value=0,index=0):
    sm = sizeof(msg)
    actual = self.usb.usbControlMsg(self.handle,0x40,cmd,value,index,byref(msg),sm,5000)
    if actual != sm:
        raise UsbPacketLengthError("Unexpected packet length %d [%d] in controlOut transaction 0x%2x" % (actual,sm,cmd))
    return

if __name__ == "__main__":
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

    # Execute a vendor command
    result = c_short()
    sv = sizeof(result)
    value = 0
    index = 0
    cmd = 0xD2
    actual = usb.usbControlMsg(handle,0xC0,cmd,value,index,byref(result),sv,5000)
    if actual != sv:
        raise ValueError,"Unexpected packet length %d [%d] in controlIn transaction 0x%2x" % (actual,sv,cmd)
    print "Version: %x" % result.value

    result = c_short()
    sv = sizeof(result)
    value = 0
    index = 0
    cmd = 0xD3
    actual = usb.usbControlMsg(handle,0xC0,cmd,value,index,byref(result),sv,5000)
    if actual != sv:
        raise ValueError,"Unexpected packet length %d [%d] in controlIn transaction 0x%2x" % (actual,sv,cmd)
    print "High speed: %x" % result.value
    
    while True:
        try:
            d = input("Digit to display: ")
            tmp = c_ubyte(d & 0xF)
            usb.usbBulkWrite(handle,epOut,byref(tmp),1,5000)
        except:
            break
    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
