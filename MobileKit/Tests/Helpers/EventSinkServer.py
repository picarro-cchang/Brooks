"""
Copyright 2013 Picarro Inc.
"""

from Host.Common import CmdFIFO
from Host.Common import SharedTypes


class EventSinkServer(object):

    def __init__(self):
        self.events = []

        # Do not run at the same time as the EventManager
        self.rpcServer = CmdFIFO.CmdFIFOServer(('', SharedTypes.RPC_PORT_LOGGER),
                                               ServerName='TestHelperEventSinkServer',
                                               ServerDescription='Host test helper that receives log events')
        self.rpcServer.register_function(self.RPC_LogEvent, NameSlice=4)

    def run(self):
        self.rpcServer.serve_forever()

    def stop(self):
        self.rpcServer.Stop()

    def __len__(self):
        return len(self.events)
        
    def __getitem__(self, idx):
        return self.events[idx]

    def RPC_LogEvent(self, *args):
        self.events.append(args)

