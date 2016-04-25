from collections import deque
import json
from mock import call, MagicMock
import numpy as np
import os
import sys
import tempfile
import traceback
import unittest
from Host.Pipeline.Blocks import Pipeline
from Host.Pipeline.EthaneBlocks import (EthaneClassifier, EthaneComputationBlock, EthaneDispositionBlock,
                                        JsonWriterBlock, VehicleExhaustClassifier)
from traitlets.config import Config

class EthaneDispositionBlockTest(unittest.TestCase):
    def test_verdict_calls1(self):
        myconfig = Config()
        myconfig.EthaneClassifier.nng_lower = 0.0
        myconfig.EthaneClassifier.nng_upper = 0.1e-2
        myconfig.EthaneClassifier.ng_lower = 2.0e-2
        myconfig.EthaneClassifier.ng_upper = 10.0e-2
        myconfig.EthaneClassifier.nng_prior = 0.27
        myconfig.EthaneClassifier.thresh_confidence = 0.9
        myconfig.EthaneClassifier.reg = 0.05
        myconfig.VehicleExhaustClassifier.ve_ethylene_sdev_factor = 2.0
        myconfig.VehicleExhaustClassifier.ve_ethylene_lower = 0.05
        myconfig.VehicleExhaustClassifier.ve_ethane_sdev_factor = 1.0
        myconfig.VehicleExhaustClassifier.ve_ethane_upper = 0.02

        self.edb = EthaneDispositionBlock(config=myconfig)
        self.edb.vehicle_exhaust_classifier.compare_above = MagicMock(return_value=True)
        self.edb.vehicle_exhaust_classifier.compare_below = MagicMock(return_value=True)
        ethane_ratio = 1.0
        ethane_ratio_sdev = 2.0
        ethylene_ratio = 3.0
        ethylene_ratio_sdev = 4.0
        newDat = dict(ETHANE_RATIO=ethane_ratio,
                      ETHANE_RATIO_SDEV=ethane_ratio_sdev,
                      ETHYLENE_RATIO=ethylene_ratio,
                      ETHYLENE_RATIO_SDEV_RAW=ethylene_ratio_sdev)

        result = self.edb.newData(newDat)
        # Check ethylene comparison
        self.edb.vehicle_exhaust_classifier.compare_above.assert_called_once_with(ethylene_ratio,
                                                                                  ethylene_ratio_sdev,
                                                                                  self.edb.vehicle_exhaust_classifier.ve_ethylene_sdev_factor,
                                                                                  self.edb.vehicle_exhaust_classifier.ve_ethylene_lower)
        # Check ethane comparison
        self.edb.vehicle_exhaust_classifier.compare_below.assert_called_once_with(ethane_ratio,
                                                                                  ethane_ratio_sdev,
                                                                                  self.edb.vehicle_exhaust_classifier.ve_ethane_sdev_factor,
                                                                                  self.edb.vehicle_exhaust_classifier.ve_ethane_upper)
        #
        self.assertDictContainsSubset(dict(VERDICT='VEHICLE_EXHAUST'), result)
        self.edb.stop()

    def test_vehicle_exhaust(self):
        myconfig = Config()
        myconfig.VehicleExhaustClassifier.ve_ethylene_sdev_factor = 2.0
        myconfig.VehicleExhaustClassifier.ve_ethylene_lower = 0.05
        myconfig.VehicleExhaustClassifier.ve_ethane_sdev_factor = 1.0
        myconfig.VehicleExhaustClassifier.ve_ethane_upper = 0.02
        self.vec = VehicleExhaustClassifier(config=myconfig)
        ethane_ratio = 1.0
        ethane_ratio_sdev = 2.0
        ethylene_ratio = 3.0
        ethylene_ratio_sdev = 4.0
        self.vec.compare_above = MagicMock(return_value=False)
        self.vec.compare_below = MagicMock(return_value=False)
        result = self.vec.verdict(ethane_ratio, ethane_ratio_sdev, ethylene_ratio, ethylene_ratio_sdev)
        self.assertNotEqual(result, 'VEHICLE_EXHAUST')
        self.vec.compare_above = MagicMock(return_value=False)
        self.vec.compare_below = MagicMock(return_value=True)
        result = self.vec.verdict(ethane_ratio, ethane_ratio_sdev, ethylene_ratio, ethylene_ratio_sdev)
        self.assertNotEqual(result, 'VEHICLE_EXHAUST')
        self.vec.compare_above = MagicMock(return_value=True)
        self.vec.compare_below = MagicMock(return_value=False)
        result = self.vec.verdict(ethane_ratio, ethane_ratio_sdev, ethylene_ratio, ethylene_ratio_sdev)
        self.assertNotEqual(result, 'VEHICLE_EXHAUST')
        self.vec.compare_above = MagicMock(return_value=True)
        self.vec.compare_below = MagicMock(return_value=True)
        result = self.vec.verdict(ethane_ratio, ethane_ratio_sdev, ethylene_ratio, ethylene_ratio_sdev)
        self.assertNotEqual(result, 'NOT_VEHICLE_EXHAUST')

    def test_likelihood_normalized(self):
        # Check that the integral is equal to one
        self.ec = EthaneClassifier()
        for _ in range(100):
            a = 2.0 * (np.random.random() - 0.5)
            b = a + (1.0 - a) * np.random.random()
            sigma = 0.05 + 0.09 * np.random.random()
            xvec = np.linspace(-1.0-4*sigma, 1.0+4*sigma, 2001)
            y = [self.ec.likelihood(x, a, b, sigma) for x in xvec]
            self.assertAlmostEquals((sum(y) - 0.5 * (y[0] + y[-1])) * (xvec[1] - xvec[0]), 1.0, delta=1e-3)

    def test_newData_calls(self):
        self.edb = EthaneDispositionBlock()
        data = dict(ETHANE_RATIO=1, ETHANE_RATIO_SDEV=2, ETHYLENE_RATIO=3, ETHYLENE_RATIO_SDEV_RAW=4)
        self.edb.vehicle_exhaust_classifier.verdict = MagicMock(return_value="HELLO")
        self.edb.ethane_classifier.verdict = MagicMock(return_value=("GOODBYE", 0.6))
        self.assertDictContainsSubset(dict(data, VERDICT="HELLO"), self.edb.newData(data))
        self.edb.vehicle_exhaust_classifier.verdict.assert_called_once_with(1, 2, 3, 4)
        self.edb.vehicle_exhaust_classifier.verdict = MagicMock(return_value="NOT_VEHICLE_EXHAUST")
        self.edb.ethane_classifier.verdict = MagicMock(return_value=("GOODBYE", 0.6))
        self.assertDictContainsSubset(dict(data, VERDICT="GOODBYE", CONFIDENCE=0.6), self.edb.newData(data))
        self.edb.vehicle_exhaust_classifier.verdict.assert_called_once_with(1, 2, 3, 4)

    def test_verdict_assignments(self):
        self.ec = EthaneClassifier(thresh_confidence=0.9)
        self.ec.post_prob = MagicMock(return_value=(0.98, 0.8))
        self.assertEqual(self.ec.verdict(1., 2.), ('NOT_NATURAL_GAS', 0.95))
        self.ec.post_prob = MagicMock(return_value=(0.8, 0.98))
        self.assertEqual(self.ec.verdict(1., 2.), ('NATURAL_GAS', 0.95))
        self.ec.post_prob = MagicMock(return_value=(0.8, 0.7))
        self.assertEqual(self.ec.verdict(1., 2.), ('POSSIBLE_NATURAL_GAS', 0.7))

    def test_verdict_calls2(self):
        myconfig = Config()
        myconfig.EthaneClassifier.nng_lower = 5.0
        myconfig.EthaneClassifier.nng_upper = 6.0
        myconfig.EthaneClassifier.ng_lower = 7.0
        myconfig.EthaneClassifier.ng_upper = 8.0
        myconfig.EthaneClassifier.nng_prior = 9.0
        myconfig.EthaneClassifier.thresh_confidence = 0.9
        myconfig.EthaneClassifier.reg = 10.0

        self.edb = EthaneDispositionBlock(config=myconfig)
        self.edb.vehicle_exhaust_classifier.compare_above = MagicMock(return_value=False)
        self.edb.vehicle_exhaust_classifier.compare_below = MagicMock(return_value=False)
        self.edb.ethane_classifier.post_prob = MagicMock(return_value=(0.95, 0.8))

        ethane_ratio = 1.0
        ethane_ratio_sdev = 2.0
        ethylene_ratio = 3.0
        ethylene_ratio_sdev = 4.0
        newDat = dict(ETHANE_RATIO=ethane_ratio,
                      ETHANE_RATIO_SDEV=ethane_ratio_sdev,
                      ETHYLENE_RATIO=ethylene_ratio,
                      ETHYLENE_RATIO_SDEV_RAW=ethylene_ratio_sdev)

        result = self.edb.newData(newDat)
        self.edb.ethane_classifier.post_prob.assert_called_once_with(1., 2., 5., 6., 7., 8., 9., 10.)
        self.assertDictContainsSubset(dict(VERDICT="NOT_NATURAL_GAS"), result)

    def test_post_prob(self):
        self.ec = EthaneClassifier()
        for _ in range(100):
            self.ec.likelihood = MagicMock(side_effect=[0.3, 0.4])
            p1 = np.random.random()
            reg = 0.05
            post1, post2 = self.ec.post_prob(None, None, None, None, None, None, p1, reg)
            p2 = 1.0 - p1
            self.assertAlmostEqual(post1, p1*0.3/(p1*0.3+p2*0.4+reg))
            self.assertAlmostEqual(post2, p2*0.4/(p1*0.3+p2*0.4+reg))

