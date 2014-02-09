"""
Copyright 2012 Picarro Inc.

Helper RPC server that responds to some driver requests to support the
MobileKit tests.
"""

import optparse

from Host.Common import CmdFIFO
from Host.Common import SharedTypes


class DriverEmulatorServer(object):

    def __init__(self, options):
        self.useEmptyId = options.useEmptyId

        self.rpcServer = CmdFIFO.CmdFIFOServer(
            ('', SharedTypes.RPC_PORT_DRIVER_EMULATOR),
            ServerName='TestHelperDriverEmulatorServer',
            ServerDescription=('Host test helper that responds to some driver '

          'requests.'))
        self.rpcServer.register_function(self.RPC_fetchLogicEEPROM, NameSlice=4)

    def RPC_fetchLogicEEPROM(self):
        if self.useEmptyId:
            eeprom = { 'Analyzer' : '', 'AnalyzerNum' : '' }
        else:
            eeprom = { 'Analyzer' : 'TEST', 'AnalyzerNum' : '23' }

        return (eeprom, 0)

    def run(self):
        self.rpcServer.serve_forever()


def main(options):
    DriverEmulatorServer(options).run()


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--empty-id', action='store_true', dest='useEmptyId',
                      help='Cause the Driver to return an empty Id.')
    options, _ = parser.parse_args()

    main(options)
