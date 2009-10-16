#!/usr/bin/python
#
# File Name: SpectrumManager.py
# Purpose:
#   The SpectrumManeger is a subsystem of the Measurement system.  It handles
#   all DAS communications and also is responsible for configuring spectra
#   and assembling the spectra for the Measurement System to use.
#
# Notes:
#
# ToDo:
#
# File History:
# 06-09-13 russ  First real release
# 06-09-15 russ  Support 2 lasers; Support ignored points in scheme; Return time reference when done
# 06-10-12 russ  fix for threading module time change bug
# 06-12-19 russ  Support for polar schemes and interspersed calibration points (large change)
# 06-12-21 russ  Improved performance while processing cal spectra; configurable RD timeout
# 07-01-24 sze   Changed calibration row processing to use medians, and fixed problem with branch cuts when taking median of angles.
# 07-01-26 sze   Do not use RD_WAVENUMBER_OFFSET registers with polar locking
# 07-01-29 sze   Corrected laser indices sent to Autocal1
# 07-04-16 sze   Changed DAS clock resync period to 120s
# 07-04-20 sze   Changed RDF format to version 11, to include lockSetpoint and etalonAndLaserSelect
# 07-08-23 sze   Use pickled dictionary for communication to fitter
# 07-10-24 sze   Support subsections within a spectrum for use with fast flux instrument. A single "spectrum" is an object
#                 which is sent to the fitter and is identified by a SpectrumId. For efficiency, separate spectra should
#                 not be sent too often. Subsections allow a spectrum to be further divided by the fitter.
# 07-10-24 sze   Corrected a bug in which the wrong scheme was used for processing ringdown data. It is necessary to pass
#                 the dasScheme together with each ringdown on RdQueue so that it may be used to discover the wavelength setpoint.
#                Explicitly cast some ringdown result arrays to floating point, so they can be used in filters.
# 07-10-25 sze   Use median rather than mean of tuner values at calibration points for recentering waveform for robustness
#                Added handling of min_calrows and max_offgrid (parameters in hot box calibration file)
# 08-02-13 sze   Add solenoid valves to sensor stream
# 08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj
# 08-11-26 alex  Modified gatSchemeClass method to remove memory leak
# 09-01-28 alex  Modified the spectrum masks and removed the configurable lockerMode so the old scheme files are compatible
# 09-06-25 alex  Spectrum rdf data can only be saved in files, no more memory option. Save spectrum data in either pickled RDF format or the new HDF5 (.h5) 
#                            format. Removed GetRDFString().
if __debug__: DEBUG_VERBOSITY = 1
####
## Set constants for this file...
####
APP_NAME = "SpectrumManager"
####
## Imports from external libraries...
####
import sys
if "../Common" not in sys.path: sys.path.append("../Common")
import Queue
import time
import threading
if sys.platform == 'win32':
    threading._time = time.clock #prevents threading.Timer from getting screwed by local time changes
from xmlrpclib import Binary as xmlrpc_Binary
import os.path
import cPickle
import cStringIO
if sys.platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp
import numpy
import ctypes
import math
####
## Imports from Picarro generated libraries...
####
from Include import * #the local include file
import CmdFIFO
import BetterTraceback
from SharedTypes import RPC_PORT_CAL_MANAGER, RPC_PORT_DRIVER, RPC_PORT_LOGGER, RPC_PORT_ARCHIVER
from SharedTypes import BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_SENSORSTREAM, BROADCAST_PORT_RDRESULTS
from SharedTypes import getSchemeClass, HostRdResultsType
from SharedTypes import DasVersionError
from SharedTypes import MAX_LASERS
import Autocal1  # Handles freq<->polar coords
import Broadcaster
import Listener
import ss_autogen as ss
from StringPickler import ObjAsString, PackArbitraryObject
from ProfileThreads import profileThread
from EventManagerProxy import *

from CustomConfigObj import CustomConfigObj
from tables import *

EventManagerProxy_Init(APP_NAME, PrintEverything = __debug__)
#Adjust minimum DAS versions by changing the constant(s) below...
MIN_MCU_VERSION = 5.0
MINIMUM_DAS_VERSIONS = dict(mcu = MIN_MCU_VERSION)

#Set some constants for the spectrum measurement mode...
SWEEP_SINGLE     = 0
SWEEP_CONTINUOUS = 1

MAX_SPECTRUM_WAIT_PERIOD_s = 30
RDF_VERSION = 11
MAX_TIME_CORRECTION_ALLOWANCE_ms = 2**31 #for rollover protection

TICKREF_SPECTRUM = "SP"
TICKREF_LIST = [TICKREF_SPECTRUM, ]

# Some masks for interpreting the "subSchemeID" info (subSchemeID is basically
# a pass through, with the exception of the special increment bit 15)...
# !!! NOTE: Bit 15 is reserved for increment flag in firmware, so never use it for other purposes!!!
INCR_FLAG_MASK       = 0x8000 # 32768 - Bit 15 is used for special increment flag
SPECTRUM_IGNORE_MASK = 0x4000 # 16384 - Bit 14 is used to indicate the point should be ignored
SPECTRUM_BF_MASK     = 0x2000 #  8192 - Bit 13 is unused, but used historically for backward-forward indication
SPECTRUM_ISCAL_MASK  = 0x1000 #  4096 - Bit 12 is used to flag a point as a cal point to be collected
SPECTRUM_FIRST_MASK  = 0x0800 #  2048 - Bit 11 is used to indicate the first point in the spectrum
SPECTRUM_LAST_MASK   = 0x0400 #  1024 - Bit 10 is used to indicate the last point in the spectrum

SPECTRUM_SUBSECTION_ID_MASK = 0x0300
SPECTRUM_ID_MASK    = 0x00FF #Bottom 8 bits of schemeStatus are the spectrum id/name


LOCKER_MODE_UNSPECIFIED = -1
LOCKER_MODE_FREQUENCY = 0
LOCKER_MODE_ANGLE = 1

STATE_ERROR = 0x0F
STATE_INIT = 0
STATE_READY = 1
STATE_SWEEPING = 2
#STATE_WAITING_FOR_TRIGGER = 3

StateName = {}
StateName[STATE_ERROR] = "ERROR"
StateName[STATE_INIT] = "INIT"
StateName[STATE_READY] = "READY"
StateName[STATE_SWEEPING] = "SWEEPING"
####
## Some debugging/development helpers...
####
if __debug__:
    #some debugging imports...
    from pprint import pprint
    from binary_repr import binary_repr
    #verify that we have text names for each state...
    __localsNow = {}
    __localsNow.update(locals())
    for __k in __localsNow:
        if __k.startswith("STATE_"):
            assert (__localsNow[__k] in StateName.keys()), "Code Error - A StateName string entry needs to be defined for %s." % __k
            if __k != "STATE__UNDEFINED]":
                assert __localsNow[__k] <= 0x0F, "Legit state values must be < 0x0F, with 0x0F reserved for ERROR"
    del __localsNow, __k
#endif (__debug__)

# Type conversion dictionary for ctypes to numpy

ctypes2numpy = {ctypes.c_byte:numpy.byte, ctypes.c_char:numpy.byte, ctypes.c_double:numpy.float_,
                ctypes.c_float:numpy.single, ctypes.c_int:numpy.intc, ctypes.c_int16:numpy.int16,
                ctypes.c_int32:numpy.int32, ctypes.c_int64:numpy.int64, ctypes.c_int8:numpy.int8,
                ctypes.c_long:numpy.int_, ctypes.c_longlong:numpy.longlong, ctypes.c_short:numpy.short,
                ctypes.c_ubyte:numpy.ubyte, ctypes.c_uint:numpy.uintc, ctypes.c_uint16:numpy.uint16,
                ctypes.c_uint32:numpy.uint32, ctypes.c_uint64:numpy.uint64, ctypes.c_uint8:numpy.uint8,
                ctypes.c_ulong:numpy.uint, ctypes.c_ulonglong:numpy.ulonglong, ctypes.c_ushort:numpy.ushort}

# set up a handy (and totally bogus) autocomplete reference for working in Wing...
if 0: #for Wing
    class ___RDResults(object):
        wavenum = ctypes.c_uint()
        wavenumSetpoint = ctypes.c_uint()
        thetaCal = ctypes.c_float()
        laserTemp = ctypes.c_float()
        ratio1 = ctypes.c_float()
        ratio2 = ctypes.c_float()
        correctedAbsorbance = ctypes.c_float()
        uncorrectedAbsorbance = ctypes.c_float()
        pztValue = ctypes.c_ushort()
        tunerValue = ctypes.c_ushort()
        etalonSelect = ctypes.c_int8()
        laserSelect = ctypes.c_int8()
        fitStatus = ctypes.c_short()
        schemeStatus = ctypes.c_ushort()
        msTicks = ctypes.c_uint()
        count = ctypes.c_ushort()
        subSchemeId = ctypes.c_ushort()
        schemeTableIndex = ctypes.c_ushort()
        schemeRow = ctypes.c_ushort()
        # endif (0 - bogus defs for Wing)
####
## RPC connections to other CRDS applications...
####
CRDS_Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, \
                                      APP_NAME, IsDontCareConnection = False)
CRDS_CalMgr = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_CAL_MANAGER, \
                                      APP_NAME, IsDontCareConnection = False)
####
## Custom exceptions...
####
class SpectrumManagerErr(MeasSystemError):
    """Base class for SpectrumManager exceptions (all of which should be handled internally)."""
class InvalidScheme(SpectrumManagerErr):
    """Problem encountered with a specified scheme file."""
class SpectrumCollectionErr(SpectrumManagerErr):
    """Problem encountered when collection spectrum."""
class RingdownTimeout(SpectrumCollectionErr):
    """Timed out while waiting for a ringdown to arrive."""
class FirstPointTimeout(SpectrumCollectionErr):
    """Timed out while waiting for the first point in a spectrum."""
class SweepAborted(SpectrumCollectionErr):
    """A spectrum collection was aborted, but not due to an error."""
class CommandError(MeasSystemError):
    """Root of all exceptions caused by a bad/inappropriate command."""
def AssertMinDASVersions():
    conflicts = CRDS_Driver.DAS_CheckMinVersions(MINIMUM_DAS_VERSIONS)
    if conflicts:
        problemData = dict(RequiredVersions = MINIMUM_DAS_VERSIONS, DAS_Versions = conflicts)
        Log("Version compatibility error with DAS firmware load(s).",
            problemData,
            Level = 3)
        raise DasVersionError(problemData)
def NameOfThisCall():
    return sys._getframe(1).f_code.co_name

def copyCtypesStruct(dest,src):
    """Copy contents of ctypes structure src into dest. Only assumption is that dest contains all the fields of src."""
    for f,t in src._fields_:
        setattr(dest,f,getattr(src,f))
def getLaserFromSchemeEntry(schemeEntry):
    """Extract the laser number from the appropriate field of a scheme entry, to accomodate different versions of the
       structure"""
    try:
        return schemeEntry.laserSelectAndThreshold & 0x3
    except:
        return schemeEntry.laserSelectAndUseThreshold & 0x7FFF

__lastTrailTime = None
__callsSinceLast = 0
def printTrail(name,interval=10):
    """Call this to print a diagnostic message at intervals no more frequently than 'interval' """
    global __lastTrailTime, __callsSinceLast
    now = TimeStamp()
    __callsSinceLast += 1
    if __lastTrailTime == None or now>__lastTrailTime + interval:
        print "%s was encountered %d times" % (name,__callsSinceLast)
        __callsSinceLast = 0
        __lastTrailTime = now


