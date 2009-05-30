#!/usr/bin/python
#
# File Name: usb.py
# Purpose: Python wrapper for libusb
#
# Notes:
#
# File History:
# 08-05-06 sze   Merged Windows and Linux codes
import sys
from ctypes import _Pointer, create_string_buffer, c_char, c_char_p, c_int, c_ubyte, c_ushort, c_uint, c_ulong
from ctypes import Structure, POINTER, c_void_p, cdll, byref

if sys.platform == "linux2":
    LIBUSB_PATH_MAX          = 4097
elif sys.platform == "win32":
    LIBUSB_PATH_MAX          = 512
else:
    raise ValueError("Unknown platform: %s" % sys.platform)

# Device and/or Interface Class codes
USB_CLASS_PER_INTERFACE = 0
USB_CLASS_AUDIO         = 1
USB_CLASS_COMM          = 2
USB_CLASS_HID           = 3
USB_CLASS_PRINTER       = 7
USB_CLASS_MASS_STORAGE  = 8
USB_CLASS_HUB           = 9
USB_CLASS_DATA          = 10
USB_CLASS_VENDOR_SPEC   = 0xFF

# Descriptor types
USB_DT_DEVICE           = 0x01
USB_DT_CONFIG           = 0x02
USB_DT_STRING           = 0x03
USB_DT_INTERFACE        = 0x04
USB_DT_ENDPOINT         = 0x05
USB_DT_HID              = 0x21
USB_DT_REPORT           = 0x22
USB_DT_PHYSICAL         = 0x23
USB_DT_HUB              = 0x29

# Descriptor sizes per descriptor type
USB_DT_DEVICE_SIZE      = 18
USB_DT_CONFIG_SIZE      = 9
USB_DT_INTERFACE_SIZE   = 9
USB_DT_ENDPOINT_SIZE    = 7
USB_DT_ENDPOINT_AUDIO_SIZE = 9 # Audio extension
USB_DT_HUB_NONVAR_SIZE  = 7

# All standard descriptors have these 2 fields in common
class usb_descriptor_header(Structure):
    _fields_ = [
      ("bLength",c_ubyte),
      ("bDescriptorType",c_ubyte)]

# String descriptor
class usb_string_descriptor(Structure):
    _fields_ = [
        ("bLength",c_ubyte),
        ("bDescriptorType",c_ubyte),
        ("wData",c_ushort*1)]

# HID descriptor
class usb_hid_descriptor(Structure):
    _fields_ = [
        ("bLength",c_ubyte),
        ("bDescriptorType",c_ubyte),
        ("bcdHID",c_ushort),
        ("bCountryCode",c_ubyte),
        ("bNumDescriptors",c_ubyte)]

# Endpoint descriptor
USB_MAXENDPOINTS = 32
class usb_endpoint_descriptor(Structure):
    _fields_ = [
        ("bLength",c_ubyte),
        ("bDescriptorType",c_ubyte),
        ("bEndpointAddress",c_ubyte),
        ("bmAttributes",c_ubyte),
        ("wMaxPacketSize",c_ushort),
        ("bInterval",c_ubyte),
        ("bRefresh",c_ubyte),
        ("bSynchAddress",c_ubyte),
        ("extra",c_char_p),
        ("extralen",c_int)]

USB_ENDPOINT_ADDRESS_MASK       = 0x0f # in bEndpointAddress
USB_ENDPOINT_DIR_MASK           = 0x80

USB_ENDPOINT_TYPE_MASK          = 0x03 # in bmAttributes
USB_ENDPOINT_TYPE_CONTROL       = 0
USB_ENDPOINT_TYPE_ISOCHRONOUS   = 1
USB_ENDPOINT_TYPE_BULK          = 2
USB_ENDPOINT_TYPE_INTERRUPT     = 3

# Interface descriptor
USB_MAXINTERFACES = 32
class usb_interface_descriptor(Structure):
    _fields_ = [
        ("bLength",c_ubyte),
        ("bDescriptorType",c_ubyte),
        ("bInterfaceNumber",c_ubyte),
        ("bAlternateSetting",c_ubyte),
        ("bNumEndpoints",c_ubyte),
        ("bInterfaceClass",c_ubyte),
        ("bInterfaceSubClass",c_ubyte),
        ("bInterfaceProtocol",c_ubyte),
        ("iInterface",c_ubyte),
        ("endpoint",POINTER(usb_endpoint_descriptor)),
        ("extra",c_char_p),
        ("extralen",c_int)]

