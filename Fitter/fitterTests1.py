# 08-09-18  alex  Replaced ConfigParser with CustomConfigObj
import unittest
import sys
import os
import Host.Fitter.fitterCore as fitterCore
from fitterCore import voigt
from fitterCore import galatry
from fitterCore import CubicSpline
from fitterCore import makeSplineSection
from fitterCore import loadPhysicalConstants, loadSpectralLibrary, loadSplineLibrary
from fitterCore import getAppPath, prependAppDir, readConfig, makeConfigFromNestedDict
from fitterCore import Model
from fitterCore import FrequencySquish, Quadratic, Sinusoid, Spline, BiSpline, Galatry
from fitterCore import ClassifyError, classifyKeyTuple
from fitterCore import InitialValues
from fitterCore import sigmaFilter, sigmaFilterMedian, RdfData
from fitterCore import Analysis

from Host.Common.CustomConfigObj import CustomConfigObj
from cStringIO import StringIO
from numpy import *
#from scipy.integrate import quad, Inf

################################################################################
sampleConfig1 = """
[Fundamental constants]
c=2.997925000E+8
k=1.380660000E-23
AMU=1.660570000E-27

[species list]
12C_16O2=0
H_2O=3

[peak0]
peak name="water 6513.9676"
mass=18
center=6513.9676
strength=27.5
y = 1e-2
z = 2e-2
v = -1
frequency = 6513.9676
species = 3

[peak1]
peak name="CO2 6514.252"
mass=44
center=6514.252
strength=1.74
y = 1e-2
z = 7e-4
v = -1
frequency = 6514.252
species = 0
"""
################################################################################
class VoigtTestCase(unittest.TestCase):
    def setUp(self):
        self.x = linspace(0.0,10.0,11)
    def tearDown(self):
        pass
    def testGaussianLimit(self):
        self.assert_(allclose(real(voigt(self.x,0.0)),exp(-self.x**2)),
            "Gaussian limit not correct")
    def testLorentzianLimit(self):
        y = 10.0
        self.assert_(allclose(real(voigt(self.x,y)),y/(sqrt(pi)*(self.x**2+y**2)),rtol=1e-2),
            "Lorentzian limit not correct")
    def testSpotValues(self):
        spotValues = ((1.0, 1.0, 0.3047442052569126, 0.2082189382028316),
                      (3.0, 1.0, 0.0653177772890470, 0.1739183154163490),
                      (5.0, 1.0, 0.0230031325940600, 0.1103328325535800),
                      (1.0, 3.0, 0.1642611363929863, 0.0501971351352486),
                      (3.0, 3.0, 0.0964025055830445, 0.0912363260042188),
                      (5.0, 3.0, 0.0512259965673866, 0.0828369131719072),
                      (1.0, 5.0, 0.1067977383980653, 0.0206040887146843),
                      (3.0, 5.0, 0.0829877379769018, 0.0483893652029131),
                      (5.0, 5.0, 0.0569654398881770, 0.0558387427753910),
                     )
        for x,y,re,im in spotValues:
            V = voigt(array([x],float_),array([y],float_))
            self.assert_(allclose(array([real(V[0]),imag(V[0])],float_),array([re,im],float_)),"Spot test failed")
    def testComplexConjugation(self):
        for y in arange(0.0,11.0):
            self.assert_(allclose(real(voigt(self.x,y)),real(voigt(-self.x,y))),
                "Real part of conjugation test failed")
            self.assert_(allclose(imag(voigt(self.x,y)),-imag(voigt(-self.x,y))),
                "Imaginary part of conjugation test failed")

class VoigtTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(VoigtTestCase("testGaussianLimit"))
        self.addTest(VoigtTestCase("testLorentzianLimit"))
        self.addTest(VoigtTestCase("testSpotValues"))
        self.addTest(VoigtTestCase("testComplexConjugation"))

################################################################################
class GalatryTestCase(unittest.TestCase):
    def setUp(self):
        self.x = linspace(0.0,10.0,11)
    def tearDown(self):
        pass
    def testVoigtLimit(self):
        z = 0.0001
        for y in arange(1.0,11.0):
            self.assert_(allclose(galatry(self.x,y,z),real(voigt(self.x,y)),rtol=1e-4),"Voigt limit incorrect")
#    def testIntegral(self):
#        y = 1
#        z = 0.0001
#        print quad(lambda x:galatry(array([x]),y,z,strength=1,minimum_loss=1e-8)[0],0.0,Inf)/sqrt(pi)
#        print quad(lambda x:voigt(array([x]),y)[0],0.0,Inf)/sqrt(pi)

class GalatryTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(GalatryTestCase("testVoigtLimit"))
#        self.addTest(GalatryTestCase("testIntegral"))

################################################################################
class CubicSplineTestCase1(unittest.TestCase):
    def setUp(self):
        self.xVal = array([0.0,2.0,3.0,5.0,6.5,9.0,12.0],float_)
        self.yVal = sin(self.xVal)
        self.s = CubicSpline(self.xVal,self.yVal)
        self.xFine = linspace(min(self.xVal),max(self.xVal),9)
        pass
    def tearDown(self):
        pass
    def testGetDomain(self):
        self.assert_(self.s.getDomain() == (0.0,12.0))
    def testKnotValues(self):
        self.assert_(allclose(self.yVal,self.s(self.xVal)))
    def testOutOfRange(self):
        self.assert_(allclose(self.s(-1.0),self.yVal[0]),"out of range failed, low limit")
        self.assert_(allclose(self.s(25.0),self.yVal[-1]),"out of range failed, high limit")
    def testNaturalSpline(self):
        func = lambda x: 3.0*x
        self.yVal = func(self.xVal)
        self.s = CubicSpline(self.xVal,self.yVal)
        self.assert_(allclose(self.s(self.xFine),func(self.xFine)),"natural spline test failed")
    def testLowSlope(self):
        leftSlope = 5
        xmax = max(self.xVal)
        func = lambda x: x**3 - 3*xmax*x**2 + leftSlope*x + 9
        self.yVal = func(self.xVal)
        self.s = CubicSpline(self.xVal,self.yVal,low_slope=leftSlope)
        self.assert_(allclose(self.s(self.xFine),func(self.xFine)),"left slope test failed")
    def testHighSlope(self):
        rightSlope = 7
        xmax = max(self.xVal)
        func = lambda x: (x-xmax)**3 + 3*xmax*(x-xmax)**2 + rightSlope*(x-xmax) + 7
        self.yVal = func(self.xVal)
        self.s = CubicSpline(self.xVal,self.yVal,high_slope=rightSlope)
        self.assert_(allclose(self.s(self.xFine),func(self.xFine)),"right slope test failed")
    def testBothSlopes(self):
        xmax = max(self.xVal)
        func = lambda x: x**3 - 3*x**2 + 7*x + 9
        dfunc = lambda x: 3*x**2 - 6*x + 7
        self.yVal = func(self.xVal)
        self.s = CubicSpline(self.xVal,self.yVal,low_slope=dfunc(0.0),high_slope=dfunc(xmax))
        self.assert_(allclose(self.s(self.xFine),func(self.xFine)),"both slopes test failed")
    def testSupplied2ndDerivs(self):
        func = lambda x: x**3 - 5*x**2 + 7*x + 9
        d2func = lambda x: 6*x - 10
        self.yVal = func(self.xVal)
        self.s = CubicSpline(self.xVal,self.yVal,y2_array=d2func(self.xVal))
        self.assert_(allclose(self.s(self.xFine),func(self.xFine)),"Supplied 2nd derivative test failed")

class CubicSplineTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(CubicSplineTestCase1("testGetDomain"))
        self.addTest(CubicSplineTestCase1("testKnotValues"))
        self.addTest(CubicSplineTestCase1("testOutOfRange"))
        self.addTest(CubicSplineTestCase1("testNaturalSpline"))
        self.addTest(CubicSplineTestCase1("testLowSlope"))
        self.addTest(CubicSplineTestCase1("testHighSlope"))
        self.addTest(CubicSplineTestCase1("testBothSlopes"))
        self.addTest(CubicSplineTestCase1("testSupplied2ndDerivs"))

################################################################################
class CubicSplineIniTestCase(unittest.TestCase):
    def setUp(self):
        self.func = lambda x: x**3 - 5*x**2 + 7*x + 9
        self.d2func = lambda x: 6*x - 10
        self.xVal = array([0.0,2.0,3.0,5.0,7.0,9.0,12.0],float_)
        self.yVal = self.func(self.xVal)
        self.y2Val = self.d2func(self.xVal)
        self.config = CustomConfigObj()
        self.secName = "spline0"
        self.descr = "Example spline"
        makeSplineSection(self.config,self.secName,self.descr,self.xVal,self.yVal,self.y2Val)
    def tearDown(self):
        pass
    def testReadSplineIni(self):
        s = CubicSpline.getFromConfig(self.config,self.secName)
        x = linspace(min(self.xVal),max(self.xVal),2*len(self.xVal))
        self.assert_(allclose(s(x),self.func(x)),"Reading spline config failed")
    def testTruncation(self):
        """Spline construction stops when an "f" key is missing"""
        self.config.remove_option(self.secName,"f3")
        s = CubicSpline.getFromConfig(self.config,self.secName)
        self.assertEqual(3,len(s.x_vals))
    def testMissingAOption(self):
        self.config.remove_option(self.secName,"a2")
        self.assertRaises(ValueError,CubicSpline.getFromConfig,self.config,self.secName)
    def testMissingIOption(self):
        self.config.remove_option(self.secName,"i2")
        self.assertRaises(ValueError,CubicSpline.getFromConfig,self.config,self.secName)
    def testBadSecondDerivative(self):
        self.secName = "spline1"
        makeSplineSection(self.config,self.secName,self.descr,self.xVal,self.yVal,self.y2Val+0.1)
        self.assertRaises(ValueError,CubicSpline.getFromConfig,self.config,self.secName)
    def testReadingList(self):
        func1 = lambda x: 2*x**3 - 6*x
        d2func1 = lambda x: 12*x
        xVal = linspace(1.0,5.0,5)
        makeSplineSection(self.config,"spline1","Another spline",xVal,func1(xVal),d2func1(xVal))
        # Following line should not be placed in list because of gap between indices
        makeSplineSection(self.config,"spline3","Dummy",xVal,func1(xVal),d2func1(xVal))
        sList = CubicSpline.getListFromConfig(self.config)
        self.assert_(isinstance(sList,list),"getListFromConfig does not return a list")
        self.assertEqual(len(sList),2,"List has wrong length")
        self.assertEqual(sList[0].name,self.descr,"Zeroth spline name incorrect")
        self.assertEqual(sList[1].name,"Another spline","First spline name incorrect")
        x = linspace(min(self.xVal),max(self.xVal),2*len(self.xVal))
        self.assert_(allclose(sList[0](x),self.func(x)),"Zeroth spline incorrect")
        x = linspace(min(xVal),max(xVal),2*len(xVal))
        self.assert_(allclose(sList[1](x),func1(x)),"First spline incorrect")

class CubicSplineIniTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(CubicSplineIniTestCase("testReadSplineIni"))
        self.addTest(CubicSplineIniTestCase("testTruncation"))
        self.addTest(CubicSplineIniTestCase("testMissingAOption"))
        self.addTest(CubicSplineIniTestCase("testMissingIOption"))
        self.addTest(CubicSplineIniTestCase("testBadSecondDerivative"))
        self.addTest(CubicSplineIniTestCase("testReadingList"))
################################################################################
class PathUtilsTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def testAppPath(self):
        fname = "tester.txt"
        self.assertEqual(getAppPath(),sys.argv[0],"Incorrect AppPath")
        dir, file = os.path.split(prependAppDir(fname))
        self.assertEqual(file,fname,"Incorrect filename in prependAppDir")
        self.assertEqual(dir,os.path.split(getAppPath())[0],"Incorrect directory in prependAppDir")

class PathUtilsTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(PathUtilsTestCase("testAppPath"))

################################################################################
class LoadGlobalsTestCase(unittest.TestCase):
    def setUp(self):
        fp = StringIO(sampleConfig1)
        self.config = CustomConfigObj(fp)
        fp.close()
    def tearDown(self):
        pass
    def assertClose(self,v1,v2):
        for a1,a2 in zip(v1,v2):
            if isinstance(a1,float):
                self.assert_(allclose(a1,a2),"In assertClose, %g != %g" % (a1,a2))
            else:
                self.assert_(a1==a2,"In assertClose, %s != %s" % (a1,a2))
    def testLoadPhysicalConstants(self):
        p = loadPhysicalConstants(self.config)
        self.assertClose((p["c"],p["k"],p["amu"]),(2.997925E+8, 1.38066E-23, 1.66057E-27))
    def testLoadSpectralLibrary(self):
        s = loadSpectralLibrary(self.config)
        # Note conversion of key names to lower case
        self.assertClose(s.peakDict[0],("water 6513.9676",18,6513.9676,27.5,1e-2,2e-2,-1,"h_2o"))
        self.assertClose(s.peakDict[1],("CO2 6514.252",44,6514.252,1.74,1e-2,7e-4,-1,"12c_16o2"))

class LoadGlobalsTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(LoadGlobalsTestCase("testLoadPhysicalConstants"))
        self.addTest(LoadGlobalsTestCase("testLoadSpectralLibrary"))
