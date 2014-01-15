"""
Copyright 2013, Picarro Inc.

Kills the RestartSupervisor the safe way.
"""

from Pyro import errors

from Host.Common import CmdFIFO
from Host.Common import SharedTypes
from Host.Common import EventManagerProxy


APP_NAME = 'KillRestartSupervisor'


if __name__ == '__main__':
    EventManagerProxy.EventManagerProxy_Init(APP_NAME, DontCareConnection=True)


    EventManagerProxy.Log('Preparing to kill restart supervisor.')

    restartSupervisor = CmdFIFO.CmdFIFOServerProxy(
        "http://localhost:%d" % SharedTypes.RPC_PORT_RESTART_SUPERVISOR,
        APP_NAME,
        IsDontCareConnection=False)

    try:
        restartSupervisor.Terminate()

    except errors.ProtocolError:
        # This error is expected since the process termination
        # prevents us from getting a successful response from the
        # RestartSupervisor.
        pass

    EventManagerProxy.Log('Restart supervisor stopped.')
