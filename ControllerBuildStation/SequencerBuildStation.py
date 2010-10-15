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
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import wx
import os
import sys
import traceback

from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common import SharedTypes
from Host.Common.CustomConfigObj import CustomConfigObj
from ControllerBuildStationModels import DriverProxy, RDFreqConvProxy

# For convenience in calling driver and frequency converter functions
Driver = DriverProxy().rpc
RDFreqConv = RDFreqConvProxy().rpc

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
EventManagerProxy_Init("Controller")

class Sequencer(SharedTypes.Singleton):
    "Supervises running of a sequence of schemes, using a block of four scheme table entries"
    IDLE = 0
    STARTUP = 1
    SEND_SCHEME = 2
    WAIT_UNTIL_ACTIVE = 3
    WAIT_FOR_SCHEME_DONE = 4
    initialized = False

    def __init__(self,configFile=None):
        if not self.initialized and configFile is not None:
            self.state = Sequencer.IDLE
            self.sequence = 1
            self.scheme = 1
            self.repeat = 1
            self.activeIndex = None
            self.useIndex = None
            self.sequences = None
            self.getSequences(configFile)
            self.initialized = True

    def getSequences(self,configFile):
        basePath = os.path.split(configFile)[0]
        config = CustomConfigObj(configFile)
        self.sequences = []
        self.state = Sequencer.IDLE
        # Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_IdleState)
        index = 1
        section = "SEQUENCE%02d" % (index,)
        try:
            while section in config:
                cs = config[section]
                nSchemes = int(cs["NSCHEMES"])
                schemes = []
                for i in range(nSchemes):
                    schemeFileName = os.path.join(basePath, cs["SCHEME%02d" % (i+1,)])
                    repetitions = int(cs["REPEAT%02d" % (i+1,)])
                    name, ext = os.path.splitext(schemeFileName)
                    schemes.append((SharedTypes.Scheme(schemeFileName),repetitions,ext.lower() == ".sch"))
                self.sequences.append(schemes)
                index += 1
                section = "SEQUENCE%02d" % (index,)
            Log("Sequences read: %d" % len(self.sequences))
        except Exception,e:
            LogExc("Error in sequencer ini file")

    def numSequences(self):
        return len(self.sequences)
    
    def runFsm(self):
        try:
            if self.state == Sequencer.STARTUP:
                Log("Sequencer enters STARTUP state")
                Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_IdleState)
                self.activeIndex = Driver.rdDasReg(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
                Driver.wrDasReg(interface.SPECT_CNTRL_MODE_REGISTER,interface.SPECT_CNTRL_SchemeMultipleMode)            
                self.scheme = 1
                self.repeat = 1
                self.state = Sequencer.SEND_SCHEME
            elif self.state == Sequencer.SEND_SCHEME:
                Log("Sequencer enters SEND_SCHEME state. Sequence = %d, Scheme = %d, Repeat = %d" \
                    % (self.sequence,self.scheme,self.repeat))
                self.useIndex = (self.activeIndex + 1) % 4
                schemes = self.sequences[self.sequence-1]
                scheme,rep,freqBased = schemes[self.scheme-1]
                self.repeat += 1
                if self.repeat > rep:
                    self.repeat = 1
                    self.scheme += 1
                    if self.scheme > len(schemes): 
                        self.scheme = 1
                if freqBased:
                    RDFreqConv.wrFreqScheme(self.useIndex,scheme)
                    RDFreqConv.convertScheme(self.useIndex)
                    RDFreqConv.uploadSchemeToDAS(self.useIndex)
                else:
                    Driver.wrScheme(self.useIndex,*(scheme.repack()))
                Driver.wrDasReg(interface.SPECT_CNTRL_NEXT_SCHEME_REGISTER,self.useIndex)
                if Driver.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER) == interface.SPECT_CNTRL_IdleState:
                    Driver.wrDasReg(interface.SPECT_CNTRL_STATE_REGISTER,interface.SPECT_CNTRL_StartingState)
                self.state = Sequencer.WAIT_UNTIL_ACTIVE
            elif self.state == Sequencer.WAIT_UNTIL_ACTIVE:
                self.activeIndex = Driver.rdDasReg(interface.SPECT_CNTRL_ACTIVE_SCHEME_REGISTER)
                if self.activeIndex == self.useIndex:
                    self.state = Sequencer.SEND_SCHEME
                elif Driver.rdDasReg(interface.SPECT_CNTRL_STATE_REGISTER) == interface.SPECT_CNTRL_IdleState:
                    self.state = Sequencer.IDLE
        except Exception,e:
            self.state = Sequencer.IDLE
            Log("%s" % e, Level=2)