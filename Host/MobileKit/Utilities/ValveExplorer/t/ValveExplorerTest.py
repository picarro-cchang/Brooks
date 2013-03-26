"""
Copyright 2012 Picarro Inc.

These tests are meant to be run with `nose`.
"""

import sys
import pprint

sys.path.append('..')
import ValveExplorer


class TestValveExplorer(object):

    def setup(self):
        self.v = ValveExplorer.ValveExplorer()

    def testValveSequenceOneStep(self):
        assert self.v.valveSeq is None
        self.v.genValveSequence([[0, 0, 0, 1.0]])
        assert self.v.valveSeq == [
            [0xFF, 0x0, 0],
            [0x0, 0x0, 0],
            [0x0, 0x0, 5],
            [0x0, 0x0, 0]]

    def testValveSequenceMultiStep(self):
        assert self.v.valveSeq is None
        self.v.genValveSequence([
                # Ignore all for 1s
                [0, 0, 0, 1.0],
                # Valve 0 off, ignore others for 2s
                [1, 0, 0, 2.0],
                # Valves 0 and 1 off, ignore 2 for 3s
                [1, 1, 0, 3.0],
                # All valves off for 4.5s
                [1, 1, 1, 4.2],
                # All valves on for 5s
                [2, 2, 2, 5.0],
                # Valves 0 and 2 on, valve 2 off for 6s
                [2, 1, 2, 6.0],
                # Valves 0 and 1 ignore, valve 2 on for 7s
                [0, 0, 2, 7.0]])
        assert self.v.valveSeq == [
            [0xFF, 0x0, 0],
            [0x0, 0x0, 0],
            [0x0, 0x0, 5],
            [0x1, 0x0, 10],
            [0x3, 0x0, 15],
            [0x7, 0x0, 21],
            [0x7, 0x7, 25],
            [0x7, 0x5, 30],
            [0x4, 0x4, 35],
            [0x0, 0x0, 0]]
