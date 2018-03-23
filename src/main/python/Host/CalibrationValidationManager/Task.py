# TaskManager
#
# Need:
#   Instructions (what to do)
#   RefGas (if measuring a gas and comparing to a measurement in this object)
#   Data source (if measuring an unknown gas we need the data)
#   Timer (for time based evolution of the task or sub-tasks)
#   Signals (to indicate progress or completion)
#   Slots (to accept commands to start, pause, abort)
#
# Task is an object instantiated by the TaskManager and embedded in a QThread
# so the task doesn't block the main code due to the GIL.
#
# The task start execution with QThread.start() invoking work() below.
#
# Signals:
# task_finish_signal:       Alerts TaskManager that this task has finished. Use for normal exit.
# task_abort_signal:        Alerts TaskManager that the task quit early or failed.
# task_heartbead_signal:    A periodic signal that will tell TaskManager that the task is running.
#
# Slots:
# abort_slot:               Receives TaskManager command to abort this task.
# ping_slot:                Receives TaskManager command to send task_heartbeat_signal.

# Use the SVG rendering engine for matplotlib plots generated for reports.
# If a rendering engine is not specified it will default to Qt4.  If the Qt4 or Qt5
# rendering engines are used in this context you will get the
# "QPixmap: It is not safe to use pixmaps outside the GUI thread" error message.
#
import matplotlib
matplotlib.use("SVG")
import matplotlib.pyplot as plt

import datetime
import numpy
from PyQt4 import QtCore, QtGui
from QNonBlockingTimer import QNonBlockingTimer
from QDateTimeUtilities import get_nseconds_of_latest_data
from ReferenceGas import ReferenceGas, GasEnum
import ReportUtilities

