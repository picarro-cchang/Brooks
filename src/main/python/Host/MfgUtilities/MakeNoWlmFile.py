#!/usr/bin/python
#
# FILE:
#   MakeNoWlmFile.py
#
# DESCRIPTION:
#   Create laser calibration information by scanning laser temperature and reading wavemeter
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   5-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import sys
import getopt
import os
from Queue import Queue, Empty
import serial
import socket
import time

from Host.MfgUtilities.BurleighReply import BurleighReply
from Host.MfgUtilities.WavemeterTelnetClient import WavemeterTelnetClient
from configobj import ConfigObj
from Host.autogen.interface import *
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

if hasattr(sys, "frozen"):  #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

EventManagerProxy_Init("MakeWlmFile1")


class DriverProxy(SharedTypes.Singleton):
    """Encapsulates access to the Driver via RPC calls"""
    initialized = False

    def __init__(self):
        if not self.initialized:
            self.hostaddr = "localhost"
            self.myaddr = socket.gethostbyname(socket.gethostname())
            serverURI = "http://%s:%d" % (self.hostaddr, SharedTypes.RPC_PORT_DRIVER)
            self.rpc = CmdFIFO.CmdFIFOServerProxy(serverURI, ClientName="MakeWlmFile1")
            self.initialized = True


# For convenience in calling driver functions
Driver = DriverProxy().rpc


class Averager(object):
    # Averages non-None values added to it
    def __init__(self):
        self.total = 0
        self.count = 0

    def addValue(self, value):
        if value is not None:
            self.total += value
            self.count += 1

    def getAverage(self):
        if self.count != 0:
            return self.total / self.count
        else:
            raise ValueError, "No values to average"


