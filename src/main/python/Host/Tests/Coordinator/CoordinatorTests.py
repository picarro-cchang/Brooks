"""
Copyright 2012 Picarro Inc.
"""

import os
import time
import glob
import shutil
import subprocess
import os.path

import psutil
import pywinauto


class TestCoordinator(object):

    TEST_OUTPUT_DIR = os.path.join('.', 'Output')

    def setup_method(self, m):
        if os.path.isdir(TestCoordinator.TEST_OUTPUT_DIR):
            shutil.rmtree(TestCoordinator.TEST_OUTPUT_DIR)

        os.makedirs(TestCoordinator.TEST_OUTPUT_DIR)

    def testUserEditableParamsInHeader(self):
        coord = psutil.Process(subprocess.Popen(
                ['python',
                 os.path.join('..', '..', 'Coordinator', 'Coordinator.py'),
                 '-c', 'CoordinatorTest.ini']).pid)

        # Wait for the window to launch
        time.sleep(3.0)

        # Auto-generated from swapy.
        pwa_app = pywinauto.application.Application()
        w_handle = pywinauto.findwindows.find_windows(
            title=u'User Editable Parameters', class_name='#32770')[0]
        window = pwa_app.window_(handle=w_handle)
        window.SetFocus()
        ctrl = window['OK']
        ctrl.Click()

        # Test is supposed to take 10 seconds. Wait a little extra.
        time.sleep(15.0)
        coord.kill()

        csvFiles = glob.glob('Output/*.csv')
        assert len(csvFiles) == 1

        logFiles = glob.glob('Output/*.txt')
        assert len(logFiles) == 1

        with open(csvFiles[0], 'r') as csvFp:
            lines = csvFp.readlines()

        assert lines[0].strip() == '# (Test Parameter 1) TestParam1=1'
        assert lines[1].strip() == '# (Test Parameter 2) TestParam2=2'
        assert lines[2].strip() == 'Index,Random Value'

        # Check for repeated lines
        prevLine = ''
        for line in lines:
            assert line != prevLine
            prevLine = line

    def testNoUserEditableParamsInHeader(self):
        coord = psutil.Process(subprocess.Popen(
                ['python',
                 os.path.join('..', '..', 'Coordinator', 'Coordinator.py'),
                 '-c', 'CoordinatorTestNoHeader.ini']).pid)

        # Wait for the window to launch
        time.sleep(3.0)

        # Auto-generated from swapy.
        pwa_app = pywinauto.application.Application()
        w_handle = pywinauto.findwindows.find_windows(
            title=u'User Editable Parameters', class_name='#32770')[0]
        window = pwa_app.window_(handle=w_handle)
        window.SetFocus()
        ctrl = window['OK']
        ctrl.Click()

        # Test is supposed to take 10 seconds. Wait a little extra.
        time.sleep(15.0)
        coord.kill()

        csvFiles = glob.glob('Output/*.csv')
        assert len(csvFiles) == 1

        logFiles = glob.glob('Output/*.txt')
        assert len(logFiles) == 1

        with open(csvFiles[0], 'r') as csvFp:
            lines = csvFp.readlines()

        assert lines[0].strip() == 'Index,Random Value'

        # Check for repeated lines
        prevLine = ''
        for line in lines:
            assert line != prevLine
            prevLine = line