from Host.Pipeline.Blocks import (ActionBlock, TransformBlock, MergeBlock)
import json
from numpy import asarray, isfinite, nan
import numpy as np
from math import erf
from traitlets import (Bool, Dict, Float, Instance, Integer, Unicode)
from traitlets.config.configurable import Configurable
DTR = np.pi/180.0
RTD = 180.0/np.pi
EARTH_RADIUS = 6378100.

def ratio_analysis(main_conc, trace_conc, sigma_ratio):
    # sigma_ratio = sigma_main/sigma_trace (typically < 1)
    N = len(main_conc)
    P = np.mean(trace_conc*main_conc) - np.mean(trace_conc)*np.mean(main_conc)
    vm = np.mean(main_conc**2)-np.mean(main_conc)**2
    ve = np.mean(trace_conc**2)-np.mean(trace_conc)**2
    Q = vm/sigma_ratio - sigma_ratio*ve
    # Aratio is the estimate of the trace to main ratio
    if P == 0:
        Aratio = 0.0
        Asdev = 0.0
        sigma_trace = 0.0
        sigma_main = np.std(main_conc)
        pip_energy = len(main_conc)*np.std(main_conc)**2
    else:
        rho = 0.5*Q/P
        trho = np.sign(P)*np.sqrt(1 + rho**2)
        Aratio = (trho - rho)/sigma_ratio
        # Use the amplitude estimate to estimate sigma_trace, the trace_conc concentration noise
        p = (main_conc + Aratio*trace_conc*sigma_ratio**2)/(1 + (Aratio*sigma_ratio)**2)
        n2 = trace_conc - Aratio*p
        sigma_trace = np.sqrt(np.mean(n2**2)-np.mean(n2)**2)
        sigma_main = sigma_ratio * sigma_trace
        srho = np.sqrt((1 + rho**2)/(N*P**2))*np.sqrt(vm*sigma_trace**2 + ve*sigma_main**2)
        # Asdev is the standard deviation of the amplitude ratio estimate
        Asdev = srho*(1 - rho/trho)/sigma_ratio
        # The pip energy gives the energy in the pulse which is present in the main_conc
        #  concentration, and which is scaled by the amplitude ratio in the trace_conc
        #  concentration
        pip_energy = len(p)*np.std(p)**2
    # The peak-to-peak main_conc concentration may be used to estimate the amplitude
    return Aratio, Asdev, sigma_main, sigma_trace, pip_energy, main_conc.ptp()


class EthaneClassifier(Configurable):
    nng_lower = Float(None, allow_none=True, config=True)  # Lower limit of ratio for not natural gas hypothesis
    nng_upper = Float(None, allow_none=True, config=True)  # Upper limit of ratio for not natural gas hypothesis
    ng_lower = Float(None, allow_none=True, config=True)  # Lower limit of ratio for natural gas hypothesis
    ng_upper = Float(None, allow_none=True, config=True)  # Upper limit of ratio for natural gas hypothesis
    nng_prior = Float(None, allow_none=True, config=True)  # Prior probability of not natural gas hypothesis
    thresh_confidence = Float(None, allow_none=True, config=True)  # Threshold confidence level for definite hypothesis
    reg = Float(None, allow_none=True, config=True)  # Regularization parameter
    max_confidence = Float(0.95)  # Maximum allowed value for confidence
    """Computes the classification of an indication with respect to ethane content. Returns a class
    together with a confidence in the classification for "NOT_NATURAL_GAS" and "NATURAL_GAS". For the
    "POSSIBLE_NATURAL_GAS" classification, the confidence is that the indication is natural gas.
    """
    def __init__(self, **kwargs):
        super(EthaneClassifier, self).__init__(**kwargs)

    def likelihood(self, x, a, b, sigma):
        """Computes the probability of measuring a value x from the sum of a uniform distribution on
        the interval a to  b and a normal distribution of standard deviation sigma. It is the likelihood
        of a hypothesis that a quantity is uniformly distributed between a and b when a measurement with
        uncertainty sigma yields the result x."""
        return (erf((x - a)/(np.sqrt(2)*sigma)) - erf((x-b)/(np.sqrt(2)*sigma)))/(2*(b-a))

    def post_prob(self, measurement, uncertainty, nng_lower, nng_upper, ng_lower, ng_upper, nng_prior, reg):
        ng_prior = 1 - nng_prior
        y1 = self.likelihood(measurement, nng_lower, nng_upper, uncertainty)
        y2 = self.likelihood(measurement, ng_lower, ng_upper, uncertainty)
        post1 = (nng_prior * y1) / (nng_prior * y1 + ng_prior * y2 + reg)
        post2 = (ng_prior * y2) / (nng_prior * y1 + ng_prior * y2 + reg)
        return post1, post2

    def verdict(self, ethane_ratio, ethane_ratio_sdev):
        post1, post2 = self.post_prob(ethane_ratio, ethane_ratio_sdev,
                                      self.nng_lower, self.nng_upper,
                                      self.ng_lower, self.ng_upper,
                                      self.nng_prior, self.reg)
        if post1 >= self.thresh_confidence:
            return 'NOT_NATURAL_GAS', min(post1, self.max_confidence)
        elif post2 >= self.thresh_confidence:
            return 'NATURAL_GAS', min(post2, self.max_confidence)
        else:
            return 'POSSIBLE_NATURAL_GAS', max(min(post2, self.max_confidence), 1.0-self.thresh_confidence)

