#!/usr/bin/python
from __future__ import print_function

import pdb

import sys
import os
import time
import pprint
import random
import itertools
from datetime import datetime
from copy import copy
from time import sleep
from collections import Counter, deque
from Host.Common.CustomConfigObj import CustomConfigObj


class SingleAlarmMonitor:
    """
    Contains the low/high rule for one alarm sensor.

    The problem:
    When reporting alarm events or degradation of the health of the analyzer we need to
    avoid false alarms and information overload. When the condition is near the transition
    from green to yellow or red the indicator may flicker due to stochastic and temporary
    processes.  This condition is considered noise because in a large control room with
    many systems reporting it because difficult to identify the true urgencies.

    To only report yellow (may need service soon) or red (need service now or operational
    failure) conditions that are "real", a common practice is track the individual alarm
    events and only report a problem if a minimum number events occur in a specified time
    period.  Below is how we implement this idea.

    a) Input raw data. These data come out at irregular intervals depending on the source,
       ini settings, schemes, scripts, etc.  Some data is updated more than once per second
       with irregular spacing, others are only updated every few seconds.  Instead of
       counting individual alarm events and trying to decide if enough have occured, we
       instead bin the data into buckets of a few seconds worth of data.  In this example
       we have data coming at 1Hz and we bin them into 5 second chunks.

    b) Each input data is compared to a specified alarm condition and flagged green, yellow,
       or red.  The first bin has 5 green reports, the last has 4 green and one red.

    c) For each bin find the worst report and save it.

    a) ddddd|ddddd|ddddd|ddddd|ddddd|ddddd|
     t=0     5     10

    b) ggggg|ggggg|ggYgY|RRRgg|ggggg|ggRgg|
     t=0     5     10

    c)   g     g     Y     R     g     R
     t=  0     5     10    15

    """
    def __init__(self, settings=None):

        # How long in time is a bin
        # units are seconds
        self.binInterval = 0.0

        # t_0 for determining if latest data belongs in the current
        # bin or the next one. Set to -1 if t_0 hasn't been set.
        self.binStartTime = -1


        # List that holds the alarm status.  Each element
        # holds a list that can have one or more states.
        # Valid states are LowRed, LowYellow, Green, HighYellow, HighRed.
        # If the rule is populate to check if the value crosses the
        # yellow or red threshold. If it the value is varying alot
        # e.g. swinging between HighRed and LowRed, set both
        # [HighRed, LowRed].
        # If the value is swinging between HighRed and LowYellow,
        # set [HighRed, LowYellow]
        # If the value is swinging between HighRed and HighYellow,
        # only set [HighRed].
        # If neither red or yellow is indicated, the set [Green].
        #
        self.LOW_RED = -2
        self.LOW_YELLOW = -1
        self.GREEN = 0
        self.HIGH_YELLOW = 1
        self.HIGH_RED = 2
        self.NONE = None

        # This is a short accumulator collecting the (approximately) 1Hz data for about
        # ten seconds.  The specific amount to accumulate is set in the ini file with
        # the key "binInterval".
        self.alarmStateAccumulator = [] # collect alarm states for the current bin

        # Accumulate the worst alarm from the alarmStateAccumulator (10s summary) and store
        # 5min worth of results here.  Each datum is about 10s apart.  Once 5 minutes is accumulated,
        # count the alarms in this interval and save the counts in a dict stored in the
        # 5min history array. Each time the data is counted and put into the 5min history array,
        # clear the 5min accumulator.
        # Do the same for 1hr intervals.
        self.fiveMinAccumulator = { "TIME":[], "ALARM_STATE":[] }
        self.sixtyMinAccumulator = { "TIME":[], "ALARM_STATE":[] }
        self.fiveMinHistory = {
                "TIME":[],
                "ALARM_COUNT":[],
                "LED_COLOR":[]
                }
        self.sixtyMinHistory = {
                "TIME":[],
                "ALARM_COUNT":[],
                "LED_COLOR":[]
                }

        # Thresholds for each data input comparison
        #
        self.lowYellowThreshold = 0.0
        self.lowRedThreshold = 0.0
        self.highYellowThreshold = 0.0
        self.highRedThreshold = 0.0

        # Alarm persistence
        #
        # As alarms are accumulated we have to report an alarm to the outside
        # world.  We'll call this the "public alarm".
        #
        # To figure out what alarm to report to the world, we looked at the
        # latest binned alarms in alarmStateBinnedDeque[].  The number of bins
        # too look at is set in the *BinCountWindow var below.  To decide if
        # the public alarm is red, we see if the number of red alarm states
        # seen in the bin count window exceeds redTotalCountThreshold.
        #
        # If the public alarm isn't red, we check for in a similar manner counting
        # the total number of occurances of red AND yellow alarms in the bin
        # count window.
        #
        self.shortBinCountWindow = 0 # will be 5 minutes
        self.longBinCountWindow = 0 # will be 60 minutes
        self.yellowTotalCountThreshold = 0
        self.redTotalCountThreshold = 0
        self.shortPublicAlarm = self.NONE
        self.longPublicAlarm = self.NONE
        self.shortPublicAlarmHistory = []
        self.longPublicAlarmHistory = []

        # name - Human readable name for this alarm.
        # dataSourceKey - The DataManager key for the monitored data source.
        # func - Special alarm functions (TBD). None selects the default function.
        #
        self.name = None
        self.dataSourceKey = None
        self.func = None

        # Override the constructor variable settings with the input from the
        # alarm ini file.
        # The try block tests to see if the input key exists.  This prevents
        # mis-typed keys from creating new variables.
        #
        if settings:
            for key in settings:
                try:
                    getattr(self, key)
                    setattr(self, key, settings[key])
                except AttributeError:
                    raise

        if self.dataSourceKey is None:
            raise AttributeError("dataSourceKey not defined in SingleAlarmMonitor.")


    #-----------------------------------------------------------------------------------
    def setTestState(self):
        """
        Set a basic test state so we don't need to read an ini.
        This test assumes the input data spans 0 - 10.
        """
        self.binInterval = 10.0 # 10 seconds
        self.lowRedThreshold = 1.0
        self.lowYellowThreshold = 2.0
        self.highYellowThreshold = 8.0
        self.highRedThreshold = 9.0

        self.shortBinCountWindow = 10
        self.longBinCountWindow = 30
        self.yellowTotalCountThreshold = 3
        self.redTotalCountThreshold = 3

    def setData(self, timestamp, inputData = None):
        """
        Store the latest data and timestamp for one monitor.
        """

        fiveMinProcessed = False
        sixtyMinProcessed = False

        # Set the current state. Initialize to None incase the filter
        # or input data is broken and we fall through the tests.
        # We assume that all the thresholds are unique and properly
        # ordered.
        #
        # We use inputNone in the situation where we don't have data
        # but the analyzer is working and we want to increment the
        # counter.  The state is set to green because we assume this
        # is a normal/predicted event such as during warm up when not
        # all data streams are yet producing data.
        #
        currentAlarmState = self.NONE
        if inputData is not None:
            if inputData < self.lowRedThreshold:
                currentAlarmState = self.LOW_RED
            elif inputData < self.lowYellowThreshold:
                currentAlarmState = self.LOW_YELLOW
            elif inputData > self.highRedThreshold:
                currentAlarmState = self.HIGH_RED
            elif inputData > self.highYellowThreshold:
                currentAlarmState = self.HIGH_YELLOW
            else:
                currentAlarmState = self.GREEN
        else:
            currentAlarmState = self.GREEN

        # Set in the current bin
        # If the bin is full, process it (get the most severe alarm seen, save it,
        # empty the accumulator, reset the bin start timestamp).
        # If there is no accumulator because this is the first time through, make
        # a new one.
        delta = timestamp - self.binStartTime
        if self.binStartTime < 0 or  timestamp - self.binStartTime >= self.binInterval:
            if self.binStartTime >= 0:
                (fiveMinProcessed, sixtyMinProcessed) = self.processAccumulator()
            self.binStartTime = timestamp
        self.alarmStateAccumulator.append(currentAlarmState)
        return fiveMinProcessed, sixtyMinProcessed, currentAlarmState

    def processAccumulator(self):
        """
        Process a full alarm state accumulator.

        Analyze the accumulated alarm states for a single bin time period.
        The accumulated list contains 0 or more GREEN, YELLOW, and RED alarm
        states.
        If there are any red, report the greatest (low or high) red. If the
        high/low reds are equal, report high red since (I assume) the high alarm
        condition for most parameters are the more critical case.
        If there are no reds, check yellow with the same conditions.
        And if there are no yellow, report green.

        FYI...
        l[:] = [] is the Python2 way to empty a list,
        l = [] instead will rebind and may leave a memory leak

        """
        stateToSave = self.NONE
        if not self.alarmStateAccumulator:
            return

        c = Counter(self.alarmStateAccumulator)

        # Check to see if we have any RED alarms states
        if c[self.LOW_RED] > 0 or c[self.HIGH_RED] > 0:
            if c[self.HIGH_RED] > c[self.LOW_RED]:
                stateToSave = self.HIGH_RED
            elif c[self.LOW_RED] > c[self.HIGH_RED]:
                stateToSave = self.LOW_RED
            else:
                stateToSave = self.HIGH_RED
        # Check to see if we have any YELLOW alarms states
        elif c[self.LOW_YELLOW] > 0 or c[self.HIGH_YELLOW] > 0:
            if c[self.HIGH_YELLOW] > c[self.LOW_YELLOW]:
                stateToSave = self.HIGH_YELLOW
            elif c[self.LOW_YELLOW] > c[self.HIGH_YELLOW]:
                stateToSave = self.LOW_YELLOW
            else:
                stateToSave = self.HIGH_YELLOW
        # No red or yellow seen we must be ok.
        else:
            stateToSave = self.GREEN

        #print("Process accumulator source: %s LED: %s" % (self.dataSourceKey, stateToSave))
        # Save the most severe alarm seen in this time interval.
        self.fiveMinAccumulator["TIME"].append(self.binStartTime)
        self.fiveMinAccumulator["ALARM_STATE"].append(stateToSave)
        self.sixtyMinAccumulator["TIME"].append(self.binStartTime)
        self.sixtyMinAccumulator["ALARM_STATE"].append(stateToSave)

        # Clear out to start looking at alarms in the next time interval.
        self.alarmStateAccumulator[:] = []

        # Update public alarms
        (fiveMinProcessed, sixtyMinProcessed) = self._updatePublicAlarm()
        if False and fiveMinProcessed:
            print("Time: %s" % str(datetime.now()))
            print("History of %s" % self.dataSourceKey)
            print("history 5 count:", self.fiveMinHistory["ALARM_COUNT"])
            print("history 5 state:", self.fiveMinHistory["LED_COLOR"])
        if False and sixtyMinProcessed:
            print("---> Time: %s" % str(datetime.now()))
            print("---> History of %s" % self.dataSourceKey)
            print("---> history 60 count:", self.sixtyMinHistory["ALARM_COUNT"])
            print("---> history 60 state:", self.sixtyMinHistory["LED_COLOR"])

        return (fiveMinProcessed, sixtyMinProcessed)

    def _updatePublicAlarm(self):

        # Return is a tuple.
        # fiveMinProcessed [True|False]
        # sixtyMinProcessed [True|False]
        #
        fiveMinProcessed = False
        sixtyMinProcessed = False

        for outputInterval in ["FiveMin", "SixtyMin"]:
        #for outputInterval in ["SixtyMin"]:
            if outputInterval == "FiveMin":
                accumulator = self.fiveMinAccumulator
                history = self.fiveMinHistory
                binCountWindow = self.shortBinCountWindow
            else:
                accumulator = self.sixtyMinAccumulator
                history = self.sixtyMinHistory
                binCountWindow = self.longBinCountWindow

            if len(accumulator["TIME"]) >= binCountWindow:

                # Use the time stamp of the most recent datum
                time = accumulator["TIME"][-1]

                # c - counter
                # rc - total red state count
                # yc - total yellow state count
                # alarmCount - If the alarm is red, sum of all high & low red alarms. If the alarm
                #      is yellow or green, sum of all high & low red and yellows.  We report alarm
                #      count for green so that we can (hopefully) spot a problem early on.
                #
                alarmColor = self.GREEN
                c = Counter(accumulator["ALARM_STATE"])
                rc = c[self.LOW_RED] + c[self.HIGH_RED]
                yc = c[self.LOW_YELLOW] + c[self.HIGH_YELLOW]
                alarmCount = 0

                if rc >= self.redTotalCountThreshold:
                    alarmCount = rc
                    if c[self.LOW_RED] > c[self.HIGH_RED]:
                        alarmColor = self.LOW_RED
                    else:
                        alarmColor = self.HIGH_RED
                elif rc + yc >= self.yellowTotalCountThreshold:
                    alarmCount = rc + yc
                    if c[self.LOW_YELLOW] > c[self.HIGH_YELLOW]:
                        alarmColor = self.LOW_YELLOW
                    else:
                        alarmColor = self.HIGH_YELLOW
                else:
                    alarmCount = rc + yc
                    alarmColor = self.GREEN


                history["TIME"].append(time)
                history["ALARM_COUNT"].append(alarmCount)
                history["LED_COLOR"].append(alarmColor)

                accumulator["TIME"][:] = []
                accumulator["ALARM_STATE"][:] = []

                if outputInterval == "FiveMin":
                    fiveMinProcessed = True
                if outputInterval == "SixtyMin":
                    sixtyMinProcessed = True

        return (fiveMinProcessed, sixtyMinProcessed)