class _SensorData(object):
    """A structure for sensor data relevant to the spectra (needed for fit).
    """
    def __init__(self):
        self.SensorTime_s = 0.
        self.Cavity_P_Torr = 0.
        self.Cavity_T_C = 0.
        self.Laser_T_C = 0.
        self.Etalon_T_C = 0.
        self.WarmBox_T_C = 0.
        self.LaserTec_I_mA = 0.
        self.WarmBoxTec_I_mA = 0.
        self.HotBoxTec_I_mA = 0.
        self.Heater_I_mA = 0.
        self.Environment_T_C = 0.
        self.InletValve_Pos = 0
        self.OutletValve_Pos = 0
        self.SolenoidValves = 0
    def copy(self):
        """Returns a copy of this object.
        """
        newCopy = _SensorData()
        for k in self.__dict__:
            setattr(newCopy, k, getattr(self, k))
        return newCopy
    def __str__(self):
        buf = ""
        buf += "%7.1f" % self.SensorTime_s
        keys = self.__dict__.keys()
        keys.sort()
        for k in keys:
            if k != "SensorTime_s":
                buf += " %5.1f" % getattr(self, k)
        return buf
    def __repr__(self):
        return repr(self.__dict__)

class DasScheme(object):
    """DAS scheme management class that handles alternates.

    Schemes are handled in the following way, with notes on how they should be made:
     1. Spectrum start is identified with bit 12 of subSchemeID (dec = 4096)
          - Automatically done, no need to specify starts in a scheme file.  All
            that need be specified is the end of a spectrum...
     2. Spectrum stop is identified with bit 11 of subSchemeID (dec =  2048)
          - This must be done right in the scheme file (add 2048 to the spectrumID
            you want to use)
          - error if possible to identify (eg: new spectrumID w/o terminator)
     3. The first point in a spectrum must have a dwell of 1
          - done automatically if not done in the scheme file
     4. The last  point in a spectrum must have a dwell of 1
          - done automatically if not done in the scheme file
     5. The increment flag (on subSchemeID) is always set on the first pt in a spectrum
          - automatically done.  Not required in scheme file.
          - it is an error to specify an increment flag in a scheme file.

    The above rules are used/checked when ForceSpectrumRules is True on teh
    Update calls.

    Note: "SubSchemeID" is a legacy name... what it really does is pass
    directly through from scheme definition to ringdown reporting. In
    addition, bit 15 (MSB) is an indicator to increment the counter.

    """
    def __init__(self, SchemeName, DasIndex_A, DasIndex_B, ForcePolarLocking, FreqConverterDict):
        self._DasIndex_A = DasIndex_A
        self._DasIndex_B = DasIndex_B
        self._CurrentIndex = -1
        self._CurrentAlternateIndex = -1
        self._OriginalScheme = None   # Holds the original scheme definition (always the starting point if doing things like freq->angle conversions)
        self._CurrentScheme = None    # Holds the current scheme definition, regardless of current index
        self._AlternateScheme = None  # Holds the alternate scheme definition, regardless of current index
        self._OriginalLockerMode = LOCKER_MODE_UNSPECIFIED
        self._LockerMode = LOCKER_MODE_UNSPECIFIED
        self._ForcePolarLocking = ForcePolarLocking
        self._FreqConverter = FreqConverterDict
        self._OriginalSchemeFileName = ""
        self.schemeClassDict = {}
        
    def GetSchemeClass(self, ver, numEntries):
        if numEntries not in self.schemeClassDict:
            self.schemeClassDict[numEntries] = getSchemeClass(ver, numEntries)
        return self.schemeClassDict[numEntries] 
        
    def CopyScheme(self, SourceScheme):
        """Returns an exact copy of the SourceScheme."""
        #First allocate the space by creating an appropriately sized scheme...
        schemeCopy = self.GetSchemeClass(CRDS_Driver.version(), SourceScheme.numEntries)()
        assert ctypes.sizeof(schemeCopy) == ctypes.sizeof(SourceScheme)
        #Now copy the memory...
        ctypes.memmove(ctypes.addressof(schemeCopy), ctypes.addressof(SourceScheme), ctypes.sizeof(SourceScheme))
        return schemeCopy
        
    def Initialize(self, InitialSchemePath, UseOldSchemeFile = False, ForceSpectrumRules = True):
        """Loads the specified scheme and uploads it to the DAS.

        The original scheme is always preserved for later use.

        The DAS table index uploaded to is the appropriate one for swapping.

        """
        self._CurrentIndex = self._DasIndex_A
        self._CurrentAlternateIndex = self._DasIndex_B
        Log("Initializing DAS scheme", dict(SchemePath = InitialSchemePath,
                                            Index_A = self._DasIndex_A,
                                            Index_B = self._DasIndex_B))
        self._OriginalSchemeFileName = os.path.split(InitialSchemePath)[1]
        self._OriginalScheme = self._LoadSchemeFromFp(file(InitialSchemePath, "r"), UseOldSchemeFile, ForceSpectrumRules)

        if (self._OriginalLockerMode == LOCKER_MODE_FREQUENCY) and self._ForcePolarLocking:
            #do the conversion
            startTime = TimeStamp()
            Log("Starting conversion of frequency scheme to polar values", dict(SchemeFile = self._OriginalSchemeFileName))
            self._CurrentScheme = self.ConvertFrequencySchemeToAngle(self._OriginalScheme)
            Log("Freq conversion completed", dict(ElapsedTime_s = (TimeStamp() - startTime), SchemeFile = self._OriginalSchemeFileName))
            self._LockerMode = LOCKER_MODE_ANGLE
        else:
            #Could maybe just set the current to the original, but am making a copy
            #in case the current ever changes for some reason (not in this case at
            #time of writing, but you never know...)
            self._CurrentScheme = self.CopyScheme(self._OriginalScheme)
            self._LockerMode = self._OriginalLockerMode
        #Now upload it...
        Log("Starting scheme upload", dict(TargetIndex = self._CurrentIndex, Scheme = self._OriginalSchemeFileName, LockerMode = self._LockerMode))
        self._BaseSchemeUpload(self._CurrentScheme, self._CurrentIndex, InitialSchemePath)
        Log("Scheme upload completed", dict(TargetIndex = self._CurrentIndex, Scheme = self._OriginalSchemeFileName))
    def ConvertFrequencySchemeToAngle(self, SrcScheme, MidRowDelay_s = 0):
        """Converts the given frequency-based scheme to an angle scheme.
        This calculation can be a bad cpu hog, in particular for the process that is running this code.
        """
        ##First make a copy of the scheme...
        startTime = TimeStamp()
        newScheme = self.CopyScheme(SrcScheme)
        dataByLaser = {}
        ## We want to use the efficient vectorized routines for polar conversion. These are methods of the objects
        ##  stored in self._FreqConverter, which are indexed by laser number.
        for i in xrange(newScheme.numEntries):
            laserNum = getLaserFromSchemeEntry(SrcScheme.schemeEntry[i])
            waveNum = float(SrcScheme.schemeEntry[i].setpoint.asUint32)/100000.0
            if laserNum not in dataByLaser:
                dataByLaser[laserNum] = ([],[])
            dataByLaser[laserNum][0].append(i)
            dataByLaser[laserNum][1].append(waveNum)
        for laserNum in dataByLaser:
            fc = self._FreqConverter[laserNum]
            waveNum = numpy.array(dataByLaser[laserNum][1],numpy.float_)
            time.sleep(0)
            thetaCal = fc.waveNumber2ThetaCal(waveNum)
            time.sleep(0)
            tLaser = fc.thetaCal2LaserTemp(thetaCal)
            time.sleep(0)
            for j,i in enumerate(dataByLaser[laserNum][0]):
                newScheme.schemeEntry[i].setpoint.asFloat = thetaCal[j]
                newScheme.schemeEntry[i].laserTemp = tLaser[j]
            time.sleep(0)
            #print "wn%03d = %.3f    Theta = %.3f LT = %.3f" % (i, waveNum, newScheme.schemeEntry[i].setpoint.asFloat, newScheme.schemeEntry[i].laserTemp)
            #print "ssid = ", newScheme.schemeEntry[i].subSchemeIdAndIncrFlag
        return newScheme
    def UpdateScheme(self, NewScheme):
        """Uploads the provided scheme to the alternate DAS location and switches
        the DAS to run it instead.

        """
        self._AlternateScheme = NewScheme
        #Upload the scheme to the "other" spot...
        self._BaseSchemeUpload(self._AlternateScheme, self._CurrentAlternateIndex, self._OriginalSchemeFileName)
        #Now swap them...
        self._SwapToAlternateScheme()
    def _SwapToAlternateScheme(self):
        #Get the accurate representation of what the DAS is currently running...
        seq = CRDS_Driver.rdSchemeSequence()
        #Fix the sequence...
        for i in range(len(seq)):
            if seq[i] == self._CurrentIndex:
                seq[i] = self._CurrentAlternateIndex
        restart = False; loop = True
        CRDS_Driver.wrSchemeSequence(seq, restart, loop)
        #Update our local scheme records...
        self._CurrentIndex, self._CurrentAlternateIndex = self._CurrentAlternateIndex, self._CurrentIndex
        self._CurrentScheme, self._AlternateScheme = self._AlternateScheme, self._CurrentScheme
        # AND NOW UPDATE THE DAS
        # - need to check the scheme sequence and substitute the appropriate index to its alt
    def _LoadSchemeFromFp(self, fp, UseOldSchemeFile, ForceSpectrumRules):
        """Loads a scheme from fp.  With ForceSpectrumRules == True the resulting
        scheme has all the "correct" subschemeIDs and dwells.

        Returns the scheme, suitable for upload to the DAS (instance is of the
        ctypes class structure dynamically obtained with getSchemeClass()).

        Corrections are made to the scheme so that the spectra are easy to
        differentiate when they are collected. There are also some changes to get
        around problems with the DAS implementation (eg: last point in scheme must
        have a dwell of one for the DAS to do what we want).

        Raises InvalidScheme if there are problems with the scheme.

        """
        try:
            Label = fp.name #legacy variable name
            nrepeat = int(fp.readline())
            numEntries = int(fp.readline())
            # The section below was commented out because the third line of the new scheme file was 
            # removed because its value was always set as 0 (frequency locker mode).
            #
            #thirdLine = fp.readline()
            #if len(thirdLine.split()) > 2:
            #    raise InvalidScheme("The third line in the scheme file MUST indicate the locker mode.  0 = frequency; 1 = angle;")
            #lockerMode = int(thirdLine)
            #if lockerMode not in [LOCKER_MODE_ANGLE, LOCKER_MODE_FREQUENCY]:
            #    raise InvalidScheme("Unrecognized locker mode: %s" % thirdLine.strip())
            #
            lockerMode = 0
            self._OriginalLockerMode = lockerMode
            #Now get and set up the appropriate scheme class (version dependent)...
            ver = CRDS_Driver.version()
            scheme = self.GetSchemeClass(ver, numEntries)()
            scheme.nrepeat = nrepeat
            scheme.numEntries = numEntries
            dwellCorrectionCount = 0

            lastSpectrumID = -1
            lastWasSpectrumLast = True

            ## Load the scheme and change subschemeIDs as appropriate...
            ##  - if dwells have issues they will be corrected later

            if scheme.nrepeat <= 0:
                problem = "nrepeat <= 0"
                Log("Invalid scheme file loaded", dict(Scheme = Label, Problem = problem), 2)
                raise InvalidScheme("'%s' in %s" % (problem, Label))
            try:
                for i in range(scheme.numEntries):
                    toks = fp.readline().split()
                    # We need to fill up the scheme structure in a version-independent way
                    sE = scheme.schemeEntry[i]
                    schemeFields = sE._fields_
                    # The number of fields present is len(schemeFields)
                    # In order to get access to field j, we use getattr(sE,schemeFields[j][0])
                    # The ctypes type of the field is schemeFields[j][1]
                    for itok,tok in enumerate(toks):
                        fieldName,fieldType = schemeFields[itok]
                        if fieldType in [ctypes.c_int] and fieldName == "setpoint":
                            setattr(sE,fieldName,100000.0*float(tok))
                        elif fieldType in [ss.DataType] and fieldName == "setpoint":
                            setpoint = ss.DataType()
                            if lockerMode == LOCKER_MODE_FREQUENCY:
                                setpoint.asUint32 = int(100000.0*float(tok))
                            elif lockerMode == LOCKER_MODE_ANGLE:
                                setpoint.asFloat = float(tok)
                            else:
                                raise InvalidScheme("Unrecognized locker mode: %d" % lockerMode)
                            setattr(sE,fieldName,setpoint)
                        elif fieldType in [ctypes.c_ushort] and fieldName == "subSchemeIdAndIncrFlag":
                            newSubSchemeId = self._SubSchemeIdConversion(int(tok), i, UseOldSchemeFile)
                            setattr(sE,fieldName,newSubSchemeId)                            
                        elif fieldType in [ctypes.c_ushort]:
                            setattr(sE,fieldName,int(tok))
                        elif fieldType in [ctypes.c_float]:
                            setattr(sE,fieldName,float(tok))
                        else:
                            raise TypeError("Unrecognized fieldType/Name in scheme processing: %s / %s" % (fieldType,fieldName))
                    if len(schemeFields) > 2 and ForceSpectrumRules:
                        #Subscheme must be done in a particular way...
                        subSchemeIdAndIncrFlag = sE.subSchemeIdAndIncrFlag
                        thisSpectrumID    = subSchemeIdAndIncrFlag & SPECTRUM_ID_MASK
                        isSpectrumLast    = subSchemeIdAndIncrFlag & SPECTRUM_LAST_MASK
                        isSpectrumFirst = False
                        if lastWasSpectrumLast:
                            isSpectrumFirst = True
                        
                        #Now for some error checking...
                        if (isSpectrumFirst or isSpectrumLast) and (scheme.schemeEntry[i].dwellCount != 1):
                            dwellCorrectionCount += 1

                        if (subSchemeIdAndIncrFlag & SPECTRUM_FIRST_MASK): #it should not be set!
                            problem = "Spectrum_start bit set in scheme file.  Bit 12 should not be set."
                            Log("Invalid scheme file loaded", dict(Scheme = Label, Problem = problem), 2)
                            raise InvalidScheme("'%s' in %s" % (problem, Label))

                        if (subSchemeIdAndIncrFlag & INCR_FLAG_MASK): #it should not be set in the file!
                            problem = "IncrFlag bit set in scheme file.  Bit 15 should not be set."
                            Log("Invalid scheme file loaded", dict(Scheme = Label, Problem = problem), 2)
                            raise InvalidScheme("'%s' in %s" % (problem, Label))

                        if (thisSpectrumID != lastSpectrumID) and (not lastWasSpectrumLast):
                            problem = "New spectrum ID encountered without previous spectrum termination."
                            Log("Invalid scheme file loaded", dict(Scheme = Label, Problem = problem), 2)
                            raise InvalidScheme("'%s' in %s" % (problem, Label))

                        #Now set up the "subSchemeID" correctly...
                        #subSchemeIdAndIncrFlag  = thisSpectrumID
                        #if isSpectrumLast:
                        #  subSchemeIdAndIncrFlag |= SPECTRUM_LAST_MASK
                        if isSpectrumFirst:
                            subSchemeIdAndIncrFlag |= SPECTRUM_FIRST_MASK
                            subSchemeIdAndIncrFlag |= INCR_FLAG_MASK
                        #Now assign the determined value to the scheme entry...
                        sE.subSchemeIdAndIncrFlag = subSchemeIdAndIncrFlag

                        #NOTE: Following diagnostic printout works for only interface versions 4.x and above
                        #print "%4d %d %2d %04x %d %d" % (i,
                        #                                 scheme.schemeEntry[i].setpoint.asUint32,
                        #                                 scheme.schemeEntry[i].dwellCount,
                        #                                 scheme.schemeEntry[i].subSchemeIdAndIncrFlag,
                        #                                 scheme.schemeEntry[i].laserSelectAndThreshold,
                        #                                 scheme.schemeEntry[i].pztSetpoint)
                        lastSpectrumID = thisSpectrumID
                        lastWasSpectrumLast = isSpectrumLast
                    #endif (ForceSpectrumRules)
                #endfor (all scheme entries)
            except Exception, exc:
                Log("Error reading scheme file", dict(Scheme = Label, Type = repr(exc), Desc = str(exc)), 2)
                raise InvalidScheme(Label)

            ## Now correct any dwell issues that might exist in scheme...
            if dwellCorrectionCount > 0:
                #we have some corrections to make to the scheme, because start or stop points have a dwell > 1...
                numEntries += dwellCorrectionCount
                #Now get and set up the appropriate scheme class (version dependent)...                
                fixedScheme = self.GetSchemeClass(ver, numEntries)()
                fixedScheme.nrepeat = nrepeat
                fixedScheme.numEntries = numEntries
                curIndex = 0
                #loop through the scheme that needs fixing...
                for i in range(scheme.numEntries):
                    dwellCount = scheme.schemeEntry[i].dwellCount
                    subSchemeIdAndIncrFlag = scheme.schemeEntry[i].subSchemeIdAndIncrFlag
                    isSpectrumFirst = (subSchemeIdAndIncrFlag & SPECTRUM_FIRST_MASK)
                    isSpectrumLast  = (subSchemeIdAndIncrFlag & SPECTRUM_LAST_MASK)
                    ID = (subSchemeIdAndIncrFlag & (SPECTRUM_SUBSECTION_ID_MASK | SPECTRUM_ID_MASK))
                    if isSpectrumFirst and (dwellCount > 1):
                        #Need to split it into 1 then the rest
                        newSS = ID | SPECTRUM_FIRST_MASK | INCR_FLAG_MASK
                        copyCtypesStruct(fixedScheme.schemeEntry[curIndex],scheme.schemeEntry[i])
                        fixedScheme.schemeEntry[curIndex].dwellCount = 1
                        fixedScheme.schemeEntry[curIndex].subSchemeIdAndIncrFlag = newSS
                        #Prevent follow-on logic from propagating the flags...
                        subSchemeIdAndIncrFlag = subSchemeIdAndIncrFlag & ~SPECTRUM_FIRST_MASK & ~INCR_FLAG_MASK & 0xFFFF
                        #Now leave the rest of the dwell to following logic...
                        dwellCount -= 1
                        curIndex += 1
                        #NOTE - we are leaving some number of dwells that doesn't have a start flag.
                    if isSpectrumLast and (dwellCount > 1):
                        copyCtypesStruct(fixedScheme.schemeEntry[curIndex],scheme.schemeEntry[i])
                        #Want to peel of the first bunch as normal points, leaving 1 with the finish flag stuff
                        fixedScheme.schemeEntry[curIndex].dwellCount = dwellCount - 1
                        fixedScheme.schemeEntry[curIndex].subSchemeIdAndIncrFlag = ID
                        dwellCount = 1
                        curIndex += 1
                        #NOTE - we are leaving a dwell of 1
                    copyCtypesStruct(fixedScheme.schemeEntry[curIndex],scheme.schemeEntry[i])
                    fixedScheme.schemeEntry[curIndex].dwellCount = dwellCount
                    fixedScheme.schemeEntry[curIndex].subSchemeIdAndIncrFlag = subSchemeIdAndIncrFlag
                    curIndex += 1
                #endfor (looping through previous scheme)
                scheme = fixedScheme
                #if __debug__:
                    #print "Corrected scheme:\n-----------------"
                    #for i in range(fixedScheme.numEntries):
                        #print "%4d %d %2d %04x %d %d" % (i,
                                                     #fixedScheme.schemeEntry[i].setpoint.asUint32,
                                                     #fixedScheme.schemeEntry[i].dwellCount,
                                                     #fixedScheme.schemeEntry[i].subSchemeIdAndIncrFlag,
                                                     #fixedScheme.schemeEntry[i].laserSelectAndThreshold,
                                                     #fixedScheme.schemeEntry[i].pztSetpoint)
                #### FREQUENCY SCHEME IS DONE(WITH CORRECTED SUBSCHEMES AND DWELLS) AT THIS POINT
            #endif (dwell correction count needed)
        finally:
            if not fp is None:
                fp.close()
        return scheme
    def _BaseSchemeUpload(self, Scheme, SchemeIndex, Label = ""):
        """Uploads a scheme referred to by the fp, with Label as a label for reporting problems.

        """
        msgStr = ObjAsString(Scheme)
        CRDS_Driver.SpectCntrl_UploadScheme(SchemeIndex, xmlrpc_Binary(msgStr), Scheme.numEntries, self._LockerMode)

    def _SubSchemeIdConversion(self, subSchemeId, rowNumber, useOldSchemeFile = False):
        """The old scheme files use bit 15 to represent the "end bit", but it won't work for new scheme method because
        bit 15 has to be reserved for the "increment flag" in firmware. The new scheme method has to move the end bit 
        to bit 10 and leave bit 15 available if running old scheme files.
        The "end bit" should be removed if it shows in the first row (the old scheme files always set "end bit" in first row)
        """
        if useOldSchemeFile:
            endBit = (subSchemeId & 0x8000) >> 15
            subSchemeId &= 0x7FFF # Keep bit 0 ~ bit 14
            if rowNumber > 0:
                subSchemeId += (endBit * SPECTRUM_LAST_MASK) # Only add the 'end bit' back when it's not in the first row
        elif rowNumber == 0:
            subSchemeId &= (~SPECTRUM_LAST_MASK) # Get rid of 'end bit' from the first row
        return subSchemeId
    