class VehicleExhaustClassifier(Configurable):
    ve_ethylene_sdev_factor = Float(None, allow_none=True, config=True)  # Ethylene standard deviation factor for vehicle exhaust
    ve_ethylene_lower = Float(None, allow_none=True, config=True)  # Ethylene lower level for vehicle exhaust
    ve_ethane_sdev_factor = Float(None, allow_none=True, config=True)  # Ethane standard deviation factor for vehicle exhaust
    ve_ethane_upper = Float(None, allow_none=True, config=True)  # Ethane upper level for vehicle exhaust
    """Determine if an indication is due to vehicle exhaust"""
    def __init__(self, **kwargs):
        super(VehicleExhaustClassifier, self).__init__(**kwargs)

    def compare_above(self, value, sdev, sdev_factor, lower_threshold):
        """Returns True if value exceeds lower threshold by sdev_factor*sdev"""
        return value - sdev_factor * sdev > lower_threshold

    def compare_below(self, value, sdev, sdev_factor, upper_threshold):
        """Returns True if value is less than upper threshold by sdev_factor*sdev"""
        return value + sdev_factor * sdev < upper_threshold

    def verdict(self, ethane_ratio, ethane_ratio_sdev, ethylene_ratio, ethylene_ratio_sdev):
        if (self.compare_above(ethylene_ratio, ethylene_ratio_sdev, self.ve_ethylene_sdev_factor, self.ve_ethylene_lower) and
            self.compare_below(ethane_ratio, ethane_ratio_sdev, self.ve_ethane_sdev_factor, self.ve_ethane_upper)):
            return 'VEHICLE_EXHAUST'
        else:
            return 'NOT_VEHICLE_EXHAUST'

class EthaneDispositionBlock(TransformBlock):
    ethane_classifier = Instance(EthaneClassifier, allow_none=True)
    vehicle_exhaust_classifier = Instance(VehicleExhaustClassifier, allow_none=True)

    """Computes the disposition of an indication"""
    def __init__(self, **kwargs):
        super(EthaneDispositionBlock, self).__init__(self.newData, **kwargs)
        self.ethane_classifier = EthaneClassifier(config=self.config)
        self.vehicle_exhaust_classifier = VehicleExhaustClassifier(config=self.config)

    def newData(self, newDat):
        ethane_ratio = newDat['ETHANE_RATIO']
        ethane_ratio_sdev = newDat['ETHANE_RATIO_SDEV']
        ethylene_ratio = newDat['ETHYLENE_RATIO']
        ethylene_ratio_sdev = newDat['ETHYLENE_RATIO_SDEV']
        confidence = float('nan')
        verdict = self.vehicle_exhaust_classifier.verdict(ethane_ratio, ethane_ratio_sdev, ethylene_ratio,
                                                          ethylene_ratio_sdev)
        if verdict == 'NOT_VEHICLE_EXHAUST':
            verdict, confidence = self.ethane_classifier.verdict(ethane_ratio, ethane_ratio_sdev)
        return dict(newDat, VERDICT=verdict, CONFIDENCE=confidence)

