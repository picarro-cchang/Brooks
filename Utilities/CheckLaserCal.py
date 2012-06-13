#
#  Copyright (c) 2011-2012 Picarro, Inc. All rights reserved
#

"""
Checks the laser calibration using the specified .wlm file and
computes a laser temperature offset whic is applied to the initial WLM
calibration to create a modified set of wavenumber to
temperature/temperature to wavenumber coefficients for the warm box
.ini file.
"""

import os
import traceback
import shutil
import time
from Queue import Queue, Empty
from optparse import OptionParser

from numpy import sqrt, linalg, array, dot, unwrap, sin, cos, arctan2

# Special module with way too many items to worry about importing
# individually.
#pylint: disable=W0401,W0614
from Host.autogen.interface import *
#pylint: enable=W0401,W0614
from Host.Common import CmdFIFO, SharedTypes
from Host.Common.Listener import Listener
from Host.Common.EventManagerProxy import EventManagerProxy_Init
from Host.Common.WlmCalUtilities import AutoCal, WlmFile
from Host.Common.Averager import Averager
from Host.Common.CustomConfigObj import CustomConfigObj
from TemperatureScanData import TemperatureScanData


class CheckLaserCal(object):
    """
    Logic for driving the laser calibration process.
    """

    LASER_TEMPERATURE_WAIT_S = 3.5

    def __init__(self, opts):
        self.opts = opts

        if self.opts.aLaserNum <= 0 or self.opts.aLaserNum > MAX_LASERS:
            raise ValueError("Laser number must be in range 1..%d." %
                             MAX_LASERS)

        if not os.path.exists(opts.wlmFilename):
            raise ValueError("WLM calibration file %s does not exist." %
                             opts.wlmFilename)

        if self.opts.waitTime < 0.0:
            raise ValueError("Negative wait time %f minutes is invalid." %
                             self.opts.waitTime)

        if not os.path.exists(self.opts.wbFilename):
            raise ValueError("WB calibration file '%s' does not exist." %
                             self.opts.wbFilename)

        self.wlmFile = WlmFile(file(opts.wlmFilename, 'r'))

        self.driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" %
                                                 SharedTypes.RPC_PORT_DRIVER,
                                                 "CheckLaserCal")

        self.measured = TemperatureScanData()
        self.ref = TemperatureScanData()

        # Define a queue for the sensor stream data
        self.queue = Queue(0)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0
        self.tempTol = 0.01
        self.cachedResult = None
        self.listener = Listener(self.queue,
                                 SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                                 SensorEntryType, self.streamFilter)

    def flushQueue(self):
        while True:
            try:
                self.queue.get(False)
                continue
            except Empty:
                break

    def streamFilter(self, result):
        """
        This filter is designed to enqueue sensor entries which all
        have the same timestamp.  A 3-ple consisting of the timestamp,
        a dictionary of sensor data at that time and a dictionary of
        the most current sensor data as of that time is placed on the
        listener queue. The dictionary is keyed by the stream name
        (e.g. STREAM_Laser1Temp gives the key "Laser1Temp" obtained by
        starting from the 7'th character in the stream index) A state
        machine is used to cache the first sample that occure at a new
        time and to return the dictionary collected at the last time.
        """
        types = STREAM_MemberTypeDict

        self.latestDict[types[result.streamNum][7:]] = result.value

        if self.streamFilterState == "RETURNED_RESULT":
            self.lastTime = self.cachedResult.timestamp
            self.resultDict = {
                types[self.cachedResult.streamNum][7:]: self.cachedResult.value
                }

        if result.timestamp != self.lastTime:
            self.cachedResult = SensorEntryType(result.timestamp,
                                                result.streamNum, result.value)
            self.streamFilterState = "RETURNED_RESULT"
            if self.resultDict:
                return (self.lastTime, self.resultDict.copy(),
                        self.latestDict.copy())
            else:
                return
        else:
            self.resultDict[types[result.streamNum][7:]] = result.value
            self.streamFilterState = "COLLECTING_DATA"

    def run(self):
        self.doTemperatureScan()

        # Do a sanity check scan verifying that the current
        # min./max. ratio ranges are within the previous WLM ranges.
        for i in [0, 1]:
            measuredMin = self.measured.min()[i]
            refMin = self.ref.min()[i]

            if abs(measuredMin - refMin) > self.opts.ratioTol * refMin:
                print "Ratio%d minimum invalid: %0.3f (ref: %0.3f)" % \
                    (i + 1, measuredMin, refMin)

            measuredMax = self.measured.max()[i]
            refMax = self.measured.max()[i]

            if abs(measuredMax - refMax) > self.opts.ratioTol * refMax:
                print "Ratio%d maximum invalid: %0.3f (ref: %0.3f)" % \
                    (i + 1, measuredMax, refMax)

        # Compute least squares fit to both sets of data. However, we
        # constrain the fits to share the same slope, which requires a
        # slightly more complex solution.
        #
        # We want to solve the system:
        # y = mx + c1
        # z = mx' + c2
        # where y = measured theta, z = reference theta, x = measured
        # laser temperature and x' = laser temperature for reference data.
        aTa = array([[sum([x ** 2 for x in self.measured.temps]) +
                      sum([x ** 2 for x in self.ref.temps]),
                      sum([x for x in self.measured.temps]),
                      sum([x for x in self.ref.temps])],
                     [sum([x for x in self.measured.temps]),
                      len(self.measured.temps), 0],
                     [sum([x for x in self.ref.temps]), 0,
                      len(self.measured.temps)]])

        aTy = array([dot(array(self.measured.temps),
                          array(unwrap(self.measured.thetas))) +
                      dot(array(self.ref.temps),
                          array(unwrap(self.ref.thetas))),
                     sum(unwrap(self.measured.thetas)),
                     sum(unwrap(self.ref.thetas))])

        v = linalg.solve(aTa, aTy)

        m = v[0]
        c1 = v[1]
        c2 = v[2]

        print "Measured:  y = %0.3f * x + %0.3f" % (m, c1)
        print "Reference: z = %0.3f * x + %0.3f" % (m, c2)

        deltaT = (c2 - c1) / m
        print "Calculated temperature offset: %0.3f C" % deltaT

        # Regenerate the W2T/T2W coefficients using the adjusted temperature.
        self.wlmFile.TLaser = array(
            [t + deltaT for t in self.wlmFile.TLaser])
        self.wlmFile.generateWTCoeffs()

        print 'New T2W coefficients:'
        for i, c in enumerate(self.wlmFile.TtoW.coeffs):
            print "T2W_%d = %f" % (i, c)
        print "TEMP_CEN = %f" % self.wlmFile.TtoW.xcen
        print "TEMP_SCALE = %f" % self.wlmFile.TtoW.xscale
        print "TEMP_ERMS = %f" % sqrt(self.wlmFile.TtoW.residual)

        print 'New W2T coefficients:'
        for i, c in enumerate(self.wlmFile.WtoT.coeffs):
            print "W2T_%d = %f" % (i, c)
        print "WAVENUM_CEN = %f" % self.wlmFile.WtoT.xcen
        print "WAVENUM_SCALE = %f" % self.wlmFile.WtoT.xscale
        print "WAVENUM_ERMS = %f" % sqrt(self.wlmFile.WtoT.residual)

        self._updateWarmBoxCalibration()

    def _updateWarmBoxCalibration(self):
        """
        Backup the existing Warm Box calibration and update the T2W
        and W2T coefficients/parameters. Lastly, delete the matching
        _active calibration so it will be recreated.
        """

        wbFilenameBase = os.path.splitext(self.opts.wbFilename)[0]
        wbFilenameBackup = "%s_%s.ini.lcbak" % \
            (wbFilenameBase, time.strftime("%Y%m%d_%H%M%S", time.localtime()))

        shutil.copyfile(self.opts.wbFilename, wbFilenameBackup)
        print "Backed up Warm Box calibration: '%s'" % wbFilenameBackup

        wbFile = CustomConfigObj(self.opts.wbFilename)
        laserSec = wbFile["ACTUAL_LASER_%d" % self.opts.aLaserNum]

        # This is just to be consistent. AFAIK nothing uses this
        # value.
        laserSec['COARSE_CURRENT'] = self.driver.rdDasReg(
            "LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % self.opts.aLaserNum)

        for i, c in enumerate(self.wlmFile.TtoW.coeffs):
            laserSec["T2W_%d" % i] = c
        laserSec['TEMP_CEN'] = self.wlmFile.TtoW.xcen
        laserSec['TEMP_SCALE'] = self.wlmFile.TtoW.xscale
        laserSec['TEMP_ERMS'] = sqrt(self.wlmFile.TtoW.residual)

        for i, c in enumerate(self.wlmFile.WtoT.coeffs):
            laserSec["W2T_%d" % i] = c
        laserSec['WAVENUM_CEN'] = self.wlmFile.WtoT.xcen
        laserSec['WAVENUM_SCALE'] = self.wlmFile.WtoT.xscale
        laserSec['WAVENUM_ERMS'] = sqrt(self.wlmFile.WtoT.residual)

        wbFile.write()
        print "Warm Box calibration '%s' updated." % self.opts.wbFilename

        wbActive = "%s_active.ini" % wbFilenameBase

        try:
            os.remove(wbActive)
        except OSError:
            print "Unable to remove '%s'." % wbActive

    def _laserTemp(self, last):
        """
        Return the temperature of the active laser based on the last set of
        filtered data.
        """

        return last["Laser%dTemp" % self.opts.aLaserNum]

    class WLMConverter(object):

        @staticmethod
        def toTheta(autoCal, r1, r2):
            """
            Convert a pair of ratios into a theta based on the WLM
            calibration.
            """

            var1 = (autoCal.ratio1Scale * (r2 - autoCal.ratio2Center) -
                    autoCal.ratio2Scale * (r1 - autoCal.ratio1Center) *
                    sin(autoCal.wlmPhase))
            var2 = (autoCal.ratio2Scale * (r1 - autoCal.ratio1Center) *
                    cos(autoCal.wlmPhase))
            return arctan2(var1, var2)

    def doTemperatureScan(self):
        """
        Run a scan of the laser across the temperature range specified in the
        WLM file.
        """

        autoCal = AutoCal()
        autoCal.loadFromWlmFile(self.wlmFile)

        try:
            ctx = self.driver.saveRegValues([
                "LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" %
                self.opts.aLaserNum,
                "LASER%d_MANUAL_FINE_CURRENT_REGISTER" % self.opts.aLaserNum,
                ("FPGA_INJECT", "INJECT_CONTROL")])

            if self.opts.waitTime > 0:
                print "Waiting %0.1f minutes..." % self.opts.waitTime
                time.sleep(60.0 * self.opts.waitTime)

            self.driver.selectActualLaser(self.opts.aLaserNum)
            self.driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" %
                            self.opts.aLaserNum, 32768)
            self.driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" %
                            self.opts.aLaserNum, TEMP_CNTRL_EnabledState)

            print "Starting scan (%0.3f - %0.3f C)" % (self.wlmFile.TLaser[0],
                                                       self.wlmFile.TLaser[-1])

            for i in range(len(self.wlmFile.TLaser)):
                laserTargetTemp = self.wlmFile.TLaser[i]
                print "Laser target = %0.3f C" % laserTargetTemp

                self.driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT"
                                     "_REGISTER" % self.opts.aLaserNum,
                                     laserTargetTemp)

                self.flushQueue()

                startTime, current, last = self.queue.get()
                t = startTime
                wait = startTime + self.LASER_TEMPERATURE_WAIT_S

                deltaT = abs(self._laserTemp(last) - laserTargetTemp)

                while t < wait or deltaT > self.tempTol:
                    t, current, last = self.queue.get()
                    deltaT = abs(self._laserTemp(last) - laserTargetTemp)

                print "Actual laser = %.3f C" % self._laserTemp(last)

                # Average at least 1s of data
                ratio1Avg = Averager()
                ratio2Avg = Averager()
                laserTempAvg = Averager()

                startTime, current, last = self.queue.get()
                t = startTime

                while True:
                    try:
                        t, current, last = self.queue.get(False)
                        ratio1Avg.addValue(current.get("Ratio1"))
                        ratio2Avg.addValue(current.get("Ratio2"))
                        laserTempAvg.addValue(current.get("Laser%dTemp" %
                                                          self.opts.aLaserNum))

                    except Empty:
                        if t - startTime < 1000:
                            continue

                        ratio1 = ratio1Avg.getAverage()
                        ratio2 = ratio2Avg.getAverage()
                        laserTemp = laserTempAvg.getAverage()
                        break

                    except:
                        print traceback.format_exc()

                ratio1 /= 32768.0
                ratio2 /= 32768.0

                self.measured.addR1(ratio1)
                self.measured.addR2(ratio2)

                print "ratio1 = %0.3f, ratio2 = %0.3f" % (ratio1, ratio2)

                ratio1Ref = self.wlmFile.Ratio1[i]
                ratio2Ref = self.wlmFile.Ratio2[i]

                self.ref.addR1(ratio1Ref)
                self.ref.addR2(ratio2Ref)

                theta = self.WLMConverter.toTheta(autoCal, ratio1, ratio2)
                thetaRef = self.WLMConverter.toTheta(autoCal, ratio1Ref,
                                                  ratio2Ref)

                print "Theta = %0.3f rad, Theta ref = %0.3f rad" % (theta,
                                                                    thetaRef)

                self.measured.addTemperature(laserTemp)
                self.measured.addTheta(theta)

                self.ref.addTemperature(laserTargetTemp)
                self.ref.addTheta(thetaRef)

        finally:
            self.driver.restoreRegValues(ctx)
            self.driver.startEngine()


def main():
    usage = """
%prog [options]

Checks the current laser calibration against the specified WLM file. The
specified Warm Box calibration file will be updated to use a new computed
temperature offset. (A backup of the previous Warm Box calibration is also
created.)
"""

    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--file', dest='wlmFilename', metavar='WLMFILE',
                      help='Read WLM calibration from WLMFILE')
    parser.add_option('-c', '--cal', dest='wbFilename', metavar='WBFILE',
                      help='Update WBFILE with new W2T/T2W calibration')
    parser.add_option('-a', '--laser', type='int', dest='aLaserNum',
                      help='Actual laser number to scan (starting at 1)')
    parser.add_option('-w', '--wait', dest='waitTime', metavar='TIME',
                      type='float', default=0.0,
                      help='(optional) Time to wait before starting in ' +
                          'minutes')
    parser.add_option('-t', '--tolerance', dest='ratioTol', metavar='TOL',
                      type='float', default=0.1,
                      help='(optional) Allowed tolerance when verifying ' +
                      'that current WLM ratios are within the original ' +
                      'ratios.')

    options, _ = parser.parse_args()

    EventManagerProxy_Init("CheckLaserCal")

    cal = CheckLaserCal(options)
    cal.run()


if __name__ == "__main__":
    main()
