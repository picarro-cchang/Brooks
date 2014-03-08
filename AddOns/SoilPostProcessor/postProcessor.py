"""
Copyright 2013, Picarro Inc.
"""

from __future__ import with_statement

import sys
import optparse
import pprint
import time
import csv
import shutil
import os.path

import numpy
from scipy import stats
from matplotlib import pyplot

from Host.Common import DatFile

from ChiSquared import ChiSquared
from Chamber import Chamber
from Measurement import Measurement


#  SIDs from the JFAADS v6 fitter:
#    2  Ammonia and water from AADS (V6 modifies schemes to unify NH3
#       and H2O measurements)
#    3  "Big water" from AADS (not used)
#    4  Ammonia only from AADS (not used starting with V6)
#   25  CH4 from CFADS
#   45  N2O only
#   46  CO2 at 6058.2 wvn developed for JADS
#   47  N2O, CO2, and HDO
SPECIES = {
    'NH3' : [2.0, 3.0, 4.0],
    'CH4' : [25.0],
    'N2O' : [45.0, 47.0],
    'CO2' : [46.0, 47.0],
    'H2O' : [2.0, 3.0, 47.0]
    }


def _log(msg):
    # Use this as a hook to interface with central app logging later.
    print msg


def _epochTimeFromRow(row):
    return float((row.split()[5]).strip())


def _nearestIdx(t, data, roundToZero=True):
    """
    Data should be in (epochTime, value) tuples. roundToZero controls the
    direction.
    """

    minDt = 100.0
    idx = 0
    for i, d in enumerate(data):
        dt = abs(d[0] - t)
        if dt < minDt:
            minDt = dt
            idx = i

    if data[idx][0] < t and not roundToZero:
        idx += 1
    elif data[idx][0] > t and roundToZero:
        idx -= 1

    assert idx >= 0 and idx < len(data)

    return idx


def main(opts):
    # Load chamber configurations
    assert opts.chambersFile
    chambers = Chamber.loadFromCSV(opts.chambersFile)

    # Load requested measurement configurations
    assert opts.measurementsFile
    measurements = Measurement.loadFromCSV(opts.measurementsFile)

    # Build the complete dataset for analysis
    assert opts.datDir
    rows = []
    headerRow = None

    for f in os.listdir(opts.datDir):
        _, ext = os.path.splitext(f)

        if ext != '.dat':
            continue

        if f == 'master.dat':
            continue

        with open(os.path.join(opts.datDir, f), 'r') as fp:
            print "Adding '%s'"  % f

            rawRows = fp.readlines()

            if not headerRow:
                headerRow = rawRows[0]

            allRows = []
            for i, r in enumerate(rawRows):
                if len(r.split()) == len(headerRow.split()):
                    allRows.append(r)
                else:
                    print "Skip: %s %s" % (f, i)

            rows.extend(allRows[1:])

    assert headerRow

    # Sort by epoch time
    rows.sort(key=_epochTimeFromRow)
    rows.insert(0, headerRow)

    with open(os.path.join(opts.datDir, 'master.dat'), 'w') as fp:
        fp.writelines(rows)

    rawData = DatFile.DatFile(os.path.join(opts.datDir, 'master.dat'),
                              ['species', 'EPOCH_TIME', 'CH4', 'N2O', 'CO2',
                               'H2O', 'ChemDetect'])

    data = {
        'CH4' : [],
        'N2O' : [],
        'CO2' : [],
        'H2O' : []
        }

    chemDetect = {
        'CH4' : [],
        'N2O' : [],
        'CO2' : [],
        'H2O' : []
        }


    if opts.filterData:
        for i, sid in enumerate(rawData['species']):
            t = float(rawData['EPOCH_TIME'][i])

            for k in data.keys():
                if float(sid) in SPECIES[k]:
                    data[k].append((t, float(rawData[k][i])))
                    chemDetect[k].append(float(rawData['ChemDetect'][i]))
    else:
        for i, t in enumerate(rawData['EPOCH_TIME']):
            for k in data.keys():
                data[k].append((float(t), float(rawData[k][i])))
                chemDetect[k].append(float(rawData['ChemDetect'][i]))

    if hasattr(sys, 'frozen'):
        root = os.path.abspath(os.path.dirname(sys.executable))
    else:
        root = os.path.abspath(os.path.dirname(__file__))

    outputRoot = os.path.join(root, 'output', time.strftime('%Y%m%d-%H%M%S',
                                                            time.gmtime()))
    if not os.path.isdir(outputRoot):
        os.makedirs(outputRoot)

    results = []
    header = ['Name',
              'Temperature (degK)',
              'Chamber',
              'Volume (m^3)',
              'PV/RA',
              'PV/RAT']
    for species in Measurement.SPECIES:
        header.extend(["%s Fit R^2" % species,
                       "%s Slope (ppm/s)" % species,
                       "%s Slope Uncertainty (ppm/s)" % species,
                       "%s Flux (micromol/m^2/s)" % species,
                       "%s Flux Uncertainty (micromol/m^2/s)" % species])

    for m in measurements:
        result = [m.name,
                  m.temperatureK,
                  m.chamber,
                  chambers[m.chamber].volume,
                  chambers[m.chamber].pvRA(),
                  chambers[m.chamber].pvRAT(m.temperatureK)]

        measurementDir = os.path.join(outputRoot, m.name)
        if not os.path.exists(measurementDir):
            os.makedirs(measurementDir)

        for species in Measurement.SPECIES:
            startIdx = _nearestIdx(m.startEpoch, data[species],
                                   roundToZero=False)
            stopIdx = _nearestIdx(m.stopEpoch, data[species])

            print "startIdx = %s, stopIdx = %s" % (startIdx, stopIdx)

            if stopIdx < startIdx:
                print "Error: measurement = '%s', start=%s, stop=%s" % (m.name,
                                                                        m.startEpoch,m.stopEpoch)

            epochTime = [x[0] for x in data[species][startIdx:stopIdx]]
            conc = [x[1] for x in data[species][startIdx:stopIdx]]

            a, b, sigmaA, sigmaB = ChiSquared.fitStraightLine(
                epochTime,
                conc)

            fit = (b * (numpy.array(epochTime) - epochTime[0])) + a
            r = stats.pearsonr(conc, fit)[0]

            result.extend([
                r * r,
                b,
                sigmaB,
                chambers[m.chamber].flux(b, sigmaB, m.temperatureK)[0],
                chambers[m.chamber].flux(b, sigmaB, m.temperatureK)[1]])

            fig, concAxis = pyplot.subplots()
            concAxis.plot(epochTime, conc, 'bo', label="%s - Raw" % species)
            concAxis.plot(epochTime, fit, 'r', label="%s - Fit" % species)
            concAxis.set_xlabel('Epoch time (s)')
            concAxis.set_ylabel("%s concentration (ppm)" % species)