################################################################################
class BasisFunctionsTestCase(unittest.TestCase):
    def setUp(self):
        self.model = Model()
        self.fQuad = lambda x,xc,a,b,c: a*(x-xc)**2 + b*(x-xc) + c
        self.fSinusoid = lambda x,a,b,c,d: a*cos(2*pi*(x-b)/c + d)

    def testModelAttributes(self):
        self.assertEqual(self.model.pressure,140,"Default pressure incorrect")
        self.assertEqual(self.model.temperature,298,"Default temperature incorrect")
        self.assertEqual(self.model.x_center,0,"Default center frequency incorrect")
        self.model.setAttributes(temperature=310,pressure=70,x_center=6500)
        self.assertEqual(self.model.pressure,70,"New pressure incorrect")
        self.assertEqual(self.model.temperature,310,"New temperature incorrect")
        self.assertEqual(self.model.x_center,6500,"New center frequency incorrect")
        try:
            self.model.setAttributes(invalid=100)
        except ValueError:
            pass
        else:
            raise "Expected a ValueError"

    def testQuadratic1(self):
        self.assertEqual(Quadratic.numParams(),3,"Number of parameters is incorrect")
        a = 1; b = 2; c = 3; xc = 6500.0
        q = Quadratic(curvature=a,slope=b,offset=c)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        self.model.setAttributes(x_center=6500)
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,b,c)))

    def test2ComponentModel(self):
        a1 = 1; b1 = 2; c1 = 3; xc = 6500.0
        a2 = 4; b2 = 5; c2 = 6
        # Check alternative ways of setting parameters
        q1 = Quadratic(curvature=a1,slope=b1,offset=c1)
        q2 = Quadratic(array([c2,b2,a2],float_))

        self.model.addToModel(q1,0)
        self.model.addToModel(q2,0)

        self.model.createParamVector()
        self.model.setAttributes(x_center=xc)
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fQuad(xVal,xc,a1,b1,c1)+self.fQuad(xVal,xc,a2,b2,c2)))

    def testScalarArguments(self):
        a = 1; b = 2; c = 3; xc = 6500.0
        q = Quadratic(curvature=a,slope=b,offset=c)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        self.model.setAttributes(x_center=6500)
        xVal = linspace(6499.0,6501.0,11)
        yVal = self.fQuad(xVal,xc,a,b,c)
        for i,x in enumerate(xVal):
            self.assert_(not iterable(x))
            self.assertAlmostEqual(q(x),yVal[i])
            # Check that useModifier has no effect when one is not defined
            self.assertAlmostEqual(q(x,useModifier=True),yVal[i])

    def testMemoization(self):
        a = 1; b = 2; c = 3; xc = 6500.0
        q = Quadratic(curvature=a,slope=b,offset=c)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        self.model.setAttributes(x_center=xc)
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,b,c)))
        self.assertFalse(q.memoUsed,"First pass should not use memo")
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,b,c)))
        self.assertTrue(q.memoUsed,"Second pass should use memo")
        xVal = linspace(6499.0,6501.0,12)
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,b,c)))
        self.assertFalse(q.memoUsed,"Third pass should not use memo")
        bnew = 2.5
        # Modify a model parameter
        self.model.parameters[1] = bnew
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertFalse(q.memoUsed,"Fourth pass should not use memo")
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertTrue(q.memoUsed,"Fifth pass should use memo")
        self.assert_(allclose(q(xVal,useModifier=True),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertFalse(q.memoUsed,"Sixth pass should not use memo")
        self.assert_(allclose(q(xVal,useModifier=True),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertFalse(q.memoUsed,"Seventh pass should not use memo")
        self.assert_(allclose(q(xVal,useModifier=False),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertFalse(q.memoUsed,"Eighth pass should not use memo")
        self.assert_(allclose(q(xVal,useModifier=False),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertTrue(q.memoUsed,"Ninth pass should use memo")
        xVal[4] += 0.1
        self.assert_(allclose(q(xVal),self.fQuad(xVal,xc,a,bnew,c)))
        self.assertFalse(q.memoUsed,"Tenth pass should not use memo")

    def testFrequencySquish1(self):
        self.assertEqual(FrequencySquish.numParams(),2,"Number of parameters is incorrect")
        a = 1; b = 2; c = 3; xc = 6500.0
        sq_a = 1.1; sq_b = 0.9
        sq = FrequencySquish(squish=sq_b, offset=sq_a)
        s = lambda x: x + sq_a + sq_b*(x-xc)
        q = Quadratic(curvature=a,slope=b,offset=c)
        self.model.registerXmodifier(sq)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        self.model.setAttributes(x_center=6500)
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fQuad(s(xVal),xc,a,b,c)))
        # Check that we can use the frequency modifier on a component function
        self.assertFalse(allclose(q(xVal,useModifier=False),self.fQuad(s(xVal),xc,a,b,c)))
        self.assert_(allclose(q(xVal,useModifier=True),self.fQuad(s(xVal),xc,a,b,c)))

    def testFrequencySquish2(self):
        """Test alternate way of specifying squish parameters"""
        a = 1; b = 2; c = 3; xc = 6500.0
        sq_a = 1.1; sq_b = 0.9
        sq = FrequencySquish(array([sq_a,sq_b],float_))
        s = lambda x: x + sq_a + sq_b*(x-xc)
        q = Quadratic(curvature=a,slope=b,offset=c)
        self.model.registerXmodifier(sq)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        self.model.setAttributes(x_center=6500)
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fQuad(s(xVal),xc,a,b,c)))

    def testParameterSettingWithSquish(self):
        a = 1; b = 2; c = 3; xc = 6500.0
        sq_a = 1.1; sq_b = 0.9
        sq = FrequencySquish(array([sq_a,sq_b],float_))
        s = lambda x: x + sq_a + sq_b*(x-xc)
        q = Quadratic(curvature=a,slope=b,offset=c)
        self.model.registerXmodifier(sq)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        self.model.setAttributes(x_center=6500)
        bnew = 2.5
        # Modify a model parameter: 0,1 for squish; 2,3,4 for Quadratic
        self.model.parameters[3] = bnew
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fQuad(s(xVal),xc,a,bnew,c)))

    def testSinusoid1(self):
        self.assertEqual(Sinusoid.numParams(),4,"Number of parameters is incorrect")
        a = 1.0; b = 6500.0; c = 3.0; d = 0.5
        q = Sinusoid(amplitude=a,center=b,period=c,phase=d)
        self.model.addToModel(q,0)
        self.model.createParamVector()
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fSinusoid(xVal,a,b,c,d)))

    def testSinusoid2(self):
        """Test alternate way of specifying sinusoid parameters"""
        self.assertEqual(Sinusoid.numParams(),4,"Number of parameters is incorrect")
        a = 1.0; b = 6500.0; c = 3.0; d = 0.5
        q = Sinusoid(array([a,b,c,d],float_))
        self.model.addToModel(q,0)
        self.model.createParamVector()
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fSinusoid(xVal,a,b,c,d)))

    def testSpline1(self):
        self.assertEqual(Spline.numParams(),5,"Number of parameters is incorrect")
        xc = 6500.0
        func = lambda x,a,b,c,d: a*(x-xc)**3 + b*(x-xc)**2 + c*(x-xc) + d
        d2func = lambda x,a,b,c,d: 6*a*(x-xc) + 2*b
        knots = array([6499.0,6499.5,6500.3,6501.0],float_)
        a0 = 5; b0 = 6; c0 = 7; d0 = 8
        a1 = 1; b1 = 2; c1 = 3; d1 = 4
        config = CustomConfigObj()
        makeSplineSection(config,"spline0","spline0",knots,
            func(knots,a0,b0,c0,d0),d2func(knots,a0,b0,c0,d0))
        makeSplineSection(config,"spline1","spline1",knots,
            func(knots,a1,b1,c1,d1),d2func(knots,a1,b1,c1,d1))
        lib = loadSplineLibrary(config)
        # Do not distort frequency axis for first spline
        q1 = Spline(freqShift=0.0,baselineShift=0.0,amplitude=1.0,squishParam=0.0,
                    squishCenter=xc,splineIndex=1)
        self.model.addToModel(q1,0)
        self.model.createParamVector()
        xVal = linspace(6499.5,6500.5,11)
        self.assert_(allclose(self.model(xVal),func(xVal,a1,b1,c1,d1)),"Single spline failed")
        # Add in a second spline
        fs = 0.1; bs = 0.2; amp = 2.0; sq = 0.3
        q0 = Spline(freqShift=fs,baselineShift=bs,amplitude=amp,squishParam=sq,
                    squishCenter=xc,splineIndex=0)
        self.model.addToModel(q0,0)
        self.model.createParamVector()
        xs = xc + (xVal-xc)*(1. + 0.02*arctan(sq))
        self.assert_(allclose(self.model(xVal),func(xVal,a1,b1,c1,d1)+
                     amp*func(xs-fs,a0,b0,c0,d0)+bs),"Dual spline with distortion failed")

    def testBiSpline1(self):
        self.assertEqual(BiSpline.numParams(),7,"Number of parameters is incorrect")
        xc = 6500.0
        func = lambda x,a,b,c,d: a*(x-xc)**3 + b*(x-xc)**2 + c*(x-xc) + d
        d2func = lambda x,a,b,c,d: 6*a*(x-xc) + 2*b
        knots = array([6499.0,6499.5,6500.3,6501.0],float_)
        a0 = 5; b0 = 6; c0 = 7; d0 = 8
        a1 = 5.1; b1 = 5.9; c1 = 7.1; d1 = 7.9
        config = CustomConfigObj()
        makeSplineSection(config,"spline0","spline0",knots,
            func(knots,a0,b0,c0,d0),d2func(knots,a0,b0,c0,d0))
        makeSplineSection(config,"spline1","spline1",knots,
            func(knots,a1,b1,c1,d1),d2func(knots,a1,b1,c1,d1))
        lib = loadSplineLibrary(config)
        b = BiSpline(freqShift=0.0,baselineShift=0.0,amplitude=1.0,squishParam=0.0,
                    squishCenter=xc,yEffective=1.2,yMultiplier=0.9,splineIndexA=0,
                    splineIndexB=1)
        self.model.addToModel(b,0)
        self.model.createParamVector()
        xVal = linspace(6499.5,6500.5,11)
        sA = func(xVal,a0,b0,c0,d0)
        sB = func(xVal,a1,b1,c1,d1)
        wt = 0.9*(1.2-1.0)
        self.assert_(allclose(self.model(xVal),(1.0-wt)*sA + wt*sB),"Bispline failed")

    def testBiSpline2(self):
        self.assertEqual(BiSpline.numParams(),7,"Number of parameters is incorrect")
        xc0 = 6500.0
        xc1 = 6500.1
        func0 = lambda x: sin(x-xc0)
        func1 = lambda x: sin(x-xc1)
        knots = xc0 + linspace(1,3,100)
        config = CustomConfigObj()
        # Make splines with no second derivative information
        makeSplineSection(config,"spline0","spline0",knots,func0(knots))
        makeSplineSection(config,"spline1","spline1",knots,func1(knots))
        lib = loadSplineLibrary(config)
        b = BiSpline(freqShift=0.0,baselineShift=0.0,amplitude=1.0,squishParam=0.0,
                    squishCenter=xc0,yEffective=1.2,yMultiplier=0.9,splineIndexA=1,
                    splineIndexB=0)
        self.model.addToModel(b,0)
        self.model.createParamVector()
        xm,ym = b.getPeak()
        ytest = b(array([xm-0.001,xm,xm+0.001],"d"))
        self.assert_(ytest[0]<=ytest[1] and ytest[2]<=ytest[1])

    def testBiSpline3(self):
        self.assertEqual(BiSpline.numParams(),7,"Number of parameters is incorrect")
        xc0 = 6500.0
        xc1 = 6500.0
        pi = 3.141592654
        func0 = lambda x: cos((x-xc0)*(2*pi))
        func1 = lambda x: cos((x-xc1)*(2*pi))
        knots = xc0 + linspace(-10.0,10.0,100)
        config = CustomConfigObj()
        # Make splines with no second derivative information
        makeSplineSection(config,"spline0","spline0",knots,func0(knots))
        makeSplineSection(config,"spline1","spline1",knots,func1(knots))
        lib = loadSplineLibrary(config)
        b = BiSpline(freqShift=0.0,baselineShift=0.0,amplitude=1.0,squishParam=0.0,
                    squishCenter=xc0,yEffective=1.0,yMultiplier=0.0,splineIndexA=1,
                    splineIndexB=0)
        self.model.addToModel(b,0)
        self.model.createParamVector()
        peakInterval = (6499.5,6500.3)
        xm,ym = b.getPeak(peakInterval)
        ytest = b(array([xm-0.001,xm,xm+0.001],"d"))
        self.assert_(ytest[0]<=ytest[1] and ytest[2]<=ytest[1] and peakInterval[0]<=xm and xm<=peakInterval[1])
        peakInterval = (6500.5,6501.3)
        xm,ym = b.getPeak(peakInterval)
        ytest = b(array([xm-0.001,xm,xm+0.001],"d"))
        self.assert_(ytest[0]<=ytest[1] and ytest[2]<=ytest[1] and peakInterval[0]<=xm and xm<=peakInterval[1])

    def testInitialValuesByFunctionIndex(self):
        a0 = 6.0; b0 = 5.0; c0 = 4.0; xc = 6501.0
        q = Quadratic(array([c0,b0,a0],float_))
        a1 = 1.0; b1 = 6500.0; c1 = 3.0; d1 = 0.5
        s = Sinusoid(array([a1,b1,c1,d1],float_))
        self.model.addToModel(q,1001)
        self.model.addToModel(s,1003)
        self.model.setAttributes(x_center=xc)
        self.model.createParamVector()
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fQuad(xVal,xc,a0,b0,c0)+self.fSinusoid(xVal,a1,b1,c1,d1)))
        iv = InitialValues()
        iv[1001,0] = 3.0 # Overrides c0
        iv[1003,2] = 4.5 # Overrides c1
        self.model.createParamVector(iv)
        self.assert_(allclose(self.model(xVal),self.fQuad(xVal,xc,a0,b0,3.0)+self.fSinusoid(xVal,a1,b1,4.5,d1)))

    def testInitialValuesByBaseIndex(self):
        a0 = 6.0; b0 = 5.0; c0 = 4.0; xc = 6501.0
        q = Quadratic(array([c0,b0,a0],float_))
        a1 = 1.0; b1 = 6500.0; c1 = 3.0; d1 = 0.5
        s = Sinusoid(array([a1,b1,c1,d1],float_))
        self.model.addToModel(q,1001)
        self.model.addToModel(s,1003)
        self.model.setAttributes(x_center=xc)
        self.model.createParamVector()
        xVal = linspace(6499.0,6501.0,11)
        self.assert_(allclose(self.model(xVal),self.fQuad(xVal,xc,a0,b0,c0)+self.fSinusoid(xVal,a1,b1,c1,d1)))
        iv = InitialValues()
        iv["base",0] = 3.0 # Overrides c0
        iv["base",5] = 4.5 # Overrides c1
        self.model.createParamVector(iv)
        self.assert_(allclose(self.model(xVal),self.fQuad(xVal,xc,a0,b0,3.0)+self.fSinusoid(xVal,a1,b1,4.5,d1)))

class BasisFunctionsTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(BasisFunctionsTestCase("testModelAttributes"))
        self.addTest(BasisFunctionsTestCase("testQuadratic1"))
        self.addTest(BasisFunctionsTestCase("test2ComponentModel"))
        self.addTest(BasisFunctionsTestCase("testMemoization"))
        self.addTest(BasisFunctionsTestCase("testScalarArguments"))
        self.addTest(BasisFunctionsTestCase("testFrequencySquish1"))
        self.addTest(BasisFunctionsTestCase("testFrequencySquish2"))
        self.addTest(BasisFunctionsTestCase("testParameterSettingWithSquish"))
        self.addTest(BasisFunctionsTestCase("testSinusoid1"))
        self.addTest(BasisFunctionsTestCase("testSinusoid2"))
        self.addTest(BasisFunctionsTestCase("testSpline1"))
        self.addTest(BasisFunctionsTestCase("testBiSpline1"))
        self.addTest(BasisFunctionsTestCase("testBiSpline2"))
        self.addTest(BasisFunctionsTestCase("testBiSpline3"))
        self.addTest(BasisFunctionsTestCase("testInitialValuesByFunctionIndex"))
        self.addTest(BasisFunctionsTestCase("testInitialValuesByBaseIndex"))

################################################################################
class KeyTupleTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def testFirstElementClassification(self):
        self.assertRaises(ClassifyError,classifyKeyTuple,(-1,))
        # Result of classification is class1, class2, key1, key2
        self.assertEqual(classifyKeyTuple((0,)),(0,0,0,None,()),"Spectral peak 0")
        self.assertEqual(classifyKeyTuple((999,)),(0,0,999,None,()),"Spectral peak 999")
        self.assertEqual(classifyKeyTuple((1000,)),(1,0,1000,None,()),"Special function 1000")
        self.assertEqual(classifyKeyTuple("base"),(2,0,"base",None,()),"base")
        self.assertEqual(classifyKeyTuple("name"),(3,0,"name",None,()),"name")
        self.assertEqual(classifyKeyTuple("std_dev_res"),(3,0,"std_dev_res",None,()),"std_dev_res")
        self.assertEqual(classifyKeyTuple("time"),(3,0,"time",None,()),"time")
    def testSecondElementClassification(self):
        self.assertEqual(classifyKeyTuple((999,3)),(0,1,999,3,()),"Spectral peak 999, param 3")
        self.assertEqual(classifyKeyTuple((999,"peak")),(0,2,999,"peak",()),"Spectral peak 999, peak")
        self.assertEqual(classifyKeyTuple((999,"base")),(0,2,999,"base",()),"Spectral peak 999, base")
        self.assertEqual(classifyKeyTuple((999,"center")),(0,3,999,"center",()),"Spectral peak 999, center")
        self.assertEqual(classifyKeyTuple((999,"strength")),(0,3,999,"strength",()),"Spectral peak 999, strength")
        self.assertEqual(classifyKeyTuple((999,"y")),(0,3,999,"y",()),"Spectral peak 999, y")
        self.assertEqual(classifyKeyTuple((999,"z")),(0,3,999,"z",()),"Spectral peak 999, z")
        self.assertEqual(classifyKeyTuple((999,"v")),(0,3,999,"v",()),"Spectral peak 999, v")
        self.assertEqual(classifyKeyTuple((999,"scaled_strength")),(0,4,999,"scaled_strength",()),"Spectral peak 999, scaled_strength")
        self.assertEqual(classifyKeyTuple((999,"scaled_y")),(0,4,999,"scaled_y",()),"Spectral peak 999, scaled_y")
        self.assertEqual(classifyKeyTuple((999,"scaled_z")),(0,4,999,"scaled_z",()),"Spectral peak 999, scaled_z")
        self.assertRaises(ClassifyError,classifyKeyTuple,(999,"invalid"))
        self.assertRaises(ClassifyError,classifyKeyTuple,(999,"y","extra"))
    def testExtraElementClassification(self):
        self.assertEqual(classifyKeyTuple((1002,"peak")),(1,2,1002,"peak",()),"Function 1002, peak")
        self.assertEqual(classifyKeyTuple((1002,"peak",1.2,3.4)),(1,2,1002,"peak",(1.2,3.4)),"Function 1002, peak, extra params")
        self.assertRaises(ClassifyError,classifyKeyTuple,(999,"peak",1.2,3.4))
        self.assertRaises(ClassifyError,classifyKeyTuple,(1002,2,1.2,3.4))

class KeyTupleTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(KeyTupleTestCase("testFirstElementClassification"))
        self.addTest(KeyTupleTestCase("testSecondElementClassification"))
        self.addTest(KeyTupleTestCase("testExtraElementClassification"))

################################################################################
class InitialValuesTestCase(unittest.TestCase):
    def setUp(self):
        self.iv = InitialValues()
    def tearDown(self):
        pass
    def testBaseAssignment(self):
        self.iv["base",19] = 1.0
        self.assertEqual(self.iv.ivDict,dict(base={19:1.0}),'assignment to "base",19')
        self.iv["base",20] = 2.0
        self.assertEqual(self.iv.ivDict,dict(base={19:1.0,20:2.0}),'assignment to two base variables')
        self.iv["base",19] = None
        self.assertEqual(self.iv.ivDict,dict(base={20:2.0}),'deleting a base variable')
        self.iv["base",20] = None
        self.assertEqual(self.iv.ivDict,{},'deleting remaining base variable')
    def testPeakAssignmentUnscaledValues(self):
        self.iv[999,"center"] = 6500
        self.iv[999,"strength"] = 1.0
        self.iv[999,"y"] = 0.01
        self.iv[999,"z"] = 0.005
        self.iv[999,"v"] = 0.001
        self.assertEqual(self.iv.ivDict,{999:{0:6500,1:1.0,2:0.01,3:0.005,4:0.001}},'assignment to peak 999 unscaled values')
        self.iv[17,"strength"] = 2.0
        self.assertEqual(self.iv.ivDict,{17:{1:2.0},999:{0:6500,1:1.0,2:0.01,3:0.005,4:0.001}},'assignment to two peaks')
        self.iv[999,"z"] = None
        self.assertEqual(self.iv.ivDict,{17:{1:2.0},999:{0:6500,1:1.0,2:0.01,4:0.001}},'deleting peak attribute')
        self.iv[17,1] = 3.0
        self.assertEqual(self.iv.ivDict,{17:{1:3.0},999:{0:6500,1:1.0,2:0.01,4:0.001}},'changing peak attribute')
        self.iv[17,"strength"] = None
        self.assertEqual(self.iv.ivDict,{999:{0:6500,1:1.0,2:0.01,4:0.001}},'deleting entire peak')
    def testPeakAssignmentScaledValues(self):
        self.iv[999,"scaled_strength"] = 1.0
        self.iv[999,"scaled_y"] = 0.01
        self.iv[999,"scaled_z"] = 0.005
        self.assertEqual(self.iv.ivDict,{999:{"scaled_strength":1.0,"scaled_y":0.01,"scaled_z":0.005}},'assignment to peak 999 scaled values')
        self.iv[999,"scaled_y"] = 0.02
        self.assertEqual(self.iv.ivDict,{999:{"scaled_strength":1.0,"scaled_y":0.02,"scaled_z":0.005}},'changing peak attribute')
        self.iv[999,"scaled_z"] = None
        self.assertEqual(self.iv.ivDict,{999:{"scaled_strength":1.0,"scaled_y":0.02}},'deleting peak attribute')
    def testSpecialAssignment(self):
        self.iv[1001,3] = 1.0
        self.assertEqual(self.iv.ivDict,{1001:{3:1.0}},'assignment to special function')
        self.iv[1001,4] = 0.5
        self.iv[1001,0] = 2.5
        self.assertEqual(self.iv.ivDict,{1001:{0:2.5,3:1.0,4:0.5}},'multiple assignment to special function')
        self.iv[1000,2] = 4.0
        self.assertEqual(self.iv.ivDict,{1000:{2:4.0},1001:{0:2.5,3:1.0,4:0.5}},'assignment to two special functions')

class InitialValuesTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(InitialValuesTestCase("testBaseAssignment"))
        self.addTest(InitialValuesTestCase("testSpecialAssignment"))
        self.addTest(InitialValuesTestCase("testPeakAssignmentUnscaledValues"))
        self.addTest(InitialValuesTestCase("testSpecialAssignment"))
