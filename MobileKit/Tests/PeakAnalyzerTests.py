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
from File6Analysis import File6Analysis
from File7Analysis import File7Analysis

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
                                                                '*.dat'),
                                       legacyValveStop=1378852045.0)
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
                                    -32.40,
                                    decimal=2)
        testing.assert_almost_equal(float(analysisFile['UNCERTAINTY'][0]),
                                    0.16,
                                    decimal=2)
        testing.assert_almost_equal(float(analysisFile['REPLAY_MAX'][0]),
                                    12.321,
                                    decimal=3)
        testing.assert_almost_equal(float(analysisFile['REPLAY_LMIN'][0]),
                                    2.366,
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
                                                                '*.dat'),
                                       legacyValveStop=1347068294.0)
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
                                                                '*.dat'),
                                       legacyValveStop=0.0)
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

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file4_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)
        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS)) == \
            len(set(analysisFile.columnNames()))
        assert len(analysisFile['EPOCH_TIME']) is 1

        assert int(float(analysisFile['DISPOSITION'][0])) == \
            PeakAnalyzer.DISPOSITIONS.index('USER_CANCELLATION')

    def testHighUncertainty(self):
        shutil.copyfile(os.path.join(self.datRoot, 'file5_analysis.dat'),
                        os.path.join(self.testDir, 'file5_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'),
                                       legacyValveStop=time.mktime(time.gmtime()))
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file5_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)

        assert len(analysisFile['EPOCH_TIME']) is 2
        assert int(float(analysisFile['DISPOSITION'][0])) == \
            PeakAnalyzer.DISPOSITIONS.index('UNCERTAINTY_OOR')
        assert int(float(analysisFile['DISPOSITION'][1])) == \
            PeakAnalyzer.DISPOSITIONS.index('COMPLETE')

    def testPeakConcentration(self):
        shutil.copyfile(os.path.join(self.datRoot, 'file6_analysis.dat'),
                        os.path.join(self.testDir, 'file6_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'),
                                       legacyValveStop=0.0)
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file6_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)

        assert len(analysisFile['EPOCH_TIME']) is 8
        testing.assert_array_almost_equal(
            File6Analysis.EPOCH_TIME,
            [float(t) for t in analysisFile['EPOCH_TIME']])
        testing.assert_array_almost_equal(
            File6Analysis.DISTANCE,
            [float(d) for d in analysisFile['DISTANCE']])
        testing.assert_array_almost_equal(
            File6Analysis.GPS_ABS_LONG,
            [float(p) for p in analysisFile['GPS_ABS_LONG']])
        testing.assert_array_almost_equal(
            File6Analysis.GPS_ABS_LAT,
            [float(p) for p in analysisFile['GPS_ABS_LAT']])
        testing.assert_array_almost_equal(
            File6Analysis.CONC,
            [float(c) for c in analysisFile['CONC']])
        testing.assert_array_almost_equal(
            File6Analysis.DELTA,
            [float(d) for d in analysisFile['DELTA']])
        testing.assert_array_almost_equal(
            File6Analysis.UNCERTAINTY,
            [float(u) for u in analysisFile['UNCERTAINTY']])
        testing.assert_array_almost_equal(
            File6Analysis.REPLAY_MAX,
            [float(r) for r in analysisFile['REPLAY_MAX']])
        testing.assert_array_almost_equal(
            File6Analysis.REPLAY_LMIN,
            [float(r) for r in analysisFile['REPLAY_LMIN']])
        testing.assert_array_almost_equal(
            File6Analysis.REPLAY_RMIN,
            [float(r) for r in analysisFile['REPLAY_RMIN']])
        testing.assert_array_almost_equal(
            File6Analysis.DISPOSITION,
            [float(d) for d in analysisFile['DISPOSITION']])

    def testDeltaOORAndKeelingSize(self):
        shutil.copyfile(os.path.join(self.datRoot, 'file7_analysis.dat'),
                        os.path.join(self.testDir, 'file7_analysis.dat'))

        pa = PeakAnalyzer.PeakAnalyzer(analyzerId='TEST0000',
                                       listen_path=os.path.join(self.testDir,
                                                                '*.dat'),
                                       legacyValveStop=0.0)
        analyzerThread = threading.Thread(target=pa.run)
        analyzerThread.setDaemon(True)
        analyzerThread.start()

        time.sleep(5.0)

        analysisResults = os.path.join(self.testDir, 'file7_analysis.analysis')
        assert os.path.exists(analysisResults)

        analysisFile = DatFile.DatFile(analysisResults)

        assert len(analysisFile['EPOCH_TIME']) is 7
        testing.assert_array_almost_equal(
            File7Analysis.EPOCH_TIME,
            [float(t) for t in analysisFile['EPOCH_TIME']])
        testing.assert_array_almost_equal(
            File7Analysis.DISTANCE,
            [float(d) for d in analysisFile['DISTANCE']],
            decimal=3)
        testing.assert_array_almost_equal(
            File7Analysis.GPS_ABS_LONG,
            [float(p) for p in analysisFile['GPS_ABS_LONG']])
        testing.assert_array_almost_equal(
            File7Analysis.GPS_ABS_LAT,
            [float(p) for p in analysisFile['GPS_ABS_LAT']])
        testing.assert_array_almost_equal(
            File7Analysis.CONC,
            [float(c) for c in analysisFile['CONC']])
        testing.assert_array_almost_equal(
            File7Analysis.DELTA,
            [float(d) for d in analysisFile['DELTA']])
        testing.assert_array_almost_equal(
            File7Analysis.UNCERTAINTY,
            [float(u) for u in analysisFile['UNCERTAINTY']])
        testing.assert_array_almost_equal(
            File7Analysis.REPLAY_MAX,
            [float(r) for r in analysisFile['REPLAY_MAX']])
        testing.assert_array_almost_equal(
            File7Analysis.REPLAY_LMIN,
            [float(r) for r in analysisFile['REPLAY_LMIN']])
        testing.assert_array_almost_equal(
            File7Analysis.REPLAY_RMIN,
            [float(r) for r in analysisFile['REPLAY_RMIN']])
        testing.assert_array_almost_equal(
            File7Analysis.DISPOSITION,
            [float(d) for d in analysisFile['DISPOSITION']])
