#!/usr/bin/python
#
"""
File Name: PeriphToZmq.py
Purpose: Utility to listen to serial sockets and send data via ZMQ

File History:
    2013-09-05 sze  Initial version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""

import getopt
import os
import Queue
import sys
import time
import zmq

from Host.PeriphIntrf.PeriphIntrf import PeriphIntrf
import Host.Common.StringPickler as StringPickler
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.parsePeriphIntrfConfig import parsePeriphIntrfConfig

# Set up a useful AppPath reference...
if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

APP_NAME = "PeriphToZmq"
APP_DESCRIPTION = "Sends peripheral data to zmq"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "serial2socket.ini"
BROADCAST_PORT_PERIPH_ZMQ = 45065


class QManager(object):

    def __init__(self, queue):
        self.queue = queue

    def send(self, data):
        self.queue.put(data)


class PeriphToZmq(object):

    def __init__(self, configFile):
        self.context = zmq.Context()
        self.broadcastSock = self.context.socket(zmq.PUB)
        self.broadcastSock.bind("tcp://0.0.0.0:%d" % BROADCAST_PORT_PERIPH_ZMQ)
        self.queue = Queue.Queue()
        self.qManager = QManager(self.queue)
        self.pi = PeriphIntrf(configFile, self.qManager)

    def run(self):
        try:
            while True:
                data = self.queue.get()
                self.broadcastSock.send(data)
        finally:  # Get here on keyboard interrupt or other termination
            self.broadcastSock.close()
            self.context.term()

HELP_STRING = \
    """

PeriphToZmq.py [-h] [-c <FILENAME>] publishes peripheral data to a ZMQ socket

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""


def PrintUsage():
    print HELP_STRING


def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    # assemble a dictionary where the keys are the switches and values are
    # switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    # Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile

if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    p = PeriphToZmq(configFile)
    p.run()