"""
Copyright 2013 Picarro Inc.
"""

import os
import optparse
import sqlite3
import fnmatch
from os import path
from datetime import datetime

from Host.Common import DatFile


def _createDb(dataDb):
    c = dataDb.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS data('
              'id INTEGER PRIMARY KEY,'
              'analyzerId TEXT,'
              'speciesId INTEGER,'
              'multiPosValve REAL,'
              'solenoidValve REAL,'
              'epochTime REAL,'
              'CO REAL,'
              'CO2 REAL)')
    dataDb.commit()
               
def _insertFile(dataDb, fname, analyzer):
    dat = DatFile.DatFile(fname, ['SPECTRUMID', 'DATE', 'TIME', 'MULTI_POS_VALVE', 'SOLENOID_VALVES', 'CO', 'CO2'])
    c = dataDb.cursor()
    for i, _ in enumerate(dat['SPECTRUMID']):
        epochTime = (datetime.strptime("%s %s" % (dat['DATE'][i], dat['TIME'][i]),
                                       "%m/%d/%y %H:%M:%S.%f") - datetime.utcfromtimestamp(0)).total_seconds()
        c.execute('INSERT INTO data('
                  'analyzerId, speciesId, multiPosValve, solenoidValve, epochTime, CO, CO2) '
                  'VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (analyzer, dat['SPECTRUMID'][i], dat['MULTI_POS_VALVE'][i], dat['SOLENOID_VALVES'][i], epochTime,
                   dat['CO'][i], dat['CO2'][i]))
    dataDb.commit()

def main(opts):
    dbFile = path.join(path.dirname(__file__), 'data.db')
    dataDb = sqlite3.connect(dbFile)

    _createDb(dataDb)

    # Start walking files
    for root, dirs, files in os.walk(opts.rootDir):
        print root
        for f in files:
            if fnmatch.fnmatch(f, '*.dat'):
                print "\t%s" % f
                _insertFile(dataDb, path.join(root, f), opts.analyzer)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--root', dest='rootDir', metavar='ROOT')
    parser.add_option('--analyzer', dest='analyzer', metavar='ANALYZER')
    
    opts, _ = parser.parse_args()

    main(opts)