USB_MAXALTSETTING = 128 # Hard limit

class usb_interface(Structure):
    _fields_ = [
        ("altsetting",POINTER(usb_interface_descriptor)),
        ("num_altsetting",c_int)]

# Configuration descriptor information
USB_MAXCONFIG = 8
class usb_config_descriptor(Structure):
    _fields_ = [
        ("bLength",c_ubyte),
        ("bDescriptorType",c_ubyte),
        ("wTotalLength",c_ushort),
        ("bNumInterfaces",c_ubyte),
        ("bConfigurationValue",c_ubyte),
        ("iConfiguration",c_ubyte),
        ("bmAttributes",c_ubyte),
        ("MaxPower",c_ubyte),
        ("interface",usb_interface),
        ("extra",c_char_p),
        ("extralen",c_int)]

# Device descriptor
class usb_device_descriptor(Structure):
    _fields_ = [
        ("bLength",c_ubyte),
        ("bDescriptorType",c_ubyte),
        ("bcdUSB",c_ushort),
        ("bDeviceClass",c_ubyte),
        ("bDeviceSubClass",c_ubyte),
        ("bDeviceProtocol",c_ubyte),
        ("bMaxPacketSize0",c_ubyte),
        ("idVendor",c_ushort),
        ("idProduct",c_ushort),
        ("bcdDevice",c_ushort),
        ("iManufacturer",c_ubyte),
        ("iProduct",c_ubyte),
        ("iSerialNumber",c_ubyte),
        ("bNumConfigurations",c_ubyte)]

class usb_ctrl_setup(Structure):
    _fields_ = [
        ("bRequestType",c_ubyte),
        ("bRequest",c_ubyte),
        ("wValue",c_ushort),
        ("wIndex",c_ushort),
        ("wLength",c_ushort)]

# Standard requests
USB_REQ_GET_STATUS              = 0x00
USB_REQ_CLEAR_FEATURE           = 0x01
# 0x02 is reserved
USB_REQ_SET_FEATURE             = 0x03
# 0x04 is reserved */
USB_REQ_SET_ADDRESS             = 0x05
USB_REQ_GET_DESCRIPTOR          = 0x06
USB_REQ_SET_DESCRIPTOR          = 0x07
USB_REQ_GET_CONFIGURATION       = 0x08
USB_REQ_SET_CONFIGURATION       = 0x09
USB_REQ_GET_INTERFACE           = 0x0A
USB_REQ_SET_INTERFACE           = 0x0B
USB_REQ_SYNCH_FRAME             = 0x0C

USB_TYPE_STANDARD               = (0x00 << 5)
USB_TYPE_CLASS                  = (0x01 << 5)
USB_TYPE_VENDOR                 = (0x02 << 5)
USB_TYPE_RESERVED               = (0x03 << 5)

USB_RECIP_DEVICE                = 0x00
USB_RECIP_INTERFACE             = 0x01
USB_RECIP_ENDPOINT              = 0x02
USB_RECIP_OTHER                 = 0x03

# Various libusb API related stuff

USB_ENDPOINT_IN                 = 0x80
USB_ENDPOINT_OUT                = 0x00

# Error codes
USB_ERROR_BEGIN                 = 500000

# Data types

class usb_device(Structure):
    pass

class usb_bus(Structure):
    pass

usb_device._fields_ = [
    ("next",POINTER(usb_device)),
    ("prev",POINTER(usb_device)),
    ("filename",c_char*LIBUSB_PATH_MAX),
    ("bus",POINTER(usb_bus)),
    ("descriptor",usb_device_descriptor),
    ("config",POINTER(usb_config_descriptor)),
    ("dev",c_void_p),
    ("devnum",c_ubyte),
    ("num_children",c_ubyte),
    ("children",POINTER(POINTER(usb_device)))]

usb_bus._fields_ = [
    ("next",POINTER(usb_bus)),
    ("prev",POINTER(usb_bus)),
    ("dirname",c_char*LIBUSB_PATH_MAX),
    ("devices",POINTER(usb_device)),
    ("location",c_ulong),
    ("root_dev",POINTER(usb_device))]

