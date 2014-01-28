"""
Copyright 2014 Picarro Inc
"""

import subprocess
from os import path

from Host.Common import CmdFIFO
from Host.Common import SharedTypes


class DriverRPCTests(object):

    def setup_method(self, m):
        root = path.abspath(path.dirname(__file__))
        subprocess.check_call(['python', path.join(root, '..', '..', 'Supervisor', 'Supervisor.py'),
                               path.join(root, 'data', 'supervisor_driver.ini')])
        self.driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%s" % SharedTypes.RPC_PORT_DRIVER,
                                                 'DriverRPCTests',
                                                 IsDontCareConnection=False)

    def teardown_method(self, ):
        self.driver = None
        supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%s" % SharedTypes.RPC_PORT_SUPERVISOR,
                                                'DriverRPCTests',
                                                IsDontCareConnection=False)


    def testAllVersions(self):
        keys = ['interface', 'host release', 'host version id', 'host version no', 'src version id', 'src version no',
                'config - app version no', 'config - instr version no', 'config - common version no']

        versions = self.driver.allVersions()
        for k in keys:
            assert k in versions



