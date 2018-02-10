
import sys
from PyQt4 import QtCore
from PyQt4 import QtGui

class QNonBlockingTimer(QtCore.QObject):
    finish_signal = QtCore.pyqtSignal()
    tick_signal = QtCore.pyqtSignal(str)

    def __init__(self,
                 set_time_sec = None,       # How long the timer runs, 'None' runs forever
                 tick_interval_sec = 1,     # Interval between tick signals
                 parent = None
                 ):
        super(QNonBlockingTimer, self).__init__(parent)
        self.set_time_sec = set_time_sec
        self.countdown = set_time_sec
        self.tick_timer = QtCore.QTimer()
        self.tick_timer.setInterval(tick_interval_sec * 1000)
        self.tick_timer.timeout.connect(self.tick)
        self.event_loop = QtCore.QEventLoop()
        return

    def start(self):
        QtCore.QTimer.singleShot(self.set_time_sec * 1000, self.stop)
        self.tick_timer.start()
        self.event_loop.exec_()
        return

    def tick(self):
        self.countdown -= 1
        self.tick_signal.emit(str(self.countdown))
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



