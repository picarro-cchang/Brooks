import sys
if "../../Expt/NewHostCore/Common" not in sys.path: sys.path.append("../../Expt/NewHostCore/Common")

import ss_autogen
from usb import LibUSB, USB_ENDPOINT_IN, USB_ENDPOINT_OUT
from crc import CRC_calcChecksum
from ctypes import addressof, byref, c_float, c_ubyte, c_uint, c_uint16, cast
from ctypes import memmove, POINTER, sizeof, string_at, Structure
from random import randrange
import unittest
import inspect
import time
from socket import htonl

ERR_PROB = 0.0
DEBUG = False

# VENDOR_ID = 0x547
# PRODUCT_ID = 0x81
VENDOR_ID = 0x4B4
PRODUCT_ID = 0x1002

TRANSPORT_DEFAULT_OUT_ENDPOINT = USB_ENDPOINT_OUT | 2
TRANSPORT_DEFAULT_IN_ENDPOINT  = USB_ENDPOINT_IN  | 6
TRANSPORT_DEBUG_OUT_ENDPOINT   = USB_ENDPOINT_OUT | 4
TRANSPORT_DEBUG_IN_ENDPOINT    = USB_ENDPOINT_IN  | 8

fragmentErrorStrings = {}
FLAG_LAST_FRAGMENT_INCOMPLETE_ERROR    = 0x1
fragmentErrorStrings[FLAG_LAST_FRAGMENT_INCOMPLETE_ERROR] = "Last fragment incomplete"
FLAG_FIRST_FRAGMENT_MISSING_ERROR      = 0x2
fragmentErrorStrings[FLAG_FIRST_FRAGMENT_MISSING_ERROR]   = "First fragment missing"
FLAG_FRAGMENT_ORDER_ERROR              = 0x4
fragmentErrorStrings[FLAG_FRAGMENT_ORDER_ERROR]           = "Fragment out of order"
FLAG_FRAGMENT_NUMBER_COMMANDS_ERROR    = 0x8
fragmentErrorStrings[FLAG_FRAGMENT_NUMBER_COMMANDS_ERROR] = "Number of commands error"
FLAG_FRAGMENT_SIZE_ERROR               = 0x10
fragmentErrorStrings[FLAG_FRAGMENT_SIZE_ERROR]            = "Fragment size error"
FLAG_CRC_ERROR                         = 0x20
fragmentErrorStrings[FLAG_CRC_ERROR]                      = "CRC error"
FLAG_RX_INDEX_ERROR                    = 0x40
fragmentErrorStrings[FLAG_RX_INDEX_ERROR]                 = "Rx index error"

class FragmentHeader(Structure):
    _fields_ = [("fragNum",c_uint16, 8),
                ("fragTotal",c_uint16, 8),
                ("fragStatus",c_uint16, 8),
                ("numberCommands",c_uint16, 8),
                ("crc",c_uint)]

class CommandHeader(Structure):
    _fields_ = [("type",c_uint16,4),
                ("region",c_uint16,4),
                ("status",c_uint16,8),
                ("length",c_uint16,16),
                ("address",c_uint)]

TRANSPORT_FRAGMENT_SIZE = 64
TRANSPORT_FRAGMENT_PAYLOAD_SIZE = TRANSPORT_FRAGMENT_SIZE - sizeof(FragmentHeader)
TRANSPORT_DEFAULT_CONFIG = 1
TRANSPORT_DEFAULT_INTERFACE = 0
TRANSPORT_DEFAULT_COMMAND_TIMEOUT_MS = 3000
    
Fragment = c_ubyte * TRANSPORT_FRAGMENT_SIZE

class TransportError(Exception):
    pass
class TransportOpenCloseError(TransportError):
    pass
class TransportClaimInterfaceError(TransportError):
    pass
class TransportCommError(TransportError):
    pass
class TransportFragmentSizeError(TransportError):
    pass
class TransportTxError(TransportError):
    pass
class TransportRxError(TransportError):
    pass
class TransportReadFragmentTimeout(TransportError):
    pass

# List of regions   
REGISTER_REGION             = 1
MCU_REGION                  = 2   
MCU_IMAGE_REGION            = 3   
DSP_REGION                  = 4   
DSP_IMAGE_REGION            = 5   
FPGA_REGION                 = 6   
FLASH_REGION                = 7   
CAL_LASER_BASED_REGION      = 8   
RTC_REGION                  = 9   
RD_SCHEME_REGION            = 10   
RD_CAPTURE_BUFFER_REGION    = 11   
RD_OSC_BUFFER_REGION        = 12   
WLMCAL_REGION               = 13   
LSRCAL_REGION               = 14   
JTAG_IMAGE_REGION           = 15

