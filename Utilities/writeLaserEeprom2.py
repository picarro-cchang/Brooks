import configobj
import numpy as np
import cPickle
import socket
import struct
import time
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.hostDasInterface import Operation, OperationGroup
from Host.Common.StringPickler import StringAsObject, ObjAsString
from Host.Common.WlmCalUtilities import WlmFile

class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False
    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr,
                SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI,ClientName="CalibrateSystem")
            self.initialized = True

# For convenience in calling driver functions
Driver = DriverProxy().rpc

def encode(pickleString):
    """Convert a pickle string into a stream of 32-bit quantities, where the
        first word is the number of bytes in the string and the following
        words consist of the packed string in little-endian format"""
    n = len(pickleString)
    result = [n]
    pad = 0
    if n % 4:
        pad = 4 - (n%4)
    fmt = "%dI" % ((n+pad)//4,)
    return [n] + [i for i in struct.unpack(fmt,pickleString + (pad*" "))]

def decode(wordArray):
    """Returns a Python object from a packed pickled string, passed as an
    array of 32-bit words. The first word is the length in bytes of the 
    pickled string"""
    n = wordArray[0]
    s = struct.pack("%dI"%((n+3)//4,),*wordArray[1:])
    return cPickle.loads(s)

def eepromWrite(whichEeprom,wordArray,startAddress,pageSize):
    """Write the 32-bit wordArray to the specified EEPROM starting at byte
    address startAddress (which must be divisible by 4). The pageSize 
    (<=64, in bytes) is used to perform the writing in chunks, being careful
    not to cross page boundaries."""

    if startAddress % 4:
        raise ValueError("startAddress must be a multiple of 4 in eepromWrite")
    if pageSize <= 0 or pageSize > 64:
        raise ValueError("pageSize must lie between 1 and 64")

    myEnv = Byte64EnvType()
    start = 0
    while True:
        pageEnd = pageSize * ((startAddress + pageSize) // pageSize)
        nBytes = pageEnd - startAddress
        dataToSend = wordArray[start:start+nBytes//4]
        if len(dataToSend) == 0: break
        for i,d in enumerate(dataToSend):
            myEnv.buffer[i] = d
        Driver.wrEnvFromString("BYTE64_ENV",Byte64EnvType,ObjAsString(myEnv))
        op = Operation("ACTION_EEPROM_WRITE",[i2cByIdent[whichEeprom][0],startAddress,nBytes],"BYTE64_ENV")
        Driver.doOperation(op)
        print startAddress
        startAddress = pageEnd
        start += nBytes//4
        while not Driver.doOperation(Operation("ACTION_EEPROM_READY",[i2cByIdent[whichEeprom][0]])):
            time.sleep(0.1)

def eepromRead(whichEeprom,startAddress,chunkSize):
    """Reads from the specified EEPROM starting at byte address startAddress 
    (which must be divisible by 4). The first four bytes specifies the number
    of subsequent bytes to be read. This is rounded up to a multiple of 4.
    The chunkSize (<=64, in bytes) is used to perform the reading in chunks for efficiency."""
    
    if startAddress % 4:
        raise ValueError("startAddress must be a multiple of 4 in eepromRead")
    if chunkSize <= 0 or chunkSize > 64:
        raise ValueError("chunkSize must lie between 1 and 64")

    myEnv = Byte64EnvType()
    op = Operation("ACTION_EEPROM_READ",[i2cByIdent[whichEeprom][0],startAddress,4],"BYTE64_ENV")
    Driver.doOperation(op)
    result = StringAsObject(Driver.rdEnvToString("BYTE64_ENV",Byte64EnvType),Byte64EnvType)
    nBytes = result.buffer[0]
    wordArray = [nBytes]
    nBytes = 4*((nBytes + 3) // 4)
    startAddress += 4
    while nBytes > 0:
        bytesRead = min(nBytes,chunkSize)
        op = Operation("ACTION_EEPROM_READ",[i2cByIdent[whichEeprom][0],startAddress,bytesRead],"BYTE64_ENV")
        Driver.doOperation(op)
        result = StringAsObject(Driver.rdEnvToString("BYTE64_ENV",Byte64EnvType),Byte64EnvType)
        for i in range(bytesRead//4):
            wordArray.append(result.buffer[i])
        print startAddress
        startAddress += bytesRead
        nBytes -= bytesRead
    return wordArray
            
if __name__ == '__main__':
    # Write parameters from WLM file to laser EEPROM
    # fname = r'C:\work\G2000\InstrConfig\Integration\Laser_969807_CO2.wlm'
    fname = r'C:\work\G2000\InstrConfig\Integration\Laser_970174_CH4.wlm'

    fp = file(fname,'r')
    wlmFile = WlmFile(fp)
    sec = {}
    sec["COARSE_CURRENT"] = float(wlmFile.parameters["laser_current"])
    sec["WAVENUM_CEN"]    = wlmFile.WtoT.xcen
    sec["WAVENUM_SCALE"]  = wlmFile.WtoT.xscale
    sec["W2T_0"],sec["W2T_1"],sec["W2T_2"],sec["W2T_3"] = wlmFile.WtoT.coeffs
    sec["TEMP_CEN"]    = wlmFile.TtoW.xcen
    sec["TEMP_SCALE"]  = wlmFile.TtoW.xscale
    sec["T2W_0"],sec["T2W_1"],sec["T2W_2"],sec["T2W_3"] = wlmFile.TtoW.coeffs
    sec["TEMP_ERMS"] = np.sqrt(wlmFile.WtoT.residual)
    sec["WAVENUM_ERMS"] = np.sqrt(wlmFile.TtoW.residual)
    fp.close()

    header = []
    fp = file(fname,'r')
    while True:
        line = fp.readline()
        if line.strip() == "[Data]": break
        header.append(line)
    hdrDict = configobj.ConfigObj(header)
    fp.close()
    laserDat = dict(parameters=sec,
                    serialNo=hdrDict["CRDS Header"]["Filename"][6:12],
                    date=hdrDict["CRDS Header"]["Date"],
                    time=hdrDict["CRDS Header"]["Time"],
                    laserTemperature = wlmFile.TLaser,
                    waveNumber = wlmFile.WaveNumber)
    s = cPickle.dumps(laserDat,-1)
    w = encode(s)
    raw_input("Press return to write...")
    startAddress = 0
    eepromWrite("LASER2_EEPROM",w,startAddress,32)
    
    
    
    
    
    
