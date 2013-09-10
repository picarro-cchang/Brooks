"""
Copyright 2013 Picarro Inc.

Soil chamber model
"""

from __future__ import with_statement

import math
import csv


class Chamber(object):

    # Standard atmospheric pressure in Pascals
    PRESSURE = 101223.7
    GAS_CONST = 8.3144


    @staticmethod
    def loadFromCSV(csvFile):
        """
        Load a set of chambers from a .csv file. Returns a dict of Chamber
        instances keyed by chamber name.
        """

        chambers = {}
        with open(csvFile, 'rb') as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                chambers[row['Name']] = Chamber(float(row['Volume']),
                                                float(row['Area']))

        return chambers

    def __init__(self, volume, area):
        assert isinstance(volume, float)
        assert isinstance(area, float)

        self.volume = volume
        self.area = area

    def flux(self, concSlope, concSlopeSigma, temperature):
        """
        If the concentration slope is in ppm/s, then the returned flux is in
        micromol/m^2/s.
        """

        pvRat = (Chamber.PRESSURE * self.volume) / (Chamber.GAS_CONST *
                                                    self.area * temperature)
        return (concSlope * pvRat, concSlopeSigma * math.fabs(pvRat))

    def pvRA(self):
        """
        Intermediate value that may be reported as an output column.
        """

        return (Chamber.PRESSURE * self.volume) / (Chamber.GAS_CONST * self.area)

    def pvRAT(self, temperature):
        """
        Intermediate value that may be reported as an output column.
        """

        return self.pvRA() * (1.0 / temperature)