################################################################################
class GalatryBasisTestCase(unittest.TestCase):
    def setUp(self):
        fp = StringIO(sampleConfig1)
        config = CustomConfigObj(fp)
        fp.close()
        self.constants = loadPhysicalConstants(config)
        self.spectralLib = loadSpectralLibrary(config)
        self.splineLib = loadSplineLibrary(config)
        self.model = Model()
    def tearDown(self):
        pass
    def testGalatryFromLibrary(self):
        self.assertEqual(Galatry.numParams(),5,"Number of parameters is incorrect")
        g = Galatry(peakNum=0)
        self.model.addToModel(g,0)
        # N.B. Need to call setAttributes BEFORE createParamVector for the values to be used
        self.model.setAttributes(x_center=6513.9676,pressure=140,temperature=300)
        self.model.createParamVector()
        self.assertTrue(allclose(g.initialParams,[6513.9676,27.5,1e-2,2e-2,-1]),'Check parameters read in from library')
        P = self.model.pressure
        T = self.model.temperature
        self.assertTrue(allclose(g.initialParams[0],g.getCurrentParametersFromModel()[0]),'Check center is unchanged')
        self.assertTrue(allclose(g.initialParams[1:4]*P,g.getCurrentParametersFromModel()[1:4]),'Check pressure scaling')
        v = sqrt(2*self.constants['k']*T/((g.mass*self.constants['amu'])*self.constants['c']**2))*g.initialParams[0]
        self.assertTrue(allclose(v,g.getCurrentParametersFromModel()[4]),'Check Doppler broadening')
        xVal = linspace(6513.5,6514.5,31)
        a = g.getCurrentParametersFromModel()
        y = a[1]*galatry((xVal-a[0])/a[4],a[2],a[3],a[1])
        self.assertTrue(allclose(self.model(xVal),y),'Check Galatry values')
    def testGalatryFromScaledParameters(self):
        g = Galatry(center=6514.252,scaled_y=1e-3,scaled_z=7e-4,v=1e-2,scaled_strength=1.74,mass=44)
        self.model.addToModel(g,0)
        self.model.createParamVector()
        P = self.model.pressure
        self.assertTrue(allclose(g.initialParams,[6514.252,1.74,1e-3,7e-4,1e-2]),'Check parameters')
        xVal = linspace(6513.5,6514.5,31)
        a = array([6514.252,1.74,1e-3,7e-4,1e-2],float_)
        a[1:4] *= P
        y = a[1]*galatry((xVal-a[0])/a[4],a[2],a[3],a[1])
        self.assertTrue(allclose(self.model(xVal),y),'Check Galatry values')
    def testGalatryWithInitialValue1(self):
        self.assertEqual(Galatry.numParams(),5,"Number of parameters is incorrect")
        g = Galatry(peakNum=0)
        self.model.addToModel(g,0)
        # N.B. Need to call setAttributes BEFORE createParamVector for the values to be used
        self.model.setAttributes(x_center=6513.9676,pressure=140,temperature=300)
        iv = InitialValues()
        iv[0,"center"] = 6515.0
        iv[0,"strength"] = 4000.0
        iv[0,"scaled_y"] = 5e-3
        iv[0,"v"] = 2e-2
        self.model.createParamVector(iv)
        P = self.model.pressure
        T = self.model.temperature
        # initialParameters are not affected by InitialValues objects
        self.assertTrue(allclose(g.initialParams,[6513.9676,27.5,1e-2,2e-2,-1]),'Check parameters read in from library')
        a = g.getCurrentParametersFromModel()
        # CurrentParametersFromModel are overwritten by InitialValues objects
        self.assertTrue(allclose(a,[6515.0,4000.0,5e-3*P,2e-2*P,2e-2]),'Check parameters read in from library')

class GalatryBasisTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(GalatryBasisTestCase("testGalatryFromLibrary"))
        self.addTest(GalatryBasisTestCase("testGalatryFromScaledParameters"))
        self.addTest(GalatryBasisTestCase("testGalatryWithInitialValue1"))

