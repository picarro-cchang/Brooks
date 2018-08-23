
import sys
import time
from PyQt4 import QtCore
from PyQt4 import QtGui
from functools import partial

class QNonBlockingTimer(QtCore.QObject):
    finish_signal = QtCore.pyqtSignal()
    tick_signal = QtCore.pyqtSignal(int,int, str, bool)
    ping_signal = QtCore.pyqtSignal(int,str)

    def __init__(self,
                 set_time_sec = None,       # How long the timer runs, 'None' runs forever
                 tick_interval_sec = 1,     # Interval between tick signals
                 description = "",          # Desc. emitted with timer signals
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
        self.ping_signal.emit(self.countdown_sec, self.description)
        return

    def stop(self):
        self.tick_timer.stop()
        self.event_loop.quit()
        self.finish_signal.emit()
        return


class QThreadedTimer(QtCore.QThread):
    finish_signal = QtCore.pyqtSignal()
    tick_signal = QtCore.pyqtSignal(int,int, str, bool)
    ping_signal = QtCore.pyqtSignal(int,str)

    def __init__(self,
                 set_time_sec = None,       # How long the timer runs, 'None' runs forever
                 tick_interval_sec = 1,     # Interval between tick signals
                 description = "",          # Desc. emitted with timer signals
                 busy_hint = False,         # If True, progress bars can show busy or waiting indication
                 parent = None
                 ):
        QtCore.QThread.__init__(self)
        self.set_time_sec = set_time_sec
        self.countdown_sec = set_time_sec
        self.description = description
        self.busy_hint = busy_hint
        return

    def __del__(self):
        self.wait()

    def run(self):
        set_time = 5
        t = QNonBlockingTimer(set_time_sec=self.set_time_sec, description=self.description, busy_hint=self.busy_hint)
        t.tick_signal.connect(self.tick_signal, type=QtCore.Qt.DirectConnection)
        t.finish_signal.connect(self.finish_signal, type=QtCore.Qt.DirectConnection)
        t.start()


def main():
    @QtCore.pyqtSlot(int, int, str, bool)
    def tick_slot(countdown, set_time, desc, busy):
        print("\t\t\t=== > Timer Count down: {0}".format(countdown))
        return

    def finish_slot():
        print("Timer finished")
        return

    # Demonstrate the QNonBlockingTimer stopping execution of this thread while the timer counts down.
    # Although it's blocking this thread, the GUI thread will continue to be responsive.
    # You will see the timer count down and then the counting loop the follow will be run.
    #
    # Use this timer if you want to pause a working thread and wait for user input, or you want
    # a delay, say for a gas to equilibrate, while keeping the GUI responsive.
    #
    print("Example 1 ========================================")
    set_time = 5
    print("Setting a timer to countdown {0} seconds.".format(set_time))
    t = QNonBlockingTimer(set_time)
    t.tick_signal.connect(tick_slot)
    t.finish_signal.connect(finish_slot)
    t.start()
    for i in xrange(5):
        print("Doing work after the timer releases the current thread. i={0}".format(i))
        time.sleep(1)
    print("\n\n\n")

    # Demonstrate the threaded version of QNonBlockingTimer.  In this case the timer starts and execution
    # of the current thread continues.  You will see the timer count down and simultaneously you will see
    # the loop that follow run at the same time (actually execution is switching rapidly between the
    # threads so they will look like they are running concurrently.
    #
    # Use this timer if you don't want the calling thread blocked.  You can use this as an independent
    # timer, like a stop watch.
    #
    print("Example 2 ========================================")
    tt_a = QThreadedTimer(set_time_sec=10, description="tt_a", busy_hint=False)
    tt_a.tick_signal.connect(tick_slot, type=QtCore.Qt.DirectConnection)
    tt_a.finish_signal.connect(finish_slot)
    tt_a.start()
    for i in xrange(15):
        print("--- > Main counter. i={0}".format(i))
        time.sleep(1)

    exit(1)

if __name__ == "__main__":
    app = QtCore.QCoreApplication(sys.argv)
    main()
    sys.exit(app.exec_())



