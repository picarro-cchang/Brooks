#!/usr/bin/python
#
# File Name: SchemeProcessor.py
#
# Purpose: Processes frequency-based scheme files, evaluating embedded
#  codes in a sandbox
#
# Notes:
#
# File History:
# 2010-10-21 sze   Created file
# 2018-09-10 sze   Added handling of schemeInfo for passing any appropriate metadata

import os
import pickle
from Host.autogen.interface import NUM_SCHEME_ROWS
from Host.Common.configobj import ConfigObj
from copy import deepcopy

# Memoize configuration files for efficiency
configMemo = {}


def clearMemo():
    configMemo.clear()


class Row(object):
    keynames = {
        'setpoint': 0,
        'dwell': 1,
        'subschemeId': 2,
        'virtualLaser': 3,
        'threshold': 4,
        'pzt': 5,
        'laserTemp': 6,
        'extra1': 7,
        'extra2': 8,
        'extra3': 9,
        'extra4': 10,
        'frontMirrorDac': 11,
        'backMirrorDac': 12,
        'coarsePhaseDac': 13,
        'modeIndex': 14,
    }

    def __init__(self, *a, **k):
        self.data = 15 * [0]
        self.data[:len(a)] = a
        for n in k:
            if n in self.keynames:
                self.data[self.keynames[n]] = k[n]
            else:
                raise IndexError('Unknown key %s in scheme row' % n)

    def __getattr__(self, n):
        if n in self.keynames:
            return self.data[self.keynames[n]]
        else:
            raise AttributeError('Unknown key %s when getting scheme row attribute' % n)

    def __setattr__(self, n, v):
        if n in self.keynames:
            self.data[self.keynames[n]] = v
        else:
            object.__setattr__(self, n, v)

    def __str__(self):
        return "%.5f,%d,%d,%d,%d,%d,%.4f,%d,%d,%d,%d,%d,%d,%d,%d" % (
            self.setpoint, self.dwell, self.subschemeId, self.virtualLaser, self.threshold, self.pzt, self.laserTemp, self.extra1,
            self.extra2, self.extra3, self.extra4, self.frontMirrorDac, self.backMirrorDac, self.coarsePhaseDac, self.modeIndex)

    def __repr__(self):
        return "Row(%s)" % self.__str__()


class SchemeError(Exception):
    pass


