#!/usr/bin/python
#
# File Name: IsotechGC.py
# Purpose: Uses TTL interface to communicate with Isotech GC
#
# Notes: Uses TTLIntrf as the core with customized functions for Isotech GC
# 03-06-09 alex Created file

import sys
from Host.Common.TTLIntrf import TTLIntrf

ASSERT_SIG = 0
DEASSERT_SIG = 1

# Define input (status) and output (control) lines
STAT_START_SAMPLE = 1
STAT_X_SAMPLE_ACK = 2
CTRL_X_SAMPLE = 1
CTRL_Y_SAMPLE = 2

class GC(TTLIntrf):
    def __init__(self):
        TTLIntrf.__init__(self, ASSERT_SIG, DEASSERT_SIG)

    def getStartSample(self):
        return self.getStatus(STAT_START_SAMPLE)

    def getXSampleAck(self):
        return self.getStatus(STAT_X_SAMPLE_ACK)

    def sendXSample(self):
        self.assertControl(CTRL_X_SAMPLE)

    def sendXVent(self):
        self.deassertControl(CTRL_X_SAMPLE)

    def sendYSample(self):
        self.assertControl(CTRL_Y_SAMPLE)

    def sendYVent(self):
        self.deassertControl(CTRL_Y_SAMPLE)

    # The following functions are not useful in real applications, but good for in-lab testing
    def getCtrlXSample(self):
        return self.getControl(CTRL_X_SAMPLE)

    def getCtrlYSample(self):
        return self.getControl(CTRL_Y_SAMPLE)