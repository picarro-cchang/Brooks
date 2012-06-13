#
# Copyright (c) 2012 Picarro, Inc. All rights reserved
#
"""
Store temperature scan data in this class. The class could also be extended
to include additional data like laser current and etalon readings.
"""


class TemperatureScanData(object):
    """
    Convenience container for storing temperature scan data. Should provide
    clean access to scan results.
    """

    def __init__(self):
        self.temps = []
        self.thetas = []
        self.ratios = [[], []]

    # In the future we can wrap min()/max() into __getattr__ and then
    # we can cache the list comprehension so we don't have to run it
    # more than once.
    def min(self):
        """
        Returns an array [ratio 1 minimum, ratio 2 minimum].
        """
        return [min(r) for r in self.ratios]

    def max(self):
        """
        Returns an array [ratio 1 maximum, ratio 2 maximum].
        """
        return [max(r) for r in self.ratios]

    def addR1(self, r):
        self.ratios[0].append(r)

    def addR2(self, r):
        self.ratios[1].append(r)

    def addTemperature(self, t):
        self.temps.append(t)

    def addTheta(self, t):
        self.thetas.append(t)
