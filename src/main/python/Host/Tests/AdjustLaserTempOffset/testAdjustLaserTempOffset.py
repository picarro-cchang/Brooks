#!/usr/bin/python
#
"""
Description: Test script for adjusting laser temperature offset value
             to compensate for laser aging.

Details:     Tests are hard-coded for 4 virtual lasers: 1, 2, 4, 5.
             Each test inits everything (including whether the control
             loop is on) so they can be run in any order.

Copyright (c) 2013 Picarro, Inc. All rights reserved.
"""
#import unittest
import pytest

from Host.Common.DoAdjustTempOffset import doAdjustTempOffset


# to emulate a _FREQ_CONV_ object
class PseudoFreqConv(object):
    def __init__(self):
        self.fineCurrentOffsets = {}
        self.newFineCurrentOffsets = {}

        # init existing laser current offset values for our 4 virtual lasers
        self.fineCurrentOffsets["currentOffset_1"] = 0.068426
        self.fineCurrentOffsets["currentOffset_2"] = -0.000138
        self.fineCurrentOffsets["currentOffset_4"] = 0.194392
        self.fineCurrentOffsets["currentOffset_5"] = 0.047620

        self.newFineCurrentOffsets["currentOffset_1"] = 0.0
        self.newFineCurrentOffsets["currentOffset_2"] = 0.0
        self.newFineCurrentOffsets["currentOffset_4"] = 0.0
        self.newFineCurrentOffsets["currentOffset_5"] = 0.0

    def getLaserTempOffset(self, vLaser):
        return self.fineCurrentOffsets["currentOffset_%d" % vLaser]

    def setLaserTempOffset(self, vLaser, newOffset):
        # save off new values in case need them for testing
        # we don't want to clobber our known initial values so
        # a new test starts with a different set of current offsets
        self.newFineCurrentOffsets["currentOffset_%d" % vLaser] = newOffset


def initInstrParams(instr):
    # init instrument settings that are found in the LaserTempOffsets_xxx.ini file
    instr["la_fineLaserCurrent_gain"] = 1e-7
    instr["la_fineLaserCurrent_maxStep"] = .001
    instr["la_fineLaserCurrent_minFineCurrent"] = 5000
    instr["la_fineLaserCurrent_maxFineCurrent"] = 60000

    instr["la_enabled"] = 1.0

    instr["la_fineLaserCurrent_1_target"] = 26050
    instr["la_fineLaserCurrent_2_target"] = 36900
    instr["la_fineLaserCurrent_4_target"] = 27550
    instr["la_fineLaserCurrent_5_target"] = 30650


def enableControlLoop(instr, fEnable):
    if (fEnable):
        instr["la_enabled"] = 1.0
    else:
        instr["la_enabled"] = 0.0


def initGoodData(data=None, devExpected=None, instr=None):
    # hard-coded table of virtual lasers 1, 2, 4, 5 with
    # reasonable values for mean fine current
    # Note: None of these should match their target or
    #       tests may fail because they expect the new offset
    #       to be different from the current offset
    currentMeans = {1: 25974, 2: 36389, 4: 27552, 5: 30649}

    for vLaserNum in currentMeans:
        name = "fineLaserCurrent_%d_mean" % vLaserNum
        curMean = currentMeans[vLaserNum]
        data[name] = curMean

        target_name = "la_fineLaserCurrent_%d_target" % vLaserNum
        devExpected[vLaserNum] = curMean - instr[target_name]


def initBadDataHigh(data):
    # virtual laser 2 has a too high mean
    # Note: None should match their targets or will result in false negatives
    currentMeansBad = {1: 25974, 2: 60001, 4: 60000, 5: 69999}

    for vLaserNum in currentMeansBad:
        name = "fineLaserCurrent_%d_mean" % vLaserNum
        data[name] = currentMeansBad[vLaserNum]


def initBadDataLow(data):
    # virtual laser 5 has a too low mean
    # Note: None should match their targets or will result in false negatives
    #       Testing edge cases around the 5000 limit
    currentMeansBad = {1: 25974, 2: 5001, 4: 5000, 5: 4999}

    for vLaserNum in currentMeansBad:
        name = "fineLaserCurrent_%d_mean" % vLaserNum
        data[name] = currentMeansBad[vLaserNum]


