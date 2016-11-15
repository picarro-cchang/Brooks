# Utility to listen to container in order to receive shutdown command

import subprocess32 as subprocess
import time

from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.SharedTypes import RPC_PORT_CONTAINER

def getHostIp():
    """Within a docker container, get the IP of the host (for bridge networking)"""
    for line in subprocess.check_output(["netstat", "-nr"]).split("\n"):
        if line.startswith('0.0.0.0'):
            return line.split()[1]

hostIp = getHostIp()

ContainerServer = CmdFIFOServerProxy(
    "http://%s:%d" % (hostIp, RPC_PORT_CONTAINER), 
    "Container Client", IsDontCareConnection=False)

# Shut down container and analyzer
print "Sending shutdown command"
ContainerServer.shutdown()
while True:
    time.sleep(1.0)
