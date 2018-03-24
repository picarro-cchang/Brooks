#
#

import sys
import qdarkstyle
from QLoginDialog import QLoginDialog
import DataBase
from functools import partial
from PyQt4 import QtCore, QtGui
from QReferenceGasEditor import QReferenceGasEditorWidget
from QPlotWidget import QPlotWidget
from QTaskWizardWidget import QTaskWizardWidget
from QTaskEditorWidget import QTaskEditorWidget
from Host.CalibrationValidationManager.TaskManager import TaskManager

class Window(QtGui.QMainWindow):
    def __init__(self, iniFile): #, username=None, fullname=None):
        super(Window, self).__init__()
        self.setFixedSize(1024, 768)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        self._db = DataBase
        self.display_login_dialog()
        self.tm = None
        self.iniFile = iniFile
        # self.username = None #username
        # self.fullname = None #fullname
        self._init_gui()
        self._startup_settings()
        self.tm = self.setUpTasks_()
        self._set_connections()
        self.show()
        QtCore.QTimer.singleShot(100, self._late_start)
        return

    def _late_start(self):
        # self.display_login_dialog()
        # self.show()
        self.start_data_stream_polling()
        return

    def _set_connections(self):
        self.closeBtn.clicked.connect(self.close)
        # self.loginBtn.clicked.connect(self.display_login_dialog)
        self.tm.task_countdown_signal.connect(self.update_progressbar)
        self.tm.report_signal.connect(self.taskWizardWidget.set_report)
        self.tm.reference_gas_signal.connect(self.tableWidget.display_reference_gas_data)
        self.tm.task_settings_signal.connect(self.taskEditorWidget.display_task_settings)
        self.tm.prompt_user_signal.connect(self.taskWizardWidget.prompt_user)
        self.tm.job_complete_signal.connect(self.taskWizardWidget.job_complete)
        self.tm.job_aborted_signal.connect(self.taskWizardWidget.job_aborted)
        self.taskWizardWidget.start_run_signal.connect(partial( self.tableWidget.disable_edit, True))
        self.taskWizardWidget.start_run_signal.connect(self.start_running_tasks)
        self.taskWizardWidget.next_signal.connect(self.tm.next_subtask_signal)
        self.taskWizardWidget.view_editors_signal.connect(self._view_reference_gas_settings)
        self.taskWizardWidget.hide_editors_signal.connect(self._startup_settings)
        self.taskWizardWidget.abort_signal.connect(self.tm.abort_slot)

    def _init_gui(self):
        self.closeBtn = QtGui.QPushButton("Close")
        # self.loginBtn = QtGui.QPushButton("Login")
        hb = QtGui.QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(self.closeBtn)
        # hb.addWidget(self.loginBtn)
        hb.addSpacing(10)   # Fudge to line up button with widgets above

        self.plotWidget = QPlotWidget()
        self.text_edit = QtGui.QTextEdit(QtCore.QString("In _init_gui"))
        self.tableWidget = QReferenceGasEditorWidget()
        self.taskWizardWidget = QTaskWizardWidget()
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

    def display_login_dialog(self):
        ld = QLoginDialog(self)
        ret = ld.exec_()
        if ret == 0:
            self.close()
        return

    def setUpTasks_(self):
        tm = TaskManager(iniFile=self.iniFile, db=self._db) #, username=self.username, fullname=self.fullname)
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

    def update_data_stream(self):
        """
        Method call by self._data_timer to get the current data stream for plotting.
        We use a try/except because the first call can throw a KeyError if we get
        here before the data store has initialized its dictionaries.
        :return:
        """
        try:
            timestamps = self.tm.ds.getList("analyze_H2O2", "time")
            data = self.tm.ds.getList("analyze_H2O2", "CH4")
            d = {}
            if data:
                d["CH4 [PPM]"] = data[-1]
                d["H2O2 [PPM]"] = self.tm.ds.getList("analyze_H2O2", "H2O2")[-1]
                d["H2O [PPM]"] = self.tm.ds.getList("analyze_H2O2", "H2O")[-1]
            self.plotWidget.setData(timestamps, data, d)
        except Exception as e:
            print("E:",e)
            pass
        return

def HandleCommandSwitches():
    import getopt

    shortOpts = 'c:'
    longOpts = ["ini=", "username=", "fullname="]
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

    username = ""
    if "--username" in options:
        username = options["--username"]

    fullname = ""
    if "--fullname" in options:
        fullname = options["--fullname"]

    return (configFile, username, fullname)

def main():
    app = QtGui.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
    (configFile, username, fullname) = HandleCommandSwitches()
    # GUI = Window(sys.argv[1])
    GUI = Window(iniFile=configFile) #, username=username, fullname=fullname)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()