class CSpectrum(object):
    """A class for holding a collected spectrum.

    FirstRdTime_s is the actual clock time of the first RD (in seconds since
    epoch). All subsequent RDs added to the spectrum will be recorded as
    relative times from this value.

    If StreamDir is specified, the spectrum will be stored to file.
    If no StreamDir specified, the spectrum is collected in memory (removed on 06/25/09).
    In either case, when the spectrum is finished (check this with IsFinished)
    the RDF contents are retrieved with GetRDFString() (removed on 06/25/09).

    On creation of an instance, a file header is written.

    """

    def __init__(self, SpectrumID, FirstRdTime_s, TagalongDataDict, SchemeTableIndex, StreamDir, UseHDF5):
        self.SpectrumID = SpectrumID        # ID of the spectrum referred to (bottom 8 bits of subSchemeID)
        self.SchemeTableIndex = SchemeTableIndex
        self._FirstRdTime_s = FirstRdTime_s
        self.Measurement_Time_s = -1
        
        self._StreamDir = StreamDir
        self.UseHDF5 = UseHDF5
        if self.UseHDF5:
            self.Name = "%03d_%013d.h5" % (self.SpectrumID, int(time.time()*1000))
            self._StreamPath = os.path.join(self._StreamDir, self.Name)
            self._StreamFP = openFile(self._StreamPath, "w")
        else:
            self.Name = "%03d_%013d.rdf" % (self.SpectrumID, int(time.time()*1000))
            self._StreamPath = os.path.join(self._StreamDir, self.Name)
            self._StreamFP = file(self._StreamPath, "wb")
            
        self.NumPts = 0
        self._Finished = False
        self.TagalongData = TagalongDataDict
        self._RdBuffer = {}
        self._RdfDict = {}

        #Initialize the sensor averaging...
        self._AvgCount = 0
        self._AvgSensors = _SensorData()
        self._SumSensors = _SensorData()

        #Get the version number
        self._RdfDict["version"] = RDF_VERSION

        #Initialize the _RdBuffer with the names and types of fields in HostRdResultsType
        for fname,ftype in HostRdResultsType._fields_:
            self._RdBuffer[fname] = ([],ftype)
        self._RdBuffer["time"]= ([],ctypes.c_float)
        
        self._RdfFilters = Filters(complevel=1,fletcher32=True)

    def getNumPts(self):
        return self.NumPts

    def _DoSensorAveraging(self, SensorData):
        assert isinstance(SensorData, _SensorData) #for Wing
        self._AvgCount += 1.
        for k in self._AvgSensors.__dict__.keys():
            thisSum = getattr(self._SumSensors, k) + getattr(SensorData, k)
            setattr(self._SumSensors, k, thisSum)
            newAvg = thisSum / self._AvgCount
            setattr(self._AvgSensors, k, newAvg)
    def IsFinished(self):
        """Returns true if the spectrum has been fully acquired."""
        return self._Finished

    def AppendPoint(self, RdData, SensorData, RingDownTime_s):
        """Adds a single set of Data to the spectrum (at a single RingDownTime_s)
        """
        if 0: assert isinstance(RdData, ___RDResults) #for Wing

        for fname,ftype in HostRdResultsType._fields_:
            if fname in self._RdBuffer:
                self._RdBuffer[fname][0].append(getattr(RdData,fname))
        self._RdBuffer["time"][0].append(RingDownTime_s)
        self.NumPts += 1

        if SensorData == None: return

        #Sneak in the local ringdown time for sensor averaging...
        SensorData.SensorTime_s = RingDownTime_s
        self._DoSensorAveraging(SensorData)

    def Finish(self,controlData):
        """Closes off the acquisition of the spectrum.

        After this is done, no more data can be added, IsFinished() returns true,
        and GetRDFString() will work (removed on 06/25/09).

        """
        self._RdfDict = {"rdData" : {}, "sensorData" : {}, "tagalongData" : {}}
        # Convert the contents of self._RdBuffer lists into numpy arrays
        for fname in self._RdBuffer:
            data,dtype = self._RdBuffer[fname]
            self._RdfDict["rdData"][fname] = numpy.array(data,ctypes2numpy[dtype])
        # Explicitly cast some of these to arithmetic friendly types for filtering
        self._RdfDict["rdData"]["wavenum"] = numpy.array(self._RdfDict["rdData"]["wavenum"],numpy.float_)
        self._RdfDict["rdData"]["wavenumSetpoint"] = numpy.array(self._RdfDict["rdData"]["wavenumSetpoint"],numpy.float_)
        self._RdfDict["rdData"]["pztValue"] = numpy.array(self._RdfDict["rdData"]["pztValue"],numpy.single)
        self._RdfDict["rdData"]["tunerValue"] = numpy.array(self._RdfDict["rdData"]["tunerValue"],numpy.single)

        # Append averaged sensor data
        self._AvgSensors.SensorTime_s += self._FirstRdTime_s
        self._RdfDict["sensorData"] = self._AvgSensors.__dict__

        self._RdfDict["sensorData"]["SchemeID"] = self.SchemeTableIndex
        self._RdfDict["sensorData"]["SpectrumID"] = self.SpectrumID
        self._RdfDict["sensorData"]["SpectrumStartTime"] = self._FirstRdTime_s

        #Write the tagalong data values...
        self._RdfDict["tagalongData"] = self.TagalongData

        #Write control data dictionary for pacing, etc...
        self._RdfDict["controlData"] = controlData

        if self.UseHDF5:
            # Create HDF5 table file
            for dataKey in self._RdfDict.keys():
                subDataDict = self._RdfDict[dataKey]
                if len(subDataDict) > 0:
                    sortedKeys = sorted(subDataDict.keys())
                    if isinstance(subDataDict.values()[0], numpy.ndarray):
                        # Array
                        sortedValues = [subDataDict.values()[i] for i in numpy.argsort(subDataDict.keys())]
                        dataRec = numpy.rec.fromarrays(sortedValues, names=sortedKeys)
                    elif isinstance(subDataDict.values()[0], list) or isinstance(subDataDict.values()[0], tuple):
                        # Convert list or tuple to array
                        sortedValues = [numpy.array(subDataDict.values()[i]) for i in numpy.argsort(subDataDict.keys())]
                        dataRec = numpy.rec.fromarrays(sortedValues, names=sortedKeys)
                    else:
                        # Non-array
                        sortedValues = [subDataDict.values()[i] for i in numpy.argsort(subDataDict.keys())]
                        dataRec = numpy.rec.fromrecords([sortedValues], names=sortedKeys)
                    self._StreamFP.createTable("/", dataKey, dataRec, dataKey, filters=self._RdfFilters)
        else:
            # Pickle the _RdfDict 
            self._StreamFP.write(cPickle.dumps(self._RdfDict,cPickle.HIGHEST_PROTOCOL)) 
            
        self._StreamFP.close()
        self.Measurement_Time_s = self._AvgSensors.SensorTime_s
        self._Finished = True

