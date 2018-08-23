# Utility to listen to container in order to receive shutdown command

import os
import time
from Host.Common.CmdFIFO import CmdFIFOServer
from Host.Common.SharedTypes import RPC_PORT_CONTAINER


def shutdown():
    print "Stopping container"
    os.system('docker stop picarro_analyzer')
    print "Shutting down in 30s (Ctrl-C to abort)"
    time.sleep(30.0)
    os.system('dbus-send --system --print-reply --dest="org.freedesktop.ConsoleKit" /org/freedesktop/ConsoleKit/Manager org.freedesktop.ConsoleKit.Manager.Stop')


def main():
    print "Server for handling instrument shutdown"
    rpcServer = CmdFIFOServer(("", RPC_PORT_CONTAINER),
                              ServerName="Container",
                              ServerDescription="Server for container requests",
                              threaded=True)
    rpcServer.register_function(shutdown)
    rpcServer.serve_forever()

if __name__ == "__main__":
    main()
