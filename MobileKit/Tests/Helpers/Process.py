"""
Copyright 2013 Picarro Inc.
"""

import time
from datetime import datetime

import psutil


class ProcessLaunchError(Exception):
    pass

class ProcessKillError(Exception):
    pass


class ProcessHelpers(object):

    @staticmethod
    def waitForLaunch(process, test, timeout):
        """
        Wait for the specified process to launch as determined by the test
        function.
        """

        assert isinstance(process, psutil.Process)

        start = datetime.today()
        while (datetime.today() - start).seconds < timeout:
            if process.is_running() and test():
                return

        raise ProcessLaunchError("Timeout after '%s' seconds waiting for "
                                 "launch" % timeout)

    @staticmethod
    def waitForKill(process, timeout):
        """
        Wait for the specified process to finish being killed.
        """

        assert isinstance(process, psutil.Process)

        start = datetime.today()
        while (datetime.today() - start).seconds < timeout:
            if not process.is_running():
                return

        raise ProcessKillError("Timeout after '%s' seconds waiting for "
                                 "kill" % timeout)