# List of operation types   
READ_OPERATION              = 1   
WRITE_OPERATION             = 2   
START_OPERATION             = 3   
STOP_OPERATION              = 4   
ABORT_OPERATION             = 5   
FAIL_OPERATION              = 6

# List of access type   
PUBLIC_ACCESS               = 1   
PRIVATE_ACCESS              = 2

def printCtypesStructure(struct):
    for f in type(struct)._fields_:
        print "%16s: %s" % (f[0],getattr(struct,f[0])) 

def byteswap(data):
    """Byte swap data as 32-bit chunks"""
    nbytes = sizeof(data)
    nlongs = nbytes // 4
    longArray = (c_uint * nlongs).from_address(addressof(data))
    for i in range(nlongs): longArray[i] = htonl(longArray[i])

def dumpCommandHeader(h):
    print "Command/Response Header:"
    print "type: 0x%x, region: 0x%x, status: 0x%x, length: %d, address: 0x%x" % (h.type,h.region,h.status,h.length,h.address)

def dumpPayload(payload):
    print "Payload:"
    for p in payload: print "%s" % p,
    print
    
class DasUSB(object):
    def __init__(self):
        self.usb = LibUSB()
        self.usbHandle = None
        self.vid = None
        self.pid = None
        self.txFragmentHeader = FragmentHeader()
        self.rxFragmentHeader = FragmentHeader()
        self.txBuffer = Fragment()
        self.txOffset = 0
        self.rxBuffer = Fragment()
        self.rxOffset = 0
        self.commandTimeout = TRANSPORT_DEFAULT_COMMAND_TIMEOUT_MS
        self.debug = DEBUG
        self.errProb = ERR_PROB
        
    def writeFragment(self,fragment,timeout=None):
        if timeout == None: timeout = self.commandTimeout
        if self.debug:
            print "writeFragment called"
            buffer = cast(byref(fragment),POINTER(c_ubyte))
            for i in range(TRANSPORT_FRAGMENT_SIZE): 
                print "%02x" % int(buffer[i]),
                if (i+1)%8 == 0: print
            print
        byteswap(fragment)
        ret = self.usb.usbBulkWrite(self.usbHandle,self.outEp,byref(fragment),TRANSPORT_FRAGMENT_SIZE,timeout)
        if ret < 0:
            raise TransportCommError("usbBulkWrite returns error %s (%d)" % (self.usb.usbStrerror(),ret))
        if ret != TRANSPORT_FRAGMENT_SIZE:
            raise TransportFragmentSizeError("writeFragment only wrote %s bytes (should be %s)" % (ret,TRANSPORT_FRAGMENT_SIZE))
        byteswap(fragment)
        
    def readFragment(self,fragment,timeout=None):
        if timeout == None: timeout = self.commandTimeout
        ret = self.usb.usbBulkRead(self.usbHandle,self.inEp,byref(fragment),TRANSPORT_FRAGMENT_SIZE,timeout)
        if ret < 0:
            raise TransportCommError("usbBulkRead returns error %s (%d)" % (self.usb.usbStrerror(),ret))
        if ret != TRANSPORT_FRAGMENT_SIZE:
            raise TransportFragmentSizeError("readFragment only read %s bytes (should be %s)" % (ret,TRANSPORT_FRAGMENT_SIZE))
        byteswap(fragment)
        if self.debug:
            print "readFragment called"
            buffer = cast(byref(fragment),POINTER(c_ubyte))
            for i in range(TRANSPORT_FRAGMENT_SIZE): 
                print "%02x" % int(buffer[i]),
                if (i+1)%8 == 0: print
            print
    
    def _claimInterfaceWrapper(self,func,*args,**kwargs):
        """Wraps function call between claim interface and release interface. Raises TransportClaimInterfaceError on failure"""
        if self.usbHandle == None: raise TransportOpenCloseError("USB not open")
        if self.debug: print "About to claim interface"
        stat = self.usb.usbClaimInterface(self.usbHandle,TRANSPORT_DEFAULT_INTERFACE)
        if stat < 0:
            #self.usb.usbReset(self.usbHandle)
            self.usbHandle = None
            self.TRANSPORT_open(self.vid,self.pid)
            raise TransportClaimInterfaceError("Error %s (%d) while claiming interface for %s" % (self.usb.usbStrerror(),stat,func.__name__))
        else:
            try:
                return func(*args,**kwargs)
            finally:
                if self.debug: print "About to release interface"
                stat = self.usb.usbReleaseInterface(self.usbHandle,TRANSPORT_DEFAULT_INTERFACE)
                if stat < 0:
                    raise TransportClaimInterfaceError("Error %s (%d) while releasing interface for %s" % (self.usb.usbStrerror(),stat,func.__name__))

    #def _claimInterfaceWrapper(self,func,*args,**kwargs):
    #    return func(*args,**kwargs)
                
    def TRANSPORT_debug(self,enable):
        self.debugEnabled = enable
        if enable:
            self.inEp  = TRANSPORT_DEBUG_IN_ENDPOINT
            self.outEp = TRANSPORT_DEBUG_OUT_ENDPOINT
        else:
            self.inEp  = TRANSPORT_DEFAULT_IN_ENDPOINT
            self.outEp = TRANSPORT_DEFAULT_OUT_ENDPOINT