class EthaneComputationBlockTest(unittest.TestCase):
    def setUp(self):
        self.ecb = EthaneComputationBlock(1.0, methane_ethane_sdev_ratio=0.2, methane_ethylene_sdev_ratio=0.09)

    def tearDown(self):
        self.ecb.stop()

    def test_newData1(self):
        deque0 = deque()
        for i in range(100):
            deque0.append(dict(DISTANCE=i, CH4=2.0*i, C2H6=3.0*i, PF_c2h4_conc=4.0*i))
        deque1 = deque()
        distance = 40
        sigma = 6.5
        width = max(5.0, sigma)
        amplitude = 0.5
        ethane_nominal_sdev = 0.004  # Default value
        peak = dict(DISTANCE=distance, SIGMA=sigma, AMPLITUDE=amplitude)
        deque1.append(peak)
        self.ecb.calculate_ratios = MagicMock(return_value=dict(HELLO=43))
        for result in self.ecb.newData(deque0, deque1):
            self.assertDictContainsSubset(dict(peak, HELLO=43), result)
        self.assertEqual(len(self.ecb.calculate_ratios.call_args_list), 1)
        args, kwargs = self.ecb.calculate_ratios.call_args_list[0]
        np.testing.assert_allclose(args[0], 2.0*np.arange(np.ceil(distance-3.0*width), np.ceil(distance+3.0*width)))
        np.testing.assert_allclose(args[1], 3.0*np.arange(np.ceil(distance-3.0*width), np.ceil(distance+3.0*width)))
        np.testing.assert_allclose(args[2], 4.0*np.arange(np.ceil(distance-3.0*width), np.ceil(distance+3.0*width)))
        self.assertEqual(args[3], amplitude)
        self.assertEqual(args[4], width)
        self.assertEqual(args[5], ethane_nominal_sdev)

    def test_newData2(self):
        deque0 = deque()
        ethane_nominal_sdev = 0.010
        for i in range(100):
            deque0.append(dict(DISTANCE=i, CH4=2.0*i, C2H6=3.0*i, PF_c2h4_conc=4.0*i, C2H6_nominal_sdev=ethane_nominal_sdev))
        deque1 = deque()
        distance = 40
        sigma = 6.5
        width = max(5.0, sigma)
        amplitude = 0.5
        peak = dict(DISTANCE=distance, SIGMA=sigma, AMPLITUDE=amplitude)
        deque1.append(peak)
        self.ecb.calculate_ratios = MagicMock(return_value=dict(HELLO=43))
        for result in self.ecb.newData(deque0, deque1):
            self.assertDictContainsSubset(dict(peak, HELLO=43), result)
        self.assertEqual(len(self.ecb.calculate_ratios.call_args_list), 1)
        args, kwargs = self.ecb.calculate_ratios.call_args_list[0]
        np.testing.assert_allclose(args[0], 2.0*np.arange(np.ceil(distance-3.0*width), np.ceil(distance+3.0*width)))
        np.testing.assert_allclose(args[1], 3.0*np.arange(np.ceil(distance-3.0*width), np.ceil(distance+3.0*width)))
        np.testing.assert_allclose(args[2], 4.0*np.arange(np.ceil(distance-3.0*width), np.ceil(distance+3.0*width)))
        self.assertEqual(args[3], amplitude)
        self.assertEqual(args[4], width)
        self.assertEqual(args[5], ethane_nominal_sdev)

    def test_newData_maxLookback(self):
        self.ecb.maxLookback = 1
        deque0 = deque()
        for i in range(100):
            deque0.append(dict(DISTANCE=i, CH4=2.0*i, C2H6=3.0*i, PF_c2h4_conc=4.0*i))
        deque1 = deque()
        distance = 40
        sigma = 6.5
        width = max(5.0, sigma)
        amplitude = 0.5
        peak = dict(DISTANCE=distance, SIGMA=sigma, AMPLITUDE=amplitude)
        deque1.append(peak)
        self.ecb.calculate_ratios = MagicMock(return_value=dict(HELLO=43))
        with self.assertRaisesRegexp(RuntimeError, 'increase value of maxLookback'):
            for result in self.ecb.newData(deque0, deque1):
                pass

    def test_ratio_analysis(self):
        # Synthesize many pulses, carry out analysis and check that the estimates and their uncertainties
        #  cover the correct values with the expected frequency
        nsigma = 2.0
        ntrials = 1000
        max_oob_frac = 0.075
        base = np.arange(0, 100)
        ampl_oob = 0
        sigma_m_oob = 0
        sigma_e_oob = 0
        for _ in range(ntrials):
            pos = 50.0 + 20.0 * np.random.random()
            width = 2.0  + 18.0 * np.random.random()
            pulse = np.exp(-0.5*((base - pos) /width) ** 2)
            sigma_m = 0.001 + 0.001 * np.random.random()
            sigma_e = 0.001 + 0.010 * np.random.random()
            sigma_ratio = sigma_m / sigma_e
            ampl = 0.05 * np.random.randn()
            methane = 2.0 + pulse + sigma_m * np.random.randn(len(pulse))
            ethane = 0.01 + ampl * pulse + sigma_e * np.random.randn(len(pulse))
            Aratio, Astd, sigma_main, sigma_trace, pip_energy, methane_ptp = self.ecb.ratio_analysis(methane, ethane, sigma_ratio)
            self.assertAlmostEqual(methane_ptp, methane.ptp(), delta=1e-4*abs(methane_ptp))
            self.assertAlmostEqual(pip_energy, len(methane) * np.std(methane) **2, delta=1e-4*abs(pip_energy))
            if abs(ampl-Aratio) > nsigma * Astd:
                ampl_oob += 1
            var_trace = sigma_trace ** 2
            var_trace_std = (sigma_e ** 2) * np.sqrt(2.0/len(methane))
            if abs(sigma_e**2-var_trace) > nsigma * var_trace_std:
                sigma_e_oob += 1
            var_main = sigma_main ** 2
            var_main_std = (sigma_m ** 2) * np.sqrt(2.0/len(methane))
            if abs(sigma_m**2-var_main) > nsigma * var_main_std:
                sigma_m_oob += 1
            if ampl < 0.1 and sigma_ratio < 0.5:
                self.assertLess(abs(1.0 - sigma_trace / (np.sqrt(pip_energy) * Astd)), 0.01)
        self.assertLessEqual(max(ampl_oob, sigma_e_oob, sigma_m_oob), max_oob_frac*ntrials,
                             "Too many (ampl: %.2f%%, trace_sdev: %.2f%%, main_sdev: %.2f%%) out of bounds estimates at %s*sigma" % \
                             (100.0*float(ampl_oob)/ntrials, 100.0*float(sigma_e_oob)/ntrials, 100.0*float(sigma_m_oob)/ntrials, nsigma))

    def test_ratio_analysis_zeros(self):
        # Check that arrays of zeros for trace concentrations does not cause problems
        base = np.arange(0, 100)
        pos = 50.0
        width = 15.0
        pulse = np.exp(-0.5*((base - pos) /width) ** 2)
        sigma_ratio = 0.1
        methane = 2.0 + pulse
        ethane = np.zeros_like(methane)
        Aratio, Astd, sigma_main, sigma_trace, pip_energy, methane_ptp = self.ecb.ratio_analysis(methane, ethane, sigma_ratio)
        self.assertEqual(Aratio, 0.0)
        self.assertEqual(Astd, 0.0)
        self.assertEqual(sigma_trace, 0.0)

    def test_calculate_ratios_calls(self):
        # Test that the ratio_analysis functions are called correctly
        methane = [1, 2, 3, 4]
        ethane = [5, 6, 7, 8]
        ethylene = [5, 4, 3, 2]
        amplitude = 0.5
        width = 3.0
        methane_ethane_sdev_ratio = 0.2
        methane_ethylene_sdev_ratio = 0.09
        ethane_nominal_sdev = 0.01

        self.ecb.ratio_analysis = MagicMock(
            side_effect=[(1, 2, 3, 4, 5, 6),
                         (7, 8, 9, 10, 11, 12)])
        self.ecb.calculate_ratios(methane, ethane, ethylene, amplitude, width, ethane_nominal_sdev)

        self.assertEqual(len(self.ecb.ratio_analysis.call_args_list), 2)  # Check called twice
        args, kwargs = self.ecb.ratio_analysis.call_args_list[0]  # First call
        np.testing.assert_allclose(args[0], np.asarray(methane))
        np.testing.assert_allclose(args[1], np.asarray(ethane))
        self.assertAlmostEqual(args[2], methane_ethane_sdev_ratio)
        args, kwargs = self.ecb.ratio_analysis.call_args_list[1]  # Second call
        np.testing.assert_allclose(args[0], np.asarray(methane))
        np.testing.assert_allclose(args[1], np.asarray(ethylene))
        self.assertAlmostEqual(args[2], methane_ethylene_sdev_ratio)

    def test_calculate_ratios_results1(self):
        # Test that the results from ratio_analysis functions are returned correctly
        methane = [1, 2, 3, 4]
        ethane = [5, 6, 7, 8]
        ethylene = [5, 4, 3, 2]
        amplitude = 0.5
        width = 3.0
        methane_ethane_sdev_ratio = 0.2
        methane_ethylene_sdev_ratio = 0.09
        ethane_nominal_sdev = 0.01

        ethane_conc_sdev = 0.02
        self.ecb.ratio_analysis = MagicMock(
            side_effect=[(1, 2, 3, ethane_conc_sdev, 5, 6),
                         (7, 8, 9, 10, 11, 12)])
        result = self.ecb.calculate_ratios(methane, ethane, ethylene, amplitude, width, ethane_nominal_sdev)
        self.assertDictContainsSubset(dict(ETHANE_RATIO=1), result)
        self.assertDictContainsSubset(dict(ETHANE_RATIO_SDEV_RAW=2), result)
        self.assertDictContainsSubset(dict(ETHANE_RATIO_SDEV=2*max(1.0, 6/amplitude)), result)
        self.assertDictContainsSubset(dict(ETHANE_CONC_SDEV=ethane_conc_sdev), result)
        self.assertDictContainsSubset(dict(ETHYLENE_RATIO=7), result)
        self.assertDictContainsSubset(dict(ETHYLENE_RATIO_SDEV_RAW=8), result)
        self.assertDictContainsSubset(dict(ETHYLENE_RATIO_SDEV=8*max(1.0, 6/amplitude)), result)
        self.assertDictContainsSubset(dict(ETHYLENE_CONC_SDEV=10), result)
        self.assertDictContainsSubset(dict(PIP_ENERGY=5), result)
        self.assertDictContainsSubset(dict(METHANE_PTP=6), result)

    def test_calculate_ratios_results2(self):
        # Test that the results from ratio_analysis functions are returned correctly when the ethane concentration
        #  sdev is initially less than the nominal value
        methane = [1, 2, 3, 4]
        ethane = [5, 6, 7, 8]
        ethylene = [5, 4, 3, 2]
        amplitude = 0.5
        width = 3.0
        methane_ethane_sdev_ratio = 0.2
        methane_ethylene_sdev_ratio = 0.09
        ethane_nominal_sdev = 0.01

        ethane_conc_sdev = 0.005
        factor = ethane_nominal_sdev / ethane_conc_sdev
        self.ecb.ratio_analysis = MagicMock(
            side_effect=[(1, 2, 3, ethane_conc_sdev, 5, 6),
                         (7, 8, 9, 10, 11, 12)])
        result = self.ecb.calculate_ratios(methane, ethane, ethylene, amplitude, width, ethane_nominal_sdev)
        self.assertDictContainsSubset(dict(ETHANE_RATIO=1), result)
        self.assertDictContainsSubset(dict(ETHANE_RATIO_SDEV_RAW=factor*2), result)
        self.assertDictContainsSubset(dict(ETHANE_RATIO_SDEV=factor*2*max(1.0, 6/amplitude)), result)
        self.assertDictContainsSubset(dict(ETHANE_CONC_SDEV=factor*ethane_conc_sdev), result)
        self.assertDictContainsSubset(dict(ETHYLENE_RATIO=7), result)
        self.assertDictContainsSubset(dict(ETHYLENE_RATIO_SDEV_RAW=8), result)
        self.assertDictContainsSubset(dict(ETHYLENE_RATIO_SDEV=8*max(1.0, 6/amplitude)), result)
        self.assertDictContainsSubset(dict(ETHYLENE_CONC_SDEV=10), result)
        self.assertDictContainsSubset(dict(PIP_ENERGY=5), result)
        self.assertDictContainsSubset(dict(METHANE_PTP=6), result)

