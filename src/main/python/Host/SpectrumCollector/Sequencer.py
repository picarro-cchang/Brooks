#!/usr/bin/python
#
# FILE:
#   Sequencer.py
#
# DESCRIPTION:
#   Top level frame for the controller application
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   07-Apr-2009  sze  Initial version.
#   19-Jul-2010  sze  Moved to spectrum collector
#   16-Dec-2013  sze  Allow scheme sequences to be loaded that depend on the peak detector
#                      state. This will allow for dealing with high background in surveyor.
#   22-Feb-2014  sze  Read back next scheme register for comparison with active scheme register
#                       when in WAIT_UNTIL_ACTIVE state
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import os
import sys
import time

from threading import Thread, Lock
from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common import SharedTypes, CmdFIFO
from Host.Common.SchemeProcessor import Scheme
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import RPC_PORT_FREQ_CONVERTER, RPC_PORT_DRIVER

APP_NAME = "Sequencer"

if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init(APP_NAME)

# For convenience in calling driver and frequency converter functions
Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection=False)

RDFreqConv = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                        APP_NAME, IsDontCareConnection=False)


class Sequencer(object):

    """Supervises running of a sequence of schemes, using a block of four scheme table entries. The sequences
    are stored in self.sequences, keyed either by a numeric code (for sequences from the Master.ini file) or by
    the name of the mode (for sequences in non-integration mode).

    Each sequence is stored in self.sequences as a tuple (scheme, repetitions, freq_based). "scheme" is an 
    instance of the Scheme class defined in Host.Common.SchemeProcessor, "repetitions" is the number of repetitions
    of the scheme required and "freq_based" is True for a scheme containing ringdown frequencies and False for a
    scheme consisting of wavelength monitor angles.
    """
    IDLE = 0
    STARTUP = 1
    SEND_SCHEME = 2
    WAIT_UNTIL_ACTIVE = 3

    def __init__(self):
        self.state = Sequencer.IDLE
        self.sequence = '1'  # Sequence to run (key in self.sequences)
        self.scheme = 1
        self.repeat = 1
        self.group = 1
        self.activeIndex = None
        self.useIndex = None
        self.sequences = {}
        self.getSequences(Driver.getConfigFile())
        self.initialized = True
        self.laserTypes = {}
        self.inDas = {}
        self.loadSequencePending = False
        self.loadSequenceLock = Lock()
        self.pendingSequence = ""

    def runInThread(self):
        sequencerThread = Thread(target=self.runFsm)
        sequencerThread.setDaemon(True)
        sequencerThread.start()

    def removeNumericSequences(self):
        # Remove sequences whose names are integers, since these should be
        #  overwritten when the master file is reloaded
        keysToDelete = []
        for key in self.sequences:
            try:
                int(key)
                keysToDelete.append(key)
            except:
                pass
        for key in keysToDelete:
            del self.sequences[key]

    def getSequences(self, configFile):
        # Read sequences from configFile (typically Master.ini) into self.sequences
        basePath = os.path.split(configFile)[0]
        config = CustomConfigObj(configFile)
        self.removeNumericSequences()
        self.state = Sequencer.IDLE
        # Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_IdleState)
        nseq = 0
        for section in config:
            if section.upper().startswith("SEQUENCE"):
                try:
                    index = int(section[len("SEQUENCE"):])
                    cs = config[section]
                    nSchemes = int(cs["NSCHEMES"])
                    schemes = []
                    for i in range(nSchemes):
                        schemeFileName = os.path.join(basePath, cs["SCHEME%02d" % (i + 1,)])
                        repetitions = int(cs["REPEAT%02d" % (i + 1,)])
                        _, ext = os.path.splitext(schemeFileName)
                        schemes.append((Scheme(schemeFileName), repetitions, ext.lower() == ".sch"))
                    self.sequences["%s" % index] = schemes
                    nseq += 1
                except:
                    LogExc("Error in processing schemes for %s" % section, Level=3)
        Log("Sequences read: %d" % nseq)

    def addNamedSequenceOfSchemeConfigs(self, name, schemeConfigs):
        try:
            for name_suffix in schemeConfigs:
                schemes = []
                schemeList = schemeConfigs[name_suffix].schemes
                for schemeFileName in schemeList:
                    _, ext = os.path.splitext(schemeFileName)
                    schemes.append((Scheme(schemeFileName), 1, ext.lower() == ".sch"))
                self.sequences[name + name_suffix] = schemes
                Log("Added named sequence: %s" % name + name_suffix, Level=0)
        except:
            LogExc("Error in processing scheme configuration for %s" % name, Level=3)

    def getSequenceNames(self):
        return self.sequences.keys()

    def reloadSequences(self):
        self.getSequences(Driver.getConfigFile())

    def setSequenceName(self, seq):
        self.sequence = str(seq)

    def getSequenceName(self):
        return self.sequence

    def startSequence(self):
        self.state = Sequencer.STARTUP

    def getCurrent(self):
        ss = Driver.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER)
        active = Driver.rdDasReg(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
        if ss in [interface.SPECT_CNTRL_RunningState] and self.state not in [Sequencer.IDLE]:
            return self.inDas.get(active, None)

    def runFsm(self):
        # This implements a state machine running in an infinite loop that supervises loading of schemes
        #  by the driver
        scs = RDFreqConv.getShortCircuitSchemeStatus()
        baseSequenceName = self.sequence
        while True:
            try:
                if self.state == Sequencer.STARTUP:
                    for vLaserNum in range(1, interface.NUM_VIRTUAL_LASERS + 1):
                        RDFreqConv.useSpline(vLaserNum)
                    Log("Sequencer enters STARTUP state")
                    Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER, interface.SPECT_CNTRL_IdleState)
                    self.activeIndex = Driver.rdDasReg(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
                    seqList = self.sequences[self.sequence]
                    # seqList is a list of tuples [(scheme,repetitions,freq_based),...] that define the
                    #  sequence
                    if not seqList:
                        self.state = Sequencer.IDLE
                    elif isinstance(seqList[0], tuple):
                        if scs:
                            Driver.setMultipleNoRepeatScan()
                        else:
                            Driver.setMultipleScan()
                        self.scheme = 1
                        self.repeat = 1
                        self.state = Sequencer.SEND_SCHEME
                elif self.state == Sequencer.SEND_SCHEME:
                    # Read the peak detector state since this may modify the scheme sequence
                    #  required
                    peakDetectState = Driver.rdDasReg("PEAK_DETECT_CNTRL_STATE_REGISTER")
                    stateName = interface.PEAK_DETECT_CNTRL_StateTypeDict[peakDetectState]
                    stateName = stateName[len("PEAK_DETECT_CNTRL_"):]
                    # The state name is used to modify the base name of the sequence
                    self.loadSequenceLock.acquire()
                    try:
                        if self.loadSequencePending:
                            if self.pendingSequence not in self.sequences:
                                raise ValueError("Invalid sequence name: %s" % self.pendingSequence)
                            baseSequenceName = self.pendingSequence
                        trialSequenceName = baseSequenceName + '_' + stateName
                        if trialSequenceName in self.sequences:
                            self.pendingSequence = trialSequenceName
                        else:
                            self.pendingSequence = baseSequenceName
                        if self.pendingSequence != self.sequence:
                            self.setSequenceName(self.pendingSequence)
                            self.scheme = 1
                            self.repeat = 1
                    finally:
                        self.loadSequencePending = False
                        self.loadSequenceLock.release()

                    # Set "useIndex" to the next available index in the group of four
                    self.useIndex = (self.activeIndex + 1) % 4
                    schemes = self.sequences[self.sequence]
                    scheme, rep, freqBased = schemes[self.scheme - 1]
                    Log("Sequencer enters SEND_SCHEME state. Sequence = %s, Scheme = %d (%s), Repeat = %d, Table = %d"
                        % (self.sequence, self.scheme, os.path.split(scheme.fileName)[-1], self.repeat, self.useIndex))
                    self.inDas[self.useIndex] = (self.sequence, self.scheme, self.repeat, scheme.fileName)
                    # Increment repeat and scheme number as needed
                    self.repeat += 1
                    if self.repeat > rep:
                        self.repeat = 1
                        self.scheme += 1
                        if self.scheme > len(schemes):
                            self.scheme = 1
                    # Frequency-based schemes need to be compiled, whereas angle-based schemes are sent directly
                    #  to the DAS
                    if freqBased:
                        RDFreqConv.wrFreqScheme(self.useIndex, scheme)
                        RDFreqConv.convertScheme(self.useIndex)
                        RDFreqConv.uploadSchemeToDAS(self.useIndex)
                    else:
                        Driver.wrScheme(self.useIndex, *(scheme.repack()))
                    # Specify the just-loaded scheme to be the next one to execute
                    Driver.wrDasReg(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER, self.useIndex)
                    if Driver.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER) == interface.SPECT_CNTRL_IdleState:
                        Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER, interface.SPECT_CNTRL_StartingState)
                    self.state = Sequencer.WAIT_UNTIL_ACTIVE
                elif self.state == Sequencer.WAIT_UNTIL_ACTIVE:
                    # Loop around until the active scheme index is equal to the one we are expecting (in self.useIndex).
                    #  When this is the case, we can send the next scheme or stop, if the SPECT_CNTRL_STATE_REGISTER
                    #  is in the idle state
                    self.activeIndex = Driver.rdDasReg(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
                    next = Driver.rdDasReg(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER)
                    if next != self.useIndex:
                        Log("Unexpected next scheme register contents", Data={"expected":self.useIndex, "contents":next})
                    if self.activeIndex == next:
                        self.state = Sequencer.SEND_SCHEME
                    elif Driver.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER) == interface.SPECT_CNTRL_IdleState:
                        self.state = Sequencer.IDLE
            except Exception:
                self.state = Sequencer.IDLE
                LogExc("Sequencer state machine exception: %s", Level=2)
            time.sleep(0.5)