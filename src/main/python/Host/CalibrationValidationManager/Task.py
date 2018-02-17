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

from PyQt4 import QtCore
from QNonBlockingTimer import QNonBlockingTimer
from QDateTimeUtilities import get_nseconds_of_latest_data
from ReferenceGas import ReferenceGas, GasEnum

class Task(QtCore.QObject):
    task_finish_signal = QtCore.pyqtSignal(str)
    task_abort_signal = QtCore.pyqtSignal(str)
    task_heartbeat_signal = QtCore.pyqtSignal(str)
    task_countdown_signal = QtCore.pyqtSignal(int, int, str)
    task_next_signal = QtCore.pyqtSignal()

    def __init__(self,
                 my_parent = None,
                 settings = {},
                 results = {},
                 reference_gases = {},
                 my_id = None,
                 data_source = None):
        super(Task, self).__init__()
        self._my_parent = my_parent
        self._reference_gases = reference_gases
        self._settings = settings
        self._my_id = my_id
        self._running = False
        self._results = results
        self.data_source = data_source
        self._mutex = QtCore.QMutex()
        self.set_connections()
        return

    # ----------------------------------------------------------------------------------
    # Task start/stop management methods
    #
    def set_connections(self):
        self._my_parent.ping_task_signal.connect(self.ping_slot)
        return

    def work(self):
        if "Simulation" in self._settings:
            # refConc = self._reference_gases[self._settings["Gas"]].getGasConcPpm(GasEnum.CH4)
            # self.data_source.setOffset("CH4", refConc)
            (key, conc) = self._settings["Simulation"]
            self.data_source.setOffset(key, conc)

        self._running = True
        aborted_work = False
        self.simple_avg_measurement()
        if aborted_work:
            self.task_abort_signal.emit(self._my_id)
        else:
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
        self.pre_task_instructions()

        if "GasDelayBeforeMeasureSeconds" in self._settings:
            t = QNonBlockingTimer(set_time_sec=int(self._settings["GasDelayBeforeMeasureSeconds"]),
                                  description="Waiting for " +
                                              self._settings["Data_Key"] +
                                              " to equilibrate:")
            t.tick_signal.connect(self.task_countdown_signal)
            t.start()

        if "GasMeasureSeconds" in self._settings:
            t = QNonBlockingTimer(set_time_sec=int(self._settings["GasMeasureSeconds"]),
                                  description="Measuring " +
                                              self._settings["Data_Key"])
            t.tick_signal.connect(self.task_countdown_signal)
            t.start()

        try:
            timestamps = self.data_source.getList(self._settings["Data_Source"], "time")
            data = self.data_source.getList(self._settings["Data_Source"], self._settings["Data_Key"])
            (subset_times, subset_data, flag) =\
                get_nseconds_of_latest_data(timestamps, data, int(self._settings["GasMeasureSeconds"]))
            print(flag)
            if subset_data:
                avg_data = sum(subset_data)/len(subset_data)
                self._results[self._my_id] = {self._settings["Data_Key"]: avg_data}
        except Exception as e:
            print("Excep: %s" %e)

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
        instructions = "Open the correct valve to let in the gas and then click NEXT"
        t = QNonBlockingTimer(set_time_sec=1e10,
                              description=instructions + self._my_id)
        t.tick_signal.connect(self.task_countdown_signal)
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
        instructions = "Close the gas valve and then click NEXT"
        t = QNonBlockingTimer(set_time_sec=1e10,
                              description=instructions + self._my_id)
        t.tick_signal.connect(self.task_countdown_signal)
        self.task_next_signal.connect(t.stop)
        t.start()
        return
