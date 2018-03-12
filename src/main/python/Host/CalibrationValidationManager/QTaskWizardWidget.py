from PyQt4 import QtCore, QtGui


class QTaskWizardWidget(QtGui.QWidget):
    start_run_signal = QtCore.pyqtSignal()
    next_signal = QtCore.pyqtSignal()
    abort_signal = QtCore.pyqtSignal()
    view_gases_signal = QtCore.pyqtSignal()
    hide_gases_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setLayout( self._init_gui() )
        self._startup_settings()
        self._set_connections()
        return

    def _init_gui(self):
        self._startRunBtn = QtGui.QPushButton("Start Run")
        self._nextBtn = QtGui.QPushButton("Next")
        self._abortBtn = QtGui.QPushButton("Abort")
        self._viewReportBtn = QtGui.QPushButton("View Report")
        self._text_edit = QtGui.QTextEdit("Instructions to user TBD")
        self._text_edit.setReadOnly(True)
        self._task_progressbar = QtGui.QProgressBar()

        # Set up a two state button
        self._ref_gases_visible = False
        self._viewReferenceGasesBtn = QtGui.QPushButton("Show Gases")

        hb = QtGui.QHBoxLayout()
        hb.addWidget(self._abortBtn)
        hb.addStretch(1)
        hb.addWidget(self._viewReferenceGasesBtn)
        hb.addWidget(self._viewReportBtn)
        hb.addWidget(self._startRunBtn)
        hb.addWidget(self._nextBtn)

        vb = QtGui.QVBoxLayout()
        vb.addWidget(self._text_edit)
        vb.addWidget(self._task_progressbar)
        vb.addLayout(hb)

        gb = QtGui.QGroupBox("Wizard")
        gb.setLayout(vb)

        mgl = QtGui.QGridLayout()
        mgl.addWidget(gb, 0, 0)
        return mgl

    def _set_connections(self):
        self._startRunBtn.clicked.connect(self._start_run)
        self._nextBtn.clicked.connect(self._next_step)
        self._abortBtn.clicked.connect(self._abort)
        self._viewReportBtn.clicked.connect(self._view_report)
        self._viewReferenceGasesBtn.clicked.connect(self._view_reference_gases_button_clicked)

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
        self._startRunBtn.setDisabled(True)
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
        print("Abort button pressed")
        # put user confirmation dialog here
        # send the abort signal
        # reset the widget states
        # Show a message box
        result = QtGui.QMessageBox.question(self,
                                            'Message', "Do you want to abort all tasks to start over or exit?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No)

        if result == QtGui.QMessageBox.Yes:
            print 'Yes.'
            QtGui.QMessageBox.critical(self,
                                       'Critical',
                                       "Abort code TBD",
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)
        else:
            print 'No.'
        return

    def _view_report(self):
        QtGui.QMessageBox.critical(self,
                                   'Critical',
                                   "View report code TBD",
                                   QtGui.QMessageBox.Ok,
                                   QtGui.QMessageBox.Ok)
        return

    def _view_reference_gases_button_clicked(self):
        if self._ref_gases_visible:
            self._ref_gases_visible = False
            self._viewReferenceGasesBtn.setText("Show Gases")
            self.hide_gases_signal.emit()
        else:
            self._ref_gases_visible = True
            self._viewReferenceGasesBtn.setText("Hide Gases")
            self.view_gases_signal.emit()
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
        self._text_edit.setText("Job completed, message TBD")
        self._startup_settings()
        self._viewReportBtn.setEnabled(True)
        return
