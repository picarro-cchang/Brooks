import subprocess32
import QGuiText
from PyQt4 import QtCore, QtGui

class QReportDisplayDialog(QtGui.QDialog):
    def __init__(self, fileName = None, textDoc = None, parent = None):
        QtGui.QDialog.__init__(self)
        self.setFixedSize(1024, 768)
        self._textEditWidget = QtGui.QTextEdit()
        self._textEditWidget.setDocument(textDoc)
        self._fileNameWidget = QtGui.QLineEdit(fileName)
        self.setLayout( self._initGui() )
        self._setConnections()
        return

    def _initGui(self):
        self._okBtn = QtGui.QPushButton("OK")

        fnhb = QtGui.QHBoxLayout()
        fnhb.addWidget(QtGui.QLabel("Validation Report File:"))
        fnhb.addWidget(self._fileNameWidget)

        hb = QtGui.QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(self._okBtn)

        gl = QtGui.QGridLayout()
        gl.addWidget(self._textEditWidget, 0, 0)
        gl.addLayout(fnhb, 1, 0)
        gl.addLayout(hb, 2, 0)
        return gl

    def _setConnections(self):
        self._okBtn.clicked.connect(self.close)
        return

class QTaskWizardWidget(QtGui.QWidget):
    start_run_signal = QtCore.pyqtSignal()
    next_signal = QtCore.pyqtSignal()
    abort_signal = QtCore.pyqtSignal()
    job_complete_signal = QtCore.pyqtSignal()
    view_editors_signal = QtCore.pyqtSignal()
    hide_editors_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self._reportTextObj = None          # QTextDocument object containing the measurement report
        self._reportFileName = None         # File name of the PDF doc containing _reportTextObj
        self._running = False               # Track if we are in a validation run
        self.setLayout( self._init_gui() )
        self._startup_settings()
        self._set_connections()
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        return

    def _init_gui(self):
        self._startRunBtn = QtGui.QPushButton("Start Run")
        self._nextBtn = QtGui.QPushButton("Next")
        self._abortBtn = QtGui.QPushButton("Abort")
        self._viewReportBtn = QtGui.QPushButton("View Report")
        self._openFileManagerBtn = QtGui.QPushButton("Download Report")
        self._text_edit = QtGui.QTextEdit(QGuiText.welcome_text())
        self._text_edit.setReadOnly(True)
        self._task_progressbar = QtGui.QProgressBar()

        # Set up a two state button
        self._editors_visible = False
        self._showEditorsBtn = QtGui.QPushButton("Show Editors")

        self._startRunBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._nextBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._abortBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._viewReportBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._openFileManagerBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._text_edit.setFocusPolicy(QtCore.Qt.NoFocus)
        self._task_progressbar.setFocusPolicy(QtCore.Qt.NoFocus)
        self._showEditorsBtn.setFocusPolicy(QtCore.Qt.NoFocus)

        hb = QtGui.QHBoxLayout()
        hb.addWidget(self._abortBtn)
        hb.addStretch(1)
        hb.addWidget(self._showEditorsBtn)
        hb.addWidget(self._openFileManagerBtn)
        hb.addWidget(self._viewReportBtn)
        hb.addWidget(self._startRunBtn)
        hb.addWidget(self._nextBtn)

        vb = QtGui.QVBoxLayout()
        vb.addWidget(self._text_edit)
        vb.addWidget(self._task_progressbar)
        vb.addLayout(hb)

        gb = QtGui.QGroupBox()
        gb.setLayout(vb)

        mgl = QtGui.QGridLayout()
        mgl.addWidget(gb, 0, 0)
        return mgl

    def _set_connections(self):
        self._startRunBtn.clicked.connect(self._start_run)
        self._nextBtn.clicked.connect(self._next_step)
        self._abortBtn.clicked.connect(self._abort)
        self._viewReportBtn.clicked.connect(self._view_report)
        self._showEditorsBtn.clicked.connect(self._show_editors_button_clicked)
        self._openFileManagerBtn.clicked.connect(self._open_filemanager)

    def _startup_settings(self):
        """
        Set the widgets states before starting a measurement run.
        :return:
        """
        self._startRunBtn.setEnabled(True)
        self._nextBtn.setEnabled(False)
        self._abortBtn.setEnabled(False)
        self._viewReportBtn.setEnabled(False)
        self._task_progressbar.setRange(0, 100)
        self._task_progressbar.setValue(0)

    def _start_run(self):
        """
        Start the main measurement job.
        Set the local widgets for this state.
        :return:
        """
        self._running = True
        self._reportTextObj = None
        self._startRunBtn.setEnabled(False)
        self._nextBtn.setEnabled(False)
        self._viewReportBtn.setEnabled(False)
        self._abortBtn.setEnabled(True)
        self.start_run_signal.emit()

    def _next_step(self):
        """
        After the user clicks NEXT run this method. This advances to the
        next task.
        :return:
        """
        self._nextBtn.setDisabled(True)
        self.next_signal.emit()

    def _abort(self):
        """
        Confirm abort of measurement job.  If confirmed send a signal and
        let the TaskManager manage further user interaction or programmed
        shutdown activities.
        :return:
        """
        # put user confirmation dialog here
        # send the abort signal
        # reset the widget states
        # Show a message box
        result = QtGui.QMessageBox.question(self,
                                            'Message', "Do you want to abort all tasks to start over or exit?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No)

        if result == QtGui.QMessageBox.Yes:
            QtGui.QMessageBox.critical(self,
                                       'Critical',
                                       "Close all gas valves then click OK",
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)
            self.abort_signal.emit()
        else:
            print 'No.'
        return

    def _view_report(self):
        report_dialog = QReportDisplayDialog(fileName = self._reportFileName, textDoc = self._reportTextObj, parent = self)
        report_dialog.exec_()
        return

    def _open_filemanager(self):
        cmd = ["python",
               "/usr/local/picarro/qtLauncher/FileManager/main.py",
               "--dir",
               "/home/picarro/I2000/Log/ValidationReport",
               "--name",
               "ValidationReport"]
        p = subprocess32.Popen(cmd, stdin=None, stdout=None, stderr=None)
        return

    def _show_editors_button_clicked(self):
        if self._editors_visible:
            self._editors_visible = False
            if not self._running:
                self._text_edit.setText(QGuiText.welcome_text())
            self._showEditorsBtn.setText("Show Editors")
            self.hide_editors_signal.emit()
        else:
            self._editors_visible = True
            if not self._running:
                self._text_edit.setText(QGuiText.editor_instructions())
            self._showEditorsBtn.setText("Hide Editors")
            self.view_editors_signal.emit()
        return

    def prompt_user(self):
        """
        If the current task is requires the user to do something, a message
        alerting the user is set (in setText()) and here the NEXT button
        is enabled.
        :return:
        """
        self._nextBtn.setEnabled(True)
        return

    def setText(self, text):
        self._text_edit.setText(QtCore.QString(text))
        return

    def setProgressBar(self, percent_complete, busy):
        """
        Update the progress bar as a task proceeds.
        If busy = True, we are waiting for user input and set the progress bar in busy
        indicator mode (bar slides back and forth).
        :param percent_complete:
        :param busy:
        :return:
        """
        if busy:
            self._task_progressbar.setRange(0, 0)
        else:
            self._task_progressbar.setRange(0, 100)
            self._task_progressbar.setValue(percent_complete)
        return

    def job_complete(self):
        self._running = False
        self._text_edit.setText("Job completed, message TBD")
        self._startup_settings()
        self._viewReportBtn.setEnabled(True)
        self.job_complete_signal.emit()
        return

    def job_aborted(self):
        self._running = False
        self._text_edit.setText("Job Aborted")
        self._startup_settings()
        self._viewReportBtn.setEnabled(False)
        return

    def set_report(self, fileName, obj):
        """
        Receive the report (a QTextDocument) and save it for display.  This object is cleared if a
        new job is started.
        :param obj:
        :return:
        """
        self._reportFileName = fileName
        self._reportTextObj = obj
        return

    def warming_up_warming_dialog(self):
        str = "The analyzer is warming up and cannot measure the validation gas.\n"
        str += "Wait until data appears in the time series plot and then click START.\n"
        QtGui.QMessageBox.information(self,
                                      'Information',
                                      str,
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
        self._startup_settings()
        return