class EthaneComputationBlock(MergeBlock):
    """Computes ethane to methane ratio from the distance interpolated analyzer data (connected
    to input 0) and the output of the space-scale analyzer block (connected to input 1)"""
    # Parameters to fetch from configuration source. Set default to None so that an error is raised
    #  if there is no configuration data
    methane_ethane_sdev_ratio = Float(None, allow_none=True, config=True)
    methane_ethylene_sdev_ratio = Float(None, allow_none=True, config=True)
    interval = Float()
    maxLookback = Integer()
    methane_key = Unicode("CH4")
    ethylene_key = Unicode("C2H4")
    ethane_key = Unicode("C2H6")
    ethane_nominal_sdev_key = Unicode("AnalyzerEthaneConcentrationUncertainty")
    distance_key = Unicode("DISTANCE")
    width_key = Unicode("SIGMA")
    amplitude_key = Unicode("AMPLITUDE")
    lookup = Dict()
    min_key = Integer(allow_none=True)
    max_key = Integer(allow_none=True)
    def __init__(self, interval, maxLookback=1000, **kwargs):
        super(EthaneComputationBlock, self).__init__(self.newData, nInputs=2, **kwargs)
        assert isinstance(interval, float)
        assert interval > 0
        self.interval = interval
        self.maxLookback = maxLookback
        self.lookup = {}
        self.min_key = None
        self.max_key = None

    def ratio_analysis(self, main_conc, trace_conc, sigma_ratio):
        return ratio_analysis(main_conc, trace_conc, sigma_ratio)

    def calculate_ratios(self, methane, ethane, ethylene, amplitude, width, ethane_nominal_sdev):
        methane = np.asarray(methane)
        ethane = np.asarray(ethane)
        ethylene = np.asarray(ethylene)
        ethane_ratio, ethane_ratio_sdev, methane_sdev, ethane_sdev, pip_energy, methane_ptp = \
            self.ratio_analysis(methane, ethane, self.methane_ethane_sdev_ratio)
        # Make sure that the reported standard deviation is at least equal to the nominal value
        sdev_factor = max(ethane_nominal_sdev / ethane_sdev, 1.0)
        ethane_sdev *= sdev_factor
        methane_sdev *= sdev_factor
        ethane_ratio_sdev = max(ethane_ratio_sdev * sdev_factor, 0.001)
        ethylene_ratio, ethylene_ratio_sdev, _, ethylene_sdev, _, _ = \
            self.ratio_analysis(methane, ethylene, self.methane_ethylene_sdev_ratio)

        ethylene_nominal_sdev = ethane_nominal_sdev * self.methane_ethane_sdev_ratio / self.methane_ethylene_sdev_ratio;
        sdev_factor = max(ethylene_nominal_sdev / ethylene_sdev, 1.0)
        ethylene_sdev *= sdev_factor
        ethylene_ratio_sdev = ethylene_ratio_sdev * sdev_factor
            
        return {'ETHANE_RATIO':ethane_ratio,
                'ETHANE_RATIO_SDEV_RAW':ethane_ratio_sdev,
                'ETHANE_RATIO_SDEV':ethane_ratio_sdev*max(1.0, methane_ptp/amplitude),
                'ETHANE_CONC_SDEV':ethane_sdev,
                'ETHYLENE_RATIO':ethylene_ratio,
                'ETHYLENE_RATIO_SDEV_RAW':ethylene_ratio_sdev,
                'ETHYLENE_RATIO_SDEV':ethylene_ratio_sdev*max(1.0, methane_ptp/amplitude),
                'ETHYLENE_CONC_SDEV':ethylene_sdev,
                'PIP_ENERGY':pip_energy,
                'METHANE_PTP':methane_ptp
               }

    def newData(self, deque0, deque1, lastCall=False):
        while len(deque0) > 0:
            # Data on deque0 come from the distance interpolator block and are saved in self.lookup
            data = deque0.popleft()
            distance = data[self.distance_key]
            if isfinite(distance):
                key = int(round(distance/self.interval))
                self.min_key = min(self.min_key, key) if self.min_key is not None else key
                self.max_key = max(self.max_key, key+1) if self.max_key is not None else key+1
                self.lookup[key] = {self.methane_key:data[self.methane_key],
                                    self.ethane_key:data[self.ethane_key],
                                    self.ethylene_key:data.get(self.ethylene_key, 0.0),
                                    self.ethane_nominal_sdev_key:data.get(self.ethane_nominal_sdev_key, 0.004)}

        if self.min_key is not None and self.max_key is not None:
            while self.max_key - self.maxLookback > self.min_key:
                # Remove data in self.lookup that is more than self.maxLookback before current
                if self.min_key in self.lookup:
                    del self.lookup[self.min_key]
                self.min_key += 1

            if self.lookup:
                # Get peak information from deque1 and try to find a window of data in self.lookup
                #  which may be used to compute the peak ratios. We choose a window of 3.0*width on
                #  either side of the peak center, where width is the greater of 5.0m or the value
                #  from the peak finder
                while len(deque1) > 0:
                    data = deque1.popleft()
                    distance = data[self.distance_key]
                    if isfinite(distance):
                        width = max(5.0, data[self.width_key])
                        amplitude = data[self.amplitude_key]
                        min_key = int(round((distance - 3.0*width)/self.interval))
                        max_key = int(round((distance + 3.0*width)/self.interval))
                        # Check that we have data available to do the amplitude comparison
                        if self.min_key <= min_key and self.max_key >= max_key:
                            methane = []
                            ethane = []
                            ethylene = []
                            ethane_nominal_sdev = 0.004
                            for key in range(min_key, max_key):
                                methane.append(self.lookup[key][self.methane_key])
                                ethane.append(self.lookup[key][self.ethane_key])
                                ethylene.append(self.lookup[key][self.ethylene_key])
                                ethane_nominal_sdev = self.lookup[key][self.ethane_nominal_sdev_key]
                            yield dict(data, **self.calculate_ratios(asarray(methane),
                                                                     asarray(ethane),
                                                                     asarray(ethylene),
                                                                     amplitude,
                                                                     width,
                                                                     ethane_nominal_sdev))
                        elif lastCall or min_key < self.min_key:
                            if min_key < 0:
                                return
                            if min_key < self.min_key:
                                raise RuntimeError("Please increase value of maxLookback in EthaneComputationBlock")
                            yield dict(data, **{"ETHANE_RATIO":nan, "ETHANE_RATIO_SDEV":nan,
                                                "ETHYLENE_RATIO":nan, "ETHYLENE_RATIO_SDEV":nan})
                        else:
                            deque1.appendleft(data)
                            return
                    # If the distance is not finite, return nan
                    else:
                        yield dict(data, **{"ETHANE_RATIO":nan, "ETHANE_RATIO_SDEV":nan,
                                            "ETHYLENE_RATIO":nan, "ETHYLENE_RATIO_SDEV":nan})

class JsonWriterBlock(ActionBlock):
    filename = Unicode()
    fp = Instance(file)
    firstRow = Bool()
    def __init__(self, filename, **kwargs):
        super(JsonWriterBlock, self).__init__(self.newData, **kwargs)
        self.filename = filename
        self.fp = open(self.filename, "w")
        self.fp.write("[")
        self.firstRow = True
        self.setContinuation(self._continuation)

    def newData(self, data):
        if self.firstRow:
            self.firstRow = False
        else:
            self.fp.write(",\n")
        try:
            self.fp.write(json.dumps(data, allow_nan=False))
        except ValueError:
            result = json.dumps(data)
            result = result.replace("NaN", "null").replace("-Infinity", "null").replace("Infinity", "null")
            self.fp.write(result)

    def _continuation(self, srcBlock):
        if self.fp:
            self.fp.write("]\n")
            self.fp.close()
        self.defaultContinuation(srcBlock)