#        print "Unimplemented function %s called" % inspect.getframeinfo(inspect.currentframe())[2]

    def TRANSPORT_initTxFragmentHeader(self):
        self.txFragmentHeader.crc = 0
        self.txFragmentHeader.fragNum = 1
        self.txFragmentHeader.fragTotal = 1
        self.txFragmentHeader.fragStatus = 0
        self.txFragmentHeader.numberCommands = 0
        self.txOffset = sizeof(FragmentHeader)
    
    def TRANSPORT_initRxFragmentHeader(self):
        self.rxFragmentHeader.fragNum = 0
        self.rxFragmentHeader.fragTotal = 0
        self.rxFragmentHeader.numberCommands = 0
        self.rxOffset = sizeof(FragmentHeader)
 
    def TRANSPORT_init(self):
        self.usb.usbInit()
        self.TRANSPORT_initTxFragmentHeader()
        self.TRANSPORT_initRxFragmentHeader()
        self.TRANSPORT_debug(False)
        return 0
        
    def TRANSPORT_open(self,vid,pid):
        self.vid = vid
        self.pid = pid
        for bus in self.usb.usbBusses():
            for pDev in self.usb.usbDevices(bus):
                dev = pDev.contents
                # print "%s,%x,%x" % (dev.filename, dev.descriptor.idVendor, dev.descriptor.idProduct)
                if dev.descriptor.idVendor == self.vid and dev.descriptor.idProduct == self.pid:
                    self.usbHandle = self.usb.usbOpen(pDev)
        if self.usbHandle == None:
            raise TransportOpenCloseError("Device with VID: 0x%x, PID: 0x%x not found" % (self.vid,self.pid))
        if self.usb.usbSetConfiguration(self.usbHandle,TRANSPORT_DEFAULT_CONFIG) < 0:
            self.usb.usbClose(self.usbHandle)
            self.usbHandle = None
            self.usb.usbInit()
            raise TransportOpenCloseError("Setting config %d failed on open" % (TRANSPORT_DEFAULT_CONFIG,))
        # Claim and release the default interface to check that this works        
        try:
            self._claimInterfaceWrapper(lambda:None)
        except TransportClaimInterfaceError:
            self.usb.usbClose(self.usbHandle)
            self.usbHandle = None
            self.usb.usbInit()
            raise
        # self.usb.usbClaimInterface(self.usbHandle,TRANSPORT_DEFAULT_INTERFACE) #
        return 0

    def TRANSPORT_close(self,ignoreErrors=False):
        try:
            if self.usbHandle != None:
                # self.usb.usbReleaseInterface(self.usbHandle,TRANSPORT_DEFAULT_INTERFACE) #
                ret = self.usb.usbClose(self.usbHandle)
                self.usbHandle = None
                if ret < 0: raise TransportOpenCloseError("usbClose raises error %s (%d)" % (self.usb.usbStrerror(),ret))
            else:
                raise TransportOpenCloseError("TRANSPORT_close called with null usb handle")
            return 0
        except:
            if ignoreErrors: return 0
            raise
        
    def TRANSPORT_loopback_test(self):
        """Runs the diagnostic loopback test in the Cypress software and returns a list of indices at which failures occured"""
        saved = self.debugEnabled
        f = Fragment()
        for i in range(TRANSPORT_FRAGMENT_SIZE): f[i] = randrange(256)
        g = Fragment()
        self.TRANSPORT_debug(True)
        def _loopback_test():
            self.writeFragment(f)
            self.readFragment(g)
        try:
            self._claimInterfaceWrapper(_loopback_test)
            badIndices = []
            for i in range(TRANSPORT_FRAGMENT_SIZE):
                if g[i] != f[i] | 0x80: badIndices.append(i)
            return badIndices
        finally:
            self.TRANSPORT_debug(saved)

    def TRANSPORT_sendFragment(self):
        """Send any pending commands in the current fragment. Any errors cause an exception"""
        crc = CRC_calcChecksum(0,self.txFragmentHeader,4)
        crc = CRC_calcChecksum(crc,(c_ubyte*TRANSPORT_FRAGMENT_PAYLOAD_SIZE).\
        from_address(addressof(self.txBuffer)+sizeof(FragmentHeader)),TRANSPORT_FRAGMENT_PAYLOAD_SIZE)

        if randrange(1000)>=1000 * self.errProb:
            self.txFragmentHeader.crc = crc
        else:
            print "CRC error in sendFragment"
            self.txFragmentHeader.crc = crc^1
        
        memmove(byref(self.txBuffer),byref(self.txFragmentHeader),sizeof(FragmentHeader))
        self.writeFragment(self.txBuffer)

    def TRANSPORT_getFragment(self):
        """Get a single fragment from the USB endpoint, validate checksum and return the 
        fragment header and payload. Throws an exception if unsuccessful."""
        try:
            self.readFragment(self.rxBuffer,200)
        except TransportError,e:
            raise TransportReadFragmentTimeout("Timeout in readFragment: %s" % e)
        fragHeader = FragmentHeader()
        memmove(byref(fragHeader),byref(self.rxBuffer),sizeof(FragmentHeader))
        stat = fragHeader.fragStatus
        errors = []
        for flag in fragmentErrorStrings:
            if stat & flag: errors.append(fragmentErrorStrings[flag])
        if stat != 0:
            raise TransportTxError(", ".join(errors))

        if randrange(1000)<1000 * self.errProb:
            print "CRC error introduced in getFragment"
            fragHeader.crc = fragHeader.crc^1

        fragPayload = (c_ubyte*TRANSPORT_FRAGMENT_PAYLOAD_SIZE).\
        from_address(addressof(self.rxBuffer)+sizeof(FragmentHeader))
        # Verify checksum
        crc = CRC_calcChecksum(0,self.rxBuffer,4)
        crc = CRC_calcChecksum(crc,fragPayload,TRANSPORT_FRAGMENT_PAYLOAD_SIZE)

        if crc != fragHeader.crc:
            raise TransportRxError("CRC error, received: %08x, expected: %08x" % (fragHeader.crc,crc))
        return fragHeader, fragPayload

    awaitingFirst = 1
    withinResponse = 2
    skipRemaining = 3
    
    def TRANSPORT_getResponse(self,responseHeader,payload):
        """Get a response from the DAS. Result is placed in payload, and is truncated if there is 
        insufficient space. Returns number of bytes copied to payload. Throws an exception on an 
        error or timeout."""
        
        maxLength = sizeof(payload)
        desiredFragment = 1
        state = DasUSB.awaitingFirst
        payloadOffset = 0
        
        while True: # Loop getting fragments associated with the required response
            try:
                fragPayloadOffset = 0
                fragHeader, fragPayload = self.TRANSPORT_getFragment()
            except TransportReadFragmentTimeout:
                raise
            except Exception, e: # Loop until we get a fragment with fragNum == fragTotal
                errMsg = "%s" % e
                print "Error %s when calling TRANSPORT_getFragment" % errMsg
                state = DasUSB.skipRemaining

            if state == DasUSB.awaitingFirst:    
                if fragHeader.fragNum != 1: continue # loop for next
                # Found first fragment
                memmove(byref(responseHeader),addressof(fragPayload),sizeof(CommandHeader))
                fragPayloadOffset += sizeof(CommandHeader)
                dataLeft = responseHeader.length
                totalFragments = fragHeader.fragTotal
                state = DasUSB.withinResponse
            elif state == DasUSB.withinResponse:
                # Check for fragment assembly problems
                if fragHeader.fragNum != desiredFragment: 
                    errMsg = "Received fragment %d when expecting %d" % (fragHeader.fragNum,desiredFragment)
                    state = DasUSB.skipRemaining
                if fragHeader.fragTotal != totalFragments:
                    errMsg = "fragTotal changed from %d to %d" % (totalFragments,fragHeader.fragTotal)
                    state = DasUSB.skipRemaining
                
            if state == DasUSB.skipRemaining:
                if fragHeader.fragNum == fragHeader.fragTotal:
                    raise TransportAssemblyError(errMsg)
            else:
                # Transfer from the fragment payload into the response payload
                bufferLeft = sizeof(fragPayload) - fragPayloadOffset
                nbytes = min(bufferLeft,maxLength)
                if nbytes>0: 
                    memmove(addressof(payload)+payloadOffset,addressof(fragPayload)+fragPayloadOffset,nbytes)
                dataLeft -= nbytes
                payloadOffset += nbytes
                maxLength -= nbytes
                if fragHeader.fragNum != fragHeader.fragTotal:
                    desiredFragment = fragHeader.fragNum + 1
                else:
                    # print "Fragment reassembly successful"
                    # dumpCommandHeader(responseHeader)
                    # dumpPayload(payload)
                    return responseHeader.length-dataLeft
    
    def TRANSPORT_sendCommand(self,commandHeader,payload):
        """Transmit a command to the DAS. Note that the payload length must be written 
        into commandHeader.length. Any errors cause an exception to be thrown"""
        self.TRANSPORT_initTxFragmentHeader()
        # The command and data occupy sizeof(CommandHeader) + length bytes. These have to be broken up into fragments 
        #  each with a header occupying sizeof(FragmentHeader) bytes, so there are TRANSPORT_FRAGMENT_PAYLOAD_SIZE bytes 
        #  available per fragment
        totalLength = commandHeader.length + sizeof(CommandHeader)
        self.txFragmentHeader.fragTotal = (totalLength + TRANSPORT_FRAGMENT_PAYLOAD_SIZE - 1)// TRANSPORT_FRAGMENT_PAYLOAD_SIZE
        # Copy command header
        memmove(addressof(self.txBuffer)+self.txOffset,byref(commandHeader),sizeof(CommandHeader))
        self.txOffset += sizeof(CommandHeader)
        self.txFragmentHeader.numberCommands = 1 # Only value allowed, for now
        # Loop over sending payload chunks
        dataLeft = commandHeader.length
        bytesCopied = 0
        while dataLeft > 0:
            bufferLeft = TRANSPORT_FRAGMENT_SIZE - self.txOffset
            if dataLeft < bufferLeft:
                memmove(addressof(self.txBuffer)+self.txOffset,addressof(payload)+bytesCopied,dataLeft)
                self.txOffset += dataLeft
                bytesCopied += dataLeft
                dataLeft = 0
                self.TRANSPORT_sendFragment()
                self.TRANSPORT_initTxFragmentHeader()
            else:
                memmove(addressof(self.txBuffer)+self.txOffset,addressof(payload)+bytesCopied,bufferLeft)
                self.TRANSPORT_sendFragment()
                self.txFragmentHeader.fragNum += 1
                bytesCopied += bufferLeft
                dataLeft -= bufferLeft
                self.txOffset = sizeof(FragmentHeader)
        return

    def TRANSPORT_setTimeoutMs(self,timeout):
        self.commandTimeout = timeout
        return 0
        
    def TRANSPORT_flushReceiver(self):    
        dummy = Fragment()
        def flush():
            nFlush = 0
            while True:
                ret = self.usb.usbBulkRead(self.usbHandle,self.inEp,byref(dummy),TRANSPORT_FRAGMENT_SIZE,10)
                if ret < 0: break
                nFlush += 1
            return nFlush
        print "Fragments flushed: %d" % (self._claimInterfaceWrapper(flush),)
        
    def TRANSPORT_injectRogueByte(self):
        """Deliberately injects a single byte into USB stream to test error recovery"""
        def inject():
            self.usb.usbBulkWrite(self.usbHandle,self.outEp,byref(c_ubyte(0x42)),1,self.commandTimeout)
        self._claimInterfaceWrapper(inject)
        return 0
    
    def TRANSPORT_sendAndReceive(self,type,region,address,dataBuffer,replyBuffer):
        """Carries out a transaction of the specified type with the DAS. This sends a command to the DAS with the data in dataBuffer
        and receives a reply. The reply acknowledges the command by echoing the region and address parameters, and also fills up the 
        replyBuffer. Returns the reply length and status from the receive command as a tuple, and throws an exception on an error"""

        scmd = CommandHeader()
        rcmd = CommandHeader()

        scmd.type = type
        scmd.region = region
        scmd.status = 0
        scmd.length = sizeof(dataBuffer)
        scmd.address = address
        
        def sendAndReceive():
            try:
                self.TRANSPORT_sendCommand(scmd,dataBuffer)
                while True:
                    self.TRANSPORT_getResponse(rcmd,replyBuffer)
                    if scmd.type == rcmd.type and scmd.region == rcmd.region and scmd.address == rcmd.address: break
            except Exception,e:
                # TODO: Get proper error message for failure
                print "Error in sendAndReceive %s" % (e,)
                rcmd.status = ss_autogen.ERROR_PERMISSION_DENIED
                
        self._claimInterfaceWrapper(sendAndReceive)
        return (rcmd.length, rcmd.status)