class AlarmSystemV3:
    """
    Class to manage multiple alarm monitors.  Monitors are stored in alarms dict
    where the keys are the "dataSourceKey" specified in the alarm ini file. The
    dataSourceKey should be a valid DataManager key.

    """
    def __init__(self, iniFile):
        self.alarms = {}
        self.iniFile = iniFile
        settings = self._readIni()
        for sectionKey in settings.keys():
            try:
                a = SingleAlarmMonitor(settings[sectionKey])
                self.alarms[getattr(a, "dataSourceKey")] = a
            except Exception as error:
                raise

    def _readIni(self):
        """
        Read the ini that configures this object.

        [Alarm_Globals]
        binInterval = 10
        shortBinCountWindow = 10
        longBinCountWindow = 30
        yelloTotalCountThreshold = 3
        redTotalCountThreshold = 3
        func = Default

        [Alarm_Test_0]
        name = "Test Alarm 0"
        dataSource = NH3
        lowRedThreshold = 1.0
        lowYellowThreshold = 2.0
        highYellowThreshold = 8.0
        highRedThreshold = 9.0

        [Alarm_Test_1]
        name = "Test Alarm 1"
        dataSource = HCl
        lowRedThreshold = 1.5
        lowYellowThreshold = 2.0
        highYellowThreshold = 7.5
        highRedThreshold = 8.5

        Section "Alarm_Globals" is optional.
        All other section names are freeform and define specific alarms.
        Specific alarm options can override global options for that alarm.
        The options name variables in the class SingleAlarmMonitor so see
        that class's documentation for appropriate values.

        """
        if sys.platform == 'win32':
            # Win7 location for ini files
            pass
        else:
            # Linux paths
            try:
                # harded coded ini location in my dev environment
                #ini = CustomConfigObj(os.path.expanduser('~') + "/git/host/Config/AMADS/AppConfig/Config/DataManager/AlarmSystemV3.ini")
                #ini = CustomConfigObj(os.path.expanduser('~') + "/git/host/Config/CFADS_Simulation/AppConfig/Config/DataManager/AlarmSystemV3.ini")
                #print("IniFile: %s" % self.iniFile)
                ini = CustomConfigObj(self.iniFile)
                ini.ignore_option_case_off()
            except Exception as e:
                print("Exception::", e)
                raise

        # Make a list of ini sections and see if a global settings section
        # exists. If it does, make a dict of its options.
        alarmSections = ini.list_sections()
        alarmGlobals = {}
        if "Alarm_Globals" in alarmSections:
            alarmSections.remove("Alarm_Globals")
            alarmGlobals = dict(ini.list_items("Alarm_Globals"))

        # Go through the remaining sections that define specific alarms.
        # Use the global settings as a start and add new options, overriding
        # any globals that have been previously set.  Use copy() to ensure
        # all alarms have their own settings.
        alarmSettings = {}
        for section in alarmSections:
            settings = copy(alarmGlobals)
            settings.update(dict(ini.list_items(section)))
            alarmSettings[section] = settings

        # Convert all number strings to floats or ints
        for section in alarmSettings:
            for key, value in alarmSettings[section].items():
                try:
                    alarmSettings[section][key] = float(value)
                except:
                    pass
                #print("key value", key, value)

        return alarmSettings

    def updateAllMonitors(self, time, inputDataDict):
        """
        Take data from the DataManager and update all monitors with a key
        that matches a DataManager key. Time is a Unix timestamp.
        """
        fiveMinProcessed = False
        sixtyMinProcessed = False

        listOfAlarmKeys = self.alarms.keys()
        listOfInputDataKeys = inputDataDict.keys()

        # See if there are any keys in common between the input data dict
        # and the list of monitors.  If there aren't, return without any
        # calls to setData() otherwise it will mess up the counters.
        #
        # We end up in this situation in at least two ways.
        # 1) When not in measurement mode, the input dict doesn't have any
        #   keys/value pairs for gas measurements.  If the monitors are
        #   only set for gas concentrations, durning the lengthy warm up
        #   phase there will be a number of setData() calls with no matching
        #   keys.
        # 2) Once in measurment mode, periodically the input dict is missing
        #   the concentration key/value pairs.  Or at least that's what it's
        #   doing in the CFADS simulator.  I don't know if this is a bug or
        #   by design, perhaps related to how the scheme is set.  Either way,
        #   the missing concentrations, when that's all the monitors are set
        #   for, causes errors in the monitor counters.
        #
        sa = set(listOfAlarmKeys)
        sb = set(listOfInputDataKeys)
        c = sa.intersection(sb)
        if not c:
            return False, False

        # If there is at least one input key that matches a monitor key then
        # update the monitor(s). If some keys are missing in the input data,
        # like in the warm up mode where we have keys for pressure and temperature
        # but not gas concentrations, update the monitors with missing keys with
        # fake (harmless) data so that all monitors' counters are in sync.
        #
        latestLedStatus = {}
        try:
            for key, value in inputDataDict.items():
                if key in listOfAlarmKeys:
                    five, sixty, latestLedStatus[key] = self.alarms[key].setData(int(time), value)
                    if five:
                        fiveMinProcessed = True
                    if sixty:
                        sixtyMinProcessed = True
                    listOfAlarmKeys.remove(key)
            # Finish up monitors that didn't have data this time around.
            for key in listOfAlarmKeys:
                self.alarms[key].setData(int(time))
        except KeyError as e:
            print("AlarmSystemV3::updateAllMonitors KeyError", e)
        except Exception as e:
            print("AlarmSystemV3::updateAllMonitors unhandled exception", e)
        return (fiveMinProcessed, sixtyMinProcessed, latestLedStatus)

    def getAllMonitorStatus(self):
        """
        Return single line strings with red, yellow, green status for each key.
        """

        # Go through each alarm and make a single string with the format
        #
        # <timestamp>, color_0, color_1, color_2, etc.
        #
        # Not all data sources start at the same time, e.g. gas concentrations don't
        # report until after warm up, so uninitialized alarms are designated with 'N'.
        # For the timestamp, we just use the first valid time source and ignore small
        # time differences between sources since we are polling the results every
        # few minutes to every few hours.
        #
        # If there is no valid timestamp because the code polls too early, the timestamp
        # is denoted with 'NA'.
        #
        alarmFiveMinList = []
        alarmSixtyMinList = []
        timestamp = "NA"
        latestCodeDict = {}

        def alarmCodeToStr(code):
            str = "G"
            if abs(code) == 2:
                str = "R"
            elif abs(code) == 1:
                str = "Y"
            return str

        try:
            firstTime = True
            for key, value in self.alarms.items():
                #if value.fiveMinHistory["TIME"]:
                #    timestamp = value.fiveMinHistory["TIME"][-1]
                timestamp = str(datetime.now())
                if value.fiveMinHistory["LED_COLOR"]:
                    alarmFiveMinList.append(alarmCodeToStr(value.fiveMinHistory["LED_COLOR"][-1]))
                else:
                    alarmFiveMinList.append('N')
                if value.sixtyMinHistory["LED_COLOR"]:
                    alarmSixtyMinList.append(alarmCodeToStr(value.sixtyMinHistory["LED_COLOR"][-1]))
                else:
                    alarmSixtyMinList.append('N')
                latestCodeDict[key] = value.fiveMinHistory["LED_COLOR"][-1]
            alarmFiveMinList.insert(0, str(timestamp))
            alarmSixtyMinList.insert(0, str(timestamp))
        except KeyError as e:
            print("AlarmSystemV3::getAllMonitorStatus", e)
        except Exception as e:
            print("AlarmSystemV3::getAllMonitorStatus unhandled exception ", e)
        return (','.join(alarmFiveMinList), ','.join(alarmSixtyMinList), latestCodeDict)

    def getAllMonitorStatusHeader(self):
        """
        Column definition of getAllMonitorStatus().
        """
        keyList = []
        try:
            keyList = self.alarms.items().keys()
        except:
            keyList.append("fail!")
        return ','.join(keyList)

    def getAllMonitorDiagnostics(self):
        try:
            for key, value in self.alarms.items():
                colorHistory = []
                for localDict in self.alarms[key].longPublicAlarmHistory:
                    colorHistory.append(localDict["LED_COLOR"])
                print("LED History:", colorHistory)
        except Exception as e:
            print("AlarmSystemV3::getAllMonitorDiagnostics unhandled exception ", e)
        return

#-----------------------------------------------------------------------------------
def main():
    #pdb.set_trace()
    singleAlarmTest = False

    # Test the single alarm class with random data.
    if singleAlarmTest:
        oneAlarm = SingleAlarmMonitor()
        oneAlarm.setTestState()
        for t in xrange(1, 201):
            data = 3.0 + random.gauss(0, 0.5)
            oneAlarm.setData(t, data)
        oneAlarm.processAccumulator()
        print("Short:", oneAlarm.shortPublicAlarmHistory)

    # Test the alarm manager which will read an ini to create
    # two monitors.
    print("Creating Alarm Manager")
    alarmManager = AlarmSystemV3("test_ini")

    dataDict = {}

    for i in xrange(3601):
        #dataDict["HCl"] = 4.0
        dataDict["NH3"] = 6.0
        if i%20 == 0:
            dataDict["NH3"] = 5.0 + 9.5 #+ random.gauss(0, 2.5)
        alarmManager.updateAllMonitors(i, dataDict)

    #alarmManager.getAllMonitorDiagnostics()

if __name__ == '__main__':
    main()
