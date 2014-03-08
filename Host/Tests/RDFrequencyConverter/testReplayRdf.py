#!/usr/bin/python
"""
FILE:
  testReplayRdf.py

DESCRIPTION:
  Utility to broadcast contents of RDF files as though they were coming from the Driver.
  This allows us to test the operation of the WLM calibration routines in the RD Frequency Converter.

SEE ALSO:
  Specify any related information.

HISTORY:
  11-Dec-2013  sze  Initial version

 Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from ctypes import c_float
import inspect
import os
import pylab
import subprocess
from tables import openFile
import time
import threading

from Host.autogen import interface
from Host.Common import CmdFIFO, SharedTypes, StringPickler, timestamp
from Host.Common.Broadcaster import Broadcaster
from Host.Common.SchemeProcessor import Scheme

class DummyDriver(object):
    """Simulates Driver RPC handler"""
    def __init__(self):
        self.server = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_DRIVER),
                                            ServerName = "DummyDriver",
                                            ServerDescription = "Dummy Driver (testReplayRdf)",
                                            threaded = True)
        self._register_rpc_functions()
        self.rpcThread = None

    def _register_rpc_functions_for_object(self, obj):
        """ Registers the functions in obj for RPC access

        NOTE - this automatically registers ALL member functions that don't start with '_'.

        i.e.:
          - if adding new rpc calls, just define them (with no _) and you're done
          - if putting helper calls in the class for some reason, use a _ prefix
        """
        classDir = dir(obj)
        for s in classDir:
            attr = obj.__getattribute__(s)
            if callable(attr) and (not s.startswith("_")) and (not inspect.isclass(attr)):
                #if __debug__: print "registering", s
                self.server.register_function(attr, DefaultMode=CmdFIFO.CMD_TYPE_Blocking)

    def _register_rpc_functions(self):
        """Registers the functions accessible by XML-RPC
        """
        self._register_rpc_functions_for_object( self )
        
    def _startServer(self):
        """Start RPC server in a separate thread of execution"""
        self.rpcThread = threading.Thread(target=self.server.serve_forever)
        self.rpcThread.setDaemon(daemonic=True)
        self.rpcThread.start()
        
    def stopScan(self):
        print "Driver.stopScan called"

    #def rdDasReg(self, *args, **kwargs):
    #    argList = [("%s" % a) for a in args]
    #    argList.extend([("%s=%r" % (key, kwargs[key])) for key in kwargs])
    #    print "Driver.rdDasReg(%s) called" % ",".join(argList)

    def rdDasReg(self, regName):
        if regName == "ANALYZER_TUNING_MODE_REGISTER":
            return interface.ANALYZER_TUNING_CavityLengthTuningMode
        
    def hostGetTicks(self):
        return timestamp.getTimestamp()

    def wrVirtualLaserParams(self, vLaserNum, laserParams):
        print "Driver.wrVirtualLaserParams(%d, %s) called" % (vLaserNum, laserParams)
    
    def wrScheme(self, *args, **kwargs):
        argList = [("%s" % a) for a in args]
        argList.extend([("%s=%r" % (key, kwargs[key])) for key in kwargs])
        # print "Driver.wrScheme(%s) called" % ",".join(argList)

    def wrDasReg(self, *args, **kwargs):
        argList = [("%s" % a) for a in args]
        argList.extend([("%s=%r" % (key, kwargs[key])) for key in kwargs])
        # print "Driver.wrDasReg(%s) called" % ",".join(argList)

    def wrFPGA(self, *args, **kwargs):
        argList = [("%s" % a) for a in args]
        argList.extend([("%s=%r" % (key, kwargs[key])) for key in kwargs])
        # print "Driver.wrFpga(%s) called" % ",".join(argList)

class RdfReplay(object):
    """Object to allow user to broadcast contents of a collection of ringdown files.
    
    Args:
        fileNameList: List of fully qualified RDF filenames to replay.
        rdFreqConv: Dictionary with keys:
            source: Python source file of Ringdown Frequency Converter
            config: Configuration file for Ringdown Frequency Converter
    """
    def __init__(self, fileNameList, rdFreqConv):
        self.fileNameList = fileNameList
        self.broadcaster = Broadcaster(SharedTypes.BROADCAST_PORT_RDRESULTS, "RdfReplay")
        self.rdFreqConvSrc = rdFreqConv["source"]
        self.rdFreqConvIni = rdFreqConv["config"]
        self.rdFreqConv = None
        self.rdFreqConvRpc = None
        self.schemeFiles = []
        self.activeTable = 0
        self.schemes = []
        self.schemeIndex = 0

    def startRdFreqConv(self):
        self.rdFreqConv = subprocess.Popen(["python.exe", self.rdFreqConvSrc, "-c", 
                                            self.rdFreqConvIni], stderr=file("NUL", "w"))
        self.rdFreqConvRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_FREQ_CONVERTER,
                                    "testReplayRdf", IsDontCareConnection = False)
        self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                    "testReplayRdf", IsDontCareConnection = False)
        self.rdFreqConvRpc.loadWarmBoxCal()
        self.rdFreqConvRpc.loadHotBoxCal()

    def stopRdFreqConv(self):
        self.rdFreqConv.terminate()
        self.rdFreqConv.wait()
        
    def sendRdfFile(self, fname):
        """Send an RDF file via the broadcaster.
        
        Args:
            fname: Name of file to send
        """
        self.sendScheme()
        print "Sending %s" % fname
        with openFile(fname, "r") as h5:
            rdData = h5.root.rdData.read()
        # Convert the numpy record array into a RingdownEntryType object
        rdEntry = interface.RingdownEntryType()
        for k in range(len(rdData)):
            for fieldName, fieldType in rdEntry._fields_:  # pylint: disable=W0212
                if fieldType == c_float:
                    setattr(rdEntry, fieldName, float(rdData[fieldName][k]))
                else:
                    setattr(rdEntry, fieldName, int(rdData[fieldName][k])) 
            rdEntry.schemeVersionAndTable &= 0xF
            dataStr = StringPickler.ObjAsString(rdEntry)
            self.broadcaster.send(dataStr)
    
    def setSchemeFiles(self, schemeFiles, startTable=0):
        """Specify the list of scheme files to be used, and the scheme table for the first file.
        
        Args:
            schemeFiles: List of filenames containing the scheme files
            startTable: Index of scheme table into which the first file is to be loaded
        """
        self.schemeFiles = schemeFiles
        nschemes = len(schemeFiles)
        for i in range(nschemes):
            schemeFileName = schemeFiles[i]
            _, ext = os.path.splitext(schemeFileName)
            self.schemes.append((Scheme(schemeFileName), 1, ext.lower() == ".sch"))       
        self.activeTable = startTable
        self.schemeIndex = 0
    
    def sendScheme(self):
        """Compile and send next scheme in the sequence to the DAS.
        """
        scheme, rep, freqBased = self.schemes[self.schemeIndex]
        assert rep == 1
        
        print "Scheme %s is being loaded into table %s" \
            % (os.path.split(scheme.fileName)[-1], self.activeTable)
        
        if freqBased:
            self.rdFreqConvRpc.wrFreqScheme(self.activeTable, scheme)
            self.rdFreqConvRpc.convertScheme(self.activeTable)
            self.rdFreqConvRpc.uploadSchemeToDAS(self.activeTable)
        else:
            self.driverRpc.wrScheme(self.activeTable, *(scheme.repack()))
        self.driverRpc.wrDasReg(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER, self.activeTable)
        
        self.schemeIndex = (self.schemeIndex + 1) % len(self.schemes)
        self.activeTable = (self.activeTable + 1) % 4
        
    def run(self):
        """Interactively broadcast the ringdown files.
        """
        print "Starting RDFrequencyConverter"
        rr.startRdFreqConv()
        raw_input("<Enter> to start sending RDF files")
        startPos = 0
        totFiles = len(self.fileNameList)
        try:
            while True:
                response = raw_input("%d files left to send. <Enter> to send one file or specify number to send: " % 
                                     (totFiles - startPos,))
                try:
                    nFiles = int(response)
                except ValueError:
                    nFiles = 1
                for fileNum in range(startPos, startPos + nFiles):
                    fname = self.fileNameList[fileNum]
                    self.sendRdfFile(fname)
                    time.sleep(0.5)
                startPos += nFiles
                # Wait for the frequency converters to update
                time.sleep(1.0)
                config = self.rdFreqConvRpc.getWarmBoxConfig()
                coeffSect = config['VIRTUAL_CURRENT_2']
                ncoeffs = int(config['VIRTUAL_PARAMS_2']['NCOEFFS'])
                coeffs = [float(coeffSect['COEFF%d' % i]) for i in range(ncoeffs)]
                pylab.plot(coeffs)
                pylab.title("After processing %s" % fname)
                pylab.show()
                if startPos >= totFiles:
                    break
        finally:
            self.stopRdFreqConv()
    
if __name__ == "__main__":
    dirName = r"C:\temp\CorruptingRDFS\RDF"
    fileNames = []
    with file(os.path.join(dirName, "fileList.txt"), "r") as fp:
        for line in fp:
            assert isinstance(line, (str, unicode))
            line = line.strip()
            if line.startswith("#"):
                continue
            fileNames.append(os.path.join(dirName, line))
    rdFreqConv = dict(source = r"c:\Users\stan\Dropbox\GitHub\host\Host\RDFrequencyConverter\RDFrequencyConverter.py", 
                      config = r"c:\temp\CorruptingRDFS\RDFrequencyConverter.ini")
    #schemeFiles = [r"c:\temp\CorruptingRDFS\_Beta_CFKADS_nocal_v2.sch",
    #               r"c:\temp\CorruptingRDFS\_Beta_CFKADS_cal_v2.sch"]
    schemeFiles = [r"c:\temp\CorruptingRDFS\_Beta_CFKADS_cal_v2.sch"]
    
    dd = DummyDriver()
    dd._startServer()  # pylint: disable=W0212
    rr = RdfReplay(fileNames, rdFreqConv)
    rr.setSchemeFiles(schemeFiles, startTable=2)
    rr.run()
    
"""
Notes:
We need to broadcast interface.RingdownEntryType objects to the BROADCAST_PORT_RD_RESULTS

class RingdownEntryType(Structure):
    _fields_ = [
    ("timestamp",c_longlong),
    ("wlmAngle",c_float),
    ("uncorrectedAbsorbance",c_float),
    ("correctedAbsorbance",c_float),
    ("status",c_ushort),
    ("count",c_ushort),
    ("tunerValue",c_ushort),
    ("pztValue",c_ushort),
    ("laserUsed",c_ushort),
    ("ringdownThreshold",c_ushort),
    ("subschemeId",c_ushort),
    ("schemeVersionAndTable",c_ushort),
    ("schemeRow",c_ushort),
    ("ratio1",c_ushort),
    ("ratio2",c_ushort),
    ("fineLaserCurrent",c_ushort),
    ("coarseLaserCurrent",c_ushort),
    ("fitAmplitude",c_ushort),
    ("fitBackground",c_ushort),
    ("fitRmsResidual",c_ushort),
    ("laserTemperature",c_float),
    ("etalonTemperature",c_float),
    ("cavityPressure",c_float)
    ]

"""