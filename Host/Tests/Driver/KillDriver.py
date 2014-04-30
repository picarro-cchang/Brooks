"""
Kill driver periodically to check operation of restart mechanism
Copyright 2014 Picarro Inc
"""
import random
import subprocess
import time
from os import path

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

EventManagerProxy_Init("KillDriver")

root = path.abspath(path.dirname(__file__))
subprocess.Popen(['python', path.join(root, '..', '..', 'EventManager', 'EventManager.py'), '-v', 
                            '-c', path.join(root, 'EventManager.ini')])

attempts = 0
while True:
    attempts += 1
    subprocess.Popen(['python', path.join(root, '..', '..', 'Driver', 'Driver.py'), '-c',
                                path.join(root, 'driver.ini')])
    Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%s" % RPC_PORT_DRIVER,
                                             'DriverRPCTests',
                                             IsDontCareConnection=False)
    time.sleep(20)
    print Driver.allVersions()
    Driver.CmdFIFO.StopServer()
    wait = 30.0*random.random()
    msg = "Completed attempt %d, waiting for %.1f s" % (attempts, wait)
    print msg
    Log(msg)
    time.sleep(wait)
    