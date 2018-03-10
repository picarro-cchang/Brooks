#
#

import sys
from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
from functools import partial
from QReferenceGasEditor import QReferenceGasEditorWidget
from DateAxisItem import DateAxisItem
from QPlotWidget import QPlotWidget
from Host.CalibrationValidationManager.TaskManager import TaskManager

# dummy data for cylinder table widget
data = {'col1':['1','2','3'], 'col2':['4','5','6'], 'col3':['7','8','9']}

class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 700, 700)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        self.tm = None
        self._init_gui()
        self.tm = self.setUpTasks_()
        self.show()
        self._set_connections()
        self.start_data_stream_polling()
        return

    def _set_connections(self):
        self.run_btn.clicked.connect(self.start_running_tasks)
        self.run_btn.clicked.connect(partial(self.tableWidget.disable_edit, True))

        self.ping_btn.clicked.connect(self.ping_running_tasks)
        self.next_btn.clicked.connect(self.tm.next_subtask_signal)

        self.tm.task_countdown_signal.connect(self.update_progressbar)
        self.tm.report_signal.connect(self.text_edit.setDocument)
        self.tm.reference_gas_signal.connect(self.tableWidget.display_reference_gas_data)

    def _init_gui(self):
        self.run_btn = QtGui.QPushButton("Run", self)
        self.ping_btn = QtGui.QPushButton("Ping", self)
        self.next_btn = QtGui.QPushButton("NEXT", self)
        self.task_label = QtGui.QLabel("Click RUN to start the validation process.")
        self.task_progressbar = QtGui.QProgressBar()
        self.task_progressbar.setValue(0)
        self.plotWidget = QPlotWidget()
        self.text_edit = QtGui.QTextEdit(QtCore.QString("In _init_gui"))
        self.tableWidget = QReferenceGasEditorWidget()
        gl = QtGui.QGridLayout()
        gl.addWidget(self.run_btn,0,0)
        gl.addWidget(self.ping_btn,1,0)
        gl.addWidget(self.task_label,2,0)
        gl.addWidget(self.task_progressbar,3,0)
        gl.addWidget(self.next_btn,4,0)
        gl.addWidget(self.plotWidget, 5, 0)
        gl.addWidget(self.text_edit,6,0)
        gl.addWidget(self.tableWidget, 7, 0)
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
        self.tableWidget.table.save_reference_gas_data()
        return

    def update_progressbar(self, countdown_sec, set_time_sec, description):
        """
        This is a slot to receive a progress signal from a running task.
        :param countdown_sec:
        :param set_time_sec:
        :param description:
        :return:
        """
        self.task_progressbar.setValue((set_time_sec - countdown_sec)*100/set_time_sec)
        self.task_label.setText(QtCore.QString(description))
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