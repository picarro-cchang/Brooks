#!/usr/bin/python
#
"""
File Name: testSequencer.py
Purpose: Unit tests for the Sequencer

File History:
    2013-11-25  sze 

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import unittest
import os
from Host.SpectrumCollector import Sequencer

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

class myDriver(object):
    @staticmethod
    def getConfigFile():
        return os.path.join(SCRIPT_DIR, 'Master1.ini')

class myRDFreqConv(object):
    pass

class TestSequencer(unittest.TestCase):

    def setUp(self):
        self.sequencer = Sequencer.Sequencer()

    def tearDown(self):
        pass

    def testSetup(self):
        self.sequencer.reloadSequences()
        self.assertEqual(len(self.sequencer.sequences),2)
        # Check correct number of schemes in each sequence
        self.assertEqual(len(self.sequencer.sequences['1']),1)
        self.assertEqual(len(self.sequencer.sequences['2']),2)
        # Check correct number of repetitions in each sequence
        scheme, repetitions, freq_based = self.sequencer.sequences['1'][0]
        self.assertEqual((repetitions, freq_based),(1,True))
        scheme, repetitions, freq_based = self.sequencer.sequences['2'][0]
        self.assertEqual((repetitions, freq_based),(2,True))
        scheme, repetitions, freq_based = self.sequencer.sequences['2'][1]
        self.assertEqual((repetitions, freq_based),(2,True))



def setup_module():
    Sequencer.Driver = myDriver
    Sequencer.RDFreqConv = myRDFreqConv


def teardown_module():
    pass

if __name__ == '__main__':
    unittest.main()