class WlmFileMaker(object):
    freqQuery = {"WA-7000": "READ:SCAL:FREQ?\n", "WA-7600": "READ:SCAL:FREQ?\n", "228A": "READ:FREQ?\n"}

    def __init__(self, configFile, options):
        self.config = ConfigObj(configFile)
        self.port = 'COM1'
        self.ipAddr = None

        if "-a" in options:
            self.ipAddr = options["-a"]
        elif "IP_ADDR" in self.config["SETTINGS"]:
            self.ipAddr = self.config["SETTINGS"]["IP_ADDR"]

        if "-l" in options:
            self.laserNum = int(options["-l"])
        else:
            self.laserNum = int(self.config["SETTINGS"]["LASER"])
        if self.laserNum <= 0 or self.laserNum > MAX_LASERS:
            raise ValueError("LASER must be in range 1..4")

        if "-f" in options:
            fname = options["-f"]
        else:
            fname = self.config["SETTINGS"]["FILENAME"]
        self.fname = fname.strip() + ".nowlm"
        self.fp = file(self.fname, "w")

        if "-w" in options:
            self.waitTime = float(options["-w"])
        else:
            self.waitTime = float(self.config["SETTINGS"]["WAIT_TIME"])
        if self.waitTime < 0:
            raise ValueError("Negative WAIT_TIME is invalid")

        if "-i" in options:
            self.coarseCurrent = int(options["-i"])
        else:
            self.coarseCurrent = float(self.config["SETTINGS"]["LASER_CURRENT"])
        if self.coarseCurrent < 0 or self.coarseCurrent >= 65536:
            raise ValueError("LASER_CURRENT must be in range 0..65535")

        if "-p" in options:
            self.port = options["-p"]
        else:
            self.port = self.config["SETTINGS"].get("COM_PORT", self.port)

        if "--min" in options:
            self.tempMin = float(options["--min"])
        else:
            self.tempMin = float(self.config["SETTINGS"]["TEMP_MIN"])
        if self.tempMin < 3.0 or self.tempMin >= 55.0:
            raise ValueError("TEMP_MIN must be in range 3.0 to 55.0")

        if "--max" in options:
            self.tempMax = float(options["--max"])
        else:
            self.tempMax = float(self.config["SETTINGS"]["TEMP_MAX"])
        if self.tempMax < 3.0 or self.tempMax > 55.0:
            raise ValueError("TEMP_MAX must be in range 3.0 to 55.0")

        if "--step" in options:
            self.tempStep = float(options["--step"])
        else:
            self.tempStep = float(self.config["SETTINGS"]["TEMP_STEP"])
        if self.tempStep < 0.01 or self.tempStep > 10.0:
            raise ValueError("TEMP_STEP must be in range 0.01 to 10.0")

        if "--tol" in options:
            self.tempTol = float(options["--tol"])
        else:
            self.tempTol = float(self.config["SETTINGS"]["TEMP_TOLERANCE"])
        if self.tempTol < 0.001 or self.tempTol > 0.1:
            raise ValueError("TEMP_TOLERANCE must be in range 0.001 to 0.1")

        self.simulation = False
        if "--sim" in options or "SIMULATION" in self.config:
            self.simulation = True
            if "--wmin" in options:
                self.simWmin = float(options["--wmin"])
            else:
                self.simWmin = float(self.config["SIMULATION"]["WAVENUM_MINTEMP"])
            if "--wmax" in options:
                self.simWmax = float(options["--wmax"])
            else:
                self.simWmax = float(self.config["SIMULATION"]["WAVENUM_MAXTEMP"])

        # Define a queue for the sensor stream data
        self.queue = Queue(0)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0

        self.listener = Listener(self.queue, SharedTypes.BROADCAST_PORT_SENSORSTREAM, SensorEntryType, self.streamFilter)

        # Open serial port or TCP connection to wavemeter for non-blocking read
        if self.ipAddr is None:
            try:
                self.ser = serial.Serial(self.port, 19200, timeout=0)
                self.wavemeter = BurleighReply(self.ser, 0.02)
            except:
                raise Exception("Cannot open serial port - aborting")
        else:
            try:
                self.wavemeter = WavemeterTelnetClient(self.ipAddr, 1.0)
            except:
                raise Exception("Cannot open TCP connection to %s, Aborting." % self.ipAddr)
        self.serialTimeout = 10.0

    def WaitForString(self, timeout, msg=""):
        tWait = 0
        while tWait < timeout:
            reply = self.wavemeter.GetString().strip()
            if reply != "":
                # print "Reply >%s<" % (list(reply),)
                return reply
            time.sleep(0.5)
            tWait += 0.5
        else:
            raise IOError(msg)

    def readWavenumber(self):
        while True:
            self.wavemeter.PutString(self.freqQuery[self.model])
            try:
                reply = self.WaitForString(self.serialTimeout, "Timeout waiting for response to READ command")
                # N.B. Sunnyvale Burleigh and Bristol read out frequencies in THz
                waveno = float(reply) / 0.0299792458
                return waveno
            except IOError:
                print "COMMS timeout, trying again"
                pass  # Try again

    def flushQueue(self):
        while True:
            try:
                self.queue.get(False)
                continue
            except Empty:
                break

    def streamFilter(self, result):
        # This filter is designed to enqueue sensor entries which all have the same timestamp.
        #  A 3-ple consisting of the timestamp, a dictionary of sensor data at that time
        #  and a dictionary of the most current sensor data as of that time
        #  is placed on the listener queue. The dictionary is keyed by the stream name
        #  (e.g. STREAM_Laser1Temp gives the key "Laser1Temp" obtained by starting from the 7'th
        #  character in the stream index)
        #  A state machine is used to cache the first sample that occure at a new time and to
        #  return the dictionary collected at the last time.
        self.latestDict[STREAM_MemberTypeDict[result.streamNum][7:]] = result.value

        if self.streamFilterState == "RETURNED_RESULT":
            self.lastTime = self.cachedResult.timestamp
            self.resultDict = {STREAM_MemberTypeDict[self.cachedResult.streamNum][7:]: self.cachedResult.value}

        if result.timestamp != self.lastTime:
            self.cachedResult = SensorEntryType(result.timestamp, result.streamNum, result.value)
            self.streamFilterState = "RETURNED_RESULT"
            if self.resultDict:
                return self.lastTime, self.resultDict.copy(), self.latestDict.copy()
            else:
                return
        else:
            self.resultDict[STREAM_MemberTypeDict[result.streamNum][7:]] = result.value
            self.streamFilterState = "COLLECTING_DATA"

    def run(self):
        # Check that the driver can communicate
        try:
            print "Driver version: %s" % Driver.allVersions()
        except:
            raise ValueError, "Cannot communicate with driver, aborting"

        if not self.simulation:
            print "Asking wavemeter for identification"
            self.wavemeter.PutString("\n")
            time.sleep(1.0)
            self.wavemeter.PutString("*IDN?\n")
            reply = self.WaitForString(self.serialTimeout, "Timeout waiting for response to *IDN?")
            print "Wavemeter id: %s" % reply
            if "WA-7000" in reply:
                self.model = "WA-7000"
            elif "WA-7600" in reply:
                self.model = "WA-7600"
            elif "228A" in reply:
                self.model = "228A"
            else:
                raise ValueError, "Unrecognized wavemeter model"
        else:
            print "Using simulation mode for wavemeter"

        try:
            regVault = Driver.saveRegValues([
                "LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum,
                "LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.laserNum,
                "LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.laserNum, ("FPGA_INJECT", "INJECT_CONTROL")
            ])

            if self.waitTime > 0:
                print "Waiting for %.1f minutes" % self.waitTime
                time.sleep(60.0 * self.waitTime)

            self.fp.write("[CRDS Header]\n")
            self.fp.write("FileType=Wavelength Monitor Calibration\n")
            self.fp.write("Filename=%s\n" % self.fname)
            self.fp.write(time.strftime("Date=%Y%m%d\n", time.localtime()))
            self.fp.write(time.strftime("Time=%H%M%S\n", time.localtime()))
            self.fp.write("\n[Parameters]\n")

            # Set up laser current and select the laser
            Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.laserNum, self.coarseCurrent)
            Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.laserNum, 32768)
            Driver.selectActualLaser(self.laserNum)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum, self.tempMin)

            print "Turning off laser, and ensuring no spectrum acquisition is active"
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % self.laserNum, LASER_CURRENT_CNTRL_DisabledState)
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER", SPECT_CNTRL_IdleState)
            # TO DO: Turn off SOA as well
            time.sleep(2.0)

            # Write out offset information to file
            self.fp.write("laser_current=%.2f\n" % self.coarseCurrent)

            tDuration = 20
            print "Turning on laser and waiting for %.1f seconds for stabilization" % tDuration
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" % self.laserNum, LASER_CURRENT_CNTRL_ManualState)

            self.flushQueue()
            tStart, d, last = self.queue.get()
            t = tStart
            ticker = tStart
            while t < tStart + tDuration * 1000:
                if t > ticker + 1000:
                    sys.stderr.write(".")
                    ticker += 1000
                t, d, last = self.queue.get()
            print

            self.fp.write("\n[Data column names]\n")
            self.fp.write("0=Laser temperature\n")
            self.fp.write("1=Wavenumber\n")
            self.fp.write("\n[Data]\n")

            self.tempScan = self.tempMin
            print "Scanning laser temperature from %.3f to %.3f" % (self.tempMin, self.tempMax)
            Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" % self.laserNum, TEMP_CNTRL_EnabledState)

            while self.tempScan <= self.tempMax:
                Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % self.laserNum, self.tempScan)
                # Wait for laser temperature to stabilize
                tWait = 3.5
                self.flushQueue()
                tStart, d, last = self.queue.get()
                t = tStart
                while t < tStart + tWait or abs(last["Laser%dTemp" % self.laserNum] - self.tempScan) > self.tempTol:
                    t, d, last = self.queue.get()

                time.sleep(2.0)
                if self.simulation:
                    waveno = self.simWmin + (self.tempScan - self.tempMin) / (self.tempMax - self.tempMin) * (self.simWmax -
                                                                                                              self.simWmin)
                else:
                    # Read wavemeter twice, first read is to flush any information from before
                    #  the temperature stabilized
                    waveno = self.readWavenumber()
                    waveno = self.readWavenumber()

                # Read the wavelength monitor data
                laserTempAvg = Averager()
                tStart, d, last = self.queue.get()
                t = tStart
                # Average the available information in the queue

                while True:
                    try:
                        t, d, last = self.queue.get(False)
                        laserTempAvg.addValue(d.get("Laser%dTemp" % self.laserNum))
                    except Empty:
                        if t - tStart < 1000: continue
                        laserTemp = laserTempAvg.getAverage()
                        msg = "%9.3f %12.5f" % (laserTemp, waveno)
                        self.fp.write("%s\n" % msg)
                        print msg
                        break
                self.tempScan += self.tempStep
            print "Calibration done, result is in file: %s" % self.fname

        finally:
            if self.fp:
                self.fp.close()
            self.wavemeter.Close()
            Driver.restoreRegValues(regVault)
            Driver.startEngine()


HELP_STRING = """MakeNoWlmFile.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-a                   ip address or host name for TCP communication (overrides serial port)
-c                   specify a config file:  default = "./MakeNoWlmFile.ini"
-f                   name of output file (without extension)
-i                   coarse laser current (digitizer units)
-l                   laser number (1-index)
--max                maximum laser temperature
--min                minimum laser temperature
-p                   communications port
--sim                do not use wavemeter (use --wmin and --wmax to specify wavenumbers at min and max temperatures)
--step               laser temperature step
--tol                laser temperature tolerance
-w                   wait time (in minutes)
--wmin               wavenumber at minimum temperature
--wmax               wavenumber at maximum temperature
"""


def printUsage():
    print HELP_STRING


def handleCommandSwitches():
    shortOpts = 'ha:c:i:l:f:p:w:'
    longOpts = ["help", "min=", "max=", "step=", "tol=", "sim", "wmin=", "wmax="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options.setdefault(o, a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h', "")
    #Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options


if __name__ == "__main__":
    configFile, options = handleCommandSwitches()
    m = WlmFileMaker(configFile, options)
    m.run()