# TEST ONLY
    def TRANSPORT_send(self,scmd,dataBuffer):
        def send():
            self.TRANSPORT_sendCommand(scmd,dataBuffer)
        self._claimInterfaceWrapper(send)
    
    def TRANSPORT_readRegister(self,reg,reply):
        """Reads register "reg" into ctypes object "reply" """
        replyLen,status = self.TRANSPORT_sendAndReceive(READ_OPERATION,REGISTER_REGION,reg,c_ubyte(0),reply)
        return status
    
    def TRANSPORT_writeRegister(self,reg,data,reply=None):
        """Writes ctypes object "data" into register "reg" """
        if reply == None:
            replyLen,status = self.TRANSPORT_sendAndReceive(WRITE_OPERATION,REGISTER_REGION,reg,data,c_ubyte(0))
        else:
            replyLen,status = self.TRANSPORT_sendAndReceive(WRITE_OPERATION,REGISTER_REGION,reg,data,reply)
        return status

    def TRANSPORT_readRegisterWithPayload(self,reg,payload,reply):
        """Reads register "reg" of specified "payload" into ctypes object "reply" """
        replyLen,status = self.TRANSPORT_sendAndReceive(READ_OPERATION,REGISTER_REGION,reg,payload,reply)
        return status

    def TRANSPORT_startMemory(self,region):
        replyLen,status = self.TRANSPORT_sendAndReceive(START_OPERATION,region,0,c_ubyte(0),c_ubyte(0))
        return status

    def TRANSPORT_readMemory(self,region,address,reply):
        """
        Purpose:    Reads from a memory region into a ctype object
        Arguments:  region  - index of region to read
                    address - address within region (must be even)
                    reply - ctype object to receive result (must be multiple of 4 bytes).
                    Passed by reference to DLL.
        Exceptions: Raised on a transport layer error
        """
        max_size = 8192
        offset = 0
        bytes_left = sizeof(reply)
        while bytes_left > 0:
            length = bytes_left
            if length > max_size: length = max_size
            replyBuffer = (c_ubyte*length).from_address(addressof(reply)+offset)
            replyLen,status = self.TRANSPORT_sendAndReceive(READ_OPERATION,region,address,c_uint(length),replyBuffer)
            if status < 0:
                return status
            address += length
            offset += length
            bytes_left -= length
        return 0

    def TRANSPORT_writeMemory(self,region,address,data):
        """
        Purpose:    Writes data from a ctype object to a memory region
        Arguments:  region  - index of region to write
                    address - address within region
                    data - ctype object to write
        Exceptions: Raised on a transport layer error
        """
        chunk_size = 48
        data_len = sizeof(data)
        a = addressof(data)
        while data_len > chunk_size:
            dataBuffer = (c_ubyte*chunk_size).from_address(a)
            replyLen,status = self.TRANSPORT_sendAndReceive(WRITE_OPERATION,region,address,dataBuffer,c_uint(0))
            if status < 0:
                return status
            address += chunk_size
            a += chunk_size
            data_len -= chunk_size
            time.sleep(0) #to yield the processor if/when transferring a large data block
        #endwhile
        if data_len > 0:
            dataBuffer = (c_ubyte*data_len).from_address(a)
            replyLen,status = self.TRANSPORT_sendAndReceive(WRITE_OPERATION,region,address,dataBuffer,c_uint(0))
            if status < 0:
                return status
        return 0

    def TRANSPORT_stopMemory(self,region,crc):
        """
        Purpose:    Stops transfer to a memory region
        Arguments:  region  - index of region
                    crc - CRC of data written
        Exceptions: Raised on a transport layer error
        """
        replyLen,status = self.TRANSPORT_sendAndReceive(STOP_OPERATION,region,0,c_uint(crc),c_uint(0))
        return status

    def TRANSPORT_abortMemory(self,region):
        """
        Purpose:    Aborts transfer to a memory region
        Arguments:  region  - index of region
        Exceptions: Raised on a transport layer error
        """
        replyLen,status = self.TRANSPORT_sendAndReceive(ABORT_OPERATION,region,0,c_uint(0),c_uint(0))
        return status
    
    def TRANSPORT_restartUsb(self):
        #if self.usbHandle != None: self.usb.usbReset(self.usbHandle)
        self.usbHandle = None
        time.sleep(1.0)
        self.TRANSPORT_init()
        self.TRANSPORT_open(self.vid,self.pid)

    def TRANSPORT_getFifoByteCounts(self):
        def getFifoByteCounts():
            result = (c_ubyte*4)()
            self.usb.usbControlMsg(self.usbHandle,0xC0,0xB1,0x00,0x00,byref(result),sizeof(result),5000)
            return result
        return self._claimInterfaceWrapper(getFifoByteCounts)
        
    def TRANSPORT_resetCpld(self):
        def resetCpld():
            result = c_ubyte()
            self.usb.usbControlMsg(self.usbHandle,0xC0,0xB3,0x0000,0x00,byref(result),1,5000)
            return result
        return self._claimInterfaceWrapper(resetCpld)

