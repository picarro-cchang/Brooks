
import sys
from PyQt4 import QtCore
from PyQt4 import QtGui

class QNonBlockingTimer(QtCore.QObject):
    finish_signal = QtCore.pyqtSignal()
    tick_signal = QtCore.pyqtSignal(int,int, str, bool)

    def __init__(self,
                 set_time_sec = None,       # How long the timer runs, 'None' runs forever
                 tick_interval_sec = 1,     # Interval between tick signals
                 description = None,        # Desc. emitted with timer signals
                 busy_hint = False,         # If True, progress bars can show busy or waiting indication
                 parent = None
                 ):
        super(QNonBlockingTimer, self).__init__(parent)
        self.set_time_sec = set_time_sec
        self.countdown_sec = set_time_sec
        self.description = description
        self.busy_hint = busy_hint
        self.master_timer = None
        self.tick_timer = QtCore.QTimer()
        self.tick_timer.setInterval(tick_interval_sec * 1000)
        self.tick_timer.timeout.connect(self.tick)
        self.event_loop = QtCore.QEventLoop()
        return

    def start(self):
        self.tick_signal.emit(self.countdown_sec, self.set_time_sec, self.description, self.busy_hint)
        self.master_timer = QtCore.QTimer.singleShot(self.set_time_sec * 1000, self.stop)
        self.tick_timer.start()
        self.event_loop.exec_()
        return

    def tick(self):
        self.countdown_sec -= 1
        self.tick_signal.emit(self.countdown_sec, self.set_time_sec, self.description, self.busy_hint)
        return

    def stop(self):
        self.tick_timer.stop()
        self.event_loop.quit()
        self.finish_signal.emit()
        return


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    t = QNonBlockingTimer(5)
    t.start()
    exit(1)



