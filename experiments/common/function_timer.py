import time
import inspect


class FunctionTimer(object):
    def __init__(self, time_unit='ms'):
        self.start = None
        self.end = None
        self.time_unit = time_unit

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        self.end = time.time()
        if self.time_unit == 'ms':
            total_time = 1000*(self.end - self.start)
        elif self.time_unit == 's':
            total_time = self.end - self.start
        else:
            raise KeyError(f'Time unit: {self.time_unit} not supported!')
        if __debug__:
            print(f'Total time: {round(total_time, 2)} {self.time_unit}\n')