class CalPoint(object):
    """Structure for collecting interspersed cal ringdowns in a scheme."""
    def __init__(self):
        self.tunerVals = []
        self.thetaCalCos = []
        self.thetaCalSin = []
        self.laserTempVals = []
        self.laserIndex = -1
        self.Count = 0

def calcWeights(x):
    """Calculate weights associated with integer array x. Elements of x must be sorted. The weight associated with x[i] is
    the number of times x[i] appears in the array, and this is placed in the result array w[i]."""
    w = numpy.zeros(x.shape,numpy.int_)
    kprev = 0
    c = 1
    for k in range(1,len(x)):
        if x[k] != x[k-1]:
            w[kprev:k] = c
            kprev = k
            c = 1
        else:
            c += 1
    w[kprev:] = c
    return w

def medianHist(values,freqs,useAverage=True):
    """Compute median from arrays of values and frequencies. The array of values need not be in ascending order"""
    if len(values) != len(freqs):
        raise ValueError("Lengths of values and freqs must be equal in medianHist")
    perm = numpy.argsort(values)
    csum = numpy.cumsum(freqs[perm])
    if useAverage and (csum[-1] % 2 == 0):
        mid2 = csum[-1]/2
        mid1 = mid2 - 1
        return 0.5*(values[perm[sum(mid1 >= csum)]]+values[perm[sum(mid2 >= csum)]])
    else:
        mid = (csum[-1]-1)/2
        return values[perm[sum(mid >= csum)]]

