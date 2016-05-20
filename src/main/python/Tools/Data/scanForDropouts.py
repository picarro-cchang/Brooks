"""
Copyright 2013 Picarro Inc.

Scan a series of .dat files for any data dropouts.
"""

from __future__ import with_statement

import optparse
import re
import pprint
import os.path
import datetime
import time

from Host.Common import namedtuple


DATALOG_RE = re.compile(r'([A-Z]{4,6}\d{4}).*-DataLog_(User|Private)\.dat')
EXCLUDE_DIRS = ['.bzr', '.git']

DELTA_STATS = []
DeltaStat = namedtuple.namedtuple('DeltaStat', 't dt hp12CH4 hr12CH4 path')


def _parseDatFile(path):
    print path

    first = True

    with open(path, 'r') as fp:
        lines = fp.readlines()

        colNames = {}
        for i, name in enumerate(lines[0].split()):
            colNames[name] = i

        epochTimeIdx = None

        if 'EPOCH_TIME' in colNames:
            epochTimeIdx = colNames['EPOCH_TIME']
        else:
            dateIdx = colNames['DATE']
            timeIdx = colNames['TIME']

        hp12CH4Idx = colNames['HP_12CH4']
        hr12CH4Idx = colNames['HR_12CH4']

        for l in lines[1:]:
            vals = l.split()

            try:
                if epochTimeIdx:
                    t = float(vals[epochTimeIdx])
                else:
                    dateStr = vals[dateIdx]
                    timeStr = vals[timeIdx].split('.')[0]
                    t = datetime.datetime.strptime("%s %s" % (dateStr, timeStr),
                                                   "%Y-%m-%d %H:%M:%S")
                    t = time.mktime(t.timetuple())

                s = dict(t=t,
                         hp12CH4=float(vals[hp12CH4Idx]),
                         hr12CH4=float(vals[hr12CH4Idx]),
                         path=path,
                         dt=0.0)
            except:
                import traceback
                traceback.print_exc()
                print "Malformed line: # vals (%s) != # column names (%s)" % (
                    len(vals), len(colNames.keys()))
                return

            if not first:
                s.update(dt=s['t'] - DELTA_STATS[-1]['t'])

            first = False
            DELTA_STATS.append(s)


def main(opts):
    for root, dirs, files in os.walk(opts.rootDir):
        for d in EXCLUDE_DIRS:
            if d in dirs:
                dirs.remove(d)

        for f in files:
            m = DATALOG_RE.search(f)
            if m is not None:
                _parseDatFile(os.path.join(root, f))

    with open('stats.csv', 'w') as fp:
        fp.write("Epoch Time (s),Delta Time (s),HP 12CH4 (ppm),"
                 "HR 12CH4 (ppm),File\n")
        for s in DELTA_STATS:
            fp.write("%s,%s,%s,%s,%s\n" % (s['t'], s['dt'], s['hp12CH4'],
                                           s['hr12CH4'], s['path']))

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--root', '-r', dest='rootDir',
                      metavar='ROOT_DIR', help='The root directory to start '
                      'scanning for .dat files.')

    options, _ = parser.parse_args()

    main(options)
