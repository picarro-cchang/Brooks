#!/usr/bin/python
"""
FILE:
  HostToDspSender.py

DESCRIPTION:
  Access the DSP after programming using the Cypress USB

SEE ALSO:
  Specify any related information.

HISTORY:
  29-Nov-2013  sze  Extracted from hostDasInterface

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from ctypes import addressof, c_char, c_float, c_longlong, c_short, c_uint, sizeof, Structure
import time
import types

from Host.autogen import interface
from Host.Common.analyzerUsbIf import AnalyzerUsb
from Host.Common.crc import calcCrc32
from Host.Common.DspAccessor import DspAccessor
from Host.Common.SharedTypes import DasException, DasCommsException, getSchemeTableClass, lookup, Operation, Singleton

# The 6713 has 192KB of internal memory from 0 through 0x2FFFF
#  With the allocation below, the register area contains 16128 4-byte
#   registers. The host area occupies the top 1KB of internal memory

SHAREDMEM_BASE = interface.SHAREDMEM_ADDRESS
REG_BASE = interface.SHAREDMEM_ADDRESS
SENSOR_BASE      = interface.SHAREDMEM_ADDRESS + \
    4 * interface.SENSOR_OFFSET
MESSAGE_BASE     = interface.SHAREDMEM_ADDRESS + \
    4 * interface.MESSAGE_OFFSET
GROUP_BASE       = interface.SHAREDMEM_ADDRESS + \
    4 * interface.GROUP_OFFSET
OPERATION_BASE   = interface.SHAREDMEM_ADDRESS + \
    4 * interface.OPERATION_OFFSET
OPERAND_BASE     = interface.SHAREDMEM_ADDRESS + \
    4 * interface.OPERAND_OFFSET
ENVIRONMENT_BASE = interface.SHAREDMEM_ADDRESS + \
    4 * interface.ENVIRONMENT_OFFSET
HOST_BASE        = interface.SHAREDMEM_ADDRESS + \
    4 * interface.HOST_OFFSET
RINGDOWN_BASE = interface.DSP_DATA_ADDRESS

ValveSequenceType = (interface.ValveSequenceEntryType * interface.NUM_VALVE_SEQUENCE_ENTRIES)

def usbLockProtect(func):
    """Decorator using usbLock to serialize access to function f

    The lock used is a property of self.deviceUsb in the underlying USB interface
    """
    assert callable(func)
    def wrapper(self, *a, **k):
        """Wrapper for function
        """
        self.deviceUsb.usbLock.acquire()
        try:
            return func(self, *a, **k)
        finally:
            self.deviceUsb.usbLock.release()
    return wrapper

class HostToDspSender(Singleton): # pylint: disable=R0902, R0904
    """Encapsulates communications between host and DSP.

    This provides for the DSP to be programmed, as well as for accessing
    various portions of the DSP memory map.

    Args:
        deviceUsb: AnalyzerUsb object for communicating via USB
        timeout: Timeout for verifying correct sequence number
    """

    initialized = False
    # Object that keeps track of sequence numbers, and packages
    #  data for host to Dsp communications

    def __init__(self, deviceUsb=None, timeout=None):
        if not self.initialized:
            assert isinstance(deviceUsb, AnalyzerUsb)
            assert isinstance(timeout, (types.NoneType, int, long, float))
            self.seqNum = None
            self.deviceUsb = deviceUsb
            self.dspAccessor = DspAccessor(deviceUsb)
            # Used to ensure only one thread accesses USB at a time
            self.initStatus = None
            self.timeout = timeout
            self.initialized = True
            self.programmed = False
            self.oldStatus = -1
            self.status = None

    def setTimeout(self, timeout=None):
        """Set timeout for checking status.
        
        Args:
            timeout: Timeout for checking status in seconds
        """
        assert isinstance(timeout, (types.NoneType, int, long, float))
        self.timeout = timeout

    def program(self, fileName):
        """Program the DSP.
        
        Args:
            fileName: Name of file with DSP program
        """
        assert isinstance(fileName, (str, unicode))
        self.dspAccessor.program(fileName)
        self.programmed = True
            
    ############################################################################
    # The following methods are used when the host needs to write to the DSP
    #  via the host area
    ############################################################################

    @usbLockProtect
    def send(self, command, data, env=0):
        """Send the command and the associated data to the DSP to perform an action.

        Commands are sent by writing a message to the host area in the DSP memory map
            and issueing a DSPINT interrupt. A sequence number and CRC32 checksum are attached
            to the message. (Note: The total host area is 1KB in size)

        Format of message:
            HOST[0]: Command in bits 15-0, len(data) in bits 23-16,
                SeqNum in bits 31-24
            HOST[1]: Environment address in bits 15-0
            HOST[2] through HOST[len(data)+1]: Data (int or float)
            HOST[len(data)+2]: CRC32

        Args:
            command: Specifies which action is to be carried out 
            data: Payload which is an enumerable object whose elements are either integers or floats
            env: Optional environment address for the action
            
        Returns: Status code
        """
        assert isinstance(command, (int, long))
        assert hasattr(data, '__iter__')
        assert isinstance(env, (int, long))
        
        if not self.programmed:
            raise DasException("Cannot write to DSP before programming it.")
        self.initStatus = self.rdRegUint(interface.COMM_STATUS_REGISTER)
        if self.seqNum == None:
            self.seqNum = (self.getSequenceNumber() + 1) & 0xFF
        numInt = len(data)
        hostMsg = ((numInt + 3) * c_uint)()
        # The following is used to read back the host message to ensure
        #  that the EMIF transfer has taken place before signalling the DSPINT
        hostMsgConfirm = ((numInt + 3) * c_uint)()
        hostMsg[0] = ((self.seqNum & 0xFF) << 24) | \
            ((numInt & 0xFF) << 16) | (command & 0xFFFF)
        hostMsg[1] = env & 0xFFFF
        i = 2
        for datum in data:
            if isinstance(datum, int) or isinstance(datum, long):
                hostMsg[i] = c_uint(datum & 0xFFFFFFFF)
            elif isinstance(datum, float):
                floatVal = c_float(datum)
                hostMsg[i] = c_uint.from_address(addressof(floatVal)) # pylint: disable=E1101
            else:
                raise ValueError("Data type %s is unknown in send" % type(datum))
            i += 1
        hostMsg[i] = calcCrc32(0, hostMsg, 4 * (numInt + 2))
        # logging.info("CRC = %x" % hostMsg[numInt+2])
        self.oldStatus = self.rdRegUint(interface.COMM_STATUS_REGISTER)

        self.dspAccessor.hpiWrite(HOST_BASE, hostMsg)
        time.sleep(0.003)  # Necessary to ensure hpiWrite completes before signalling interrupt
        for _ in range(10):  # Retry count
            self.dspAccessor.hpiRead(HOST_BASE, hostMsgConfirm)
            if tuple(hostMsg) == tuple(hostMsgConfirm):
                break
            time.sleep(0.01)
        else:
            raise ValueError("Writing to DSP host area failed")

        # Assert DSPINT
        self.dspAccessor.hpicWrite(0x00010003)
        # print "hpic after DSPINT: %08x" % self.dspAccessor.hpicRead()

        return self.getStatusWhenDone()  # or throw SharedTypes.DasCommsException on error

    @usbLockProtect
    def getSequenceNumber(self):
        """Get the sequence number from the COMM_STATUS_REGISTER.
        """
        ntries = 0
        startTime = time.time()
        while (self.timeout is None) or (time.time() < startTime + self.timeout):
            self.status = self.rdRegUint(interface.COMM_STATUS_REGISTER)
            ntries += 1
            if self.oldStatus & interface.COMM_STATUS_SequenceNumberMask != \
                self.status & interface.COMM_STATUS_SequenceNumberMask:
                # Status has changed since DSP has updated it
                done = (0 != (self.status & interface.COMM_STATUS_CompleteMask))
                if done:
                    seqNum = (self.status &
                              interface.COMM_STATUS_SequenceNumberMask) >> \
                        interface.COMM_STATUS_SequenceNumberShift
                    if self.seqNum == None or self.seqNum == seqNum:
                        #self.seqNum = seqNum
                        return seqNum
            # If status is unchanged or not done, sleep and try again
            time.sleep(0.1)
        # Get here if we are unable to get a sequence number. This is a severe error
        seqNum = self.seqNum
        self.seqNum = None
        msgFmt = ("Timeout getting status after %s tries. Initial status: 0x%x," +
            "Final status: 0x%x, Expected sequence number: %s")
        raise DasException(msgFmt % (ntries, self.initStatus, self.status, seqNum))

    @usbLockProtect
    def getStatusWhenDone(self):
        """Read done bit from COMM_STATUS_REGISTER.
        """
        seqNum = self.getSequenceNumber()
        try:
            if 0 != (self.status & interface.COMM_STATUS_BadCrcMask):
                raise DasCommsException("Bad CRC detected")
            if 0 != (self.status &
                     interface.COMM_STATUS_BadSequenceNumberMask):
                raise DasCommsException("DSP unexpected sequence number: %d, %d" % (seqNum, self.seqNum))
            if seqNum != self.seqNum:
                raise DasCommsException("Host unexpected sequence number: %d, %d" % (seqNum, self.seqNum))
            retVal = (
                self.status & interface.COMM_STATUS_ReturnValueMask) >> \
                interface.COMM_STATUS_ReturnValueShift
            retVal = c_short(retVal).value  # Sign extend 16-bits
            return retVal
        finally:
            # Prepare for next send
            self.seqNum = (seqNum + 1) & 0xFF
        
    ############################################################################
    # The following methods are used to read and write DSP memory from the host
    ############################################################################

    @usbLockProtect
    def wrBlock(self, *args):
        """Write a block of data to the DSP.
        
        Args: One or more quantities (int or float) to be written. Strings are looked up in the 
            interface file, so symbolic constants may also be passed.
        """
        argList = []
        for arg in args:
            argList.append(lookup(arg))
        return self.send(interface.ACTION_WRITE_BLOCK, argList)

    def wrRegFloat(self, reg, value):
        """Write a 32-bit floating point value to the specified DSP register.
        
        Args:
            reg: Name or index of DSP register
            value: Floating point quantity to be written
        """
        return self.wrBlock(reg, float(value))

    def wrRegUint(self, reg, value):
        """Write a 32-bit integer value to the specified DSP register.
        
        Args:
            reg: Name or index of DSP register
            value: Integer quantity to be written
        """
        return self.wrBlock(reg, int(value))

    @usbLockProtect
    def rdBlock(self, offset, numInt):
        """Reads a block of DSP memory into a list of unsigned 32-bit integers.
        
        Args:
            offset: Word address in DSP shared memory area
            numInt: Number of 32-bit words to read
        
        Returns: List of 32-bit unsigned integers
        """
        assert isinstance(offset, (int, long, str, unicode))
        assert isinstance(numInt, (int, long))
        addr = SHAREDMEM_BASE + 4 * lookup(offset)
        result = (c_uint * numInt)()
        self.dspAccessor.hpiRead(addr, result)
        return list(result)

    @usbLockProtect
    def rdRegFloat(self, reg):
        """Reads a single DSP register as a floating point number.
        
        Args:
            reg: Register name or index
        
        Returns: Floating point value
        """
        assert isinstance(reg, (int, long, str, unicode))
        data = c_float(0)
        self.dspAccessor.hpiRead(REG_BASE + 4 * lookup(reg), data)
        return data.value

    @usbLockProtect
    def rdRegUint(self, reg):
        """Reads a single DSP register as an unsigned 32-bit number.
        
        Args:
            reg: Register name or index
        
        Returns: Unsigned integer value
        """
        assert isinstance(reg, (int, long, str, unicode))
        data = c_uint(0)
        self.dspAccessor.hpiRead(REG_BASE + 4 * lookup(reg), data)
        return data.value

    @usbLockProtect
    def rdFPGA(self, base, reg):
        """Reads a single FPGA register as an unsigned 32-bit number.
        
        Args:
            base: FPGA block base address (can be symbolic)
            reg: Register within the block (can be symbolic)
        
        Returns: Unsigned integer value
        """
        assert isinstance(base, (int, long, str, unicode))
        assert isinstance(reg, (int, long, str, unicode))
        data = c_uint(0)
        self.dspAccessor.hpiRead(interface.FPGA_REG_BASE_ADDRESS + 4 * (lookup(base) + lookup(reg)), data)
        return data.value

    @usbLockProtect
    def wrFPGA(self, base, reg, value):
        """Writes a single FPGA register as an unsigned 32-bit number.
        
        Args:
            base: FPGA block base address (can be symbolic)
            reg: Register within the block (can be symbolic)
            value: Value to write
        """
        assert isinstance(base, (int, long, str, unicode))
        assert isinstance(reg, (int, long, str, unicode))
        assert isinstance(value, (int, long))
        self.dspAccessor.hpiWrite(interface.FPGA_REG_BASE_ADDRESS + 4 * (lookup(base) + lookup(reg)), c_uint(value))

    @usbLockProtect
    def rdDspMemArray(self, byteAddr, nwords=1):
        """Reads multiple words from DSP memory into a c_uint array.
        
        Args:
            byteAddr: Byte address in DSP memory 
            nwords: Number of 32-bit unsigned integers to read
        
        Returns: Array of (c_unint * nwords) containing data
        """
        result = (c_uint * nwords)()
        self.dspAccessor.hpiRead(byteAddr, result)
        return result

    @usbLockProtect
    def rdRingdownMemArray(self, offset, nwords=1):
        """Reads multiple words from ringdown area of DSP memory into a c_uint array.
        
        Args:
            offset: Word offset into ringdown area of DSP memory
            nwords: Number of 32-bit unsigned integers to read
        
        Returns: Array of (c_unint * nwords) containing data
        """
        result = (c_uint * nwords)()
        self.dspAccessor.hpiRead(interface.RDMEM_ADDRESS + 4 * offset, result)
        return result

    ############################################################################
    # The following methods are used to transfer data from the DSP to the host
    #  within the main loop of the driver
    ############################################################################
    
    @usbLockProtect
    def rdSensorData(self, index):
        """Reads one entry from sensor data area in DSP memory.
        
        Args:
            index: Index of the entry within the sensor data area 
                (in range 0 through interface.NUM_SENSOR_ENTRIES-1)
            
        Returns: A SensorEntryType object containing the entry. This consists
            of 16 bytes (64 bit timestamp, 32 bit stream index and 32 bit data)
        """
        assert isinstance(index, (int, long))
        data = interface.SensorEntryType()
        self.dspAccessor.hpiRead(SENSOR_BASE + 16 * index, data)
        return data

    maxSensorBlockSize = 512 / 16

    @usbLockProtect
    def rdSensorDataBlock(self, index):
        """Reads a block of entries from the sensor data area in DSP memory.
        
        The number of entries read is such that the returned array has size close to 512 bytes,
            which is the USB packet size. However, we never fetch past the end of the sensor data
            area which is of length interface.NUM_SENSOR_ENTRIES
            
        Args:
            index: Starting entry to place in block.
        
        Returns: An array of SensorEntryType objects
        """
        assert isinstance(index, (int, long))
        numEntries = min(self.maxSensorBlockSize, interface.NUM_SENSOR_ENTRIES - index)
        block = (interface.SensorEntryType * numEntries)()
        self.dspAccessor.hpiRead(SENSOR_BASE + 16 * index, block)
        return block

    @usbLockProtect
    def rdRingdownData(self, index):
        """Reads one entry from ringdown data area in DSP memory.
        
        Args:
            index: Index of the entry within the ringdown data area 
                (in range 0 through interface.NUM_RINGDOWN_ENTRIES-1)
            
        Returns: A RingdownEntryType object containing the entry.
        """
        assert isinstance(index, (int, long))
        data = interface.RingdownEntryType()
        self.dspAccessor.hpiRead(RINGDOWN_BASE + 4 * interface.RINGDOWN_ENTRY_SIZE * index, data)
        return data

    maxRingdownBlockSize = 512 / (4 * interface.RINGDOWN_ENTRY_SIZE)

    @usbLockProtect
    def rdRingdownDataBlock(self, index):
        """Reads a block of entries from the ringdown data area in DSP memory.
        
        The number of entries read is such that the returned array has size close to 512 bytes,
            which is the USB packet size. However, we never fetch past the end of the ringdown data
            area which is of length interface.NUM_RINGDOWN_ENTRIES
            
        Args:
            index: Starting entry to place in block.
        
        Returns: An array of RingdownEntryType objects
        """
        assert isinstance(index, (int, long))
        numEntries = min(self.maxRingdownBlockSize, interface.NUM_RINGDOWN_ENTRIES - index)
        block = (interface.RingdownEntryType * numEntries)()
        self.dspAccessor.hpiRead(RINGDOWN_BASE + 4 * interface.RINGDOWN_ENTRY_SIZE * index, block)
        return block

    @usbLockProtect
    def rdMessageTimestamp(self, index):
        """Reads timestamp from a message in the message data area in DSP memory.
        
        Args:
            index: Index of the entry within the message data area 
                (in range 0 through interface.NUM_MESSAGES-1)
            
        Returns: A 64 bit message timestamp
        """
        assert isinstance(index, (int, long))
        data = c_longlong(0)
        self.dspAccessor.hpiRead(MESSAGE_BASE + 128 * index, data)
        return data.value

    @usbLockProtect
    def rdMessage(self, index):
        """Reads a message in the message data area in DSP memory.
        
        Args:
            index: Index of the entry within the message data area 
                (in range 0 through interface.NUM_MESSAGES-1)
            
        Returns: A string containing the message
        """
        assert isinstance(index, (int, long))
        data = (c_char * 120)()
        self.dspAccessor.hpiRead(MESSAGE_BASE + 128 * index + 8, data)
        return data.value
        
    @usbLockProtect
    def rdDspTimerRegisters(self):
        """Reads DSP TIMER0 registers.
        
        TIMER0 is used to generate the 1ms clock which the DSP uses to track time
        
        Returns: Three 32-bit integers (Control, Period and Counter Registers)
        """
        timerRegs = (c_uint * 3)()
        self.dspAccessor.hpiRead(interface.DSP_TIMER0_BASE, timerRegs)
        return [x for x in timerRegs]

    ############################################################################
    # The following methods are used to read and write environments and
    #  carry out operations
    ############################################################################

    @usbLockProtect
    def rdEnv(self, address, envClass):
        """Reads an environment of the specified class from the DSP environment area.
        
        Args:
            address: Starting address of the environment within the environment area
            envClass: Ctypes Structure name specifying type of the environment
        
        Returns: Object of type envClass containing the environment
        """
        assert isinstance(address, (int, long, str, unicode))
        env = envClass()
        self.dspAccessor.hpiRead(ENVIRONMENT_BASE + 4 * lookup(address), env)
        return env

    def wrEnv(self, address, env):
        """Write an environment structure to the DSP environment table.
        
        Args:
            address: Name or starting address of environmental table entry. Note that an environment
                takes up one or more addresses, depending on its size.
            env: ctypes object containing the environment
        """    
        # Write the environment structure env to the environment
        #  table at the specified index (integer offset)
        assert isinstance(address, (int, long, str, unicode))
        assert isinstance(env, Structure)
        numInt = sizeof(env) / sizeof(c_uint)
        envAsArray = (c_uint * numInt).from_address(addressof(env))
        return self.wrBlock(interface.ENVIRONMENT_OFFSET + lookup(address), *envAsArray) # pylint: disable=W0142


    @usbLockProtect
    def doOperation(self, oper):
        """Carry out an operation.
        
        Args:
            oper: Instance of an Operation
            
        Returns: Status code
        """
        assert isinstance(oper, Operation)
        return self.send(oper.opcode, oper.operandList, oper.env)
    

    ############################################################################
    # The following methods are used to read and write schemes to the DSP
    ############################################################################

    @usbLockProtect
    def wrScheme(self, schemeNum, numRepeats, schemeRows):
        """Write a scheme into a scheme table in the DSP.
        
        For speed, this is done directly via the HPI interface into DSP memory rather 
        than through the host area. We need to declare the scheme areas as volatile in the
        DSP code so that they are always read from actual memory.
        
        Args:
            schemeNum: Scheme table number (0 origin)
            numRepeats: Number of repetitions of the scheme
            schemeRows: A list of rows, where each row has up to 7 entries
        """
        assert isinstance(schemeNum, (int, long))
        assert isinstance(numRepeats, (int, long))
        assert hasattr(schemeRows, '__iter__')
        
        schemeBase = interface.DSP_DATA_ADDRESS + 4 * interface.SCHEME_OFFSET
        if schemeNum >= interface.NUM_SCHEME_TABLES:
            raise ValueError("Maximum number of schemes available is %d" % interface.NUM_SCHEME_TABLES)

        schemeTableAddr = schemeBase + 4 * schemeNum * interface.SCHEME_TABLE_SIZE
        self.doOperation(Operation("ACTION_WB_INV_CACHE", [schemeTableAddr, 4 * interface.SCHEME_TABLE_SIZE]))
        schemeTable = getSchemeTableClass(len(schemeRows))()
        schemeTable.numRepeats = numRepeats
        schemeTable.numRows = len(schemeRows)
        for i, row in enumerate(schemeRows):
            schemeTable.rows[i].setpoint = float(row[0])
            schemeTable.rows[i].dwellCount = int(row[1])
            schemeTable.rows[i].subschemeId = int(row[2]) if len(row) >= 3 else 0
            schemeTable.rows[i].virtualLaser = int(row[3]) if len(row) >= 4 else 0
            schemeTable.rows[i].threshold = int(row[4]) if len(row) >= 5 else 0
            schemeTable.rows[i].pztSetpoint = int(row[5]) if len(row) >= 6 else 0
            schemeTable.rows[i].laserTemp = int(1000 * row[6]) if len(row) >= 7 else 0
        self.dspAccessor.hpiWrite(schemeTableAddr, schemeTable)

    @usbLockProtect
    def rdScheme(self, schemeNum):
        """Read a scheme into a scheme table in the DSP.
        
        Args:
            schemeNum: Scheme table number (0 origin)
        Returns:
            A dictionary with numRepeats as the number of repetitions and schemeRows as a list of
            7-tuples containing:
            (setpoint, dwellCount, subschemeId, virtualLaser, threshold, pztSetpoint, laserTemp)
        
        """
        assert isinstance(schemeNum, (int, long))
        # Read from scheme table schemeNum
        schemeBase = interface.DSP_DATA_ADDRESS + 4 * interface.SCHEME_OFFSET
        if schemeNum >= interface.NUM_SCHEME_TABLES:
            raise ValueError("Maximum number of schemes available is %d" % interface.NUM_SCHEME_TABLES)

        schemeTableAddr = schemeBase + 4 * schemeNum * interface.SCHEME_TABLE_SIZE
        self.doOperation(Operation("ACTION_WB_CACHE", [schemeTableAddr, 4 * interface.SCHEME_TABLE_SIZE]))
        schemeHeader = interface.SchemeTableHeaderType()
        self.dspAccessor.hpiRead(schemeTableAddr, schemeHeader)
        schemeTable = getSchemeTableClass(schemeHeader.numRows)()
        self.dspAccessor.hpiRead(schemeTableAddr, schemeTable)
        return {"numRepeats": schemeTable.numRepeats,
                "schemeRows": [(row.setpoint, row.dwellCount, row.subschemeId, row.virtualLaser,
                               row.threshold, row.pztSetpoint, 0.001 * row.laserTemp) for row in schemeTable.rows]}
    

    ############################################################################
    # The following methods are used to read and write valve sequences to 
    #  the DSP
    ############################################################################

    @usbLockProtect
    def wrValveSequence(self, sequenceRows):
        """Write a valve sequence to the DSP.
        
        Args:
           sequenceRows: List of triples (mask, duration, value) specifying, for
              each step, the valves to affect, the duration (integer number of 
              0.2s intervals), and the target states of the affected valves. The
              mask and value are at most 8 bits wide, and the duration is 16 bits
              wide.
        """
        assert hasattr(sequenceRows, '__iter__')
        valveSequenceBase = interface.SHAREDMEM_ADDRESS + 4 * interface.VALVE_SEQUENCE_OFFSET
        valveSequence = (ValveSequenceType)()
        if len(sequenceRows) > interface.NUM_VALVE_SEQUENCE_ENTRIES:
            raise ValueError("Maximum number of rows in a valve sequence is %d" % interface.NUM_VALVE_SEQUENCE_ENTRIES)
        for i, (mask, value, dwell) in enumerate(sequenceRows):
            if mask < 0 or mask > 0xFF:
                raise ValueError, "Mask in valve sequence is eight bits wide"
            if value < 0 or value > 0xFF:
                raise ValueError, "Value in valve sequence is eight bits wide"
            if dwell < 0 or dwell > 0xFFFF:
                raise ValueError, "Dwell in valve sequence is sixteen bits wide"
            valveSequence[i].maskAndValue = (mask << 8) | (value & 0xFF)
            valveSequence[i].dwell = dwell
        self.dspAccessor.hpiWrite(valveSequenceBase, valveSequence)

    @usbLockProtect
    def rdValveSequence(self):
        """Reads the valve sequence from the DSP.
        
        Returns: List of triples (mask, duration, value) specifying, for
              each step, the valves to affect, the duration (integer number of 
              0.2s intervals), and the target states of the affected valves. The
              mask and value are at most 8 bits wide, and the duration is 16 bits
              wide.
        """
        # Reads the valve sequence as a list of triples (mask,value,duration)
        valveSequenceBase = interface.SHAREDMEM_ADDRESS + 4 * interface.VALVE_SEQUENCE_OFFSET
        valveSequence = (ValveSequenceType)()
        self.dspAccessor.hpiRead(valveSequenceBase, valveSequence)
        sequenceRows = []
        for i in range(interface.NUM_VALVE_SEQUENCE_ENTRIES):
            entry = valveSequence[i]
            sequenceRows.append(((entry.maskAndValue >> 8) & 0xFF, entry.maskAndValue & 0xFF, entry.dwell))
        return sequenceRows
    

    ############################################################################
    # The following methods are used to read and write virtual laser
    #  parameters to the DSP
    ############################################################################


    @usbLockProtect
    def wrVirtualLaserParams(self, vLaserNum, vLaserParams):
        """Write virtual laser parameters to the DSP.
        
        Args:
           vLaserNum: ONE-based index of the virtual laser
           vLaserParams: Object of type interface.VirtualLaserParamsType containing parameters
        """
        virtualLaserParamsBase = interface.DSP_DATA_ADDRESS + 4 * interface.VIRTUAL_LASER_PARAMS_OFFSET
        if vLaserNum > interface.NUM_VIRTUAL_LASERS:
            raise ValueError("Maximum number of virtual lasers available is %d" % interface.NUM_VIRTUAL_LASERS)
        if not isinstance(vLaserParams, interface.VirtualLaserParamsType):
            raise ValueError("Invalid object to write in wrVirtualLaserParams")
        virtualLaserParamsAddr = virtualLaserParamsBase + 4 * (vLaserNum - 1) * interface.VIRTUAL_LASER_PARAMS_SIZE
        self.doOperation(Operation("ACTION_WB_INV_CACHE", 
                                   [virtualLaserParamsAddr, 4 * interface.VIRTUAL_LASER_PARAMS_SIZE]))
        self.dspAccessor.hpiWrite(virtualLaserParamsAddr, vLaserParams)

    @usbLockProtect
    def rdVirtualLaserParams(self, vLaserNum):
        """Read virtual laser parameters from the DSP.
        
        Args:
           vLaserNum: ONE-based index of the virtual laser
           
        Returns: Object of type interface.VirtualLaserParamsType containing parameters
        """
        virtualLaserParamsBase = interface.DSP_DATA_ADDRESS + 4 * interface.VIRTUAL_LASER_PARAMS_OFFSET
        if vLaserNum > interface.NUM_VIRTUAL_LASERS:
            raise ValueError("Maximum number of virtual lasers available is %d" % interface.NUM_VIRTUAL_LASERS)
        vLaserParams = interface.VirtualLaserParamsType()
        virtualLaserParamsAddr = virtualLaserParamsBase + 4 * (vLaserNum - 1) * interface.VIRTUAL_LASER_PARAMS_SIZE
        self.doOperation(Operation("ACTION_WB_CACHE", 
                                   [virtualLaserParamsAddr, 4 * interface.VIRTUAL_LASER_PARAMS_SIZE]))
        self.dspAccessor.hpiRead(virtualLaserParamsAddr, vLaserParams)
        return vLaserParams