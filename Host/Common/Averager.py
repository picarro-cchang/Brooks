#
# Simple class to create averagers.
#
# Copyright (c) 2012 Picarro, Inc. All rights reserved
#

class Averager(object):
    # Averages non-None values added to it
    def __init__(self):
        self.total = 0
        self.count = 0


    def addValue(self, value):
        if value is not None:
            self.total += value
            self.count += 1


    def getAverage(self):
        if self.count == 0:
            raise ValueError, "No values to average."

        return self.total / self.count