class SpectrumManager(threading.Thread):
    """Subsystem that assembles all of the data needed for each gas measurement.

    The primary purpose in this is to assemble what is needed for the fitter.

    This is a subsystem that is meant to abstract the spectrum collection as if
    there were discrete spectra being collected, and should ideally act like an
    independent OSA. Actual implementation stuff, like the fact that multiple
    spectra are prepared for the DAS via a scheme, should not be readily
    apparent with the use of this class.

    RD and sensor data are collected with Listeners which continuously populate
    a queue from which to extract (filtered) data.

    The SpectrumManager grabs data from the queues and assembles completed
    spectra, which it makes available via a spectrum queue.

    The Meas System will then get completed spectra via the spectrum queue.

    If no StreamDir specified (the default), spectra/rdf are accumulated in
    memory only (removed on 06/25/09). If a StreamDir is specified, rdf data is streamed to files in
    this directory.

    Incoming Assumptions:
     - DAS has been initialized (temperatures stabilized, cal loaded, etc)

    Output condition (after creation of instance)
     - SpectrumManager ready for action
     - SpectrumManager does nothing until SweepStart() is called
     - DAS will *not* be sweeping (SweepStop called in __init__)

    """
    def __init__(self,
                 SpectrumQueue,
                 StreamDir,
                 UseHDF5 = False,
                 ForcePolarLocking = True,
                 WarmboxCalFilePath = "",
                 SchemeDict = {},
                 CalUpdatePeriod_s = 0,
                 RingdownTimeout_s = 0,
                 UseOldSchemeFile = False):
        # # # IMPORTANT # # #
        # THIS SHOULD ONLY CONTAIN VARIABLE/PROPERTY INITS... any actual code (like
        # talking to another CRDS app) should be in the INIT state handler.
        # # # # # # # # # # #
        self.autocalCalDict = None
        assert isinstance(SpectrumQueue, Queue.Queue) #for Wing
        threading.Thread.__init__(self)
        self.setDaemon(1)                   # Ensures that this thread disappears when the main one does

        self.__State = STATE_INIT
        self.__LastState = self.__State

        self.Schemes = {}                   # keys = Scheme def paths; values = DasScheme instances
        self.SchemesByDasIndex = {}          # another lookup method: keys = DAS table index values = DasScheme indexes

        ##Data on the spectrum being collected at the moment...
        self.ActiveSpectrumName = ""        # what spectrum is running now (name for the scheme:subscheme pair)
        self.ActiveSchemeName = ""          # Name of the scheme file used that is generating the current spectrum
        self.ActiveSpectrum = None
        self.ActiveSpectrumID = -1
        self._FirstRdTime_s = -1
        if 0: assert isinstance(self.ActiveSpectrum, CSpectrum) #for Wing
        self._CurrentCalSpectrum = {}  #keys = scheme row index; values = CalPoint instances
        self._CurrentCalScheme = None

        self.rdCache = []
        #self.ActiveSpectrumID = -1
        self.__TimeCorrection_s = -1.       # The time offset to use for the current spectrum (to correct DAS ticks to "normal" time)
        self.__RolloverCorrection_ms = {}
        self.__LastTicks_ms = {}
        self.__TicksAtCorrectionReference_ms = -1
        self._TimeAtLastTimeSync_s = -1
        self._TimeSyncPeriod_s = 120
        self._ReSyncRequested = False
        self.TimeCheckLock = threading.RLock() #shouldn't be needed since resyncs are serialized with conversions, but doing it just in case

        self.Scanning = False               # whether a spectrum is currently being taken
        self.SweepMode = SWEEP_CONTINUOUS   # what mode is running (single, repeat, continuous) - can be two bits since customer won't see continuous
        self._UninterruptedSweepCount = 0
        self.SpectrumQueue = SpectrumQueue  # The main output queue of this class!  The meas system extracts from this.
        self._StreamDir = StreamDir
        self.UseHDF5 = UseHDF5
        self._ForcePolarLocking = ForcePolarLocking
        self._DataBuffer  = None            # Holds a spectral point if one was read "by accident" (if a stop condition was missed)
        #
        #set up the queues that will more-or-less blindly collect instrument data...
        self.RdQueue = Queue.Queue()        # Will hold tuples of the RD data
        self._LatestSensors = _SensorData() #
        self._cachedSensors = None          # Copy of _LatestSensors which is sent to fitter. This changes only
                                            #  when new sensor data arrives
        self._sensorsUpdated = True         # Flag indicating sensor data have changed
        self._SweepEnabled = threading.Event()    # Flag indicating that spectrum acquisition is expected
        self._ClearErrorEvent = threading.Event() # Flag indicating that somone requested a clear of the error state.
        self._SchemeLoaded = False          #
        self._CloseRequested = False        # Set to directly terminate the SpectrumManager thread (don't know why this would be done since daemonic, though)
        self._TriggerEnabled = False        # If we ever use measurement triggering!
        self._CmdLock = threading.Lock()
        self.TagalongData = {}             # A dictionary of (value_string, timestamp) tuples to include in the rdf

        #The listeners that will listen to RD data...
        self.RdListener = None
        self.SensorListener = None

        self._WarmboxCalFilePath = WarmboxCalFilePath
        self._FreqConverter = {}  #keys = laser index; values = AutoCal instances that do wavenumber<->polar conversion
        self._SchemeDictSetupInfo = SchemeDict
        self._DasUpdateLock = threading.Lock()
        self._Broadcaster = Broadcaster.Broadcaster(BROADCAST_PORT_RD_RECALC, name="Spectrum Manager - Correct frequency ringdowns", logFunc=Log)
        self.CalUpdatePeriod_s = CalUpdatePeriod_s
        self._LastCalUpdateTime = 0
        self.RingdownTimeout_s = RingdownTimeout_s
        self.UseOldSchemeFile = UseOldSchemeFile
        
    def run(self):
        #Grab some cal parameters...
        self.autocalCalDict = CRDS_CalMgr.Hotbox_GetAutocalCal()
        #profileThread(self._MainLoop)
        self._MainLoop()
    def _AssertValidCallingState(self, StateList):
        if self.__State not in StateList:
            raise CommandError("Command invalid in present state.")
    def _MainLoop(self):
        #When started, sit and wait until a sweep is started (which sets the
        #Enabled Event). If enabled, loop and keep assembling spectra.  When
        #disabled, drop back to as if freshly started. All other activity is
        #asynchronous and event driven.
        #ALL STATE MANAGEMENT SHOULD IDEALLY BE DONE IN THIS MAIN LOOP!!!

        stateHandler = {}
        stateHandler[STATE_INIT] = self._HandleState_INIT
        stateHandler[STATE_READY] = self._HandleState_READY
        stateHandler[STATE_SWEEPING] = self._HandleState_SWEEPING
        stateHandler[STATE_ERROR] = self._HandleState_ERROR

        try:
            while not self._CloseRequested:
                stateHandler[self.__State]()
            #end while
            self.SweepStop()
            Log("SpectrumManager thread terminated due to request", Level = 2)
        except:
            LogExc("Unhandled exception trapped by last chance handler",
                Data = dict(Source = "SpectrumManager"),
                Level = 3)
            raise
    def __SetState(self, NewState):
        """Sets the state of the SpectrumManager.  Variable init is done as appropriate."""
        if NewState == self.__State:
            return

        if __debug__: #code helper - make sure state changes are happening only from where we expect
            callerName = sys._getframe(1).f_code.co_name
            if not callerName.startswith("_HandleState_"):
                raise Exception("Code error!  State changes should only be made/managed in _MainLoop!!  Change attempt made from %s." % callerName)

        #Do any state initialization that is needed...
        if NewState == STATE_READY:
            self._DataBuffer = None
            self._FirstRdTime_s = -1
            self.ActiveSpectrumID = -1
            self.ActiveSpectrum = None
        elif NewState == STATE_SWEEPING:
            self._UninterruptedSweepCount = 0
        elif NewState == STATE_ERROR:
            self._ClearErrorEvent.clear()
            self._SweepEnabled.clear()

        #and now actually change the state variable and log the change...
        self.__LastState = self.__State
        self.__State = NewState
        eventLevel = 1
        if NewState == STATE_ERROR:
            eventLevel = 3
        Log("Substate changed",
            dict(SubSystem = "SpectrumManager",
                 State = StateName[NewState],
                 PreviousState = StateName[self.__LastState]),
            Level = eventLevel)
    def _HandleState_INIT(self):
        try:
            AssertMinDASVersions()

            ##Misc init stuff...
            self._LastCalUpdateTime = TimeStamp()

            ##Load up the frequency converters for each laser in the DAS...
            cp = CustomConfigObj(self._WarmboxCalFilePath)  
            for i in range(1, MAX_LASERS + 1): # N.B. In Autocal1, laser indices are 1 based
                ac = Autocal1.AutoCal()
                try:
                    ac.getFromIni(cp, i)
                    self._FreqConverter[i - 1] = ac
                except KeyError:
                    #No such laser
                    pass
            #endfor

            ##Load up the DAS with schemes in the managed positions...
            self._ConfigureAndUploadSchemeSet(self._SchemeDictSetupInfo, self.UseOldSchemeFile)

            ##Get some starting values from the DAS and get in a known state...
            CRDS_Driver.SpectCntrl_StopScan()
            self.__SetState(STATE_READY)
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            self.__SetState(STATE_ERROR)
    def _HandleState_READY(self):
        self._SweepEnabled.wait(0.05) #used instead of simple SWEEPING state check to avoid cpu spin
        if self._SweepEnabled.isSet():
            self.__SetState(STATE_SWEEPING)
        else:
            #leave it in READY state...
            self.__SetState(STATE_READY)
    def _HandleState_SWEEPING(self):
        exitState = -2
        try: #catch unhandled exceptions for trapping to ERROR state
            try: #try the actual state handling and handle known exceptions
                if self._UninterruptedSweepCount == 0:
                    self._InitSweep()
                #Re-sync the time reference if enough time has elapsed...
                if self._ReSyncRequested or ((TimeStamp() - self._TimeAtLastTimeSync_s) > self._TimeSyncPeriod_s):
                    self._ReSyncRequested = False
                    self._GetTimeReference(TICKREF_LIST)
                self._CollectSpectrum()
                self._UninterruptedSweepCount += 1
                if self.SweepMode == SWEEP_SINGLE:
                    self.SweepStop()
                    exitState = STATE_READY
                else:
                    #leave in the same state...
                    exitState = STATE_SWEEPING
            except SweepAborted:
                #the location that this exception was raised should have cleaned up, so
                #all that we should need to do is switch the state...
                exitState = STATE_READY
            except RingdownTimeout:
                LogExc("Timed out while waiting for expected ringdown.")
                exitState = STATE_ERROR
            except FirstPointTimeout:
                LogExc("Timed out while waiting for the first ringdown in the spectrum.")
                exitState = STATE_ERROR
            #endtry
        except:
            #all unexpected exceptions also result in the ERROR state
            LogExc("Unhandled exception occurred.", dict(State = StateName[self.__State]))
            exitState = STATE_ERROR
        #endtry
        if exitState == -2:
            raise Exception("HandleState_ENABLED has a code error - the exitState has not been specified!!")
        if exitState != STATE_SWEEPING:
            self.RdListener.stop()
            self.SensorListener.stop()
            self.RdListener = None
            self.SensorListener = None
            if __debug__ and DEBUG_VERBOSITY >=2: Log("STREAM LISTENERS SET TO NONE AND SOCKETS CLOSED", Level = 0)
        self.__SetState(exitState)
    def _HandleState_ERROR(self):
        """
        Description:

        On Entry:

        Possible Exit States:

        """
        self._ClearErrorEvent.wait(0.05)
        if self._ClearErrorEvent.isSet():
            self.__SetState(STATE_INIT)
    def GetState(self):
        """Returns the current state # of the SpectrumManager."""
        return self.__State
    def GetStateName(self):
        """Returns the current state name of the SpectrumManager."""
        return StateName[self.__State]
    def _GetTimeReference(self, RefList):
        """Gets the time correction to use when interpreting RingDown time data.

        All conversions require a reference name to work with and RefList is a
        list of these names.

        CorrectTime = (RingDownTime + RolloverCorrections) + self.__TimeCorrection_s
        """
        self.TimeCheckLock.acquire()
        try:
            maxWaitTime_s = 2
            maxTimeOffset_s = 0.2
            tooLong = True

            startTime = TimeStamp()
            while (TimeStamp() - startTime) < maxWaitTime_s:
                localTime_s = time.time() #in seconds-since-epoch
                askTime_s = TimeStamp() #local high resolution ticks (in seconds)
                readTicks_ms = CRDS_Driver.DAS_GetTicks()
                readDuration_s = TimeStamp() - askTime_s
                if readDuration_s <= (2 * maxTimeOffset_s):
                    #We got a nice and short delay we can use...
                    tooLong = False
                    break
            if tooLong:
                #Couldn't get a short propagation delay?! We will use it anyway, but log
                #an event to capture the weirdness
                Log("Unable to achieve a short propagation timing error in GetTimeReference",
                    dict(ReadDuration_s = readDuration_s, MaxWaitTime_s = maxWaitTime_s),
                    Level = 2)
            if len(self.__LastTicks_ms) == 0:
                #first time through...
                for ref in RefList:
                    self.__LastTicks_ms[ref] = readTicks_ms
                    self.__RolloverCorrection_ms[ref] = 0L
            #See if our check was just after a rollover (in which case, RD entries to-be-read would
            #have rollover issues if we did nothing...
            for ref in RefList:
                if readTicks_ms < self.__LastTicks_ms[ref]:
                    #Very unlikely timing!  A rollover exactly when we re-referenced...
                    # - set it so that the rollover detection at conversion is offset correctly
                    #   - the correction offset is now based near 0 ticks, but we'll still be
                    #     getting ticks from the DAS up near 2**32
                    # - don't mess with LastTicks since ringdowns will be getting pulled out of
                    #   history with times in the past and we can't correct them yet.  They will
                    #   correct themselves as they arrive.
                    self.__RolloverCorrection_ms[ref] = -(2**32)

            #Figure out or reference time, assuming that the propagation time to the
            #DAS was half the read duration...
            self.__TicksAtCorrectionReference_ms = readTicks_ms - long(1000.*readDuration_s/2.)
            self.__TimeCorrection_s = localTime_s - float(0.001*self.__TicksAtCorrectionReference_ms)
            self._TimeAtLastTimeSync_s = askTime_s
            if __debug__: print "Time correction = %s" % self.__TimeCorrection_s
        finally:
            self.TimeCheckLock.release()
        return self.__TimeCorrection_s
    def _DasTicks2LocalTime(self, DasTicks_ms, RefName):
        """Converts DAS tick counter results into local time in seconds-since-epoch.

        Refname is an identifier for which tick reference and correction to use.
        This is in order to avoid the potential problem of out-of-order time
        correction requests coming from different sources in this program (since
        "old" time stamps could potentially be retrieved from the DAS when pulling
        from an old queue or something).

        Note that all RefNames share the same time correction reference.

        This routine is needed, because although the pc's local time is the
        absolute time base to report with, the actual timer used to indicate what
        time a particular measurement was taken uses the DAS ticks.

        """
        self.TimeCheckLock.acquire()
        try:
            if self._TimeAtLastTimeSync_s < 0:
                raise Exception("_DasTicks2LocalTime called without a previous call to _GetTimeReference")
            if DasTicks_ms < self.__LastTicks_ms[RefName]:
                #We have a rollover!
                self.__RolloverCorrection_ms[RefName] += 2**32
            localTime = (0.001 * (DasTicks_ms + self.__RolloverCorrection_ms[RefName])) + self.__TimeCorrection_s
            self.__LastTicks_ms[RefName] = DasTicks_ms
            #print "** time error = %.3f" % (localTime - time.time())
        finally:
            self.TimeCheckLock.release()
        return localTime
    def SyncToPcClock(self):
        """Re-synchronizes the ringdown data collection timing to the PC clock.

        Call this function when the pc clock is adjusted.

        This re-synchronization is done periodically by the system as specified by
        the value of self._TimeSyncPeriod_s (currently hard-coded to 120 s).

        """
        self._ReSyncRequested = True
        return "OK"
    def SweepStart(self):
        """Starts a sweep (or sweeps, if in continuous mode)."""
        self._CmdLock.acquire()
        try: #for CmdLock release
            try: #catch for DAS errors (and any other remote procedure call error)...
                ##Validate that the call is possible and/or makes sense...
                self._AssertValidCallingState([STATE_SWEEPING, STATE_READY, STATE_INIT]) #INIT allowed to start immediately when done
                if not self._SchemeLoaded:
                    Log("SweepStart attempted with no scheme load", Level = 0)
                    raise CommandError("No scheme(s) loaded yet.")
                ##React to the call...
                if self.__State == STATE_SWEEPING:
                    return #we are already sweeping
                else:
                    #Now to set the sweep enabled event which will get us out of ready state...
                    self._SweepEnabled.set()
                    if __debug__: Log("SpectrumManager sweep started with SweepStart()", Level = 0)
            except CommandError:
                if __debug__: LogExc("Command error", dict(State = StateName[self.__State]), Level = 0)
                raise
            except:
                LogExc("Unhandled exception in command call", Data = dict(Command = NameOfThisCall()))
                raise
        finally:
            self._CmdLock.release()
    def SweepStop(self):
        """Stops any DAS wavelength sweeping in progress."""
        self._CmdLock.acquire()
        try: #for CmdLock release
            try: #catch for DAS errors (and any other remote procedure call error)...
                if not self._SweepEnabled.isSet():
                    return
                self._SweepEnabled.clear()
                if __debug__: Log("SpectrumManager sweep stopped with SweepStop()", Level = 0)
            except:
                LogExc("Unhandled exception in command call", Data = dict(Command = NameOfThisCall()))
                raise
        finally:
            self._CmdLock.release()
    def _InitSweep(self):
        """"""
        ##Make sure the DAS is in the initial state we expect...
        #It should not be collecting at this point in time...
        CRDS_Driver.SpectCntrl_StopScan()
        #It should be configured to repeat or not as specified...
        if self.SweepMode == SWEEP_CONTINUOUS:
            CRDS_Driver.SpectCntrl_SetRepeatingScan()
        elif self.SweepMode == SWEEP_SINGLE:
            CRDS_Driver.SpectCntrl_SetSingleScan()

        #Get the time reference to use for the sweep...
        # - must be done before ringdowns arrive
        self._GetTimeReference(TICKREF_LIST)

        ##Set up to listen to the data we want...
        rdElementType = HostRdResultsType
        #Clear the collection queues (note that RdQueue.queue.clear() is not thread-safe, but may be fine)...
        self.RdQueue = Queue.Queue()
        #Now create the "filters" that will do most of the collection magic.
        #These listen to the ringdown and sensor streams and collect the data as
        #needed into queues that can be read when ready (in our case, in the
        #main SpectrumManager thread's run routine)...
        self.RdListener = Listener.Listener(self.RdQueue,
                                            BROADCAST_PORT_RDRESULTS,
                                            rdElementType,
                                            self._RingdownFilter,
                                            retry = True,
                                            name = "Spectrum manager ringdown results listener",logFunc = Log)

        self.SensorListener = Listener.Listener(None, # no queuing, we'll just be tracking the latest
                                                BROADCAST_PORT_SENSORSTREAM,
                                                ss.STREAM_ElementType,
                                                self._SensorFilter,
                                                retry = True,
                                                name = "Spectrum manager sensor stream listener",logFunc = Log)

        #Now kick the DAS into measuring (which means ringdowns should start
        #getting broadcasted by the Driver)...
        CRDS_Driver.SpectCntrl_StartScan()
        if __debug__: Log("SpectrumManager sweep started", Level = 0)
    def SetSchemeSequence(self, SchemeSequence, Restart = True):
        """Tells the DAS what scheme sequence that should be run.

        SchemeSequence is a list of scheme names.  eg: ["NH3", "NH3", "H2O"]

        """
        indexList = [self.Schemes[s]._CurrentIndex for s in SchemeSequence]
        loopSequence = False
        if self.SweepMode == SWEEP_CONTINUOUS:
            loopSequence = True
        try:
            CRDS_Driver.wrSchemeSequence(indexList, Restart, loopSequence)
        except:
            LogExc(Data = dict(State = StateName[self.__State]))
            #let the caller (MeasSystem) deal with it.  If it screws the SpectrumManager, we'll know.
    def _ConfigureAndUploadSchemeSet(self, SchemeSet, UseOldSchemeFile):
        """Configures and uploads the scheme set, including primary/alternate settings.

        SchemeSet must be a dictionary of tuples, where:
          - dict keys are the names to refer to the scheme
          - values are three-tuples of (scheme_path, primary_das_index, alt_das_index)
          - if alt_das_index < 0, the scheme has no alternate

        """
        assert self._FreqConverter, "debug assert - self.FreqConverter dict must be created by now."
        Log("Starting upload of all required DAS schemes")
        for k in SchemeSet.keys():
            (schemePath, indexA, indexB) = SchemeSet[k]
            self.Schemes[k] = DasScheme(k, indexA, indexB, self._ForcePolarLocking, self._FreqConverter)
            assert isinstance(self.Schemes[k], DasScheme) #for Wing
            if (indexA in self.SchemesByDasIndex.keys()) or (indexB in self.SchemesByDasIndex.keys()):
                raise SpectrumManagerErr("Scheme index already used in SchemesByDasIndex")
            self.Schemes[k].Initialize(InitialSchemePath = schemePath, UseOldSchemeFile = UseOldSchemeFile)
            self.SchemesByDasIndex[indexA] = self.Schemes[k]
            self.SchemesByDasIndex[indexB] = self.Schemes[k]

        Log("Completed upload of all required DAS schemes")
        self._SchemeLoaded = True
    def _RecalculateAndUploadAllSchemes(self):
        if self._DasUpdateLock.locked():
            if __debug__: Log("Scheme update attempted before another one finished!", Level = 2)
            #Used to let it queue up (with the lock)... now just returning.
            return #don't let it pile up... we'll update next time around.
        self._DasUpdateLock.acquire() #don't want to have a slow update cause a collision...
        try:
            newScheme = {}
            if __debug__: Log("Starting calculation of new schemes", Level = 0)
            for scheme in self.Schemes.values():
                assert isinstance(scheme, DasScheme)
                startTime = TimeStamp()
                if __debug__: Log("Freq conversion started", dict(SchemeFile = scheme._OriginalSchemeFileName), Level = 0)
                midRowDelay_s = 0.001 #Want to slow down the calculation so regular operations can proceed while converting
                newScheme[scheme] = scheme.ConvertFrequencySchemeToAngle(scheme._OriginalScheme, midRowDelay_s)
                if __debug__: Log("Freq conversion completed", dict(ElapsedTime_s = (TimeStamp() - startTime)), Level = 0)
            if __debug__: Log("Starting upload/swap of newly calculated schemes", Level = 0)
            for scheme in self.Schemes.values():
                scheme.UpdateScheme(newScheme[scheme])

            #See if we should be updating the non-volatile cal version...
            # - doing this in this function since it is on a parallel thread
            timeSinceLastCal = TimeStamp() - self._LastCalUpdateTime
            if (self.CalUpdatePeriod_s > 0) and (timeSinceLastCal > self.CalUpdatePeriod_s):
                filePath = os.path.join(self._StreamDir, "TempWlmCal.ini")
                #Now for (yet another) hack... the autocal putToIni does not include
                #old calibration stuff so we need to start from this file. Don't want
                #to mess up the cal manager version (or its cheksum integrity
                #checking) so we'll make a copy... not very efficient, but works for
                #now)...
                self.__Hack_CopyActiveWarmboxCal(filePath)
                cp = CustomConfigObj(filePath)
                for laserIndex in self._FreqConverter.keys():
                    fc = self._FreqConverter[laserIndex]
                    fc.putToIni(cp, laserIndex+1) # Note: In Autocal1, laser indices are 1 based
                try:
                    fp = file(filePath, "wb")
                    cp.write(fp)
                finally:
                    fp.close()
                CRDS_CalMgr.Warmbox_CopyOverCalFile(filePath)
                self._LastCalUpdateTime = TimeStamp()
            #endif (update cal file)
            if __debug__: Log("WLM calibration and schemes updated.", Level = 0)
        finally:
            self._DasUpdateLock.release()
    def SetTagalongData(self, Name, Value):
        """Sets RDF tagalong data (and timestamp) with the given token Name."""
        self.TagalongData[Name] = (Value, time.time())
    def GetTagalongData(self, Name):
        """Returns a [DataValue, DataTime] array for the specified token Name.

        If no data for the given name, an empty array [] is returned.

        """
        try:
            dataValue, dataTime = self.TagalongData[Name]
            return [dataValue, dataTime]
        except KeyError:
            return []
    def DeleteTagalongData(self, Name):
        """Deletes the RDF tagalong data with the specified token Name.

        On success, returns the [DataValue, DataTime] that was last recorded.
        On failure (no data with Name), an empty array [] is returned.

        """
        return list(self.TagalongData.pop(Name, []))

    def _GetControlData(self):
        return {"RdQueueSize":self.RdQueue.qsize(), "SpectrumQueueSize":self.SpectrumQueue.qsize()}

    def _batchConvert(self):
        """Convert WLM angles and laser temperatures to wavenumbers in a vectorized way, using
        thetaCalAndLaserTemp2WaveNumber"""

        if self.rdCache:
            raise RuntimeError("_batchConvert called while cache is not empty")
        thetaCal = []
        laserTemp = []
        cacheIndex = []
        for laserIndex in range(MAX_LASERS):
            thetaCal.append([])
            laserTemp.append([])
            cacheIndex.append([])
        # Get data from the queue into the cache
        index = 0
        while not self.RdQueue.empty():
            try:
                rdData,sensorData,dasScheme = self.RdQueue.get(False)
                self.rdCache.append((rdData,sensorData,dasScheme))
                if dasScheme._LockerMode == LOCKER_MODE_ANGLE:
                    laserIndex = rdData.laserSelect
                    thetaCal[laserIndex].append(rdData.thetaCal)
                    laserTemp[laserIndex].append(rdData.laserTemp)
                    cacheIndex[laserIndex].append(index)
                index += 1
            except Queue.Empty:
                break
        # Do the angle to wavenumber conversions for each laser
        for laserIndex in range(MAX_LASERS):
            if cacheIndex[laserIndex]: # There are angles to convert for this laser
                fc = self._FreqConverter[laserIndex]
                waveNo = fc.thetaCalAndLaserTemp2WaveNumber(numpy.array(thetaCal[laserIndex]), numpy.array(laserTemp[laserIndex]))
                for i,w in enumerate(waveNo):
                    index = cacheIndex[laserIndex][i]
                    rdData = self.rdCache[index][0]
                    dasScheme = self.rdCache[index][2]
                    rdData.wavenum = int(100000.0 * w)
                    try:
                        rdData.wavenumSetpoint = dasScheme._OriginalScheme.schemeEntry[rdData.schemeRow].setpoint.asUint32
                    except Exception, e:
                        rdData.wavenumSetpoint = 0
                        print "ERROR: Scheme number: %d, row: %d, exception: %s" % (rdData.schemeTableIndex,rdData.schemeRow,e)

    def _GetRingdownData(self,timeout):
        """Calls batchConvert to get ringdown data from self.RdQueue, having converted WLM angles to
        wavenumbers if necessary. For efficiency, the conversions are batched, vectorized and cached
        in the FIFO self.rdCache. If the cache is non-empty, immediately return data from it. Otherwise,
        check RdQueue to see if there are already enough data to make it worth doing a batch conversion.
        If the amount of data are insufficient, wait for the timeout duration (for more data to accumulate)
        and then do the conversion. Raises Queue.Empty if no data are available."""

        MIN_SIZE = 50
        if not self.rdCache: # i.e. cache is Empty
            if self.RdQueue.qsize() < MIN_SIZE:
                time.sleep(timeout)
            self._batchConvert()
            if not self.rdCache:
                raise Queue.Empty
        return self.rdCache.pop(0)

    def _GetSpectralDataPoint(self):
        """Pops (rdData, sensorData) out of the local ringdown queue and returns it.

        If the data is in polar coords and should be in frequency, the conversion
        is done automatically.

        Raises RingdownTimeout if no data after self.RingdownTimeout_s.

        Raises SweepAborted if the SpectrumManager is stopped for some
        reason (eg: SweepStop, Close) while waiting for data.

        """
        if self._DataBuffer:
            #The last time a spectrum was read it read one too many points, and this is it.
            rdData, sensorData = self._DataBuffer
            self._DataBuffer = None
        else:
            startTime_s = TimeStamp()
            rdData = None
            while not rdData:
                try:
                    # rdData, sensorData = self.RdQueue.get(timeout = 0.05)
                    rdData, sensorData, dasScheme = self._GetRingdownData(timeout = 0.5)
                    if 0: assert isinstance(rdData, ___RDResults)
                    bcObj = ObjAsString(rdData)
                    printTrail("Broadcasting processed ringdowns")
                    self._Broadcaster.send(bcObj)
                    #::: START DEBUG STUFF :::#
                    # fields = ["%-20s = %s" % (k, getattr(rdData, k)) for k in dir(rdData) if not k.startswith("_")]
                    #from pprint import pprint
                    #pprint(fields)
                    #::: END DEBUG STUFF :::#
                except Queue.Empty:
                    if (self.RingdownTimeout_s != 0) and ((TimeStamp() - startTime_s) > self.RingdownTimeout_s):
                        #RingdownTimeout_s = 0 means no time-out requirement is given
                        CRDS_Driver.SpectCntrl_StopScan()
                        self._SweepEnabled.clear()
                        raise RingdownTimeout("Timeout elapsed with no data in RD queue")
                #There may or may not be data at this point...
                if (not self._SweepEnabled.isSet()) or self._CloseRequested:
                    CRDS_Driver.SpectCntrl_StopScan()
                    raise SweepAborted("Aborted while trying to pull from the local ringdown queue.")
            #endwhile (not rdData)
        #endif (self._DataBuffer)
        return (rdData, sensorData)

    def __TunerCenter(self, tunerCenter):
        """This only exists for the sake of being callable by a thread (RPC calls cannot
        be called by a thread)."""
        CRDS_CalMgr.RecenterTuner(tunerCenter)

    def _ProcessCalSpectrum(self):
        """hmm"""
        # - want to calculate new polar<-> waveno coefficients to use live
        # - want to calculate new polar schemes for the current mode
        # - want to upload new schemes to the DAS
        # - want to modify non-volatile (file) coefficients (occasionally)

        startTime = TimeStamp()
        if __debug__: Log("Starting _ProcessCalSpectrum")

        #Grab some cal parameters...
        d = self._CurrentCalSpectrum #character saver (and to be easily compatible with Sze's old code)
        pi = numpy.pi #shortcut
        # d is the dictionary of data gleaned from the calibration rows
        if len(d) < self.autocalCalDict["min_calrows"]:
            return
        for b in d.values():
            # Find median WLM angles (N.B. Must deal with sine and cosine parts separately!),
            #  tuner voltages and laser temperatures
            b.thetaCalMed = numpy.arctan2(numpy.median(b.thetaCalSin),numpy.median(b.thetaCalCos))
            b.tunerMed = numpy.median(b.tunerVals)
            b.laserTempMed = numpy.median(b.laserTempVals)

        # Process the data one laser at a time
        calDone = False
        for laserIndex in self._FreqConverter.keys():
            if __debug__: print "CALCULATING NEW COEFFS FOR LASER INDEX %d" % laserIndex
            fc = self._FreqConverter[laserIndex]
            assert isinstance(fc, Autocal1.AutoCal)
            # Put the data into lists or arrays. Lists are needed for passing via RPC calls while arrays are
            #  more useful for mathematical operations.
            rows = [k for k in d.keys() if d[k].LaserIndex == laserIndex] #rows is now a list of row indices
            laserTemp = [d[k].laserTempMed for k in rows] #laserTemp is now a list of laserTemps matching the rows list
            laserTemp = numpy.array(laserTemp) #convert to numpy array which will actually be used for calcs
            if len(laserTemp) > 0:
                thetaCal  = numpy.array([d[k].thetaCalMed for k in rows], dtype = 'd')
                thetaHat = fc.laserTemp2ThetaCal(laserTemp)
                # Use the laser temperature to find correct revolution for WLM polar angle
                thetaCal += 2*pi*numpy.floor((thetaHat-thetaCal)/(2*pi)+0.5)
                tuner = numpy.array([d[k].tunerMed  for k in rows], dtype = 'd')
                jump = numpy.abs(numpy.diff(tuner)).max()
                if jump > self.autocalCalDict["max_jump"]:
                    Log("Calibration not done, maximum tuner jump between calibration rows: %.1f" % (jump, ))
                    continue
                indices = numpy.array(rows, dtype = 'l')
                count = numpy.array([d[k].Count for k in rows], dtype = 'l')
                tunerMean = float(numpy.sum(tuner*count) / numpy.sum(count))
                tunerDev = tuner - tunerMean
                # Use the median to center tuner for robustness
                tunerCenter = float(medianHist(tuner,count,useAverage=False))
                if __debug__:
                    Log("Standard deviation of tuner: %.1f" % (numpy.std(tunerDev), ))
                print "Standard deviation of tuner: %.1f" % (numpy.std(tunerDev) ,)
                # Center the tuner ramp waveform about the median tuner voltage at the calibration rows
                # - this can get stuck behind scheme uplaods due to Driver command
                #   serialization.  Since we don't care exactly when it happens, we'll split
                #   off a thread to do this...
                tunerCenteringThread = threading.Thread(target = self.__TunerCenter, args = (tunerCenter, ))
                tunerCenteringThread.setDaemon(1)
                tunerCenteringThread.start()

                # Calculate the shifted WLM angles which correspond to exact FSR separation
                #  The adjust_factor is an underestimate of the WLM angle shift corresponding to a digitizer
                #  unit of tuner. This provides a degree of under-relaxation and filtering.
                # print thetaCal
                thetaShifted = thetaCal - (self.autocalCalDict["adjust_factor"] * tunerDev)
                # Now use the information in scheme for updating the calibration
                perm = thetaShifted.argsort()
                thetaShifted = thetaShifted[perm]
                dtheta = numpy.diff(thetaShifted)
                # Ensure that the WLM angles are close to multiples of the FSR before we do calibration.
                #  This prevents calibrations from occurring if the pressure is changing, etc.
                m = numpy.round_(dtheta / self.autocalCalDict["approx_wlm_angle_per_fsr"])
                anglePerFsr = numpy.mean(dtheta[m == 1])
                m = numpy.round_(dtheta/anglePerFsr)
                offGrid = numpy.max(numpy.abs(dtheta/anglePerFsr - m))
                if offGrid > self.autocalCalDict["max_offgrid"]:
                    Log("Calibration not done, offGrid parameter = %.2f" % (offGrid,))
                else:
                    if __debug__: Log("Updating WLM Calibration for laser", dict(LaserNum = laserIndex))
                    #Update the live copy of the polar<->freq coefficients...
                    waveNums = range(len(rows)) #pre-allocate space
                    i = 0
                    assert isinstance(self._CurrentCalScheme, DasScheme) #for wing
                    for calRowIndex in rows:
                        waveNums[i] = float(self._CurrentCalScheme._OriginalScheme.schemeEntry[calRowIndex].setpoint.asUint32)/100000.0
                        i += 1
                    waveNums = numpy.array(waveNums, dtype = 'd')
                    waveNums = waveNums[perm] #sorts in the same way that thetaShifted was
                    #Calculate number of calibration points at each FSR, so they may be weighted properly
                    weights = calcWeights(numpy.cumsum(numpy.concatenate(([0],m))))
                    #Now do the actual updating of the local (RAM copy) conversion coefficients...
                    fc.updateWlmCal(thetaShifted, waveNums, weights, self.autocalCalDict["relax"], True, self.autocalCalDict["relax_default"], self.autocalCalDict["relax_zero"])
                    calDone = True
                #endif (offgrid)
            #endif (len laserTemp > 0)
        #endfor (looping through laser indices)
        #Now upgrade the angle based schemes loaded into the DAS...
        if calDone:
            #Upgrade *all* schemes, not just those for the current mode (or active
            #scheme sequence). Faster would be to only upgrade what is active, but
            #then you can't switch modes instantly. Sticking with the easier code
            #implementation right now...
            #Launch it on a thread so we don't stop any collection activitity
            # - would ideally leave this to the cal manager, but all the info is
            #   local... maybe best tp bring the cal manager into this process later
            #self._RecalculateAndUploadAllSchemes()
            updateThread = threading.Thread(target = self._RecalculateAndUploadAllSchemes)
            updateThread.setDaemon(1)
            updateThread.start()
            pass
        if __debug__: Log("_ProcessCalSpectrum complete!", dict(ElapsedTime_s = (TimeStamp() - startTime)))

    def __Hack_CopyActiveWarmboxCal(self, DestPath):
        """Copies the current warmbox cal to the destination minus the checksum stuff."""
        oldFilePath = CRDS_CalMgr.GetWarmboxCalPath()
        try:
            fsrc = file(oldFilePath, "r")
            fdst = file(DestPath, "w")
            lastLine = ""
            checksumFound = False
            while True:
                line = fsrc.readline()
                if line == "": break
                if line[:10] == "#checksum=":
                    checksumFound = True
                    break
                if lastLine: #don't want the \n prior to the checksum line, so we lag by one
                    fdst.write(lastLine)
                lastLine = line
            if not checksumFound:
                Log("No checksum found in active warmbox cal file", Level = 2)

        finally:
            if fsrc: fsrc.close()
            if fdst: fdst.close()
    def _CollectSpectrum(self):
        """Starts the collection of spectra according to whatever the DAS is configured to collect.

        This collects a single spectrum and returns, placing the spectrum into self.SpectrumQueue.

        """
        #This code could use a cleanup!  Too many nested ifs in the giant while loop!
        firstPointFound = False
        firstPointErrReported = False
        closeSpectrumWhenDone = False
        lastCount = -1
        lastSubSchemeID = -1
        loopCount = -1

        #Initialize the storage of the spectrum...
        spectrum = None

        while not self._CloseRequested:
            loopCount += 1
            #Pull a spectral point from the RD queue...
            rdData = None
            try:
                rdData, sensorData = self._GetSpectralDataPoint()
            except SweepAborted:
                raise
            except RingdownTimeout:
                raise
            if 0: assert isinstance(rdData, ___RDResults) # for Wing

            thisSchemeTableIndex = rdData.schemeTableIndex
            thisSubSchemeID = rdData.subSchemeId #bad name - this is the spectrum ID plus carry-through bits + inc indicator in msb
            thisSpectrumID = rdData.subSchemeId & SPECTRUM_ID_MASK
            thisCount = rdData.count
            schemeStatus = rdData.schemeStatus
            localRdTime_s = self._DasTicks2LocalTime(rdData.msTicks, TICKREF_SPECTRUM)
            errDataDict = dict(Spectrum = self.ActiveSpectrumName,
                               SchemeTableIndex = thisSchemeTableIndex,
                               SchemeRow = rdData.schemeRow,
                               SSID = thisSubSchemeID,
                               SpectrumID = thisSpectrumID,
                               Count = thisCount,
                               SchemeStatus = schemeStatus)
                               
            if __debug__ and DEBUG_VERBOSITY >= 3: Log("Data collected!", errDataDict, Level = 0)

            #if __debug__: print "%4d %3d ssid=0x%04x  %d %5d fs=%6d wn=%4.0f ab=%5.5f pzt=%5.0f" % (loopCount, rdData.schemeRow, thisSubSchemeID, thisCount, self.RdQueue.qsize(), rdData.fitStatus, rdData.wavenum, rdData.uncorrectedAbsorbance, rdData.pztOffset)

            #Figure out if we finished a scheme and whether we should process a cal spectrum...
            if (rdData.schemeStatus & ss.SchemeCompleteSingleModeBitMask) or \
               (rdData.schemeStatus & ss.SchemeCompleteRepeatModeMask):
                #if rdData.schemeRow == 0 and (len(self._CurrentCalSpectrum) > 0):
                #We just popped out the last point in a scheme (including scheme repeats)
                if len(self._CurrentCalSpectrum) > 0:
                    if self._ForcePolarLocking:
                        self._ProcessCalSpectrum()
                    self._CurrentCalSpectrum = {}
                    self._CurrentCalScheme = None
            # Append to the spectrum if this is a cal point...
            if (rdData.subSchemeId & SPECTRUM_ISCAL_MASK) and self._ForcePolarLocking:
                rowNum = rdData.schemeRow
                targettingError = 1e-5*(rdData.wavenum - rdData.wavenumSetpoint)
                if abs(targettingError) < self.autocalCalDict["max_targetting_error"]:
                    if rowNum not in self._CurrentCalSpectrum.keys():
                        self._CurrentCalSpectrum[rowNum] = CalPoint()
                        self._CurrentCalScheme = self.SchemesByDasIndex[rdData.schemeTableIndex]
                    assert isinstance(self._CurrentCalSpectrum[rowNum], CalPoint)
                    self._CurrentCalSpectrum[rowNum].Count += 1
                    self._CurrentCalSpectrum[rowNum].thetaCalCos.append(math.cos(rdData.thetaCal))
                    self._CurrentCalSpectrum[rowNum].thetaCalSin.append(math.sin(rdData.thetaCal))
                    self._CurrentCalSpectrum[rowNum].laserTempVals.append(rdData.laserTemp)
                    self._CurrentCalSpectrum[rowNum].tunerVals.append(rdData.tunerValue)
                    self._CurrentCalSpectrum[rowNum].LaserIndex = rdData.laserSelect
            #endif (Cal point)

            #Figure out if we are dealing with the first or last point in a spectrum...
            isFirstPoint = isLastPoint = False          
            if (thisSubSchemeID & SPECTRUM_FIRST_MASK):
                # For QuickSilver, we get several ringdowns, even with a dwell of 1, so ignore
                #  any subsequent ringdowns with the first point mask set
                # if firstPointFound: continue
                print "This subscheme ID: %x, firstPointFound: %d" % (thisSubSchemeID, firstPointFound)
                if __debug__:
                    if DEBUG_VERBOSITY >= 2:
                        Log("SPECTRUM_FIRST_MASK found on ringdown", errDataDict, Level = 0)
                    if firstPointFound:
                        #already found it!  Why did we get again?  Either we're on a new spectrum (handled further down) or
                        #something is pretty messed up!
                        if thisCount == lastCount:
                            Log("Two starting points found in the same spectrum?!", Level = 0)
                        else:
                            Log("Got the first point in a spectrum with a different count!", Level = 0)
                    #endif (firstPointFound)
                #endif (__debug__)
                isFirstPoint = True
                self._FirstRdTime_s = localRdTime_s
                firstPointFound = True
                lastCount = thisCount #to avoid a false error detection later
                self.ActiveSpectrumID = thisSpectrumID
            #endif (SPECTRUM_FIRST_MASK)
            if (thisSubSchemeID & SPECTRUM_LAST_MASK):
                if __debug__ and DEBUG_VERBOSITY >= 2: 
                    Log("SPECTRUM_LAST_MASK found on ringdown", errDataDict, Level = 0)
                #Single point spectra are allowed so it can be first AND last (ie: not an elif)
                isLastPoint = True
                if firstPointFound:
                    closeSpectrumWhenDone = True
                #else:
                #    For QuickSilver, we get several ringdowns, even with a dwell of 1, so ignore
                #    any ringdowns with the last point mask set if there has been no first point
                #    continue
            if firstPointFound:
                if thisCount == lastCount: #still collecting the same spectrum (normal)
                    if not spectrum:
                        spectrum = CSpectrum(thisSpectrumID, self._FirstRdTime_s, self.TagalongData, thisSchemeTableIndex, self._StreamDir, self.UseHDF5)
                        self.ActiveSpectrum = spectrum
                    #All is good and we are collecting a spectrum
                    assert sensorData == None or isinstance(sensorData, _SensorData) #for Wing
                    relativeRdTime_s = localRdTime_s - self._FirstRdTime_s
                    if not (thisSubSchemeID & SPECTRUM_IGNORE_MASK):
                        #:::: ACTUALLY ADD THE POINT TO THE SPECTRUM HERE ::::
                        #:::: ACTUALLY ADD THE POINT TO THE SPECTRUM HERE ::::
                        spectrum.AppendPoint(rdData, sensorData, relativeRdTime_s)
                        #:::: ACTUALLY ADD THE POINT TO THE SPECTRUM HERE ::::
                        #:::: ACTUALLY ADD THE POINT TO THE SPECTRUM HERE ::::
                else: #thisCount != lastCount
                    #We have somehow missed data and "this" RD is in a new spectrum (and thus
                    #the last RD was the last in the spectrum)...
                    Log("Unexpected ringdown collected - On new spectrum without previous termination.",
                        Data = errDataDict,
                        Level = 2)
                    #Set aside the point we just read for the next time a spectrum is collected...
                    self._DataBuffer = (rdData, sensorData)
                    #still going to keep what we HAVE collected, so...
                    closeSpectrumWhenDone = True
                #endif (thiscount == lastCount)
            else: #ie: not firstPointFound
                #We have somehow managed to get a RD without it being the first point
                if not firstPointErrReported:
                    firstPointErrStart = TimeStamp()
                    Log("Unexpected ringdown collected - First point not found yet.",
                        Data = errDataDict,
                        Level = 1)
                    firstPointErrReported = True
                else:
                    firstPointWaitTime_s = TimeStamp() - firstPointErrStart
                    if (self.RingdownTimeout_s != 0) and (firstPointWaitTime_s > 10 * self.RingdownTimeout_s): 
                        #10x is a bit arbitrary but ok since it shouldn't happen
                        #RingdownTimeout_s = 0 means no time-out requirement is given
                        msg = "Timeout elapsed without locating first point in spectrum."
                        Log(msg, errDataDict.update(WaitTime_s = firstPointWaitTime_s), Level = 2)
                        self._SweepEnabled.clear()
                        raise FirstPointTimeout(msg)
            #endif (firstPointFound)

            if closeSpectrumWhenDone:
                spectrum.Finish(self._GetControlData())
                # DEBUG: Print out time delay between when data are collected and placed on SpectrumQueue
                # DEBUG: Print out length of SpectrumQueue
                if __debug__:
                    print "Spectrum queue put. Delay: %.3f, QSize: %d, Pressure: %.2f" % (time.time()-spectrum._FirstRdTime_s,self.SpectrumQueue.qsize(),spectrum._RdfDict["sensorData"]["Cavity_P_Torr"])
                self.SpectrumQueue.put(spectrum)
                if __debug__: print "Spectrum finished - %d:%s; Count = %s; schemeTableIndex = %d" % (spectrum.SpectrumID, spectrum.Name, spectrum.NumPts, rdData.schemeTableIndex)
                #if __debug__: Log("Spectrum finished - %d:%s; Count = %s; schemeTableIndex = %d" % (spectrum.SpectrumID, spectrum.Name, spectrum.NumPts, rdData.schemeTableIndex), Level = 0)
                break #we are done
            #endif (closeSpectrumWhenDone)
            lastCount = thisCount
            lastSubSchemeID = thisSubSchemeID
        #endwhile (not self._CloseRequested)
        #We are not assembling a spectrum anymore
    def Close(self):
        """Closes the spectrum manager.  This stops the main SpectrumManager thread.

        No sweeping is possible after this is done. A new SpectrumManager would
        need to be created.
        """
        self._CloseRequested = True
        Log("SpectrumManager sweep stopped with Close() call.")
    def _SensorFilter(self, entry):
        """Updates the latest sensor readings.

        This is executed for every sensor value picked up from the sensor stream
        broadcast.

        """
        if 0: assert isinstance(entry, ss.STREAM_ElementType) #for Wing
        streamTime  = entry.ticks/1000.
        streamType  = entry.streamType
        streamValue = entry.value

        v = streamValue.asFloat

        self._LatestSensors.SensorTime_s = streamTime

        dataRecognized = True
        if streamType == ss.STREAM_Laser1Temp:
            self._LatestSensors.Laser_T_C = v
        elif streamType == ss.STREAM_CavityPressure:
            self._LatestSensors.Cavity_P_Torr = v
        elif streamType == ss.STREAM_CavityTemp:
            self._LatestSensors.Cavity_T_C = v
        elif streamType == ss.STREAM_Laser1Temp:
            self._LatestSensors.Laser_T_C = v
        elif streamType == ss.STREAM_EtalonTemp:
            self._LatestSensors.Etalon_T_C = v
        elif streamType == ss.STREAM_WarmChamberTemp:
            self._LatestSensors.WarmBox_T_C = v
        elif streamType == ss.STREAM_Laser1TecCurrentMon:
            self._LatestSensors.LaserTec_I_mA = v
        elif streamType == ss.STREAM_WarmChamberTecCurrentMon:
            self._LatestSensors.WarmBoxTec_I_mA = v
        elif streamType == ss.STREAM_HotChamberTecCurrentMon:
            self._LatestSensors.HotBoxTec_I_mA = v
        elif streamType == ss.STREAM_HeaterTapeIMon:
            self._LatestSensors.Heater_I_mA = v
        elif streamType == ss.STREAM_DasTemp:
            self._LatestSensors.Environment_T_C = v
        elif streamType == ss.STREAM_InletDacValue:
            self._LatestSensors.InletValve_Pos = v
        elif streamType == ss.STREAM_OutletDacValue:
            self._LatestSensors.OutletValve_Pos = v
        elif streamType == ss.STREAM_SolenoidValveStatus:
            self._LatestSensors.SolenoidValves = v
        else:
            dataRecognized = False

        self._sensorsUpdated |= dataRecognized

    def _RingdownFilter(self, RdData):
        if 0: assert isinstance(RdData, ___RDResults) #for wing
        #Put together what will be added to the RdQueue

        #rdData = (
                            #entry.lockValue,             # asUint32 = locked wavenumber; asFloat = thetaCal
                            #entry.ratio1,                # wm1_ratio
                            #entry.ratio2,                # wm2_ratio
                            #entry.correctedAbsorbance,   # loss_c
                            #entry.uncorrectedAbsorbance, # loss_u
                            #entry.pztValue,              # pzt
                            #entry.etalonSelect,          # etalon select
                            #entry.laserSelect,           # laser select
                            #entry.fitStatus,             # fitStatus
                            #entry.schemeStatus,          # schemeStatus
                            #entry.msTicks,               # milliseconds since startup
                            #entry.count,                 # schemeCounter
                            #entry.subSchemeId,           # schemeIdent
                            #entry.schemeTableIndex,      # schemeTableIndex
                            #entry.schemeRow,             # schemeRow
                            #entry.lockSetpoint,          # asUint32 = requested wavenumber; asFloat = laserTemp
        #)
        if __debug__:
            if 0: assert isinstance(RdData, ___RDResults) #for Wing
            #print "%8s" % binary_repr(rdData.schemeStatus), rdData.msTicks, rdData.subSchemeId, rdData.schemeTableIndex, rdData.schemeRow, rdData.wavenum
            #print "%r | %r" % (rdData, sensorData)
            pass
        # For efficiency, send a reference to the cached sensor values if they have not changed since the
        #  last ringdown
        if self._sensorsUpdated:
            self._sensorsUpdated = False
            self._cachedSensors = self._LatestSensors.copy()
        # Also place a pointer to the scheme to which this ringdown belongs, so we can refer to it for setpoint
        #  and frequency conversion information later
        dasScheme = self.SchemesByDasIndex[RdData.schemeTableIndex]
        return (RdData, self._cachedSensors, dasScheme)
        #return (RdData, self._LatestSensors.copy())

