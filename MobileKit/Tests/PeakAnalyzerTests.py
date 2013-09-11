"""
Copyright 2013 Picarro Inc.
"""

import os
import sys
import subprocess
import shutil
import time
import threading
import os.path

import psutil

from numpy import testing

sys.path.append(os.path.abspath(os.path.join('..', 'AnalyzerServer')))
import PeakAnalyzer
sys.path.append('DataClasses')
from File1Analysis import File1Analysis

sys.path.append(os.path.abspath(os.path.join('..', '..')))
from Host.Common import DatFile




class TestPeakAnalyzer(object):

    ANALYSIS_FIELDS = [
        'EPOCH_TIME',
        'DISTANCE',
        'GPS_ABS_LONG',
        'GPS_ABS_LAT',
        'CONC',
        'DELTA',
        'UNCERTAINTY',
        'REPLAY_MAX',
        'REPLAY_LMIN',
        'REPLAY_RMIN',
        'DISPOSITION']

    def setup_method(self, m):
        baseDir = os.path.abspath(os.path.dirname(__file__))
        self.datRoot = os.path.join(baseDir, 'data')

        self.testEnv = os.environ.update({'PYTHONPATH' :
                                          os.path.join(baseDir, '..', '..')})
        self.testDir = os.path.join(self.datRoot, m.__name__)

        if os.path.isdir(self.testDir):
            shutil.rmtree(self.testDir)

        assert not os.path.isdir(self.testDir)
        os.makedirs(self.testDir)

    def testBasicAnalysis(self):
        shutil.copyfile(os.path.join(self.datRoot, 'file1_analysis.dat'),
                        os.path.join(self.testDir, 'file1_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'))
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file1_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)

        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS)) == \
            len(set(analysisFile.columnNames()))
        assert len(analysisFile['EPOCH_TIME']) is 1

        testing.assert_almost_equal(float(analysisFile['EPOCH_TIME'][0]),
                                    1378852074.29,
                                    decimal=2)
        testing.assert_almost_equal(float(analysisFile['DISTANCE'][0]),
                                    0.147,
                                    decimal=3)
        testing.assert_almost_equal(float(analysisFile['GPS_ABS_LONG'][0]),
                                    -121.984218,
                                    decimal=6)
        testing.assert_almost_equal(float(analysisFile['GPS_ABS_LAT'][0]),
                                    37.396975,
                                    decimal=6)
        testing.assert_almost_equal(float(analysisFile['CONC'][0]),
                                    17.783,
                                    decimal=3)
        testing.assert_almost_equal(float(analysisFile['DELTA'][0]),
                                    -32.48,
                                    decimal=2)
        testing.assert_almost_equal(float(analysisFile['UNCERTAINTY'][0]),
                                    0.16,
                                    decimal=2)
        testing.assert_almost_equal(float(analysisFile['REPLAY_MAX'][0]),
                                    12.321,
                                    decimal=3)
        testing.assert_almost_equal(float(analysisFile['REPLAY_LMIN'][0]),
                                    2.280,
                                    decimal=3)
        testing.assert_almost_equal(float(analysisFile['REPLAY_RMIN'][0]),
                                    1.930,
                                    decimal=3)
        testing.assert_almost_equal(float(analysisFile['DISPOSITION'][0]),
                                    0.0,
                                    decimal=1)

    def testDatWithNoAnalysis(self):
        shutil.copyfile(os.path.join(self.datRoot, 'file2_analysis.dat'),
                        os.path.join(self.testDir, 'file2_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'))
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file2_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)

        # Should only be a header tow
        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS)) == \
            len(set(analysisFile.columnNames()))
        assert len(analysisFile['EPOCH_TIME']) is 0

    def testCancelledAnalysis(self):
        shutil.copyfile(os.path.join(self.datRoot, 'file3_analysis.dat'),
                        os.path.join(self.testDir, 'file3_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'))
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file3_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)
        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS)) == \
            len(set(analysisFile.columnNames()))
        assert len(analysisFile['EPOCH_TIME']) is 1

        assert int(float(analysisFile['DISPOSITION'][0])) == \
            PeakAnalyzer.DISPOSITIONS.index('USER_CANCELLATION')

        shutil.copyfile(os.path.join(self.datRoot, 'file4_analysis.dat'),
                        os.path.join(self.testDir, 'file4_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'))
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file4_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)
        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS)) == \
            len(set(analysisFile.columnNames()))
        assert len(analysisFile['EPOCH_TIME']) is 1

        assert int(float(analysisFile['DISPOSITION'][0])) == \
            PeakAnalyzer.DISPOSITIONS.index('USER_CANCELLATION')
