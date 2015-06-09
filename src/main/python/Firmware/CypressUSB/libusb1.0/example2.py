#!/usr/bin/env python
import usb1

def main():
    myVid = 0x3EF
    myPid = 0x1001
    epOut = 2
    
    context = usb1.USBContext()
    handle = None
    try:
        device = context.getByVendorIDAndProductID(myVid, myPid)
        if device is None:
            raise ValueError("Device with VID: 0x%x, PID: 0x%x not found" % (myVid,myPid))
        print 'ID %04x:%04x' % (device.getVendorID(), device.getProductID()), '->'.join(str(x) for x in ['Bus %03i' % (device.getBusNumber(), )] + device.getPortNumberList()), 'Device', device.getDeviceAddress()
        handle = device.open()
        handle.claimInterface(0)
        
        while True:
            try:
                d = input("Digit to display: ")
                tmp = chr(d & 0xF)
                handle.bulkWrite(epOut, tmp, timeout=5000)
            except:
                break

    finally:
        if handle:
            handle.releaseInterface(0)
            handle.close()
        context.exit()
        
if __name__ == '__main__':
    main()
