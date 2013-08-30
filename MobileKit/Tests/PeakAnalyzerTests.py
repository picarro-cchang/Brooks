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
        'REPLAY_RMIN']

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

        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS) -
                   set(analysisFile.columnNames())) is 0
        assert len(analysisFile['EPOCH_TIME']) is 8

        for f in TestPeakAnalyzer.ANALYSIS_FIELDS:
            # Ideally we should track a tolerance per-column. I settled on
            # the tightest tolerance in lieu of that.
            testing.assert_allclose(File1Analysis.COLUMNS[f],
                                    [float(x) for x in analysisFile[f]],
                                    0.001)

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
        assert len(set(TestPeakAnalyzer.ANALYSIS_FIELDS) -
                   set(analysisFile.columnNames())) is 0
        assert len(analysisFile['EPOCH_TIME']) is 0
