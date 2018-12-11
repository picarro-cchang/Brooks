#
#

import sys
import collections
from QLoginDialog import QLoginDialog
import DataBase
from functools import partial
from PyQt4 import QtCore, QtGui
from QReferenceGasEditor import QReferenceGasEditorWidget
from QPlotWidget import QPlotWidget
from QTaskWizardWidget import QTaskWizardWidget
from QTaskEditorWidget import QTaskEditorWidget
from Host.CalibrationValidationManager.TaskManager import TaskManager
from Host.Common.SingleInstance import SingleInstance

class Window(QtGui.QMainWindow):
    def __init__(self, iniFile, debug_mode=False):
        super(Window, self).__init__()
        self.setWindowTitle("Picarro Calibration Validation Tool")

        if debug_mode:
            self.setFixedSize(1024, 768)
        else:
            self.setWindowState(QtCore.Qt.WindowFullScreen)

        try:
            with open('/usr/local/picarro/qtLauncher/styleSheet.qss', 'r') as f:
                self.style_data = f.read()
                self.setStyleSheet(self.style_data)
        except Exception as e:
            # We couldn't load the Picarro style sheet so default to a vanilla style
            QtGui.QApplication.setStyle("cleanlooks")

        self._db = DataBase
        self.display_login_dialog()  # Need DB authentication here so the TaskManager can get the user information.
        self.tm = None
        self.iniFile = iniFile
        self.tm = self.setUpTasks_()
        self._init_gui()
        self._startup_settings()
        self._set_connections()
        self.show()
        QtCore.QTimer.singleShot(100, self._late_start)
        return

    def _late_start(self):
        self.start_data_stream_polling()
        return

    def _set_connections(self):
        self.closeBtn.clicked.connect(self._quit_validation_tool)
        self.resetTimerBtn.clicked.connect(self.tm.reset_autologout_timer)
        self.tm.task_countdown_signal.connect(self.update_progressbar)
        self.tm.autologout_timer_signal.connect(self.update_autologout_timer)
        self.tm.autologout_timer_finished_signal.connect(self.logout_and_shutdown)
        self.tm.report_signal.connect(self.taskWizardWidget.set_report)
        self.tm.reference_gas_signal.connect(self.tableWidget.display_reference_gas_data)
        self.tm.task_settings_signal.connect(self.taskEditorWidget.display_task_settings)
        self.tm.prompt_user_signal.connect(self.taskWizardWidget.prompt_user)
        self.tm.job_complete_signal.connect(self.taskWizardWidget.job_complete)
        self.tm.job_complete_signal.connect(partial(self.tableWidget.disable_edit, False))
        self.tm.job_aborted_signal.connect(self.taskWizardWidget.job_aborted)
        self.tm.analyzer_warming_up_signal.connect(self.taskWizardWidget.warming_up_warning_dialog)
        self.taskWizardWidget.start_run_signal.connect(partial(self.tableWidget.setDisabled, True))
        self.taskWizardWidget.start_run_signal.connect(partial(self.taskEditorWidget.setDisabled, True))
        self.taskWizardWidget.abort_signal.connect(partial(self.tableWidget.setEnabled, True))
        self.taskWizardWidget.abort_signal.connect(partial(self.taskEditorWidget.setEnabled, True))
        self.taskWizardWidget.job_complete_signal.connect(partial(self.tableWidget.setEnabled, True))
        self.taskWizardWidget.job_complete_signal.connect(partial(self.taskEditorWidget.setEnabled, True))
        self.taskWizardWidget.abort_signal.connect(partial(self.closeBtn.setEnabled, True))
        self.taskWizardWidget.job_complete_signal.connect(partial(self.closeBtn.setEnabled, True))
        self.taskWizardWidget.start_run_signal.connect(self.start_running_tasks)
        self.taskWizardWidget.next_signal.connect(self.tm.next_subtask_signal)
        self.taskWizardWidget.view_editors_signal.connect(self._view_reference_gas_settings)
        self.taskWizardWidget.hide_editors_signal.connect(self._startup_settings)
        self.taskWizardWidget.abort_signal.connect(self.tm.abort_slot)

    def _init_gui(self):
        self.closeBtn = QtGui.QPushButton("Close")
        self.closeBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resetTimerBtn = QtGui.QPushButton("Reset Auto Logout")
        self.resetTimerBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.autologoutLabel = QtGui.QLabel(" ")
        hb = QtGui.QHBoxLayout()
        hb.addSpacing(10)
        hb.addWidget(self.resetTimerBtn)
        hb.addWidget(self.autologoutLabel)
        hb.addStretch(1)
        hb.addWidget(self.closeBtn)
        hb.addSpacing(10)   # Fudge to line up button with widgets above

        self.plotWidget = QPlotWidget(self)
        self.text_edit = QtGui.QTextEdit(QtCore.QString("In _init_gui"))
        self.tableWidget = QReferenceGasEditorWidget()
        self.taskWizardWidget = QTaskWizardWidget(self.tm.co, self._db)
        self.taskEditorWidget = QTaskEditorWidget()
        gl = QtGui.QGridLayout()
        gl.addWidget(self.plotWidget, 0, 0)
        gl.addWidget(self.tableWidget, 1, 0)
        gl.addWidget(self.taskEditorWidget, 2, 0)
        gl.addWidget(self.taskWizardWidget, 3, 0)
        gl.addLayout(hb, 4, 0)
        central_widget = QtGui.QWidget()
        central_widget.setLayout(gl)
        self.setCentralWidget(central_widget)
        return

    def _startup_settings(self):
        self.plotWidget.setVisible(True)
        self.tableWidget.setVisible(False)
        self.taskEditorWidget.setVisible(False)
        return

    def _view_reference_gas_settings(self):
        self.plotWidget.setVisible(False)
        self.tableWidget.setVisible(True)
        self.taskEditorWidget.setVisible(True)

    def _quit_validation_tool(self):
        dialog = QtGui.QMessageBox(self)
        dialog.setText("Are you sure you want to close the validation tool?")
        dialog.setIcon(QtGui.QMessageBox.Question)
        dialog.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        dialog.setDefaultButton(QtGui.QMessageBox.No)
        dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        result = dialog.exec_()
        if result == QtGui.QMessageBox.Yes:
            self._db.logout()
            self.close()
        return

    def display_login_dialog(self):
        ld = QLoginDialog(self)
        ret = ld.exec_()
        if ret == 0:
            self.close()
        return

    def setUpTasks_(self):
        tm = TaskManager(iniFile=self.iniFile, db=self._db)
        return tm

    def start_data_stream_polling(self):
        """
        Set a timer that will update the local copy of the data stream at 1Hz
        :return:
        """
        self._data_timer = QtCore.QTimer(self)
        self._data_timer.timeout.connect(self.update_data_stream)
        self._data_timer.setInterval(1000)
        self._data_timer.start()
        return

    def start_running_tasks(self):
        # Remind user if user have edited parameter and forgot to save or undo
        # before starting validation
        if self.taskEditorWidget.isEditing or self.tableWidget.isEditing:
            str = "Settings changed for:\n"
            if self.taskEditorWidget.isEditing:
                str += "    * Reference Gas Editor\n"
            if self.tableWidget.isEditing:
                str += "    * Task Editor\n"
            str += "Either UNDO or SAVE settings and then click START"
            self.taskWizardWidget.abort_with_warning(str)
            return
        self.closeBtn.setEnabled(False)
        self.tm.start_work()
        return

    def ping_running_tasks(self):
        self.tm.is_task_alive_slot()
        # self.tableWidget.table.save_reference_gas_data()
        return

    def update_progressbar(self, countdown_sec, set_time_sec, description, busy):
        """
        This is a slot to receive a progress signal from a running task.
        :param countdown_sec:
        :param set_time_sec:
        :param description:
        :return:
        """
        self.taskWizardWidget.setText(QtCore.QString(description))
        self.taskWizardWidget.setProgressBar((set_time_sec - countdown_sec)*100/set_time_sec, busy)
        return

    def update_autologout_timer(self, countdown_sec, set_time_sec, description, busy):
        minutes = countdown_sec/60
        seconds = countdown_sec%60
        if countdown_sec > 30:
            self.autologoutLabel.setText("Automatic Logout in {0:02d}:{1:02d} minutes.".format(minutes, seconds))
        else:
            self.autologoutLabel.setText("<font color=yellow>Automatic Logout in {0:02d}:{1:02d} minutes!</font>".format(minutes, seconds))
        return

    def logout_and_shutdown(self):
        quit()
        return

    def update_data_stream(self):
        """
        Method call by self._data_timer to get the current data stream for plotting.
        We use a try/except because the first call can throw a KeyError if we get
        here before the data store has initialized its dictionaries.
        :return:
        """
        try:
            # A hack here, looking at TaskManager internals to get some settings from the ini.
            # self.tm.co is the ConfigObj in the TaskManager.
            # This code determines which data is displayed in the plot (primary)
            # and which data is displayed in the text label below the plot (primary + secondary)
            #
            data_source = self.tm.co["TASKS"]["Data_Source"]
            primary_data_key = self.tm.co["TASKS"]["Data_Key"]
            primary_data_key_name = self.tm.co["TASKS"]["Data_Key_Name"]

            timestamps = self.tm.ds.getList(data_source, "time")
            data = self.tm.ds.getList(data_source, primary_data_key)

            # Everything is done in PPM.  Convert PPB or % concentrations
            # to PPM
            scale = 1.0
            if "Data_Source_Units" in self.tm.co["TASKS"]:
                units = self.tm.co["TASKS"]["Data_Source_Units"]
                if units == "PPB":
                    scale = 1/1000.0
                if units == "Percent":
                    scale = 10000
                data = [i*scale for i in data]

            d = collections.OrderedDict()
            if data:
                d[primary_data_key_name] = data[-1]
                if "Secondary_Data_Key" in self.tm.co["TASKS"]:
                    secondary_data_key = self.tm.co["TASKS"]["Secondary_Data_Key"]
                    secondary_data_key_name = self.tm.co["TASKS"]["Secondary_Data_Key_Name"]
                    if isinstance(secondary_data_key, list):
                        for i, val in enumerate(secondary_data_key):
                            d[secondary_data_key_name[i]] = self.tm.ds.getList(data_source, secondary_data_key[i])[-1]
                    else:
                        d[secondary_data_key_name] = self.tm.ds.getList(data_source, secondary_data_key)[-1]
            self.plotWidget.setData(timestamps, data, primary_data_key_name, d)
        except Exception as e:
            # Even if everything working, the datastore starts out empty and the first few calls will
            # cause an exception.
            # print("E:",e)
            pass
        return


def HandleCommandSwitches():
    import getopt

    shortOpts = 'c:'
    longOpts = ["ini=", "debug_mode="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        sys.exit(1)

    options = {}
    for o, a in switches:
        options[o] = a

    configFile = ""
    if "--ini" in options:
        configFile = options["--ini"]

    # username = ""
    # if "--username" in options:
    #     username = options["--username"]
    #
    # fullname = ""
    # if "--fullname" in options:
    #     fullname = options["--fullname"]

    debug_mode = False
    if "--debug_mode" in options:
        debug_mode = options["--debug_mode"]

    return (configFile, debug_mode)

def main():
    # Save the pid file in the /tmp/ directory so Supervisor doesn't try to
    # restart the app during its MonitorApps loop
    path = "/tmp/"
    userAdminApp = SingleInstance("CalibrationValidation", path)
    if not userAdminApp.alreadyrunning():
        app = QtGui.QApplication(sys.argv)
        # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
        (configFile, debug_mode) = HandleCommandSwitches()
        GUI = Window(iniFile=configFile, debug_mode=debug_mode)
        sys.exit(app.exec_())
    else:
        print "Instance of Calibration Validation Tool already running."

if __name__ == "__main__":
    main()