from ss_autogen import *

class TransportTest(unittest.TestCase):
    def setUp(self):
        self.dasUSB = DasUSB()
        if hasattr(self.dasUSB.usb,"registerWriteHandler"):
            self.dasUSB.usb.registerWriteHandler(self.writeHandler)
            self.writeStream = {}
        if hasattr(self.dasUSB.usb,"registerReadHandler"):
            self.dasUSB.usb.registerReadHandler(self.readHandler)
    def tearDown(self):
        pass
    def writeHandler(self,ep,buffer,length):
        print "Write handler called for endpoint %d, %d bytes" % (ep,length)
        buffer = cast(buffer,POINTER(c_ubyte))
        for i in range(length): 
            print "%02x" % int(buffer[i]),
            if (i+1)%8 == 0: print
        print
        if ep == 2 | USB_ENDPOINT_OUT:
            print "Fragment Header"
            printCtypesStructure(FragmentHeader.from_address(addressof(buffer.contents)))
            print "Command Header"
            printCtypesStructure(CommandHeader.from_address(addressof(buffer.contents)+sizeof(FragmentHeader)))
            
        if ep not in self.writeStream: self.writeStream[ep] = []
        self.writeStream[ep].append(string_at(buffer,length))
        return length
    def readHandler(self,ep,buffer,length):
        print "Calling read handler on endpoint %d" % ep
        buffer = cast(buffer,POINTER(c_ubyte))
        if ep == 8 | USB_ENDPOINT_IN:
            if 4 in self.writeStream and len(self.writeStream[4])>0:
                s = self.writeStream[4][0]
                if len(s) <= length:
                    for i in range(len(s)): buffer[i] = ord(s[i]) | 0x80
                    return len(s)
        return 0
    #def testLengths(self):
        ## Check packing of bit fields in structures
        #self.assertEqual(sizeof(FragmentHeader()),8)
        #self.assertEqual(sizeof(CommandHeader()),8)
    def testLoopback(self):
        self.dasUSB.TRANSPORT_init()
        self.dasUSB.TRANSPORT_open(VENDOR_ID,PRODUCT_ID)
        for iter in range(60000):
            if iter%100 == 0: print "Iteration %d" % iter
            try:
                bad = self.dasUSB.TRANSPORT_loopback_test()
                self.assertTrue(len(bad)==0,"Loopback test fails at indices %s" % (bad,))
            except TransportError:
                try:
                    self.dasUSB.TRANSPORT_close()
                except:
                    pass
                self.dasUSB.TRANSPORT_init()
                while True:
                    try:
                        self.dasUSB.TRANSPORT_open(VENDOR_ID,PRODUCT_ID)
                        break
                    except:
                        print "Retrying TRANSPORT_open"
                        time.sleep(1.0)
        self.dasUSB.TRANSPORT_close()
    #def testTxFlush(self):
        #self.dasUSB.TRANSPORT_init()
        #self.dasUSB.TRANSPORT_open(VENDOR_ID,PRODUCT_ID)
        #self.dasUSB.txFragmentHeader.numberCommands = 1
        #self.dasUSB._claimInterfaceWrapper(self.dasUSB.TRANSPORT_flushTx)
        #self.dasUSB.TRANSPORT_close()

