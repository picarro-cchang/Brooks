"""
Copyright 2013 Picarro Inc.
"""

from __future__ import with_statement

import csv


class Measurement(object):
    """
    Represent a single measurement
    """

    SPECIES = [
        'CO2',
        'CH4',
        'N2O',
        'H2O']


    @staticmethod
    def loadFromCSV(csvFile):
        """
        Load a sequence of measurements from a .csv file. Returns a list of
        measurements.
        """

        measurements = []
        with open(csvFile, 'rb') as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                measurements.append(
                    Measurement(row['Name'],
                                float(row['Start Time']),
                                float(row['Stop Time']),
                                row['Species'],
                                float(row['Temperature']),
                                row['Chamber']))

        return measurements

    def __init__(self, name, startEpoch, stopEpoch, species, temperatureC, chamber):
        assert isinstance(name, str)
        assert isinstance(startEpoch, float)
        assert isinstance(stopEpoch, float)
        assert isinstance(species, str)
        assert (species in Measurement.SPECIES) or (species == 'All')
        assert isinstance(temperatureC, float)
        assert isinstance(chamber, str)

        self.name = name
        self.startEpoch = startEpoch
        self.stopEpoch = stopEpoch
        self.species = species
        self.temperatureK = temperatureC + 273.15
        self.chamber = chamber