################################################################################
rdfHeader = """
[CRDS Header]
Version = 11
[Average Sensor Values]
Time_(s)_ave=0.1
Cavity_pressure_(torr)_ave=1.400126E+002
Cavity_temperature_(degC)_ave=4.500024E+001
Laser_temperature_(degC)_ave=3.689400E+001
Etalon_temperature_(degC)_ave=4.539133E+001
Warm_box_temperature_(degC)_ave=4.499968E+001
Laser_TEC_current_monitor_ave=1.977188E+002
Warm_Box_TEC_current_monitor_ave=-9.037168E+003
Hot_Box_TEC_current_monitor_ave=-8.405748E+003
Heater_current_monitor_ave=0.000000E+000
Environment_temperature_(degC)_ave=2.739456E+001
Inlet_proportional_valve_ave=3.250000E+004
Outlet_proportional_valve_ave=4.062294E+004
SchemeID=14
SpectrumID=1
Spectrum_start_time=0.0
[Tagalong Data]
[Tagalong Data Times]
"""
class DataFiltersTestCase(unittest.TestCase):
    def setUp(self):
        self.wavenum = linspace(6513.5,6514.5,101)
        xc = 6514.0
        self.time = 0.01*arange(0,len(self.wavenum))
        self.ratio1 = 1.0 + 0.9*cos(2*pi*(self.wavenum-xc)/1.6)
        self.ratio2 = 1.0 + 0.85*sin(2*pi*(self.wavenum-xc)/1.6)
        self.mock = Model()
        self.mock.setAttributes(x_center=xc,temperature=300,pressure=140)
        q = Quadratic(curvature=0.0,slope=0.0,offset=800)
        self.mock.addToModel(q,1000)
        g = Galatry(peakNum=0)
        self.mock.addToModel(g,0)
        self.mock.createParamVector()
        self.uncorrectedAbsorbance = 0.001 * self.mock(self.wavenum)
        self.correctedAbsorbance = 0.001 * self.mock(self.wavenum)
        self.tunerValue = 40000 + 500000.0 * (self.wavenum % 0.02)
        self.fitStatus = zeros(shape(self.wavenum))
        self.schemeStatus = zeros(shape(self.wavenum))
        self.subSchemeId = ones(shape(self.wavenum))
        self.count = ones(shape(self.wavenum))
        self.schemeIndex = ones(shape(self.wavenum))
        self.schemeRow = arange(0,len(self.wavenum))
        self.wavenumSetpoint = self.wavenum
        self.etalonSelect = zeros(shape(self.wavenum),int8)
        self.laserSelect = zeros(shape(self.wavenum),int8)
        self.etalonAndLaserSelect = (self.laserSelect << 8) + self.etalonSelect
        self.fp = StringIO()
        self.rdfVersion = 11

        print >> self.fp, self.rdfVersion
        for i in range(len(self.wavenum)):
            print >> self.fp, "%.9e\t%.9e\t%.9e\t%.9e\t%.9e\t%.9e\t%16d\t%16d\t%16d\t%16d\t%16d\t%16d\t%16d\t%16d\t%16d\t" % \
            (self.time[i],self.ratio1[i],self.ratio2[i],self.uncorrectedAbsorbance[i],self.correctedAbsorbance[i],self.tunerValue[i], \
             100000*self.wavenum[i],self.fitStatus[i],self.schemeStatus[i],self.subSchemeId[i], \
             self.count[i],self.schemeIndex[i],self.schemeRow[i],100000*self.wavenumSetpoint[i], \
             self.etalonAndLaserSelect[i])
        print >> self.fp, rdfHeader
    def tearDown(self):
        pass
    def testSigmaFilterConstant(self):
        x = 10.0 * ones(10,float_)
        r, stat = sigmaFilter(x,0.01)
        self.assertTrue(r.all(),"Constant does not pass sigmaFilter")
        self.assertEqual(stat,{"iterations":1})
    def testSigmaFilterWithOutliers(self):
        x = 10.0 * ones(10,float_)
        x[3] = 11.0
        x[9] = 8.5
        r, stat = sigmaFilter(x,1.0)
        self.assertTrue((r==(x==10.0)).all(),"Outlier rejection test failed")
    def testSigmaFilterMedianConstant(self):
        x = 10.0 * ones(10,float_)
        r, stat = sigmaFilterMedian(x,0.01)
        self.assertTrue(r.all(),"Constant does not pass sigmaFilter")
        self.assertEqual(stat,{"iterations":1})
    def testSigmaFilterMedianWithOutliers(self):
        x = 10.0 * ones(10,float_)
        x[3] = 11.0
        x[9] = 8.5
        r, stat = sigmaFilterMedian(x,1.0)
        self.assertTrue((r==(x==10.0)).all(),"Outlier rejection test failed")
    # def testRdfDataSensorRead(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # # Keys are case insensitive
        # self.assertTrue(allclose(r["CavityPressure"],1.400126E+002),"Pressure read wrongly")
        # self.assertTrue(allclose(r["CavityTemperature"],4.500024E+001),"Temperature read wrongly")
        # self.assertTrue(allclose(r["Datapoints"],len(self.wavenum)),"Number of data points wrong")
        # self.assertTrue(allclose(r["SpectrumID"],1),"Spectrum ID wrong")
    # def testRdfDataRead(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # self.assertTrue(allclose(r.time,self.time),"Time read wrongly")
        # self.assertTrue(allclose(r.ratio1,self.ratio1),"Ratio 1 read wrongly")
        # self.assertTrue(allclose(r.ratio2,self.ratio2),"Ratio 2 read wrongly")
        # self.assertTrue(allclose(r.uncorrectedAbsorbance,self.uncorrectedAbsorbance),"uncorrectedAbsorbance read wrongly")
        # self.assertTrue(allclose(r.correctedAbsorbance,self.correctedAbsorbance),"correctedAbsorbance read wrongly")
        # self.assertTrue(allclose(r.tunerValue,self.tunerValue),"tunerValue read wrongly")
        # self.assertTrue(allclose(r.fitStatus,self.fitStatus),"fitStatus read wrongly")
        # self.assertTrue(allclose(r.schemeStatus,self.schemeStatus),"schemeStatus read wrongly")
        # self.assertTrue(allclose(r.subSchemeId,self.subSchemeId),"subSchemeId read wrongly")
        # self.assertTrue(allclose(r.count,self.count),"schemeCounter read wrongly")
        # self.assertTrue(allclose(r.schemeTableIndex,self.schemeIndex),"schemeIndex read wrongly")
        # self.assertTrue(allclose(r.schemeRow,self.schemeRow),"schemeRow read wrongly")
        # self.assertTrue(allclose(r.etalonSelect,self.etalonAndLaserSelect&0xFF),"etalonSelect read wrongly")
        # self.assertTrue(allclose(r.laserSelect,self.etalonAndLaserSelect>>8),"laserSelect read wrongly")
        # self.assertTrue(allclose(r.wavenum,self.wavenum),"wavenum read wrongly")
        # self.assertTrue(allclose(r.wavenumSetpoint,self.wavenumSetpoint),"wavenumSetpoint read wrongly")
    # def testRdfDataSorting(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # r.sortBy("uncorrectedAbsorbance")
        # self.assertTrue((diff(r.uncorrectedAbsorbance[r.indexVector])>=0).all(),"Sorting by uncorrectedAbsorbance failed")
        # r.sortBy("tunerValue")
        # self.assertTrue((diff(r.tunerValue[r.indexVector])>=0).all(),"Sorting by tunerValue failed")
    # def testRdfDataFiltering(self):
        # r1 = RdfData()
        # r1.rdfRead(StringIO(self.fp.getvalue()))
        # r2 = RdfData()
        # r2.rdfRead(StringIO(self.fp.getvalue()))
        # r1.filterBy(["wavenum"],lambda x:x>=6514,name="wavenumFilter")
        # self.assertTrue((r1.wavenum[r1.indexVector]>=6514).all(),"filter by wavenumber failed")
        # r1.filterBy(["tunerValue"],lambda x:x<=48000,name="tunerFilter")
        # self.assertTrue((r1.tunerValue[r1.indexVector]<=48000).all(),"filter by tunerValue failed")
        # self.assertEqual(r1["filterHistory"][0][0],"wavenumFilter")
        # self.assertEqual(r1["filterHistory"][1][0],"tunerFilter")
        # r2.filterBy(["tunerValue","wavenum"],lambda x,y: (x<=48000) & (y>=6514))
        # self.assertTrue(allclose(r1.wavenum[r1.indexVector],r2.wavenum[r2.indexVector]),"successive filters failed")
    # def testRdfDataSortAndFilter(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # r.sortBy("uncorrectedAbsorbance")
        # r.filterBy(["wavenum"],lambda x:(x>=6513.8) & (x<=6514.2))
        # self.assertTrue((r.wavenum[r.indexVector]>=6513.8).all(),"sort and filter: filter by wavenumber failed")
        # self.assertTrue((r.wavenum[r.indexVector]<=6514.2).all(),"sort and filter: filter by wavenumber failed")
        # self.assertTrue((diff(r.uncorrectedAbsorbance[r.indexVector])>=0).all(),"Sorting by uncorrectedAbsorbance failed")
        # r.sortBy("wavenum")
        # self.assertTrue((diff(r.wavenum[r.indexVector])>=0).all(),"Sorting by wavenum failed")
    # #=========================
    # def aggregator1(self,waveNums):
        # # Define groups of ringdowns in wavenumber bins of the specified width
        # width = 0.05
        # groups = []
        # for i,w in enumerate(waveNums):
            # if i>0:
                # if w-wmin<=width:
                    # g.append(i)
                    # continue
                # groups.append(g)
            # g = [i]
            # wmin = w
        # groups.append(g)
        # return groups
    # #=========================
    # def testRdfDataGroupByWavenumber(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # r.filterBy(["uncorrectedAbsorbance"],lambda x:x >= 0.85)
        # r.sortBy("wavenum")
        # r.groupBy(["wavenum"],self.aggregator1)
        # for g in r.groups:
            # self.assertTrue((r.uncorrectedAbsorbance[g]>=0.85).all(),"Loss filtering before grouping failed")
            # self.assertTrue(r.wavenum[g].ptp()<=0.05,"Wavenumber grouping failed")

    # def testRdfDataGroupStatistics(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # r.filterBy(["uncorrectedAbsorbance"],lambda x:x >= 0.85)
        # r.sortBy("wavenum")
        # r.groupBy(["wavenum"],self.aggregator1)
        # fields = ["wavenum","uncorrectedAbsorbance","ratio1","ratio2"]
        # r.evaluateGroups(fields)
        # for i,g in enumerate(r.groups):
            # self.assertEqual(r.groupSizes[i],len(g),"Incorrect calculation of group size")
            # for f in fields:
                # data = getattr(r,f)[g]
                # self.assertTrue(allclose(median(data),r.groupMedians[f][i]),"Incorrect calculation of group median")
                # self.assertTrue(allclose(mean(data),r.groupMeans[f][i]),"Incorrect calculation of group mean")
                # self.assertTrue(allclose(std(data),r.groupStdDevs[f][i]),"Incorrect calculation of group standard deviation")
    # def testRdfDataSparseFilter(self):
        # r = RdfData()
        # r.rdfRead(StringIO(self.fp.getvalue()))
        # r.sparse(maxPoints=1000,width=0.1,height=100000.0,xColumn="wavenum",yColumn="uncorrectedAbsorbance",sigmaThreshold=1.8)
        # self.assertEqual(len(r.groups),10)
        # for g in r.groups:
            # self.assertTrue(max(r.wavenum[g])-min(r.wavenum[g])<=0.1)
            # y = r.uncorrectedAbsorbance[g]
            # if len(y)>1:
                # self.assertTrue(max(abs(y - mean(y))) < 1.8*std(y))
        # self.assertEqual(r.filterHistory,[('sparseFilter',19,82)])            

class DataFiltersTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(DataFiltersTestCase("testSigmaFilterConstant"))
        self.addTest(DataFiltersTestCase("testSigmaFilterWithOutliers"))
        self.addTest(DataFiltersTestCase("testSigmaFilterMedianConstant"))
        self.addTest(DataFiltersTestCase("testSigmaFilterMedianWithOutliers"))
        # self.addTest(DataFiltersTestCase("testRdfDataSensorRead"))
        # self.addTest(DataFiltersTestCase("testRdfDataRead"))
        # self.addTest(DataFiltersTestCase("testRdfDataSorting"))
        # self.addTest(DataFiltersTestCase("testRdfDataFiltering"))
        # self.addTest(DataFiltersTestCase("testRdfDataSortAndFilter"))
        # self.addTest(DataFiltersTestCase("testRdfDataGroupByWavenumber"))
        # self.addTest(DataFiltersTestCase("testRdfDataGroupStatistics"))
        # self.addTest(DataFiltersTestCase("testRdfDataSparseFilter"))