#class RegisterTest(unittest.TestCase):
    #def setUp(self):
        #self.dasUSB = DasUSB()
        #self.dasUSB.TRANSPORT_init()
        #self.dasUSB.TRANSPORT_open(VENDOR_ID,PRODUCT_ID)
    #def tearDown(self):
        #self.dasUSB.TRANSPORT_close()
    #def testReadWriteSimpleRegister(self):
        #niter = 10
        #regNum = NOOP_REGISTER
        #reply = c_uint(0)
        #start = time.time()
        #for i in range(niter):
            #value = randrange(1<<32)
            #self.dasUSB.TRANSPORT_writeRegister(regNum,c_uint(value))
            #self.dasUSB.TRANSPORT_readRegister(regNum,reply)
            #self.assertEqual(reply.value,value)
        #print "Time per register read/write: %.4f" % ((time.time()-start)/(2*niter),)
    #def testReadRegisterWithPayload(self):
        #regNum = VERSION_REGISTER
        #reply = c_float(0)
        #payload = c_int(VERSION_mcu)
        #self.dasUSB.TRANSPORT_readRegisterWithPayload(regNum,payload,reply)
        #print "Das version: %.3g" % reply.value
    #def testReadWriteMemory(self):
        #for iter in range(20):
            #region = DSP_REGION
            #address = 0x8000
            #nbytes = 512
            #data = (c_ubyte*nbytes)()
            #for i in range(nbytes): data[i] = i & 0xFF
            #self.dasUSB.TRANSPORT_startMemory(region)
            #self.dasUSB.TRANSPORT_writeMemory(region,address,data)
            #self.dasUSB.TRANSPORT_stopMemory(region,CRC_calcChecksum(0,data,nbytes))
            #nbytes = 512
            #reply = (c_ubyte*nbytes)()
            #self.dasUSB.TRANSPORT_readMemory(region,address,reply)
            #for i in range(nbytes):
                #self.assertEqual(reply[i],data[i])
        
        
    #def testEnqueue1(self):
        #scmd = CommandHeader()
        #scmd.type = 1
        #scmd.region = 2
        #scmd.status = 3
        #scmd.length = 4
        #scmd.address = 5
        #self.dasUSB.TRANSPORT_init()
        #self.dasUSB.TRANSPORT_open(VENDOR_ID,PRODUCT_ID)
        #payload = (c_ubyte*scmd.length)()
        #payload[0] = 31; payload[1] = 32; payload[2] = 33; payload[3] = 34
        #self.dasUSB.TRANSPORT_enqueueCommand(scmd,payload)
        
