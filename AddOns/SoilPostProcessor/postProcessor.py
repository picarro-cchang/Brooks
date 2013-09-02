"""
Copyright 2013, Picarro Inc.
"""

from __future__ import with_statement

import sys
import optparse
import pprint
import time
import csv
import os.path

import numpy
from scipy import stats
from matplotlib import pyplot

from Host.Common import DatFile

from ChiSquared import ChiSquared
from Chamber import Chamber
from Measurement import Measurement


def _log(msg):
    # Use this as a hook to interface with central app logging later.
    print msg


def main(opts):
    # Load chamber configurations
    assert opts.chambersFile
    chambers = Chamber.loadFromCSV(opts.chambersFile)
    pprint.pprint(chambers)

    # Load requested measurement configurations
    assert opts.measurementsFile
    measurements = Measurement.loadFromCSV(opts.measurementsFile)
    pprint.pprint(measurements)

    # Assume a single dat file with all data points in it?
    assert opts.datFile
    rawData = DatFile.DatFile(opts.datFile)
    data = {
        'epochTime' : [float(x) for x in rawData['EPOCH_TIME']],
        'N2O'       : [float(x) for x in rawData['N2O_dry']],
        'CO2'       : [float(x) for x in rawData['CO2_dry']],
        'CH4'       : [float(x) for x in rawData['CH4_dry']],
        'H2O'       : [float(x) for x in rawData['H2O']]}

    if hasattr(sys, 'frozen'):
        root = os.path.abspath(os.path.dirname(sys.executable))
    else:
        root = os.path.abspath(os.path.dirname(__file__))

    outputRoot = os.path.join(root, 'output')
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
        # Always compute all results and then use the species selector
        # to report the requested result(s).
        startIdx = data['epochTime'].index(m.startEpoch)
        assert startIdx is not None
        stopIdx = data['epochTime'].index(m.stopEpoch)
        assert stopIdx is not None

        epochTime = data['epochTime'][startIdx:stopIdx]

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
            conc = data[species][startIdx:stopIdx]

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

            pyplot.plot(epochTime, conc, 'bo', label="%s - Raw" % species)
            pyplot.plot(epochTime, fit, 'r', label="%s - Fit" % species)
            pyplot.xlabel('Epoch time (s)')
            pyplot.ylabel("%s concentration (ppm)" % species)
            pyplot.legend(loc=0)
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


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--dat', dest='datFile', metavar='DAT_FILE',
                      default=None, help=('The .dat file to run the specified '
                                          'measurements again.'))
    parser.add_option('--chambers', dest='chambersFile',
                      metavar='CHAMBERS_FILE', default=None,
                      help=('The .csv file defining the properties of the '
                            'chambers used in the measurements.'))
    parser.add_option('--measurements', dest='measurementsFile',
                      metavar='MEASUREMENTS_FILE', default=None,
                      help=('The .csv file defining the parameters for '
                            'each individual measurment.'))

    options, _ = parser.parse_args()

    if not options.datFile:
        sys.exit('A .dat file must be specified.')

    if not options.chambersFile:
        sys.exit('A chamber file must be specified.')

    if not options.measurementsFile:
        sys.exit('A measurements file must be specified.')

    main(options)