class Task(QtCore.QObject):
    task_finish_signal = QtCore.pyqtSignal(str)
    task_abort_signal = QtCore.pyqtSignal(str)
    task_heartbeat_signal = QtCore.pyqtSignal(str)
    task_countdown_signal = QtCore.pyqtSignal(int, int, str, bool)
    task_next_signal = QtCore.pyqtSignal()
    task_report_signal = QtCore.pyqtSignal(str, object)
    task_stop_clock_signal = QtCore.pyqtSignal()

    # Send up a signal if we start a timer and are waiting for user input
    task_prompt_user_signal = QtCore.pyqtSignal()

    def __init__(self,
                 my_parent = None,
                 settings = {},
                 results = {},
                 reference_gases = {},
                 my_id = None,
                 data_source = None,
                 ):
        super(Task, self).__init__()
        self._my_parent = my_parent
        self._reference_gases = reference_gases
        self._settings = settings
        self._my_id = my_id
        self._running = False
        self._abort =   False
        self._results = results
        self.skip = False                   # If true this task is never run
        self.data_source = data_source
        self._mutex = QtCore.QMutex()
        self.set_connections()

        # if "Skip" in self._settings:
        #     self.skip = self._settings["Skip"]     # Need a boolean checker here

        # Init reference unk gas arrays if a gas is associated with this task.
        # Arrays are used as these results are passed directly to array based
        # statistic tools.
        # Gas_Alias: [ list of gas tanks, e.g. "GAS0", for reporting ]
        # Gas_Name: human readable name like "CH4"
        # Meas_Conc: [ array of unk. gas measured concs. ]
        # Meas_Conc_Std: [ array of standard deviations from meas_conc data ]
        # Ref_Conc: [ array of ref. gas conc. ]
        if "Gas" in self._settings:
            gas_key = self._settings["Gas"]
            if "Skip" in gas_key:
                self.skip = True
            else:
                self._results["Gas_Name"] = self._settings["Data_Key"]
                gasEnum = GasEnum[self._settings["Data_Key"]]  # Convert the human readable gas name to the enum form
                ref_gas_conc = float(self._reference_gases[gas_key].getGasConcPpm(gasEnum))
                zero_air = self._reference_gases[gas_key].zeroAir
                if "Ref_Conc" in self._results:
                    self._results["Ref_Conc"].append(ref_gas_conc)
                else:
                    self._results["Ref_Conc"] = [ref_gas_conc]
                if "Gas" in self._results:
                    self._results["Gas"].append(gas_key)
                else:
                    self._results["Gas"] = [gas_key]
                if "Zero_Air" in self._results:
                    self._results["Zero_Air"].append(zero_air)
                else:
                    self._results["Zero_Air"] = [zero_air]
                if "Meas_Conc" not in self._results:
                    self._results["Meas_Conc"] = []
                if "Meas_Conc_Std" not in self._results:
                    self._results["Meas_Conc_Std"] = []
                if "Percent_Deviation" not in self._results:
                    self._results["Percent_Deviation"] = []

        return

    # ----------------------------------------------------------------------------------
    # Task start/stop management methods
    #
    def set_connections(self):
        self._my_parent.ping_task_signal.connect(self.ping_slot)
        return

    def abort_slot(self):
        """
        Terminate the clock of any running subtask.  _abort prevents execution from passing on to the
        next subtask.
        :return:
        """
        self._abort = True
        self.task_stop_clock_signal.emit()      # Stop the clock of any running subtasks
        self.task_abort_signal.emit(self._my_id)
        return

    def work(self):
        if "Simulation" in self._settings:
            (key, conc) = self._settings["Simulation"]
            self.data_source.setOffset(key, conc)

        self._running = True
        if "Analysis" in self._settings:
            self._results["end_time"] = str(datetime.datetime.now())
            if "Linear_Regression_Validation" in self._settings["Analysis"]:
                self.linear_regression()
            elif "Span_Validation" in self._settings["Analysis"]:
                self.span_validation()
            elif "One_Point_Validation" in self._settings["Analysis"]:
                self.one_point_validation()
            else:
                print("Undefined analysis:", self._settings["Analysis"])
        else:
            self.simple_avg_measurement()

        self.task_finish_signal.emit(self._my_id)

        self._running = False
        return

    def stop_slot(self):
        self._mutex.lock()
        self._running = False
        self._mutex.unlock()
        return

    def ping_slot(self):
        if self._running:
            self.task_heartbeat_signal.emit(self._my_id)
        return

    # ------------------------------------------------------------------------------------
    # Work to-do and helper methods
    #
    # This method is a simple example of how to get an average measurement of a gas.
    #
    def simple_avg_measurement(self):
        if self._abort:
            return

        self.pre_task_instructions()

        if self._abort:
            return

        if "GasDelayBeforeMeasureSeconds" in self._settings:
            t = QNonBlockingTimer(set_time_sec=int(self._settings["GasDelayBeforeMeasureSeconds"]),
                                  description="Waiting for " +
                                              self._settings["Data_Key"] +
                                              " to equilibrate:")
            t.tick_signal.connect(self.task_countdown_signal)
            self.task_stop_clock_signal.connect(t.stop)
            t.start()

        if self._abort:
            return

        if "GasMeasureSeconds" in self._settings:
            t = QNonBlockingTimer(set_time_sec=int(self._settings["GasMeasureSeconds"]),
                                  description="Measuring " +
                                              self._settings["Data_Key"])
            t.tick_signal.connect(self.task_countdown_signal)
            self.task_stop_clock_signal.connect(t.stop)
            t.start()

        if self._abort:
            return

        try:
            timestamps = self.data_source.getList(self._settings["Data_Source"], "time")
            data = self.data_source.getList(self._settings["Data_Source"], self._settings["Data_Key"])
            (subset_times, subset_data, flag) =\
                get_nseconds_of_latest_data(timestamps, data, int(self._settings["GasMeasureSeconds"]))
            if subset_data:
                avg_data = numpy.average(subset_data)
                std = numpy.std(subset_data)
                self._results["Meas_Conc"].append(avg_data)
                self._results["Meas_Conc_Std"].append(std)

        except Exception as e:
            print("Excep: %s" %e)

        if self._abort:
            return

        self.post_task_instructions()

        return

    def pre_task_instructions(self):
        """
        Before the main measurement task, prompt the user to hook up the correct
        gas source.
        :return:
        """
        # A timer pauses for infinite time (31 years actually) until the timer
        # is stopped.  The stop is connected to a NEXT button signal in the main
        # GUI.
        # The tick signal is needed to emit the user prompt to the main GUI.
        #
        self.task_prompt_user_signal.emit()
        delay = 1e10    # about 31 years
        busy = True     # Show busy state in progress bars if no time defined
        if "Pre_Task_Delay_Sec" in self._settings:
            delay = int(self._settings["Pre_Task_Delay_Sec"])
            busy = False
        instructions = "Generic message from Task {0}: Open the correct valve to let in the gas and then click NEXT".format(self._my_id)
        t = QNonBlockingTimer(set_time_sec=delay,
                              description=instructions,
                              busy_hint = busy)
        t.tick_signal.connect(self.task_countdown_signal)
        self.task_stop_clock_signal.connect(t.stop)
        self.task_next_signal.connect(t.stop)
        t.start()
        return

    def post_task_instructions(self):
        """
        After finishing the measurement task, prompt the user to disconnect the
        reference gas source.
        :return:
        """
        # A timer pauses for infinite time (31 years actually) until the timer
        # is stopped.  The stop is connected to a NEXT button signal in the main
        # GUI.
        #
        self.task_prompt_user_signal.emit()
        delay = 1e10    # about 31 years
        busy = True  # Show busy state in progress bars if no time defined
        if "Post_Task_Delay_Sec" in self._settings:
            delay = int(self._settings["Post_Task_Delay_Sec"])
            busy = False
        instructions = "Generic message from Task {0}: Close the reference gas valve and then click NEXT".format(self._my_id)
        t = QNonBlockingTimer(set_time_sec=delay,
                              description=instructions,
                              busy_hint = busy)
        t.tick_signal.connect(self.task_countdown_signal)
        self.task_stop_clock_signal.connect(t.stop)
        self.task_next_signal.connect(t.stop)
        t.start()
        return

    def preanalysis_data_processing(self):
        """
        Generate additional data needed for the final analysis step.
        :return:
        """
        # % deviation
        self._results["Percent_Deviation"] = []
        for idx, zeroAirFlag in enumerate(self._results["Zero_Air"]):
            if "No" in zeroAirFlag:
                measConc = self._results["Meas_Conc"][idx]
                refConc = self._results["Ref_Conc"][idx]
                self._results["Percent_Deviation"].append(abs(100.0*(measConc - refConc)/refConc))
            else:
                self._results["Percent_Deviation"].append(numpy.NaN)
        return


    def linear_regression(self):
        """
        Linear regression of the reference gas concentration (x) vs the measured
        concentration (y).
        :return: p = slope and offset of best fit line
        """
        self.preanalysis_data_processing()

        x = self._results["Meas_Conc"]
        y = self._results["Ref_Conc"]
        coeffs = numpy.polyfit(x,y,1)
        yfit = numpy.poly1d(coeffs)(x)

        ybar = numpy.sum(y)
        ssreg = numpy.sum((yfit - ybar)**2)
        sstot = numpy.sum((y - ybar)**2)
        r2 = ssreg/sstot
        self._results["slope"] = coeffs[0]
        self._results["intercept"] = coeffs[1]
        self._results["r2"] = r2

        # Find zero air measurements and see if they pass the zero test.
        #
        # The output is an array for each zero air measurement.  Normally you only measure it once
        # but we put in the ability to handle an arbitrary number if the measurement pattern
        # is repeated like low-high-low-high...
        # Each array element is a tuple with the measurement, "Pass" or "Fail, and min and max
        # fail thresholds.
        #
        #
        self._results["Zero_Air_Test"] = []
        zeroAirMin = -0.005 # -0.005 PPM or -5 PPB
        zeroAirMax = 0.010
        for idx, zeroAirFlag in enumerate(self._results["Zero_Air"]):
            if "Yes" in zeroAirFlag:
                measConc = self._results["Meas_Conc"][idx]
                if measConc > zeroAirMin and measConc < zeroAirMax:
                    self._results["Zero_Air_Test"].append((measConc, "Pass", zeroAirMin, zeroAirMax))
                else:
                    self._results["Zero_Air_Test"].append((measConc, "Fail", zeroAirMin, zeroAirMax))

        # Check to see if the slope test passes
        slope_min = 0.95
        slope_max = 1.05
        slope = self._results["slope"]
        self._results["Slope_Test"] = None
        if self._results["slope"] > slope_min and self._results["slope"] < slope_max:
            self._results["Slope_Test"] = (slope, "Pass", slope_min, slope_max)
        else:
            self._results["Slope_Test"] = (slope, "Fail", slope_min, slope_max)

        # Check if % deviation of measured vs actual exceed the passing threshold
        #
        percent_acceptance = 5.0 # 5%
        self._results["Deviation_Test"] = []
        for idx, percent_deviation in enumerate(self._results["Percent_Deviation"]):
            if numpy.isnan(percent_deviation):
                pass
            else:
                measConc = self._results["Meas_Conc"][idx]
                refConc = self._results["Ref_Conc"][idx]
                if percent_deviation < percent_acceptance :
                    self._results["Deviation_Test"].append((measConc, percent_deviation, "Pass", percent_acceptance))
                else:
                    self._results["Deviation_Test"].append((measConc, percent_deviation, "Fail", percent_acceptance))


        image = ReportUtilities.make_plot(x, y, yfit, "S", "N", "O")
        (fileName, doc) = ReportUtilities.create_report(self._settings, self._reference_gases, self._results, image)
        self.task_report_signal.emit(fileName, doc)
        return

    def span_validation(self):
        """
        Span test with zero air and one medium to high concentration source.
        :return:
        """
        self.preanalysis_data_processing()

        self._results["Zero_Air_Test"] = []
        zeroAirMin = -0.005 # -0.005 PPM or -5 PPB
        zeroAirMax = 0.010
        for idx, zeroAirFlag in enumerate(self._results["Zero_Air"]):
            if "Yes" in zeroAirFlag:
                measConc = self._results["Meas_Conc"][idx]
                if measConc > zeroAirMin and measConc < zeroAirMax:
                    self._results["Zero_Air_Test"].append((measConc, "Pass", zeroAirMin, zeroAirMax))
                else:
                    self._results["Zero_Air_Test"].append((measConc, "Fail", zeroAirMin, zeroAirMax))

        # Check if % deviation of measured vs actual exceed the passing threshold
        #
        percent_acceptance = 5.0 # 5%
        self._results["Deviation_Test"] = []
        for idx, percent_deviation in enumerate(self._results["Percent_Deviation"]):
            if numpy.isnan(percent_deviation):
                pass
            else:
                measConc = self._results["Meas_Conc"][idx]
                refConc = self._results["Ref_Conc"][idx]
                if percent_deviation < percent_acceptance :
                    self._results["Deviation_Test"].append((measConc, percent_deviation, "Pass", percent_acceptance))
                else:
                    self._results["Deviation_Test"].append((measConc, percent_deviation, "Fail", percent_acceptance))

        doc = ReportUtilities.create_report(self._settings, self._reference_gases, self._results)
        self.task_report_signal.emit(doc)
        return

    def one_point_validation(self):
        """
        Test one known reference gas. No zero air.
        :return:
        """
        self.preanalysis_data_processing()
        # Check if % deviation of measured vs actual exceed the passing threshold
        #
        percent_acceptance = 5.0 # 5%
        self._results["Deviation_Test"] = []
        for idx, percent_deviation in enumerate(self._results["Percent_Deviation"]):
            if numpy.isnan(percent_deviation):
                pass
            else:
                measConc = self._results["Meas_Conc"][idx]
                refConc = self._results["Ref_Conc"][idx]
                if percent_deviation < percent_acceptance :
                    self._results["Deviation_Test"].append((measConc, percent_deviation, "Pass", percent_acceptance))
                else:
                    self._results["Deviation_Test"].append((measConc, percent_deviation, "Fail", percent_acceptance))

        doc = ReportUtilities.create_report(self._settings, self._reference_gases, self._results)
        self.task_report_signal.emit(doc)
        return