if __name__ == "__main__":
    Log("** Spectrum Manager started as standalone!")
    sq = Queue.Queue()
    schemeDict = {}
    testPath1 = r"C:\CFBDS01\config\AppData\Schemes\CFBDS01_FSR.sch"
    testPath2 = r"C:\Code\PicarroVSS\SilverStone\_HostCore\MeasSystem\Schemes\H2S_wide_FSR_cal.sch"
    schemeDict[testPath1] = (testPath1, 0, 7)
    #schemeDict[testPath2] = (testPath2, 1, 8)
    sm = SpectrumManager(sq,
                         r"c:/picarro/crdsdata",
                         True,
                         "C:/CFBDS01/config/AppData/InstrCal/CFBDS01_Warmbox_Active.ini",
                         schemeDict,
                         10)
    sm._SweepEnabled.set()
    restart = True; loop = True;
    CRDS_Driver.startEngine() #makes sure the laser is on
    CRDS_Driver.wrSchemeSequence([0, 0, 0, 0, 0, 0, 0, 1], restart, loop)
    CRDS_CalMgr.UploadWarmboxCal()
    #CRDS_Driver.SpectCntrl_SetActiveSchemeIndex(0)
    #sm.SetSchemeSequence(["H2S"])
    sm._MainLoop() #run directly, rather than threaded, so we can debug
