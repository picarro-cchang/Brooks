# BroadcastToDataLogger.py
#
# This application broadcasts data from the file collected by InputListener.py
# to emulate a live instrument. Current version makes a single pass through the
# file and exits. To make multiple passes, it will need to change the timestamp
# data to the current time before passing the data long.
#
# The input filename is hard-coded, where "__main__" is handled near the bottom
# of this file. It must match the filename in InputListener.py.
# 
# The Config subfolder contains an example stripped down Supervisor config file.
# Paths are relative so they should work as long as the structure of this
# source code doesn't change.
#
# Run the supervisor from sources using the following command (cd to the Host\Supervisor
# folder containing Supervisor.py):
#   > Supervisor.py -c ..\Tests\DataLogger\Config\Supervisor.ini

import time
import cPickle
from Queue import Queue

from optparse import OptionParser

from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster, timestamp
from Host.Common.SharedTypes import BROADCAST_PORT_DATA_MANAGER, \
                                    STATUS_PORT_ALARM_SYSTEM, STATUS_PORT_INST_MANAGER
#from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.MeasData import MeasData
from Host.Common.AppStatus import STREAM_Status
from Host.Common.InstErrors import *
from Host.Common.parsePeriphIntrfConfig import parsePeriphIntrfConfig
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log

APP_NAME = "BroadcastToDataLogger"

EventManagerProxy_Init(APP_NAME)


class BroadcastToDataLogger(object):
    def __init__(self, filename, delay, dataMgrUseCurTime=True, fileWrap=True):
        self.DataBroadcaster = Broadcaster.Broadcaster(BROADCAST_PORT_DATA_MANAGER, APP_NAME, logFunc=Log)
        self.AlarmBroadcaster = Broadcaster.Broadcaster(STATUS_PORT_ALARM_SYSTEM, APP_NAME, logFunc=Log)
        self.InstrBroadcaster = Broadcaster.Broadcaster(STATUS_PORT_INST_MANAGER, APP_NAME, logFunc=Log)
        self.filename = filename
        self.delay = delay
        self.dataMgrUseCurTime = dataMgrUseCurTime
        self.fileWrap = fileWrap 
        
    def playback(self):
        with open(self.filename, "rb") as f:
            timeDiff = 0.0

            while True:
                if self.delay > 0:
                    time.sleep(self.delay)
                try:
                    app, data = cPickle.load(f)
                    #print app

                    if app == "DataMgr":
                        if self.dataMgrUseCurTime is True:
                            # adjust the timestamp to the current time
                            curTime = time.time()
                            dataTime = data["time"]

                            # compute difference to use
                            if timeDiff == 0.0:
                                timeDiff = curTime - dataTime

                            newDataTime = dataTime + timeDiff

                            # clamp the timestamp so not later than the current time
                            if newDataTime > curTime:
                                #print "clamping to current time, computed=", newDataTime, "current=", curTime
                                newDataTime = curTime

                            data["time"] = newDataTime

                        # broadcast the data
                        self.DataBroadcaster.send(StringPickler.PackArbitraryObject(data))

                    elif app == "AlarmSys":
                        print "AlarmSys"
                        print data
                        print "********"
                        self.AlarmBroadcaster.send(StringPickler.ObjAsString(data))

                    elif app == "InstrMgr":
                        self.InstrBroadcaster.send(StringPickler.ObjAsString(data))

                except EOFError:
                    print "reached EOF"

                    if self.fileWrap is True:
                        # wrapping file flag set, reset file pointer to beginning of the file
                        print "resetting to beginning of file"
                        f.seek(0)

                        # must reset so associated time is correct
                        timeDiff = 0.0
                    else:
                        # not wrapping, done
                        break


def main():
    usage = """
%prog [options]

Broadcast data captured by the InputListener app.
"""
    parser = OptionParser(usage=usage)

    parser.add_option('--delay', dest='delay',
                      default="0.25", help=('Delay between samples, in seconds (default=0.25).'))

    parser.add_option('-f', '--filename', dest='filename',
                      default="C:/temp/CFIDS2085_20140409.dat", help=('Filename containing data captured by InputListener.'))

    options, _ = parser.parse_args()

    print options

    delay = float(options.delay)
    filename = options.filename

    if filename is "":
        filename = "C:/temp/CFIDS2085_20140409.dat"

    bl = BroadcastToDataLogger(filename, delay)
    bl.playback()

if __name__ == "__main__":
    main()

