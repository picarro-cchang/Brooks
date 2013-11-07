"""
Copyright 2013 Picarro Inc

Wrapper around the functionality normally associated with a Picarro
.dat file.
"""

from __future__ import with_statement

import csv


class DatFile(object):

    @staticmethod
    def _load(fname, allowedCols):
        """
        Returns a dict-like object of named data streams. All data
        points are stored as strings. It is the caller's
        responsibility to cast data values to the correct type.
        """

        data = {}
        names= {}
        with open(fname, 'r') as fp:
            lines = fp.readlines()
            for i, col in enumerate(lines[0].split()):
                names[i] = col

                if allowedCols is None or col in allowedCols:
                    data[col] = []

            for line in lines[1:]:
                for i, v in enumerate(line.split()):
                    if allowedCols is None or names[i] in allowedCols:
                        data[names[i]].append(v)

        return data

    def __init__(self, fname, allowedCols):
        """
        Load and parse the specified .dat file.
        """

        self.fname = fname
        self.data = DatFile._load(self.fname, allowedCols)

    def __getattr__(self, stream):
        """
        Returns the requested data stream. An exception is raised if
        the data column does not exist.
        """

        if stream not in self.data.keys():
            raise AttributeError("'%s' is not a data column for '%s'." %
                                 (stream, self.fname))

        return self.data[stream]

    def __getitem__(self, stream):
        """
        Returns the requested data stream. An exception is raised if
        the data column does not exist.
        """

        return self.__getattr__(stream)

    def columnNames(self):
        return self.data.keys()

    def toCSV(self, outName):
        with open(outName, 'wb') as fp:
            writer = csv.writer(fp)
            names = self.columnNames()
            writer.writerow(names)
            for i in xrange(len(self.data[names[0]])):
                row = []
                for n in names:
                    row.append(self.data[n][i])
                writer.writerow(row)
