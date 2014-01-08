"""
Copyright 2013, Picarro Inc.

Kills the RestartSupervisor the safe way.
"""

import sys
import time
from datetime import datetime

from Pyro import errors

from Host.Common import CmdFIFO
from Host.Common import SharedTypes
from Host.Common import EventManagerProxy


APP_NAME = 'KillRestartSupervisor'
TIMEOUT_SECS = 30.0 * 60.0
SAFE_DAS_TEMP = 20.0


if __name__ == '__main__':
    EventManagerProxy.EventManagerProxy_Init(APP_NAME, DontCareConnection=True)


    EventManagerProxy.Log('Preparing to kill restart supervisor.')

    restartSupervisor = CmdFIFO.CmdFIFOServerProxy(
        "http://localhost:%d" % SharedTypes.RPC_PORT_RESTART_SUPERVISOR,
        APP_NAME,
        IsDontCareConnection=False)
    driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER, APP_NAME,
                                        IsDontCareConnection=False)

    start = datetime.now()

    while (datetime.now() - start).seconds < TIMEOUT_SECS:
        EventManagerProxy.Log('Waiting for DAS temperature to stabilize')

        dasTemp = driver.rdDasReg("DAS_TEMPERATURE_REGISTER")
        if dasTemp >= SAFE_DAS_TEMP:
            try:
                restartSupervisor.Terminate()

            except errors.ProtocolError:
                # This error is expected since the process termination
                # prevents us from getting a successful response from the
                # RestartSupervisor.
                pass

            EventManagerProxy.Log('Restart supervisor stopped.')
            sys.exit(1)

        time.sleep(1.0)

    EventManagerProxy.Log("DAS temperature did not stabilize after %s minutes. "
                          "Abandoing RestartSupervisor kill." % TIMEOUT_SECS)
