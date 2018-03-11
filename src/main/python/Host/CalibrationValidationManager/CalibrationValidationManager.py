#
#

import sys
from PyQt4 import QtCore, QtGui
from QReferenceGasEditor import QReferenceGasEditorWidget
from QPlotWidget import QPlotWidget
from QTaskWizardWidget import QTaskWizardWidget
from Host.CalibrationValidationManager.TaskManager import TaskManager

class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(0, 0, 1024, 768)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        self.tm = None
        self._init_gui()
        self.tm = self.setUpTasks_()
        self.show()
        self._set_connections()
        self.start_data_stream_polling()
        return

    def _set_connections(self):
        self.tm.task_countdown_signal.connect(self.update_progressbar)
        self.tm.report_signal.connect(self.text_edit.setDocument)
        self.tm.reference_gas_signal.connect(self.tableWidget.display_reference_gas_data)
        self.taskWizardWidget.start_run_signal.connect(self.start_running_tasks)

    def _init_gui(self):
        self.plotWidget = QPlotWidget()
        self.text_edit = QtGui.QTextEdit(QtCore.QString("In _init_gui"))
        self.tableWidget = QReferenceGasEditorWidget()
        self.taskWizardWidget = QTaskWizardWidget()
        gl = QtGui.QGridLayout()
        gl.addWidget(self.plotWidget, 0, 0)
        gl.addWidget(self.tableWidget, 1, 0)
        gl.addWidget(self.taskWizardWidget, 2, 0)
        central_widget = QtGui.QWidget()
        central_widget.setLayout(gl)
        self.setCentralWidget(central_widget)
        return

    def setUpTasks_(self):
        tm = TaskManager(iniFile="test")
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

    def update_progressbar(self, countdown_sec, set_time_sec, description):
        """
        This is a slot to receive a progress signal from a running task.
        :param countdown_sec:
        :param set_time_sec:
        :param description:
        :return:
        """
        self.taskWizardWidget.setText(QtCore.QString(description))
        self.taskWizardWidget.setProgressBar((set_time_sec - countdown_sec)*100/set_time_sec)
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


def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())

run()