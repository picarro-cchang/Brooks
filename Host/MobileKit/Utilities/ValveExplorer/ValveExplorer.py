"""
Copyright 2012 Picarro Inc.

Utility for exploring the timing of the MobileKit valves and the corresponding
analysis response.
"""

from __future__ import with_statement

import time
import threading
import csv

import LossStream
import ValveMaskStream

from Host.Common import CmdFIFO
from Host.Common import SharedTypes


class ValveExplorer(object):
    """
    Reads the cocentration data and sets the valves in response to the
    user's demands.
    """

    N_VALVES = 3

    def __init__(self, log=None, dataCb=None):
        self.streams = [LossStream.LossStream(dataCb),
                        ValveMaskStream.ValveMaskStream(dataCb)]
        self.valveSeq = None
        self.driver = CmdFIFO.CmdFIFOServerProxy(
            "http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
            'ValveExplorer')
        self.log = log

        self.ctx = None

        self.acqThread = None
        self.lock = threading.Lock()
        self.doStop = False

    def saveSequence(self, path):
        """
        Save the current sequence (assuming there is one) to the
        specified path as a CSV file.
        """

        if self.valveSeq is None:
            self.log("No valve sequence available to save.")
            return

        fp = csv.writer(open(path, 'ab'))
        for r in self.valveSeq:
            fp.writerow(r)

    def loadSequence(self, path):
        """
        Load the sequence file (in .csv format) located at path into
        the ValveExplorer.
        """

        fp = csv.reader(open(path, 'rb'))
        self.valveSeq = []
        for r in fp:
            if len(r) != 0:
                self.valveSeq.append([int(x) for x in r])

    def genValveSequence(self, steps):
        """
        Translates a series of valve sequence steps into a format
        appropriate for the DSP to use. The expected format of `steps`
        is [step0, step1, step2, ...], where `step{n}` is [valve0,
        valve1, valve2, time (s)]. `valve{n}` = 0 always means ignore
        and will leave that valve out of the calculated mask.
        """

        # Always start w/ all valves closed and the stop state. The
        # real sequence starts at instruction offset 2.
        self.valveSeq = []
        for s in steps:
            mask = 0
            state = 0
            for i in range(self.N_VALVES):
                if s[i] > 0:
                    mask |= (1 << i)
                    if s[i] == 2:
                        state |= (1 << i)
            self.valveSeq.append([mask, state, int(s[-1] / 0.2)])
        # Final stop state
        self.valveSeq.append([0x0, 0x0, 0])

        self._log("Generated valve sequence:\n")
        for s in self.valveSeq:
            for v in s:
                self._log("%#X " % v)
            self._log("\n")
        self._log("\n")

    def downloadValveSequence(self):
        self._setValveStep(-1)
        self.driver.wrValveSequence(self.valveSeq)

    def doDataAcquisition(self, completionCb=None):
        """
        Starts acquiring the processed loss data and resets the valve
        sequence back to the beginning. Spawns a separate thread to
        run the valve sequence.
        """

        with self.lock:
            self.doStop = False

        self.acqThread = threading.Thread(target=self._doDataAcquisition,
                                          kwargs={'completionCb' : completionCb})
        self.acqThread.start()

    def isRunning(self):
        if self.acqThread is None:
            return False
        else:
            return self.acqThread.isAlive()

    def interruptDataAcquisition(self):
        """
        Interrupts the DAQ thread and blocks until it has safely
        completed.
        """

        print "Acquiring lock..."

        with self.lock:
            self.doStop = True

        print "...Lock released. doStop = True."
        print "Start poll waiting for finish."

        # Wait for it to actually finish
        while self.isRunning():
            time.sleep(0.001)

        print "Put valve sequencer into Idle state."

        # Put valves back to idle
        self._setValveStep(len(self.valveSeq) - 1)

    def _doDataAcquisition(self, **kwargs):
        self._startAcquisition()

        with self.lock:
            stopRequested = self.doStop

        while self._isSequenceRunning() and not stopRequested:
            time.sleep(0.001)
            with self.lock:
                stopRequested = self.doStop

        self._stopAcquisition(stopRequested, kwargs['completionCb'])

    def _startAcquisition(self):
        self.ctx = self.driver.saveRegValues(
            ['PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER'])

        # Override the default Idle valve mask
        self.driver.wrDasReg(
            'PEAK_DETECT_CNTRL_IDLE_VALVE_MASK_AND_VALUE_REGISTER', 0)

        for s in self.streams:
            s.start()

        self._setValveStep(0)

    def _stopAcquisition(self, stopRequested, completionCb=None):
        print "Stopping acquisition."

        print "Stopping streams."
        for s in self.streams:
            s.stop()

        print "All streams stopped."

        self.driver.restoreRegValues(self.ctx)

        print "Driver register context restored."

        if not stopRequested and completionCb is not None:
            completionCb()

    def _isSequenceRunning(self):
        return self._getValveStep() != (len(self.valveSeq) - 1)

    def _setValveStep(self, step):
        self.driver.wrDasReg('VALVE_CNTRL_SEQUENCE_STEP_REGISTER', step)

    def _getValveStep(self):
        return self.driver.rdDasReg('VALVE_CNTRL_SEQUENCE_STEP_REGISTER')

    def _log(self, msg):
        if self.log is None:
            return

        self.log(msg)
