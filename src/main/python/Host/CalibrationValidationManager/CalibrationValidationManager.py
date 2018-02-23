#
#

import sys
from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
from DateAxisItem import DateAxisItem
from Host.CalibrationValidationManager.TaskManager import TaskManager


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 500)
        self.setWindowTitle("Picarro Calibration/Validation Tool")
        self.tm = None
        self._init_gui()
        self.tm = self.setUpTasks_()
        self.show()
        self._set_connections()
        self.start_data_stream_polling()
        return

    def _set_connections(self):
        self.btn.clicked.connect(self.start_running_tasks)
        self.ping_btn.clicked.connect(self.ping_running_tasks)
        self.next_btn.clicked.connect(self.tm.next_subtask_signal)
        self.tm.task_countdown_signal.connect(self.update_progressbar)
        self.tm.report_signal.connect(self.display_report)

    def _init_plot(self):
        time_axis = DateAxisItem("bottom")
        self._time_series_plot = pg.PlotWidget(axisItems={'bottom':time_axis})
        self._time_series_plot.setMouseEnabled(x=False,y=False)
        self._time_series_plot.setMenuEnabled(False)
        self._time_series_plot.showGrid(x=True, y=True)
        self._time_series_plot.setLabels(left="CH4 (ppm)")

        # Seems to keep time stamp labels from overlapping with eachother and over
        # the y-axis label.
        self._time_series_plot.getAxis("bottom").setStyle(autoExpandTextSpace=False)

        # Add top and right axes without labels to create a box around the plot.
        self._time_series_plot.showAxis("top",show=True)
        self._time_series_plot.getAxis("top").setStyle(showValues=False)
        self._time_series_plot.showAxis("right",show=True)
        self._time_series_plot.getAxis("right").setStyle(showValues=False)

        # return self._time_series_plot.plot(pen=pg.mkPen(color=(255,255,255), width=1))
        return self._time_series_plot.plot(width=1, symbol='o')


    def _init_gui(self):
        self.btn = QtGui.QPushButton("Run", self)
        self.ping_btn = QtGui.QPushButton("Ping", self)
        self.next_btn = QtGui.QPushButton("NEXT", self)
        self.task_label = QtGui.QLabel("Click RUN to start the validation process.")
        self.task_progressbar = QtGui.QProgressBar()
        self.task_progressbar.setValue(0)
        self.plot = self._init_plot()
        self.text_edit = QtGui.QTextEdit(QtCore.QString("In _init_gui"))
        gl = QtGui.QGridLayout()
        gl.addWidget(self.btn,0,0)
        gl.addWidget(self.ping_btn,1,0)
        gl.addWidget(self.task_label,2,0)
        gl.addWidget(self.task_progressbar,3,0)
        gl.addWidget(self.next_btn,4,0)
        gl.addWidget(self._time_series_plot,5,0)
        gl.addWidget(self.text_edit,6,0)
        central_widget = QtGui.QWidget()
        central_widget.setLayout(gl)
        self.setCentralWidget(central_widget)
        return

    def setUpTasks_(self):
        tm = TaskManager("test")
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
            self.plot.setData(timestamps,data)
        except Exception as e:
            pass
        return

    def display_report(self, str, obj):
        qpix = QtGui.QPixmap()
        qpix.loadFromData(obj.getvalue())
        img = qpix.toImage()

        # self.text_edit.setHtml(QtCore.QString(str))
        # cursor = QtGui.QTextCursor(self.text_edit.document())
        # cursor.movePosition(QtGui.QTextCursor.End)
        # cursor.insertImage(img)

        myDoc = QtGui.QTextDocument("This is a demo document")
        myDoc.setHtml(QtCore.QString(str))
        cursor = QtGui.QTextCursor(myDoc)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertImage(img)

        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setPageSize(QtGui.QPrinter.Letter)
        printer.setColorMode(QtGui.QPrinter.Color)
        printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
        printer.setOutputFileName("demo_doc.pdf")
        myDoc.print_(printer)

        self.text_edit.setDocument(myDoc)
        return


def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())

run()