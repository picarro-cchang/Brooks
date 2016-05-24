"""
Copyright 2012 Picarro Inc.

Streams data from the CM-CRDS Thermocouple Characterization firmware to a CSV
file.
"""

from __future__ import with_statement

import time
import serial
import optparse
import csv


def _readDataToCSV(opts):
    port = serial.Serial("COM%s" % opts.port)
    try:
        with open('thermocoupleTemps.csv', 'wb') as csvFp:
            writer = csv.writer(csvFp)
            while True:
                row = [time.time()]
                row.extend(port.readline().rstrip('\r\n').split(','))
                writer.writerow(row)
                csvFp.flush()
    finally:
        port.close()

def main():
    usage = """
%prog [options]

Connect to the themocouple test jig and stream the data back to a .csv file.
"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-p', '--port', dest='port', metavar='PORT',
                      default=1, help='Specify the COM port to connect to.')
    options, _ = parser.parse_args()

    _readDataToCSV(options)


if __name__ == '__main__':
    main()
