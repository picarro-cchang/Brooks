# TaskManager


# from PyQt4.QtCore import QObject, pyqtSignal
import copy
from PyQt4 import QtCore
from Host.Common.configobj import ConfigObj
from Host.DataManager.DataStore import DataStoreForQt
from ReferenceGas import ReferenceGas
from Task import Task

class TaskManager(QtCore.QObject):
    stop_signal = QtCore.pyqtSignal()       # Tell current task to stop, aborts the queue
    ping_task_signal = QtCore.pyqtSignal()
    next_subtask_signal = QtCore.pyqtSignal()
    task_countdown_signal = QtCore.pyqtSignal(int, int, str, bool)
    report_signal = QtCore.pyqtSignal(object)
    reference_gas_signal = QtCore.pyqtSignal(object)
    task_settings_signal = QtCore.pyqtSignal(object)
    prompt_user_signal = QtCore.pyqtSignal()
    job_complete_signal = QtCore.pyqtSignal()

    def __init__(self, iniFile=None):
        super(TaskManager, self).__init__()
        # self.parent = parent
        self.referenceGases = {}
        self.tasks = []
        self.threads = []
        self.running_task_idx = None    # Running task idx, None if no jobs running
        self.monitor_data_stream = False
        self.input_data = {}            # Dict of measured data
        self.results = {}
        self.co = None                  # Handle to the input ini file
        self.ds = DataStoreForQt()
        self.loadConfig()
        self.set_connections()
        self.start_data_stream()
        QtCore.QTimer.singleShot(100, self.late_start)
        return

    def loadConfig(self, iniFile = "task_manager.ini"):
        self.co = ConfigObj(iniFile)

        for key, gasConfObj in self.co["GASES"].items():
            self.referenceGases[key] = ReferenceGas(gasConfObj, key)
            # self.reference_gas_signal.emit(self.referenceGases)

        task_global_settings = {}
        for key, value in self.co["TASKS"].items():
            # Loop through [TASKS] and build a local dict of the global
            # key/value pairs to pass to each task.
            if not isinstance(value, dict):
                task_global_settings[key] = value

        for key, value in self.co["TASKS"].items():
            # The [TASKS] section is a collection of individual tasks
            # and global key-value pairs that apply to all tasks.
            # Individual tasks are in sub-sections like [[TASK0]].
            # The sub-section settings are used to instantiate a Task
            # object.
            #
            # In the dict representation of the configobj, the key is
            # just a string and you can't tell if the key represents a
            # sub-section or something else.  So what we do is given
            # a key, if the value associated with it is a dict, we
            # treat this as a configobj sub-section.  Anything else we
            # treat as a TASKS global key-value pair.  Valid values
            # in this case are floats, ints, strings, booleans, and lists.
            #
            if isinstance(value, dict):
                # Merge TASKS global and individual task settings into one
                # dict passed to each dict.
                value_copy = copy.deepcopy(value)
                value_copy.update(task_global_settings)
                task_thread = QtCore.QThread()
                task = Task(my_parent=self,
                            my_id=key,
                            settings=value_copy,
                            reference_gases=self.referenceGases,
                            results=self.results,
                            data_source=self.ds)
                task.moveToThread(task_thread)
                task_thread.started.connect(task.work)
                self.tasks.append(task)
                self.threads.append(task_thread)

        return

    def set_connections(self):
        for task in self.tasks:
            task.task_finish_signal.connect(self.task_finished_ack_slot)
            task.task_heartbeat_signal.connect(self.task_heartbeat_slot)
            task.task_countdown_signal.connect(self.task_countdown_slot)
            task.task_report_signal.connect(self.report_signal)
        return

    def late_start(self):
        """
        Post init things to do before the work starts.
        :return:
        """
        self.reference_gas_signal.emit(self.co)
        self.task_settings_signal.emit(self.co)
        return

    def start_data_stream(self):
        """
        Manage the listener that will collect broadcasted data and make the received data
        easy for the tasks to access.
        :return:
        """
        monitor_data_thread = QtCore.QThread()
        self.ds.moveToThread(monitor_data_thread)
        monitor_data_thread.started.connect(self.ds.run)
        monitor_data_thread.start()

    def start_work(self):
        """
        Kick off the first task in the task list
        :return:
        """
        self.running_task_idx = 0
        self.tasks[self.running_task_idx].task_prompt_user_signal.connect(self.prompt_user_signal)
        self.next_subtask_signal.connect(self.tasks[self.running_task_idx].task_next_signal)
        self.threads[self.running_task_idx].start()

    def move_to_next_task(self):
        """
        If there are more tasks to do, start the next one.
        The connect/disconnect signals are done here so that the NEXT button press is sent
        to the currently running task.
        :return:
        """
        if self.running_task_idx < len(self.threads)-1:
            self.tasks[self.running_task_idx].task_prompt_user_signal.disconnect(self.prompt_user_signal)
            self.next_subtask_signal.disconnect(self.tasks[self.running_task_idx].task_next_signal)
            self.running_task_idx += 1
            while self.tasks[self.running_task_idx].skip:
                self.running_task_idx += 1
            self.tasks[self.running_task_idx].task_prompt_user_signal.connect(self.prompt_user_signal)
            self.next_subtask_signal.connect(self.tasks[self.running_task_idx].task_next_signal)
            self.threads[self.running_task_idx].start()
        else:
            self.job_complete_signal.emit()
            self.running_task_idx = None
        return

    def task_finished_ack_slot(self, task_id):
        self.move_to_next_task()
        return

    def task_heartbeat_slot(self, task_id):
        """
        Get heartbeat signal from a running thread to update a progress bar
        :return:
        """
        print("Got heartbeat signal from %s" %task_id)
        return

    def task_countdown_slot(self, countdown_sec, set_time_sec, description, busy):
        self.task_countdown_signal.emit(countdown_sec, set_time_sec, description, busy)
        return

    def is_task_alive_slot(self):
        self.ping_task_signal.emit()
        return