class Scheme(object):
    def __init__(self, fileName=None):
        self.fileName = fileName
        self.lineNum = 0
        self.errors = []
        self.numErrors = 0
        # Define sandbox environment for scheme
        self.schemePath = None
        if self.fileName is not None:
            self.schemePath = os.path.split(os.path.abspath(self.fileName))[0]
        self.version = 0
        self.nrepeat = 0
        self.numEntries = 0
        self.schemeInfo = None
        self.setpoint = []
        self.dwell = []
        self.subschemeId = []
        self.virtualLaser = []
        self.threshold = []
        self.pztSetpoint = []
        self.laserTemp = []
        self.extra1 = []
        self.extra2 = []
        self.extra3 = []
        self.extra4 = []
        self.frontMirrorDac = []
        self.backMirrorDac = []
        self.coarsePhaseDac = []
        self.modeIndex = []
        if self.fileName is not None:
            self.compile()
        if self.numErrors > 0:
            raise SchemeError(self.__str__())

    def __str__(self):
        descr = ['Scheme version %d from %s' % (self.version, self.fileName)]
        if self.numErrors > 0:
            descr.append('Errors encountered while processing scheme:')
            descr += self.errors
        else:
            descr.append('Repeat count: %d, Rows: %d' % (self.nrepeat, self.numEntries))
        return '\n'.join(descr)

    def evalInEnv(self, x):
        try:
            return eval(x, self.env)
        except Exception as e:
            self.numErrors += 1
            self.errors.append("Line %d [%s]: %s" % (self.lineNum, e.__class__.__name__, e))

    def execInEnv(self, x):
        try:
            exec x in self.env
        except Exception as e:
            self.numErrors += 1
            self.errors.append("Line %d [%s]: %s" % (self.lineNum, e.__class__.__name__, e))

    def compile(self):
        self.env = {'Row': Row, 'schemeVersion': 0, 'repeat': 0, 'numRows': None, 'schemeRows': [], 'deepcopy': deepcopy}
        if self.schemePath is not None:

            def getConfig(relPath):
                path = os.path.abspath(os.path.join(self.schemePath, relPath))
                if path not in configMemo:
                    fp = open(path, 'r')
                    try:
                        configMemo[path] = ConfigObj(fp)
                    finally:
                        fp.close()
                return configMemo.get(path, {})

            self.env['getConfig'] = getConfig
        try:
            fp = open(self.fileName, "r")
        except Exception as e:
            self.numErrors += 1
            self.errors.append("[%s]: %s" % (e.__class__.__name__, e))
            return
        try:
            state = 'NORMAL'
            rowType = 'repeat'
            for x in fp:
                self.lineNum += 1
                if state == 'NORMAL':
                    x = x.strip()
                    if x:
                        cpos = x.find('#')
                        if cpos >= 0:
                            x = x[:cpos]
                        if not x:
                            continue  # Discard comments
                        elif x[0] == '$':
                            if x[1:3] == '$$':  # Start of a code block
                                state = 'CODE_BLOCK'
                                block = []
                            else:
                                x = x[1:].strip()
                                # print 'Code: ', x
                                self.execInEnv(x)
                        else:  # This is a normal scheme line
                            # This is an old-style scheme file
                            if self.env['schemeVersion'] == 0:
                                x = ",".join(x.split()) if "," not in x else x
                                if rowType == 'repeat':
                                    self.env['repeat'] = self.evalInEnv(x)
                                    rowType = 'numRows'
                                elif rowType == 'numRows':
                                    self.env['numRows'] = self.evalInEnv(x)
                                    rowType = 'schemeRow'
                                else:
                                    x = 'Row(%s)' % x
                                    self.env['schemeRows'].append(self.evalInEnv(x))
                            else:
                                # print 'Scheme: (%s)' % x
                                x = 'Row(%s)' % x
                                self.env['schemeRows'].append(self.evalInEnv(x))
                elif state == 'CODE_BLOCK':
                    if x.strip()[:3] == '$$$':
                        self.execInEnv('\n'.join(block))
                        state = 'NORMAL'
                    else:
                        block.append(x.rstrip())
            if state == 'CODE_BLOCK':
                self.numErrors += 1
                self.errors.append("Line %d: Scheme ended within a code block" % (self.lineNum, ))

            numRows = self.env['numRows']
            schemeRows = self.env['schemeRows']
            self.numEntries = len(schemeRows) if numRows is None else numRows
            if self.numEntries != len(schemeRows):
                self.numErrors += 1
                self.errors.append("Scheme has incorrect number of rows (%d != %d)" % (len(schemeRows), self.numEntries))
            if self.numEntries > NUM_SCHEME_ROWS:
                self.numErrors += 1
                self.errors.append("Scheme has more than %d rows" % (NUM_SCHEME_ROWS, ))
            if self.numErrors == 0:
                self.nrepeat = self.env['repeat']
                self.version = self.env['schemeVersion']
                self.setpoint = [s.setpoint for s in schemeRows]
                self.dwell = [s.dwell for s in schemeRows]
                self.subschemeId = [s.subschemeId for s in schemeRows]
                self.virtualLaser = [s.virtualLaser for s in schemeRows]
                self.threshold = [s.threshold for s in schemeRows]
                self.pztSetpoint = [s.pzt for s in schemeRows]
                self.laserTemp = [s.laserTemp for s in schemeRows]
                self.extra1 = [s.extra1 for s in schemeRows]
                self.extra2 = [s.extra2 for s in schemeRows]
                self.extra3 = [s.extra3 for s in schemeRows]
                self.extra4 = [s.extra4 for s in schemeRows]
                self.frontMirrorDac = [s.frontMirrorDac for s in schemeRows]
                self.backMirrorDac = [s.backMirrorDac for s in schemeRows]
                self.coarsePhaseDac = [s.coarsePhaseDac for s in schemeRows]
                self.modeIndex = [s.modeIndex for s in schemeRows]
                self.schemeInfo = self.env.get('schemeInfo', None)
            else:
                raise SchemeError(self.__str__())
        finally:
            fp.close()
            del self.env

    def makeAngleTemplate(self):
        # Make an angle based scheme template from a frequency based scheme where the setpoint,
        #  laserTemp, frontMirrorDac, backMirrorDac and coarsePhaseDac fields are
        # copies of the original, while all the other fields point to the
        # originals
        s = Scheme()
        s.version = self.version
        s.nrepeat = self.nrepeat
        s.numEntries = self.numEntries
        s.setpoint = self.setpoint[:]
        s.dwell = self.dwell
        s.subschemeId = self.subschemeId
        s.virtualLaser = self.virtualLaser
        s.threshold = self.threshold
        s.pztSetpoint = self.pztSetpoint
        s.laserTemp = self.laserTemp[:]
        s.extra1 = self.extra1
        s.extra2 = self.extra2
        s.extra3 = self.extra3
        s.extra4 = self.extra4
        s.frontMirrorDac = self.frontMirrorDac[:]
        s.backMirrorDac = self.backMirrorDac[:]
        s.coarsePhaseDac = self.coarsePhaseDac[:]
        s.modeIndex = self.modeIndex
        s.schemeInfo = self.schemeInfo

        return s

    def repack(self):
        # Generate a tuple (repeats,zip(setpoint,dwell,subschemeId,virtualLaser,threshold,pztSetpoint,laserTemp,
        #  frontMirrorDac,backMirrorDac,coarsePhaseDac,modeIndex)) from the scheme, which is appropriate for 
        #  writing it to the DAS
        return (self.nrepeat,
                zip(self.setpoint, self.dwell, self.subschemeId, self.virtualLaser, self.threshold, self.pztSetpoint,
                    self.laserTemp, self.frontMirrorDac, self.backMirrorDac, self.coarsePhaseDac, self.modeIndex))


from sys import argv
import numpy as np

if __name__ == "__main__":
    if len(argv) > 1:
        fname = argv[1]
    else:
        fname = raw_input("Name of scheme file? ")
    s = Scheme(fname)
    s.compile()
    print "%-10d # Repetitions" % s.nrepeat
    print "%-10d # Scheme rows" % s.numEntries
    for i in range(s.numEntries):
        print "%11.5f,%6d,%6d, %1d,%6d,%6d,%8.4f, %d, %d, %d, %d, %d, %d, %d, %d" % (
            s.setpoint[i], s.dwell[i], s.subschemeId[i], s.virtualLaser[i], s.threshold[i], s.pztSetpoint[i], s.laserTemp[i],
            s.extra1[i], s.extra2[i], s.extra3[i], s.extra4[i], s.frontMirrorDac[i], s.backMirrorDac[i], s.coarsePhaseDac[i],
            s.modeIndex[i])
    if s.schemeInfo is not None:
        print "Scheme info: %s" % (s.schemeInfo, )
    # fname = "../Tests/RDFrequencyConverter/SampleScheme.sch"
    # fname = "../Tests/RDFrequencyConverter/ProgScheme.sch"