class JsonWriterBlockTest(unittest.TestCase):
    def setUp(self):
        # Set up a cStringIO object to take place of the output file, use .getvalue to fetch what is written
        if not os.path.exists('/temp'):
            os.makedirs('/temp')
        with tempfile.NamedTemporaryFile(dir='/temp', delete=False) as tmpfile:
            self.fname = tmpfile.name

    def test_empty(self):
        blk = JsonWriterBlock(self.fname)
        blk.continuationFunc(None)
        with file(self.fname, "rb") as ip:
            self.assertEqual(json.load(ip), [])
        blk.stop()  # Stop the mainLoop

    def test_single_object(self):
        blk = JsonWriterBlock(self.fname)
        obj = {'a': 'apple', 'b': 'bear', 'c': 123}
        blk.newData(obj)
        blk.continuationFunc(None)
        with file(self.fname, "rb") as ip:
            self.assertListEqual(json.load(ip), [obj])
        blk.stop()  # Stop the mainLoop

    def test_object_list(self):
        blk = JsonWriterBlock(self.fname)
        objList = [{'a': 'apple', 'b': 'bear', 'c': 123}, {'x': 45, 'y': 17}]
        for obj in objList:
            blk.newData(obj)
        blk.continuationFunc(None)
        with file(self.fname, "rb") as ip:
            self.assertListEqual(json.load(ip), objList)
        blk.stop()  # Stop the mainLoop

    def test_non_objects(self):
        blk = JsonWriterBlock(self.fname)
        myList = [[123, 'hello'], 'testing']
        for obj in myList:
            blk.newData(obj)
        blk.continuationFunc(None)
        with file(self.fname, "rb") as ip:
            self.assertListEqual(json.load(ip), myList)
        blk.stop()  # Stop the mainLoop

    def test_bad_numbers(self):
        # nan, inf and -inf should be all converted to None by JSON roundtrip
        blk = JsonWriterBlock(self.fname)
        blk.newData({'x': 1, 'y': float('nan'), 'z': float('inf')})
        blk.newData({'a': -float('inf'), 'b': 17, 'c': 95,})
        blk.continuationFunc(None)
        with file(self.fname, "rb") as ip:
            result = json.load(ip)
            self.assertListEqual(result,
                                 [{'x': 1, 'y': None, 'z': None},
                                  {'a': None, 'b': 17, 'c': 95,}])
        blk.stop()  # Stop the mainLoop


    def tearDown(self):
        os.unlink(self.fname)

if __name__ == "__main__":
    unittest.main()