import random

if __name__ == "__main__":
    #scmd = CommandHeader()
    #scmd.type = 1
    #scmd.region = 2
    #scmd.status = 3
    #scmd.length = 52
    #scmd.address = 5
    dasUSB = DasUSB()
    dasUSB.TRANSPORT_init()
    dasUSB.TRANSPORT_open(VENDOR_ID,PRODUCT_ID)
    #payload = (c_ubyte*scmd.length)()
    #payload[0] = 31; payload[1] = 32; payload[2] = 33; payload[3] = 34
    #dasUSB.TRANSPORT_send(scmd,payload)    
    
    reg = 0x0
    data = (c_ubyte*512)()
    for i in range(len(data)): data[i] = (len(data)-i) & 0xFF
    reply = c_uint()
    check = c_ubyte()
    dasUSB.usb.usbControlMsg(dasUSB.usbHandle,0xC0,0xB4,0x0000,0x00,byref(check),1,5000)
    dasUSB.usb.usbControlMsg(dasUSB.usbHandle,0xC0,0xB3,0x0000,0x00,byref(check),1,5000)
    status = dasUSB.TRANSPORT_readRegister(reg,reply)
    print "Read Status = %d" % status
    print "Reply = %x" % reply.value
    errors = 0
    warn = 0
    trial = 0
    se = ""
    while True:
        val = random.randint(0,1000000000)
        statusW = dasUSB.TRANSPORT_writeRegister(0,c_uint(val))
        statusR = dasUSB.TRANSPORT_readRegister(0,reply)
        if statusR != 0:
            se = "%s: WARNING Trial %8d, Read status %x" % (time.ctime(),trial,statusR)
            #print s
            warn += 1
        if statusW != 0:
            se = "%s: WARNING Trial %8d, Write status %x" % (time.ctime(),trial,statusW)
            #print s
            warn += 1
        if statusR == 0 and statusW == 0:
            if reply.value != val:
                se = "%s: ERROR Trial %8d, Wrote %10d, Read %10d" % (time.ctime(),trial,val,reply.value)
                #print s
                errors += 1
        if trial % 1000 == 0:
            s = "%s: Trial: %8d, Err: %5d Warn: %5d\n%s" % (time.ctime(),trial,errors,warn,se)
            print s
            se  = ""
        trial += 1
