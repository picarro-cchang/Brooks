# FitterTests2.py tests how well the fitter can find the parameters of a synthetic spectrum

import unittest
import sys
import os
from Host.Common.SharedTypes import Bunch
from fitterCore import *

from Host.Common.CustomConfigObj import CustomConfigObj
from cStringIO import StringIO
from numpy import *
from pylab import *
from matplotlib.ticker import ScalarFormatter

spLib = """
[Header]
Version=1
comment="spectral library for testing"
date=2010-08-10
[Fundamental constants]
c=2.997925000E+8
k=1.380660000E-23
AMU=1.660570000E-27
[species list]
CO2=0
H2O=1
[peak0]
peak name="CO2 6237.408"
mass=44
center=6237.408000
strength=4
y=0.01
z=0.004
v=0.000000
species=0
"""

sampleAnalysis1 = """
[Header]
Version=1
[Region Fit Definitions]
number of sections=1
Start frequency_0=6237.20
End frequency_0=6237.60
number of peaks=1
peak identification=0
center frequency=6237.408
region fit name=region 1
[Fit Sequence Parameters]
use fine?0=TRUE
[DS0]
# Coefficients are:
# (0-2) const, linear, quadratic of baseline
# (3-4) offset & scale of frequency squish
# 5 number of Galatry peaks
# (6-10) center, strength, y, z, v of Galatry peak
vary coefficients= 1,0,0, 1,0, 0, 0,1,1,0,0
"""

class BunchWithItems(Bunch,dict):
    pass
    
class FitPeakTestCase(unittest.TestCase):
    def setUp(self):
        ini = CustomConfigObj(StringIO(spLib))
        loadSpectralLibrary(ini)
        loadPhysicalConstants(ini)
        loadSplineLibrary(ini)
        Analysis.resetIndex()
        self.config = CustomConfigObj(StringIO(sampleAnalysis1))
    def tearDown(self):
        pass
    def testPeakAmplitude(self):
        self.assertEqual(Analysis.index,0,"Unexpected analysis index")
        aList = [Analysis(self.config)]
        
        # Generate the data which is to be fitted
        shiftList = linspace(-0.1,0.1,21)
        for shift in shiftList:
            m = Model()
            g0 = Galatry(peakNum=0)
            m.addToModel(g0,0)
            # N.B. Need to call setAttributes BEFORE createParamVector for the values to be used
            m.setAttributes(x_center=6237.408,pressure=140,temperature=318)
            iv = InitialValues()
            iv[0,"scaled_strength"] = 0.1
            iv[0,"scaled_y"] = 0.1
            iv[0,"center"] = 6237.408 + shift
            m.createParamVector(iv)
            # Generate simulated FSR data
            x = arange(6237.20,6237.60,0.0206)
            y = m(x)
            # x = linspace(6237.20,6237.60,101)
            # plot(x,m(x),'x')
            # gca().xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
            # grid(True)
            d = BunchWithItems(sensorDict={"Time_s":1280332987},fitData={"freq":x,"loss":m(x)+800.0,"sdev":ones(x.shape)})
            d["cavityPressure"] = 140
            d["cavityTemperature"] = 45
            r = aList[0](d)
            print shift, r['base',3]
            # print r['base',0], r['base',1], r['base',2], r['base',3]
            # print r[0,'peak'], r[0,'base'], r[0,'center'], r[0,'scaled_strength'], r[0,'scaled_y'], r[0,'scaled_z']
        # show()
        
class FitPeakTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(FitPeakTestCase("testPeakAmplitude"))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    suite.addTest(FitPeakTestSuite())

    runner.run(suite)