class TestAdjustLaserTempOffset(object):
    def setup_method(self, m):
        self._DATA_ = {}
        self._INSTR_ = {}
        self._REPORT_ = {}
        self._PERSISTENT_ = {}
        self._FREQ_CONV_ = PseudoFreqConv()
        initInstrParams(self._INSTR_)
        enableControlLoop(self._INSTR_, True)

    def outputReport(self, vLaserNum):
        name = "fineLaserCurrent_%d_dev" % vLaserNum

        if name in self._REPORT_:
            print "vLaserNum=%d  dev=%14.6f  offset= %9.6f  controlOn=%.2f" % \
                (vLaserNum,
                 self._REPORT_["fineLaserCurrent_%d_dev" % vLaserNum],
                 self._REPORT_["fineLaserCurrent_%d_offset" % vLaserNum],
                 self._REPORT_["fineLaserCurrent_%d_controlOn" % vLaserNum])

    def test_AdjustOffsetGood(self):
        print "test_AdjustOffsetGood"
        diffs = {}
        initGoodData(data=self._DATA_, instr=self._INSTR_, devExpected=diffs)
        enableControlLoop(self._INSTR_, True)

        # do the calculations and stick results in _REPORT_
        doAdjustTempOffset(instr=self._INSTR_,
                           data=self._DATA_,
                           freqConv=self._FREQ_CONV_,
                           report=self._REPORT_)

        # validate results in the report
        # should only have results for lasers 1, 2, 4, 5
        for v in range(8):
            vLaserNum = v + 1

            devName = "fineLaserCurrent_%d_dev" % vLaserNum
            ctrlName = "fineLaserCurrent_%d_controlOn" % vLaserNum
            offsetName = "fineLaserCurrent_%d_offset" % vLaserNum

            self.outputReport(vLaserNum)

            # I can't seem to make assertAlmostEqual accessible
            #if vLaserNum == 1:
                #tc = unittest.TestCase()
                #tc.assertIn(devName, self._REPORT_)
                #self.assertAlmostEqual(self._REPORT_[devName], -76.0)
                #assert(self._REPORT_[devName] == diffs[vLaserNum])

            if vLaserNum == 1 or vLaserNum == 2 or vLaserNum == 4 or vLaserNum == 5:
                assert(devName in self._REPORT_), "%s missing from _REPORT_" % (devName, )
                assert(ctrlName in self._REPORT_), "%s missing from _REPORT_" % (ctrlName, )
                assert(offsetName in self._REPORT_), "%s missing from _REPORT_" % (offsetName, )

                assert(self._REPORT_[devName] == diffs[vLaserNum])
                assert(self._REPORT_[ctrlName] == 1)

                # we expect the new calculated offsets to be different from the existing temp offset
                assert(self._REPORT_[offsetName] != self._FREQ_CONV_.getLaserTempOffset(vLaserNum))

            else:
                assert(devName not in self._REPORT_), "%s should not be in _REPORT_" % (devName, )
                assert(ctrlName not in self._REPORT_), "%s should not be in _REPORT_" % (ctrlName, )
                assert(offsetName not in self._REPORT_), "%s should not be in output report" % (offsetName, )

    def test_AdjustOffsetBadLow(self):
        print "test_AdjustOffsetBadLow"
        initBadDataLow(self._DATA_)
        enableControlLoop(self._INSTR_, True)

        # do the calculations and stick results in _REPORT_
        doAdjustTempOffset(instr=self._INSTR_,
                           data=self._DATA_,
                           freqConv=self._FREQ_CONV_,
                           report=self._REPORT_)

        # hard-coded lasers 1, 2, 4, 5 should all have control turned off
        for v in range(8):
            vLaserNum = v + 1

            ctrlName = "fineLaserCurrent_%d_controlOn" % vLaserNum
            offsetName = "fineLaserCurrent_%d_offset" % vLaserNum

            self.outputReport(vLaserNum)

            if vLaserNum == 1 or vLaserNum == 2 or vLaserNum == 4 or vLaserNum == 5:
                assert(ctrlName in self._REPORT_), "%s missing from _REPORT_" % (ctrlName, )
                assert(offsetName in self._REPORT_), "%s missing from _REPORT_" % (offsetName, )

                # control loop should be disabled for all lasers
                assert(self._REPORT_[ctrlName] == 0)

                # current offset should be unchanged since control loop disabled
                assert(self._REPORT_[offsetName] == self._FREQ_CONV_.getLaserTempOffset(vLaserNum))
            else:
                # check whether report contains items that should not be there
                assert(ctrlName not in self._REPORT_), "%s should not be in output report" % (ctrlName, )
                assert(offsetName not in self._REPORT_), "%s should not be in output report" % (offsetName, )

    def test_AdjustOffsetBadHigh(self):
            print "test_AdjustOffsetBadHigh"
            initBadDataHigh(self._DATA_)
            enableControlLoop(self._INSTR_, True)

            # do the calculations and stick results in _REPORT_
            doAdjustTempOffset(instr=self._INSTR_,
                               data=self._DATA_,
                               freqConv=self._FREQ_CONV_,
                               report=self._REPORT_)

            # hard-coded lasers 1, 2, 4, 5 should all have control turned off
            for v in range(8):
                vLaserNum = v + 1

                ctrlName = "fineLaserCurrent_%d_controlOn" % vLaserNum
                offsetName = "fineLaserCurrent_%d_offset" % vLaserNum

                self.outputReport(vLaserNum)

                if vLaserNum == 1 or vLaserNum == 2 or vLaserNum == 4 or vLaserNum == 5:
                    assert(ctrlName in self._REPORT_), "%s missing from _REPORT_" % (ctrlName, )
                    assert(offsetName in self._REPORT_), "%s missing from _REPORT_" % (offsetName, )

                    # control loop should be disabled for all lasers
                    assert(self._REPORT_[ctrlName] == 0)

                    # current offset should be unchanged since control loop disabled
                    assert(self._REPORT_[offsetName] == self._FREQ_CONV_.getLaserTempOffset(vLaserNum))
                else:
                    # check whether report contains items that should not be there
                    assert(ctrlName not in self._REPORT_), "%s should not be in output report" % (ctrlName, )
                    assert(offsetName not in self._REPORT_), "%s should not be in output report" % (offsetName, )

    def test_AdjustControlLoopOff(self):
        print "test_AdjustControlLoopOff"
        diffs = {}
        initGoodData(data=self._DATA_, instr=self._INSTR_, devExpected=diffs)
        enableControlLoop(self._INSTR_, False)

        # do the calculations and stick results in _REPORT_
        doAdjustTempOffset(instr=self._INSTR_,
                           data=self._DATA_,
                           freqConv=self._FREQ_CONV_,
                           report=self._REPORT_)

        for v in range(8):
            vLaserNum = v + 1

            ctrlName = "fineLaserCurrent_%d_controlOn" % vLaserNum
            offsetName = "fineLaserCurrent_%d_offset" % vLaserNum

            self.outputReport(vLaserNum)

            # since control loop is disabled, should be turned off (=0) for all known virtual lasers
            # the fine current offsets in the report should match the original since
            # control is turned off
            if vLaserNum == 1 or vLaserNum == 2 or vLaserNum == 4 or vLaserNum == 5:
                assert(ctrlName in self._REPORT_), "%s missing from _REPORT_" % (ctrlName, )
                assert(offsetName in self._REPORT_), "%s missing from _REPORT_" % (offsetName, )

                # control loop should be disabled for all lasers and temp offsets unchanged
                assert(self._REPORT_[ctrlName] == 0)
                assert(self._REPORT_[offsetName] == self._FREQ_CONV_.getLaserTempOffset(vLaserNum))

            else:
                assert(ctrlName not in self._REPORT_), "%s should not be in output report" % (ctrlName, )
                assert(offsetName not in self._REPORT_), "%s should not be in output report" % (offsetName, )