class usb_dev_handle(Structure):
    pass

# Load the DLL here
class LibUSB(object):
    def __init__(self):
        DLL_Path = ["libusb0.dll","/usr/lib/libusb-0.1.so.4"]
        for p in DLL_Path:        
            try:
                self.usbDLL = cdll.LoadLibrary(p)
                break
            except:
                continue
        else:
            raise ValueError("Cannot load libusb shared library")

        self.usbOpen = self.usbDLL.usb_open
        self.usbOpen.argtypes = [POINTER(usb_device)]
        self.usbOpen.restype  = POINTER(usb_dev_handle)

        self.usbClose = self.usbDLL.usb_close
        self.usbClose.argtypes = [POINTER(usb_dev_handle)]
        self.usbClose.restype  = c_int

        self.usbGetString = self.usbDLL.usb_get_string
        self.usbGetString.argtypes = [POINTER(usb_dev_handle),c_int,c_int,c_char_p,c_int]
        self.usbGetString.restype  = c_int

        self.usbGetStringSimple = self.usbDLL.usb_get_string_simple
        self.usbGetStringSimple.argtypes = [POINTER(usb_dev_handle),c_int,c_char_p,c_int]
        self.usbGetStringSimple.restype  = c_int

        self.usbGetDescriptorByEndpoint = self.usbDLL.usb_get_descriptor_by_endpoint
        self.usbGetDescriptorByEndpoint.argtypes = [POINTER(usb_dev_handle),c_int,c_ubyte,c_ubyte,\
                                          c_void_p,c_int]
        self.usbGetDescriptorByEndpoint.restype  = c_int

        self.usbGetDescriptor = self.usbDLL.usb_get_descriptor
        self.usbGetDescriptor.argtypes = [POINTER(usb_dev_handle),c_ubyte,c_ubyte,\
                                          c_void_p,c_int]
        self.usbGetDescriptor.restype  = c_int

        self.usbBulkWrite = self.usbDLL.usb_bulk_write
        self.usbBulkWrite.argtypes = [POINTER(usb_dev_handle),c_int,c_void_p,c_int,c_int]
        self.usbBulkWrite.restype  = c_int

        self.usbBulkRead = self.usbDLL.usb_bulk_read
        self.usbBulkRead.argtypes = [POINTER(usb_dev_handle),c_int,c_void_p,c_int,c_int]
        self.usbBulkRead.restype  = c_int

        self.usbInterruptWrite = self.usbDLL.usb_interrupt_write
        self.usbInterruptWrite.argtypes = [POINTER(usb_dev_handle),c_int,c_void_p,\
                                           c_int,c_int]
        self.usbInterruptWrite.restype  = c_int

        self.usbInterruptRead = self.usbDLL.usb_interrupt_read
        self.usbInterruptRead.argtypes = [POINTER(usb_dev_handle),c_int,c_void_p,\
                                          c_int,c_int]
        self.usbInterruptRead.restype  = c_int

        self.usbControlMsg = self.usbDLL.usb_control_msg
        self.usbControlMsg.argtypes = [POINTER(usb_dev_handle),c_int,c_int,c_int,c_int,\
                                       c_void_p,c_int,c_int]
        self.usbControlMsg.restype  = c_int

        self.usbSetConfiguration = self.usbDLL.usb_set_configuration
        self.usbSetConfiguration.argtypes = [POINTER(usb_dev_handle),c_int]
        self.usbSetConfiguration.restype  = c_int

        self.usbClaimInterface = self.usbDLL.usb_claim_interface
        self.usbClaimInterface.argtypes = [POINTER(usb_dev_handle),c_int]
        self.usbClaimInterface.restype  = c_int

        self.usbReleaseInterface = self.usbDLL.usb_release_interface
        self.usbReleaseInterface.argtypes = [POINTER(usb_dev_handle),c_int]
        self.usbReleaseInterface.restype  = c_int

        self.usbSetAltinterface = self.usbDLL.usb_set_altinterface
        self.usbSetAltinterface.argtypes = [POINTER(usb_dev_handle),c_int]
        self.usbSetAltinterface.restype  = c_int

        self.usbResetep = self.usbDLL.usb_resetep
        self.usbResetep.argtypes = [POINTER(usb_dev_handle),c_uint]
        self.usbResetep.restype  = c_int

        self.usbClearHalt = self.usbDLL.usb_clear_halt
        self.usbClearHalt.argtypes = [POINTER(usb_dev_handle),c_uint]
        self.usbClearHalt.restype  = c_int

        self.usbReset = self.usbDLL.usb_reset
        self.usbReset.argtypes = [POINTER(usb_dev_handle)]
        self.usbReset.restype  = c_int

        self.usbStrerror = self.usbDLL.usb_strerror
        self.usbStrerror.argtypes = []
        self.usbStrerror.restype  = c_char_p

        self.usbInit = self.usbDLL.usb_init
        self.usbInit.argtypes = []
        self.usbInit.restype = None

        self.usbSetDebug = self.usbDLL.usb_set_debug
        self.usbSetDebug.argtypes = [c_int]
        self.usbSetDebug.restype = None

        self.usbFindBusses = self.usbDLL.usb_find_busses
        self.usbFindBusses.argtypes = []
        self.usbFindBusses.restype = c_int

        self.usbFindDevices = self.usbDLL.usb_find_devices
        self.usbFindDevices.argtypes = []
        self.usbFindDevices.restype = c_int

        self.usbDevice = self.usbDLL.usb_device
        self.usbDevice.argtypes = [POINTER(usb_dev_handle)]
        self.usbDevice.restype = POINTER(usb_device)

        self.usbGetBusses = self.usbDLL.usb_get_busses
        self.usbGetBusses.argtypes = []
        self.usbGetBusses.restype = POINTER(usb_bus)

        if sys.platform == "linux2":
            self.usbDetachKernelDriverNp = self.usbDLL.usb_detach_kernel_driver_np
            self.usbDetachKernelDriverNp.argtypes = [POINTER(usb_dev_handle),c_int]
            self.usbDetachKernelDriverNp.restype = c_int


    def usbBusses(self):
        # Generator which yields all busses connected to host
        self.usbFindBusses()
        pBus = self.usbGetBusses()
        while pBus:
            yield pBus.contents
            pBus = pBus.contents.next

    def usbDevices(self,bus):
        # Generator which yields all devices connected to specified bus
        self.usbFindDevices()
        pDev = bus.devices
        while pDev:
            yield pDev
            pDev = pDev.contents.next

    def usbStringSimple(self,handle,id):
        # Pythonic interface to usbGetStringSimple
        result = create_string_buffer('\000' * 256)
        self.usbGetStringSimple(handle,id,result,256)
        return result.value

    def usbDeviceDescrDict(self,d):
        # Returns dictionary representation of device descriptor
        result = {}
        for f in d._fields_:
            r = getattr(d,f[0])
            if not isinstance(r,_Pointer):
                result[f[0]] = r
        return result

    def usbDeviceDict(self,d):
        # Returns dictionary representation of device
        result = {}
        for f in d._fields_:
            r = getattr(d,f[0])
            if not isinstance(r,_Pointer):
                result[f[0]] = r
        return result

    def usbDeviceChain(self,d):
        # Returns list of all devices linked to d
        result = [self.usbDeviceDict(d)]
        df = d
        while df.next:
            df = df.next.contents
            result.append(self.usbDeviceDict(df))
        df = d
        while df.prev:
            df = df.prev.contents
            result.insert(0,self.usbDeviceDict(df))
        return result

    def openDev(self):
        pass

if __name__ == "__main__":
    myVid = 0x547
    myPid = 0x1002
    epOut = 0x02

    usb = LibUSB()
    usb.usbInit()
    print "usbFindBusses returns %d"  % usb.usbFindBusses()
    print "usbFindDevices returns %d" % usb.usbFindDevices()
    handle = None
    for bus in usb.usbBusses():
        assert isinstance(bus,usb_bus)
        print bus.dirname
        for pDev in usb.usbDevices(bus):
            dev = pDev.contents
            assert isinstance(dev,usb_device)
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
    while True:
        try:
            d = input("Digit to display: ")
            tmp = c_ubyte(d & 0xF)
            usb.usbBulkWrite(handle,epOut,byref(tmp),1,5000)
        except SyntaxError:
            break
        except NameError:
            break
    usb.usbReleaseInterface(handle,0)
    usb.usbClose(handle)
    