#!/usr/bin/python
#
# File Name: StringPickler.py
# Purpose: Converts ctypes objects to and from raw binary strings
#
# Notes:
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-07-12 russ  Removed * import from ctypes; upgraded deprecated c_buffer call; reformat
# 06-10-30 russ  Arbitrary object serialization support for Broadcaster/Listener usage

from ctypes import create_string_buffer, addressof, c_char, sizeof, memmove

def ObjAsString(obj):
    """Takes a ctypes object (works on structures too) and returns it as a string"""
    # There is probably a better way, but this seems to work ok
    sz = sizeof(obj)
    rawType = c_char * sz
    ptr = rawType.from_address(addressof(obj))
    return ptr.raw[:sz]

def StringAsObject(aString, ObjType):
    """Takes a string and returns it as a ctypes object"""
    z = create_string_buffer(aString)
    x = ObjType()
    memmove(addressof(x),addressof(z),sizeof(x))
    #x = ObjType.from_address(addressof(z))
    #x.__internal = z #ugly hack - save a ref to the buffer!
    del z
    return x

import cPickle
import binascii
import struct

ID_COOKIE = "\x52\x00\x57\x00"

class ArbitraryObjectErr(Exception):
    "Base class for erros in Arbitrary Object processing."

class IncompletePacket(ArbitraryObjectErr):
    "String being unpacked is not a complete packet."

class ChecksumErr(ArbitraryObjectErr):
    "Checksum does not match."

class InvalidHeader(ArbitraryObjectErr):
    "First 4 bytes are not the expected cookie."

class BadDataBlock(ArbitraryObjectErr):
    "Data block does not unpickle (but checksum matches!?)"

class ArbitraryObject(object):
    """ID class for indicating when arbitrary object serialization should be used.

    Send this class (or one derived from this) to the elementType argument of
    the Listener constructor.

    There is no actual code for this class.  Support code is functional. Use
    PackArbitraryObject() or UnpackArbitraryObject().

    Serialized objects will be sent and received like this:
      <ID_COOKIE><DataLength><Data><DataChecksum>

    Where:
      <ID_COOKIE>  - a 4 byte constant identifying the start of a serialized obj
      <DataLength> - a 4 byte unsigned int indicating the total # of bytes in the
                     packet, including (cookie + len + data + checksum)
      <Data> - the data block (a binary pickle of the object)
      <DataChecksum> - the 4 byte crc32 checksum of the data block.

    """

def PackArbitraryObject(Obj):
    """Creates the full string output (length + data + checksum).

    See ArbitraryObject docstring for more detail.

    """
    data = cPickle.dumps(Obj, 1)
    dataChecksum = binascii.crc32(data)
    #print "checkSum = %r  data = %r" % (dataChecksum, data)
    dataLen = 4 + 4 + len(data) + 4 #including cookie & len prefixes and crc suffix
    packetStr = "%s%s%s%s" % (ID_COOKIE,
                              struct.pack("l", dataLen),
                              data,
                              struct.pack("l", dataChecksum))
    return packetStr

def UnPackArbitraryObject(String):
    """Strips a packed arbitrary object from the head of the string, returning
    the object and the residual (the incoming string without the leading
    packet).

    Returns a tuple: (object, string_residual), where:
      object is the unpickled object
      string_residual is the remaining bytes in the provided string.

    Raises IncompletePacket if there are not enough bytes in the packet.
    Raises ChecksumErr if the checksum does not match the data.
    Raises InvalidHeader if the magic cookie header is not found (mid-tx read?)
    Raises BadDataBlock if a supposedly valid data block won't unpickle.

    Note that the length is NOT included in the input string (it has presumably
    been stripped off by the caller).

    See ArbitraryObject docstring for more detail.

    """
    length = len(String)
    #print "Length = %s" % length
    if length < 8:
        if length < 4:
            #No cookie yet
            raise IncompletePacket
        elif String[:4] != ID_COOKIE:
            raise InvalidHeader
        else:
            #Don't have the length yet
            raise IncompletePacket
    else:
        packetLen = struct.unpack("l", String[4:8])[0]
        #print "packetLen = %r" % packetLen
        if length < packetLen:
            raise IncompletePacket
        packet = String[:packetLen]
        #print "packet = %r" % packet
        cookie = packet[:4]
        if cookie != ID_COOKIE:
            raise InvalidHeader
        data = packet[8:-4]
        #print "data = %r" % data
        checksum = struct.unpack("l", packet[-4:])[0]
        #print "checksum = %r" % checksum
        if binascii.crc32(data) != checksum:
            raise ChecksumErr
        #If we get here, we have a good data block... time to unpickle...
        try:
            obj = cPickle.loads(data)
        except:
            import sys
            print repr(sys.exc_info())
            raise BadDataBlock
        residual = String[packetLen:]
        ret = (obj, residual)
        return ret