################################################################################
sampleAnalysis1 = """
[Header]
Version=3
analysis class=bispline_max71836700
[Region Fit Definitions]
number of sections=3
Start frequency_0=6513.8
End frequency_0=6514.1
Start frequency_1=6514.1
End frequency_1=6514.4
Start frequency_2=6514.6
End frequency_2=6514.9
number of peaks=5
peak identification=0,3,5,9,7,1000,1001
center frequency=6514.0
region fit name=unknown region
[Fit Sequence Parameters]
use fine?0=TRUE
use fine?1=TRUE
[DS0]
# Coefficients are:
# (0-2) const, linear, quadratic of baseline
# (3-4) offset & scale of frequency squish
# 5 number of Galatry peaks
# (6-10) center, strength, y, z, v of Galatry peak
vary coefficients= 1,0,0, 0,0, 0, 0,1,0,0,0, 0,1,0,0,0, 0,1,0,0,0, 0,1,0,0,0, 0,1,0,0,0
dependency0=7,12,0.5750,0
dependency1=7,22,0.0115,0
dependency2=7,27,0.0057,0

[DS1]
# Coefficients are:
# (0-2) const, linear, quadratic of baseline
# (3-4) offset & scale of frequency squish
# 5 number of Galatry peaks
# (6-10) center, strength, y, z, v of Galatry peak
vary coefficients= 1,1,0, 0,0, 0, 1,1,1,1,0, 1,1,1,1,0, 1,1,1,1,0, 1,1,1,1,0, 1,1,1,1,0

[function1000]
functional_form=sinusoid
a0=-0.255
a1=6514.40000
a2=1.07
a3=+0.40

[function1001]
functional_form=sinusoid
a0=-0.0306
a1=6513.90000
a2=0.535
a3=+0.51
"""
class AnalysisTestCase(unittest.TestCase):
    def setUp(self):
        fname = r"Expt\lib1.ini"
        loadSpectralLibrary(fname)
        loadPhysicalConstants(fname)
        loadSplineLibrary(fname)
        Analysis.resetIndex()
        self.config = CustomConfigObj(StringIO(sampleAnalysis1))
    def tearDown(self):
        pass
    def testIndexing(self):
        self.assertEqual(Analysis.index,0,"Unexpected analysis index")
        aList = []
        for i in range(5):
            aList.append(Analysis(self.config))
        self.assertEqual(Analysis.index,5,"Analysis index count is incorrect")
        for i in range(5):
            self.assertEqual(aList[i].serialNumber, i,"Analysis serial number is incorrect")
            self.assertEqual(aList[i].name,"analysis_%d" % i,"Analysis name is incorrect")
    def testReadFromFile1(self):
        a = Analysis(self.config)
        self.assertTrue(allclose(a.regionStart,[6513.8,6514.1,6514.6]),"regionStart read incorrectly")
        self.assertTrue(allclose(a.regionEnd,[6514.1,6514.4,6514.9]),"regionEnd read incorrectly")
        self.assertEqual(a.nPeaks,5,"number of peaks read incorrectly")
        self.assertTrue(allclose(a.centerFrequency,6514.0),"centerFrequency read incorrectly")
        self.assertEqual(a.regionName,"unknown region","region fit name read incorrectly")
        self.assertTrue((a.basisArray==[0,3,5,9,7,1000,1001]).all(),"peak identification read incorrectly")
    def testReadFromFile2(self):
        a = Analysis(self.config)
        # Retrieve the fit sequence parameters for each pass of the fit process
        ds0, ds1 = a.fitSequenceParameters
        # Sequence 0
        self.assertTrue((ds0['variables']==array([0,7,12,17,22,27])).all(),"Variable list for sequence zero incorrect")
        self.assertEqual(ds0['useFine'],True,"useFine attribute for sequence zero incorrect")
        self.assertTrue((ds0['depSrc']==array([7,7,7])).all(),"depSrc attribute for sequence zero incorrect")
        self.assertTrue((ds0['depDest']==array([12,22,27])).all(),"depDest attribute for sequence zero incorrect")
        self.assertTrue(allclose(ds0['depSlope'],array([0.5750,0.0115,0.0057])),"depSlope attribute for sequence zero incorrect")
        self.assertTrue(allclose(ds0['depOffset'],array([0.0,0.0,0.0])),"depDest attribute for sequence zero incorrect")
        # Sequence 1
        self.assertTrue((ds1['variables']==array([0,1,6,7,8,9,11,12,13,14,16,17,18,19,21,22,23,24,26,27,28,29])).all(),
            "Variable list for sequence one incorrect")
        self.assertEqual(ds1['useFine'],True,"useFine attribute for sequence one incorrect")
        self.assertTrue((ds1['depSrc']==array([])).all(),"depSrc attribute for sequence one incorrect")
        self.assertTrue((ds1['depDest']==array([])).all(),"depDest attribute for sequence one incorrect")
        self.assertTrue(allclose(ds1['depSlope'],array([])),"depSlope attribute for sequence one incorrect")
        self.assertTrue(allclose(ds1['depOffset'],array([])),"depDest attribute for sequence one incorrect")
    def testReadFromFile3(self):
        a = Analysis(self.config)
        m = Model()
        m.setAttributes(x_center=a.centerFrequency)
        g0 = Galatry(peakNum=0)
        m.addToModel(g0,0)
        g3 = Galatry(peakNum=3)
        m.addToModel(g3,3)
        g5 = Galatry(peakNum=5)
        m.addToModel(g5,5)
        g9 = Galatry(peakNum=9)
        m.addToModel(g9,9)
        g7 = Galatry(peakNum=7)
        m.addToModel(g7,7)
        s1000 = Sinusoid(amplitude=-0.255,center=6514.4,period=1.07,phase=0.40)
        m.addToModel(s1000,1000)
        s1001 = Sinusoid(amplitude=-0.0306,center=6513.9,period=0.535,phase=0.51)
        m.addToModel(s1001,1001)
        self.assertTrue((a.basisFunctionByIndex[0].initialParams==g0.initialParams).all(),"Galatry peak 0 incorrect")
        self.assertTrue((a.basisFunctionByIndex[3].initialParams==g3.initialParams).all(),"Galatry peak 3 incorrect")
        self.assertTrue((a.basisFunctionByIndex[5].initialParams==g5.initialParams).all(),"Galatry peak 5 incorrect")
        self.assertTrue((a.basisFunctionByIndex[7].initialParams==g7.initialParams).all(),"Galatry peak 7 incorrect")
        self.assertTrue((a.basisFunctionByIndex[9].initialParams==g9.initialParams).all(),"Galatry peak 9 incorrect")
        self.assertTrue((a.basisFunctionByIndex[1000].initialParams==s1000.initialParams).all(),"Sinusoid 1000 incorrect")
        self.assertTrue((a.basisFunctionByIndex[1001].initialParams==s1001.initialParams).all(),"Sinusoid 1001 incorrect")
        # Read a string from the analysis INI file
        self.assertEqual(a.config.get("Header","analysis class"),"bispline_max71836700")

class AnalysisTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self)
        self.addTest(AnalysisTestCase("testIndexing"))
        self.addTest(AnalysisTestCase("testReadFromFile1"))
        self.addTest(AnalysisTestCase("testReadFromFile2"))
        self.addTest(AnalysisTestCase("testReadFromFile3"))
################################################################################
if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    suite.addTest(VoigtTestSuite())
    suite.addTest(GalatryTestSuite())
    suite.addTest(CubicSplineTestSuite())
    suite.addTest(CubicSplineIniTestSuite())
    suite.addTest(PathUtilsTestSuite())
    suite.addTest(LoadGlobalsTestSuite())
    suite.addTest(BasisFunctionsTestSuite())
    suite.addTest(KeyTupleTestSuite())
    suite.addTest(InitialValuesTestSuite())
    suite.addTest(GalatryBasisTestSuite())
    suite.addTest(DataFiltersTestSuite())
    suite.addTest(AnalysisTestSuite())

    runner.run(suite)
