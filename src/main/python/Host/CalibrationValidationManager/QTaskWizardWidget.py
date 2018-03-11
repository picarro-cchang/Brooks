from PyQt4 import QtCore, QtGui


class QTaskWizardWidget(QtGui.QWidget):
    start_run_signal = QtCore.pyqtSignal()
    next_signal = QtCore.pyqtSignal()
    abort_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setLayout( self._init_gui() )
        self._set_connections()
        return

    def _init_gui(self):
        self._startRunBtn = QtGui.QPushButton("Start Run")
        self._nextBtn = QtGui.QPushButton("Next")
        self._abortBtn = QtGui.QPushButton("Abort")
        self._text_edit = QtGui.QTextEdit("Text Edit H<sub>2</sub>O")
        self._text_edit.setReadOnly(True)
        self._task_progressbar = QtGui.QProgressBar()
        self._task_progressbar.setValue(0)

        hb = QtGui.QHBoxLayout()
        hb.addWidget(self._abortBtn)
        hb.addStretch(1)
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

    def _start_run(self):
        """
        Set the local widgets for this state
        :return:
        """
        self._startRunBtn.setDisabled(True)
        self.start_run_signal.emit()

    def setText(self, text):
        self._text_edit.setText(QtCore.QString(text))
        return

    def setProgressBar(self, percent_complete):
        self._task_progressbar.setValue(percent_complete)
        return