#            fig.legend(loc=0)
            chemDetectAxis = concAxis.twinx()
            chemDetectAxis.plot(epochTime, chemDetect[species][startIdx:stopIdx])
            chemDetectAxis.set_ylabel('ChemDetect')
            chemDetectAxis.set_ylim([-0.2, 1.2])
            pyplot.savefig(os.path.join(measurementDir, "%s.png" % species),
                           bbox_inches=0)
            pyplot.close()

            # Residuals
            pyplot.plot(epochTime, conc - fit, 'bo',
                        label="%s - Residual" % species)
            pyplot.xlabel('Epoch time (s)')
            pyplot.ylabel("%s residual (ppm)" % species)
            pyplot.legend(loc=0)
            pyplot.savefig(os.path.join(measurementDir,
                                        "%s-residuals.png" % species),
                           bbox_inches=0)
            pyplot.close()

        results.append(result)

    with open(os.path.join(outputRoot, 'results.csv'), 'wb') as fp:
        writer = csv.writer(fp)
        writer.writerow(header)
        writer.writerows(results)

    shutil.copy(opts.chambersFile,
                os.path.join(outputRoot, os.path.split(opts.chambersFile)[1]))
    shutil.copy(opts.measurementsFile,
                os.path.join(outputRoot,
                             os.path.split(opts.measurementsFile)[1]))


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--dat', dest='datDir', metavar='DAT_DIR',
                      default=None, help=('The directory containing the .dat '
                                          'files to analyze.'))
    parser.add_option('--chambers', dest='chambersFile',
                      metavar='CHAMBERS_FILE', default=None,
                      help=('The .csv file defining the properties of the '
                            'chambers used in the measurements.'))
    parser.add_option('--measurements', dest='measurementsFile',
                      metavar='MEASUREMENTS_FILE', default=None,
                      help=('The .csv file defining the parameters for '
                            'each individual measurment.'))
    parser.add_option('--filter', dest='filterData', action='store_true',
                      default=False,
                      help=('Filter the aggregate data by species.'))

    options, _ = parser.parse_args()

    if not options.datDir:
        sys.exit('A .dat file directory must be specified.')

    if not options.chambersFile:
        sys.exit('A chamber file must be specified.')

    if not options.measurementsFile:
        sys.exit('A measurements file must be specified.')

    main(options)
