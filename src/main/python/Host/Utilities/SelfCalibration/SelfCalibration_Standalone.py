#!/usr/bin/python
#
# FILE:
#   SelfCalibration_Standalone.py
#
# DESCRIPTION:
#   Calibrate a laser and wavelength monitor using spectroscopic information alone
#   without a wavelength monitor. This is the Near IR (G2000) version.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#  22-Mar-2017  sze  Initial release
#
#  Copyright (c) 2017 Picarro, Inc. All rights reserved
#
import bisect
import cPickle
import ctypes
import getopt
import glob
import logging
import os
import pdb
import sys
import threading
import time
import traceback
import types
from collections import OrderedDict, deque, namedtuple
from Queue import Empty, Queue

import matplotlib.pyplot as plt
import numpy as np
from configobj import ConfigObj
from scipy.optimize import leastsq, minimize
from tables import Filters, NoSuchNodeError, openFile
from traitlets import CFloat, CInt, HasTraits, TraitError, Unicode

import CmdFIFO
import hapi
import interface
from Listener import Listener
from timestamp import unixTime
from WlmCalUtilities import (AutoCal, WlmSat, bestFitCentered, bspEval,
                             bspUpdate, parametricEllipse, penalty)

APP_NAME = "CalibrateAll"
if hasattr(sys, "frozen"):  # we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

BROADCAST_PORT_RDRESULTS = 40030
BROADCAST_PORT_SENSORSTREAM = 40020
RPC_PORT_DRIVER = 50010
RPC_PORT_FREQ_CONVERTER = 50015

USE_WLMSAT = False

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection=False)

RdFreqConverter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                             APP_NAME, IsDontCareConnection=False)

# Type conversion dictionary for ctypes to numpy
ctypes2numpy = {ctypes.c_byte: np.byte, ctypes.c_char: np.byte, ctypes.c_double: np.float_,
                ctypes.c_float: np.single, ctypes.c_int: np.intc, ctypes.c_int16: np.int16,
                ctypes.c_int32: np.int32, ctypes.c_int64: np.int64, ctypes.c_int8: np.int8,
                ctypes.c_long: np.int_, ctypes.c_longlong: np.longlong, ctypes.c_short: np.short,
                ctypes.c_ubyte: np.ubyte, ctypes.c_uint: np.uintc, ctypes.c_uint16: np.uint16,
                ctypes.c_uint32: np.uint32, ctypes.c_uint64: np.uint64, ctypes.c_uint8: np.uint8,
                ctypes.c_ulong: np.uint, ctypes.c_ulonglong: np.ulonglong, ctypes.c_ushort: np.ushort}

# Routines for changing fields within an FPGA register


def _value(valueOrName):
    if isinstance(valueOrName, types.StringType):
        try:
            valueOrName = getattr(interface, valueOrName)
        except AttributeError:
            raise AttributeError(
                "Value identifier not recognized %r" % valueOrName)
    return valueOrName


def setFPGAbits(FPGAblockName, FPGAregName, optList):
    optMask = 0
    optNew = 0
    for opt, val in optList:
        bitpos = 1 << _value("%s_%s_B" % (FPGAregName, opt))
        fieldMask = (1 << _value("%s_%s_W" % (FPGAregName, opt))) - 1
        optMask |= bitpos * fieldMask
        optNew |= bitpos * val
    oldVal = Driver.rdFPGA(FPGAblockName, FPGAregName)
    newVal = ((~optMask) & oldVal) | optNew
    Driver.wrFPGA(FPGAblockName, FPGAregName, newVal)


def bin_fsr(thetaCal, lossData, binMethod, figBase=None):

    def func_to_min(peak_pos, weights):
        slopes = np.diff(peak_pos)
        if binMethod == 1:
            return sum(abs(np.diff(slopes / weights)))
        elif binMethod == 2:
            return sum(abs((slopes / weights) - np.median(slopes / weights)))
        elif binMethod == 3:
            return sum(abs((slopes / weights) - (peak_pos.ptp() / sum(weights))))

    # Use kernel density estimation techniques to find distinct cavity FSRs
    logging.info("Starting kernel density estimation for locating cavity FSRs")
    dtheta = 0.008  # radians for approx 0.1 cavityFSR
    N = 25
    theta_range = np.arange(
        dtheta * np.floor(thetaCal.min() / dtheta), thetaCal.max() + dtheta, dtheta)
    kernel = np.exp(-0.5 * (np.arange(-N, (N + 1)) / 1.5)**2)
    density = np.zeros(theta_range.shape)
    for theta in thetaCal:
        index = int(round((theta - theta_range[0]) / dtheta))
        imin = max(0, index - N)
        imax = min(index + N + 1, len(theta_range))
        density[imin: imax] += kernel[imin - index + N:imax - index + N]

    plt.figure()
    plt.plot(theta_range, density)
    plt.grid(True)
    plt.xlabel("Angle")
    plt.ylabel("Density")
    plt.title("FSR Hopping Ring-downs")
    if figBase is not None:
        plt.savefig(figBase + "_kernel_density.png")
    logging.info(
        "Finding local minima in kernel density to find bin boundaries")
    # Find positions of local minima
    dec = 3
    density_decim = density[::dec]
    valleys = (density_decim[1:-1] <= density_decim[:-2]
               ) & (density_decim[1:-1] <= density_decim[2:])
    valleys = 1 + np.flatnonzero(valleys)
    valley_pos = []
    valley_value = []
    for v in valleys:
        v = dec * v
        p = np.polyfit([-2, -1, 0, 1, 2], density[v - 2:v + 3], 2)
        if abs(p[0]) > 0.05:
            valley_pos.append(v - 0.5 * p[1] / p[0])
            valley_value.append(p[2] - 0.25 * p[1]**2 / p[0])
        else:
            valley_pos.append(v)
            valley_value.append(density[v])
    #
    # Find statistics of points between the minima
    #
    logging.info("Find statistics of points within each bin")
    valley_pos = np.asarray(valley_pos)
    peak_pos = []
    peak_std = []
    peak_count = []
    loss_mean = []
    loss_std = []
    thetaPerm = np.argsort(thetaCal)
    thetaCal = thetaCal[thetaPerm]
    lossData = lossData[thetaPerm]
    binWalls = np.digitize(theta_range[0] + valley_pos * dtheta, thetaCal)
    for i, lo in enumerate(binWalls[:-1]):
        hi = binWalls[i + 1]
        lossSel = lossData[lo:hi]
        thetaSel = thetaCal[lo:hi]
        peak_count.append(len(thetaSel))
        if len(thetaSel) > 1:
            peak_pos.append(np.mean(thetaSel))
            loss_mean.append(np.mean(lossSel))
        else:
            peak_pos.append(np.nan)
            loss_mean.append(np.nan)
        if len(thetaSel) > 2:
            peak_std.append(np.std(thetaSel))
            loss_std.append(np.std(lossSel))
        else:
            peak_std.append(np.nan)
            loss_std.append(np.nan)

    peak_pos = np.asarray(peak_pos)
    peak_std = np.asarray(peak_std)
    peak_count = np.asarray(peak_count)
    loss_mean = np.asarray(loss_mean)
    loss_std = np.asarray(loss_std)

    # Reject results with too few ringdowns
    enough = (peak_count >= 0.05 * np.mean(peak_count)) & ~np.isnan(peak_pos)
    peak_pos = peak_pos[enough]
    peak_std = peak_std[enough]
    peak_count = peak_count[enough]
    loss_mean = loss_mean[enough]
    loss_std = loss_std[enough]
    logging.info("Polishing FSR bins. Removing %d bins out of %d with fewer than %.0f points." % (
        len(enough) - np.sum(enough), len(enough), 0.05 * np.mean(peak_count)))

    weights = np.ones(len(peak_pos) - 1, dtype=int)
    best = func_to_min(peak_pos, weights)
    # Add points to improve function
    improving = True
    while improving:
        improving = False
        for k in range(len(weights)):
            unit = np.zeros(len(weights), dtype=int)
            unit[k] = 1
            trial = func_to_min(peak_pos, weights + unit)
            if trial < best:
                best = trial
                weights = weights + unit
                logging.debug(
                    "Adding bin at position %d, reducing minimization function to %f" % (k, best))
                improving = True
    insert_locations = []
    insert_peak_pos = []
    insert_peak_std = []
    insert_peak_count = []
    insert_loss_mean = []
    insert_loss_std = []

    for k, n in enumerate(weights):
        if n > 1:
            for j in range(1, n):
                insert_locations.append(k + 1)
                insert_peak_pos.append(
                    peak_pos[k] + j * (peak_pos[k + 1] - peak_pos[k]) / n)
                insert_peak_std.append(np.nan)
                insert_peak_count.append(0)
                insert_loss_mean.append(np.nan)
                insert_loss_std.append(np.nan)

    peak_pos = np.insert(peak_pos, insert_locations, insert_peak_pos)
    peak_std = np.insert(peak_std, insert_locations, insert_peak_std)
    peak_count = np.insert(peak_count, insert_locations, insert_peak_count)
    loss_mean = np.insert(loss_mean, insert_locations, insert_loss_mean)
    loss_std = np.insert(loss_std, insert_locations, insert_loss_std)
    logging.info("Added %d bins to equalize angle separation" %
                 len(insert_locations))

    best = func_to_min(peak_pos, np.ones(len(peak_pos) - 1, dtype=int))

    # Try to see if deleting points helps
    """
    improving = True
    while improving:
        improving = False
        k = 1
        while k < len(peak_pos) - 1:
            trial = func_to_min(np.delete(peak_pos, k),
                                np.ones(len(peak_pos) - 2, dtype=int))
            if trial < best:
                best = trial
                weights = weights + unit
                logging.info("Removing bin at position %d, reducing minimization function to %f" % (k, best))
                peak_pos = np.delete(peak_pos, k)
                peak_std = np.delete(peak_std, k)
                peak_count = np.delete(peak_count, k)
                loss_mean = np.delete(loss_mean, k)
                loss_std = np.delete(loss_std, k)
                improving = True
            else:
                k += 1
    """

    # plt.figure()
    #plt.plot(peak_pos, loss_mean, '.')
    # plt.grid(True)
    #plt.xlabel("Wavelength monitor angle")
    #plt.ylabel("Uncorrected Absorbance")
    #plt.title("Data collected from FSR calibration")

    # plt.figure()
    fsr_index = np.arange(len(peak_pos))
    #plt.plot(fsr_index, peak_count)
    # plt.grid(True)  # Check points lie in a band
    plt.figure()
    plt.plot(fsr_index[:-2],
             np.diff(np.log(np.diff(peak_pos)) / np.log(2.0)), '.')
    plt.fill_between(fsr_index[:-2], -0.5,
                     0.5, facecolor='yellow', alpha=0.5)
    plt.grid(True)  # Check points lie in a band
    plt.title("Log(2) Angle Separation Ratio")
    if figBase is not None:
        plt.savefig(figBase + "_wlm_angle_separation.png")

    return peak_pos, loss_mean, peak_std, loss_std


def getMultipler(x):
    if x != 0:
        mag = np.floor(np.log10(abs(x)))
        if mag >= -2:
            return 100.0, "%"
        elif mag >= -6:
            return 1.0e6, "ppm"
        elif mag >= -9:
            return 1.0e9, "ppb"
        else:
            return 1.0e12, "ppt"
    else:
        return 100.0, "%"


def fit_fsr_spectrum(dbaseName, species, wmin, wmax, p_torr, temp_C, fsr_spectrum, cavity_fsr=0.0, figBase=None):
    fc = FrequencyCalibration(dbaseName, species, wmin, wmax,
                              p_torr / 760.0, 273.15 + temp_C)
    decim = 8
    coarseData = fc.decimateData(fsr_spectrum, decim)

    if cavity_fsr != 0.0:
        # We just need to fit the frequency offset
        nu0_list = np.arange(wmin, wmax, 0.04)
        misfit = []
        logging.info(
            "FSR given (%.7f), doing brute force search for frequency values" % (cavity_fsr,))
        for nu0 in nu0_list:
            misfit.append(
                sum(fc.func_to_min((nu0, cavity_fsr), coarseData, decim)**2))
        misfit = np.asarray(misfit)
        candidates = np.argsort(misfit)
        # Plot out result of brute force search
        plt.figure()
        plt.plot(nu0_list, misfit)
        plt.grid(True)
        plt.xlabel("Start wavenumber")
        plt.ylabel("Misfit")
        plt.title("Misfit for determining frequency of first bin")
        if figBase is not None:
            plt.savefig(figBase + "_position_misfit.png")
        # Go through the most promising candidates and do a LM search for each
        res_candidates = []
        pfit_candidates = []
        pcov_candidates = []
        logging.info("Evaluating candidate solutions for deepest minimum")
        for which in candidates[:16]:
            nu0 = nu0_list[which]
            good = ~np.isnan(coarseData)
            params = (nu0,)
            pfit, pcov, infodict, errmsg, success = leastsq(
                lambda params, *
                args: fc.func_to_min(np.asarray([params[0], cavity_fsr]), *args),
                params, args=(coarseData, decim), full_output=True)
            res_candidates.append(sum(infodict["fvec"]**2))
            pfit_candidates.append(pfit)
            pcov_candidates.append(pcov)

        best = np.argmin(res_candidates)
        pfit = pfit_candidates[best]
        pcov = pcov_candidates[best]
        logging.info("Deepest minimum from brute-force search: %f at %.5f" %
                     (res_candidates[best], pfit[0]))
        logging.info("Reducing decimation of best candidate")
        while True:
            # Reduce decimation factor on best candidate
            nu0 = pfit[0]
            pcov *= sum(fc.func_to_min((nu0, cavity_fsr), coarseData, decim)
                        ** 2) / (len(coarseData) - 2)
            logging.info("Decim %d: %.5f +/- %.5f" %
                         (decim, nu0, np.sqrt(pcov[0][0])))
            nuGrid = nu0 + np.arange(len(coarseData)) * decim * cavity_fsr
            if decim == 1:
                output = fc.func_to_min(
                    (nu0, cavity_fsr), coarseData, decim, fullOutput=True)
                logging.info("Approximate concentrations from fit")
                for i, molecule in enumerate(species):
                    mult, unit = getMultipler(output["amplitudes"][i + 3])
                    logging.info("%s: %.3f +/- %.3f %s" % (molecule, mult *
                                                           output["amplitudes"][i + 3], mult * output["sdev"][i + 3], unit))
                residual = output["residual"]
                fracMisfit = sum(residual**2) / sum(coarseData[good]**2)
                plt.figure()
                plt.plot(nuGrid, coarseData, nuGrid[
                         good], coarseData[good] + residual)
                plt.grid(True)
                plt.xlabel("Wavenumber")
                plt.ylabel("Spectrum and fit")
                plt.title("Fractional misfit %.4g" % fracMisfit)
                if figBase is not None:
                    plt.savefig(figBase + "_spectrum_fit.png")
                # plt.figure()
                #plt.plot(nuGrid[good], residual)
                # plt.grid(True)
                # plt.xlabel("Wavenumber")
                # plt.ylabel("Residual")
                logging.info("Fractional misfit of spectrum: %.4g" %
                             (fracMisfit,))
                break
            decim = decim // 2
            coarseData = fc.decimateData(fsr_spectrum, decim)
            good = ~np.isnan(coarseData)
            params = (nu0,)
            pfit, pcov, infodict, errmsg, success = leastsq(
                lambda params, *
                args: fc.func_to_min(np.asarray([params[0], cavity_fsr]), *args),
                params, args=(coarseData, decim), full_output=True)

        fsr = cavity_fsr
        nu0_std = np.sqrt(pcov[0][0])
        fsr_std = 0.0
    else:
        # We need to fit both frequency offset and cavity FSR
        nu0_grid, fsr_grid = np.meshgrid(
            np.arange(wmin, wmax, 0.04), np.arange(0.019, 0.021, 0.0005))
        misfit = []
        logging.info(
            "FSR not given, doing brute force search for frequency values and FSR")
        for nu0, fsr in zip(nu0_grid.flatten(), fsr_grid.flatten()):
            misfit.append(
                sum(fc.func_to_min((nu0, fsr), coarseData, decim)**2))
        misfit = np.asarray(misfit)
        candidates = np.argsort(misfit.flatten())
        # Go through the most promising candidates and do a LM search for each
        res_candidates = []
        pfit_candidates = []
        pcov_candidates = []
        logging.info("Evaluating candidate solutions for deepest minimum")
        for which in candidates[:16]:
            nu0 = nu0_grid.flatten()[which]
            fsr = fsr_grid.flatten()[which]
            good = ~np.isnan(coarseData)
            params = (nu0, fsr)
            pfit, pcov, infodict, errmsg, success = leastsq(
                fc.func_to_min, params, args=(coarseData, decim), full_output=True)
            res_candidates.append(sum(infodict["fvec"]**2))
            pfit_candidates.append(pfit)
            pcov_candidates.append(pcov)
        best = np.argmin(res_candidates)
        pfit = pfit_candidates[best]
        pcov = pcov_candidates[best]
        logging.info("Deepest minimum from brute-force search: %f at %.5f, FSR %.7f" %
                     (res_candidates[best], pfit[0], pfit[1]))
        logging.info("Reducing decimation of best candidate")

        while True:
            nu0, fsr = pfit
            good = ~np.isnan(coarseData)
            params = (nu0, fsr)
            pfit, pcov, infodict, errmsg, success = leastsq(
                fc.func_to_min, params, args=(coarseData, decim), full_output=True)
            nu0, fsr = pfit
            pcov *= sum(fc.func_to_min((nu0, fsr), coarseData, decim)
                        ** 2) / (len(coarseData) - 2)
            logging.info("Decim %d: %.5f +/- %.5f FSR: %.7f +/- %.7f" %
                         (decim, nu0, np.sqrt(pcov[0][0]), fsr, np.sqrt(pcov[1][1])))
            nuGrid = nu0 + np.arange(len(coarseData)) * decim * fsr
            if decim == 1:
                output = fc.func_to_min(
                    (nu0, fsr), coarseData, decim, fullOutput=True)
                # print output["amplitudes"], output["sdev"]
                residual = output["residual"]
                fracMisfit = sum(residual**2) / sum(coarseData[good]**2)
                plt.figure()
                plt.plot(nuGrid, coarseData, nuGrid[
                         good], coarseData[good] + residual)
                plt.grid(True)
                plt.xlabel("Wavenumber")
                plt.ylabel("Spectrum and fit")
                plt.title("Fractional misfit %.4g" % fracMisfit)
                if figBase is not None:
                    plt.savefig(figBase + "_spectrum_fit.png")
                # plt.figure()
                # plt.plot(nuGrid[good], residual)
                # plt.grid(True)
                # plt.xlabel("Wavenumber")
                # plt.ylabel("Residual")
                logging.info("Fractional misfit of spectrum: %.4g" %
                             (fracMisfit,))
                break
            decim = decim // 2
            coarseData = fc.decimateData(fsr_spectrum, decim)
            good = ~np.isnan(coarseData)
            params = (nu0, fsr)
            pfit, pcov, infodict, errmsg, success = leastsq(
                fc.func_to_min, params, args=(coarseData, decim), full_output=True)

        nu0_std = np.sqrt(pcov[0][0])
        fsr_std = np.sqrt(pcov[1][1])

    return nu0, fsr, nu0_std, fsr_std


class FixedTraits(HasTraits):

    def __init__(self, *a, **k):
        super(FixedTraits, self).__init__(*a, **k)
        bad_keys = set(k.keys()) - set(self.trait_names())
        if bad_keys:
            raise TraitError(
                "Cannot initialize non-existent trait(s) %s" % ", ".join(bad_keys))

    def __setattr__(self, key, value):
        if hasattr(self, key) or key.startswith("_"):
            super(FixedTraits, self).__setattr__(key, value)
        else:
            raise TraitError("Cannot assign to non-existent trait %s" % key)


class ActualLaser(FixedTraits):
    BIN_METHOD = CInt(1, min=1, max=3)
    LASER_CURRENT = CInt(36000, min=0, max=65535)
    TEMP_MIN = CFloat(8.0, min=3.0, max=55.0)
    TEMP_MAX = CFloat(50.0, min=3.0, max=55.0)
    TEMP_SWEEP_RATE = CFloat(0.04, min=0.005, max=1.0)
    THRESHOLD = CInt(7000, min=2000, max=16383)
    TUNER_AMPLITUDE = CInt(10000, min=0, max=65535)
    TUNER_SLOPE = CInt(1000, min=0, max=65535)
    WAVENUM_MIN = CFloat(5931.0, min=0.0, max=20000.0)
    WAVENUM_MAX = CFloat(5952.0, min=0.0, max=20000.0)


class VirtualLaser(FixedTraits):
    ACTUAL = CInt(1, min=1, max=interface.MAX_LASERS)
    OFFSET = CFloat(0.0)
    WAVENUM_MIN = CFloat(5931.0, min=0.0, max=20000.0)
    WAVENUM_MAX = CFloat(5931.0, min=0.0, max=20000.0)


class Environment(FixedTraits):
    CAVITY_FSR = CFloat(0.0)
    CAVITY_PRESSURE = CFloat(140.0, min=20.0, max=760.0)
    FILENAME = Unicode("SelfCalibration")
    INLET_VALVE = CInt(18000, min=0, max=65535)
    WAIT_TIME = CFloat(0.0, min=0.0, max=3600.0)


class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""

    def __init__(self, **kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)


class CalibrateAll(object):

    def __init__(self, configFile, options):
        self.config = ConfigObj(configFile)
        self.options = options
        self.basePath = os.path.split(os.path.abspath(configFile))[0]
        self.actualLasers = {}
        self.virtualLasers = {}
        print "ConfigFile: ", configFile
        print "Options: ", options
        # Define a queue for the sensor stream data
        self.sensorQueue = Queue(100)
        self.streamFilterState = "COLLECTING_DATA"
        self.resultDict = {}
        self.latestDict = {}
        self.lastTime = 0
        self.ringdownQueue = Queue(100)
        self.species = {}
        self.speciesByLaser = {}
        self.getConfigs()

        fname, _ = os.path.splitext(self.env.FILENAME)
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            filename=fname + '.log',
                            filemode='w')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s %(message)s'))
        logging.getLogger("").addHandler(console_handler)
        logging.info("Command line: %s" % " ".join(sys.argv))
        self.config.filename = None
        logging.debug(
            "Dump of configuration file %s\n" % (configFile,) +
            "*** Start of configuration file dump ***\n" +
            "\n".join(self.config.write()) +
            "\n*** End of configuration file dump ***")

        self.sensorListener = Listener(
            self.sensorQueue, BROADCAST_PORT_SENSORSTREAM,
            interface.SensorEntryType, self.streamFilter,
            autoDropOldest=True)
        self.rindownListener = Listener(
            self.ringdownQueue, port=BROADCAST_PORT_RDRESULTS,
            elementType=interface.RingdownEntryType,
            retry=True, autoDropOldest=True)

    def associateRingdownsByAngle(self, thetaValues):
        """
        Given a collection of wavelength monitor angles, we wish to collect them into groups of ringdowns
        which are at the same cavity FSR. This association is done by iterating through the ringdowns in the
        order they were collected. For each ringdown, we find the group for which the latest ringdown in the group
        has a WLM angle that is closest to the WLM angle of this ringdown. If the difference is smaller than a
        specified tolerance, the ringdown is appended to the group. Otherwise a new group is started containing
        the ringdown.

        For efficiency in performing the associations, we store the groups in a two-level dictionary "rd" whose keys
        indicate the WLM angle of the latest ringdown in the group. This dictionary speeds up the search for
        the group whose most recent ringdown has a WLM angle closest to that of the current ringdown.

        We choose dtheta to be smaller than the WLM angle separation between cavity FSRs and an integer K such
        that K * dtheta is larger than the WLM angle separation between cavity FSRs. Given a WLM angle
        theta = thetaValues[i], we calculate
            idx = int(theta // dtheta)
            idx_high = idx // K
        The value i (which identifies the ringdown) will be appened to a list which will be moved to rd[idx_high][idx].

        To find the list to which i is to be appended, we look at the keys in rd[idx_high-1], rd[idx_high] and rd[idx_high+1].
        We find the key among these which is closest to idx. If this proximity is within the specified tolerance theta_tol
        (i.e., if the angles are closer than theta_tol*dtheta apart), i is appended to the list in that dictionary.

        On the other hand if no ley lies within the specified tolerance, a new list is created at rd[idx_high][idx].

        As a result of this process all the ringdowns will be placed in lists. each of which will containg ringdowns
        occurring at the same FSR. We return the lists with the ringdown indices
        """
        dtheta = 0.008  # For binning WLM angles
        K = 10
        theta_tol = 4
        rd_lookup = {}
        for i, th in enumerate(thetaValues):
            indx = int(th // dtheta)
            indx_high = indx // K
            neighbors = sorted(rd_lookup.get(indx_high - 1, {}).keys() +
                               rd_lookup.get(indx_high, {}).keys() +
                               rd_lookup.get(indx_high + 1, {}).keys())
            where = bisect.bisect_left(neighbors, indx)
            if where > 0 and indx - neighbors[where - 1] < theta_tol:
                match = neighbors[where - 1]
                group = rd_lookup[match // K][match]
            elif where < len(neighbors) and neighbors[where] - indx < theta_tol:
                match = neighbors[where]
                group = rd_lookup[match // K][match]
            else:
                match = None
                group = []
            group.append(i)
            if match is not None:
                del rd_lookup[match // K][match]
            if indx_high not in rd_lookup:
                rd_lookup[indx_high] = {}
            rd_lookup[indx_high][indx] = group
        return [rd_lookup[ih][ind] for ih in rd_lookup for ind in rd_lookup[ih]]

    def collectPztFsrInfo(self):
        logging.info(
            "Collecting PZT sensitivity information")
        lp = self.actualLasers[self.laserNum]
        assert isinstance(lp, ActualLaser)
        self.tempMin = lp.TEMP_MIN
        self.tempMax = lp.TEMP_MAX
        vLaserNum = 1
        savedLaserParams = Driver.rdVirtualLaserParams(vLaserNum)
        try:
            # Make temporary virtualLaserParams structure
            laserParams = {'actualLaser':     self.laserNum - 1,
                           'ratio1Center':    1.0,
                           'ratio1Scale':     1.05,
                           'ratio2Center':    1.0,
                           'ratio2Scale':     1.05,
                           'phase':           0.0,
                           'tempSensitivity': 0.0,
                           'calTemp':         45.0,
                           'calPressure':     760.0,
                           'pressureC0':      0.0,
                           'pressureC1':      0.0,
                           'pressureC2':      0.0,
                           'pressureC3':      0.0}
            Driver.wrVirtualLaserParams(vLaserNum, laserParams)
            laserTemp = 0.5 * (self.tempMin + self.tempMax)
            self.setupFsrHopping(laserTemp)
            Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER",
                            "SPECT_CNTRL_ContinuousMode")
            # Set up actual laser and virtual laser (for PZT offset)
            setFPGAbits("FPGA_INJECT", "INJECT_CONTROL", [
                        ("LASER_SELECT", self.laserNum - 1)])
            Driver.wrDasReg("VIRTUAL_LASER_REGISTER", vLaserNum - 1)

            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",
                            "SPECT_CNTRL_IdleState")
            Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1", 0)
            # Wait for laser temperature to stabilize then start sweeping
            while True:
                while abs(Driver.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % self.laserNum) - laserTemp) > 0.02:
                    time.sleep(1.0)
                time.sleep(5.0)
                if abs(Driver.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % self.laserNum) - laserTemp) < 0.02:
                    break

            logging.info("Capturing ringdowns in FSR Hopping Mode")
            Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",
                            interface.SPECT_CNTRL_StartingState)
            time.sleep(5.0)
            totTime = 30.0
            self.scanPztValue = 0
            self.collectForPrescribedTime(
                totTime, "laser_%d_pztscan" % self.laserNum, self.scanPzt)
        finally:
            Driver.wrVirtualLaserParams(vLaserNum, savedLaserParams)

    def collectFsrHoppingData(self):
        lp = self.actualLasers[self.laserNum]
        assert isinstance(lp, ActualLaser)
        self.tempMin = lp.TEMP_MIN
        self.setupFsrHopping(self.tempMin)
        Driver.wrDasReg("SPECT_CNTRL_MODE_REGISTER",
                        "SPECT_CNTRL_ContinuousManualTempMode")

        # Set up actual laser and virtual laser (for PZT offset)
        setFPGAbits("FPGA_INJECT", "INJECT_CONTROL", [
                    ("LASER_SELECT", self.laserNum - 1)])
        Driver.wrDasReg("VIRTUAL_LASER_REGISTER", 0)

        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",
                        "SPECT_CNTRL_IdleState")

        Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_MAX_REGISTER" %
                        self.laserNum, self.tempMax)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_MIN_REGISTER" %
                        self.laserNum, self.tempMin)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_SWEEP_INCR_REGISTER" %
                        self.laserNum, self.tempRate)

        # Wait for laser temperature to stabilize then start sweeping
        while True:
            while abs(Driver.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % self.laserNum) - self.tempMin) > 0.02:
                time.sleep(1.0)
            time.sleep(5.0)
            if abs(Driver.rdDasReg("LASER%d_TEMPERATURE_REGISTER" % self.laserNum) - self.tempMin) < 0.02:
                break

        logging.info("Capturing ringdowns in FSR Hopping Mode")
        Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",
                        "SPECT_CNTRL_StartManualState")
        time.sleep(5.0)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" %
                        self.laserNum, "TEMP_CNTRL_SweepingState")

        totTime = 0.2 * (self.tempMax - self.tempMin) / self.tempRate
        self.collectForPrescribedTime(
            totTime, "laser_%d_ringdowns" % self.laserNum)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" %
                        self.laserNum, "TEMP_CNTRL_EnabledState")

    def collectForPrescribedTime(self, totTime, tableName, updateFunc=None):
        rdDequeLen = 50
        rdInterval = 1000.0
        nextDisplay = time.time() + 1.0
        # Following is used to calculate ring-down rate
        #  while flushing the ringdownQueue before the sweep starts
        rdTimeDeque = deque()
        while True:
            try:
                rdData = self.ringdownQueue.get(block=False)
                if len(rdTimeDeque) >= rdDequeLen:
                    rdTimeDeque.popleft()
                rdTimeDeque.append(rdData.timestamp)
            except Empty:
                break
            if len(rdTimeDeque) == rdDequeLen:
                rdInterval = float(
                    rdTimeDeque[rdDequeLen - 1] - rdTimeDeque[0]) / rdDequeLen
            # Update rate display
            if time.time() >= nextDisplay:
                sys.stdout.write("\r%.1f rd/s" % (1000.0 / rdInterval,))
                nextDisplay += 1.0

        # Get the field names and data types from the ringdown entry
        self.rdBuffer = {}
        for fname, ftype in interface.RingdownEntryType._fields_:
            self.rdBuffer[fname] = ([], ftype)

        tStart = time.time()

        # Following gets ringdowns and calculates ring-down rate and percent
        #  completion which are displayed each second
        while True:
            rdData = self.ringdownQueue.get()
            if len(rdTimeDeque) >= rdDequeLen:
                rdTimeDeque.popleft()
            rdTimeDeque.append(rdData.timestamp)
            if len(rdTimeDeque) == rdDequeLen:
                rdInterval = float(
                    rdTimeDeque[rdDequeLen - 1] - rdTimeDeque[0]) / rdDequeLen
            # We turn the sequence of rdData objects into lists of columns (fields). These
            # columns are the first element of the tuple
            # self.rdBuffer[fname]
            for fname, ftype in interface.RingdownEntryType._fields_:
                if fname in self.rdBuffer:
                    self.rdBuffer[fname][0].append(getattr(rdData, fname))
            t = time.time()
            if time.time() >= nextDisplay:
                if updateFunc is not None:
                    updateFunc()
                sys.stdout.write("\r%.1f rd/s" % (1000.0 / rdInterval,))
                nextDisplay += 1.0
                complete = round(100 * (t - tStart) / totTime)
                if complete > 100.0:
                    sys.stdout.write(
                        "\r%.1f rd/s, %d%% complete\n" % (1000.0 / rdInterval, 100))
                    break
                sys.stdout.write("\r%.1f rd/s, %d%% complete" %
                                 (1000.0 / rdInterval, complete))
        # Convert to numpy arrays
        results = []
        names = []
        for fname in self.rdBuffer:
            data, dtype = self.rdBuffer[fname]
            results.append(np.asarray(data, ctypes2numpy[dtype]))
            names.append(fname)
        self.results = np.rec.fromarrays(results, names=names)
        table = self.h5.createTable(
            self.h5.root, name=tableName,
            description=self.results, filters=self.filters)
        logging.info("Average ringdown rate: %.1f rd/s" %
                     (1000 * len(self.results) / self.results["timestamp"].ptp(),))
        self.cavityPressure = Driver.rdDasReg("CAVITY_PRESSURE_REGISTER")
        self.cavityTemperature = Driver.rdDasReg("CAVITY_TEMPERATURE_REGISTER")
        table.attrs.coarseCurrent = self.coarseCurrent
        table.attrs.laserNum = self.laserNum
        table.attrs.cavityTemperature = self.cavityTemperature
        table.attrs.cavityPressure = self.cavityPressure
        table.attrs.threshold = self.threshold
        table.attrs.inletValve = self.inletValve
        table.attrs.tempMin = self.tempMin
        table.attrs.tempMax = self.tempMax
        table.attrs.tempSweepRate = self.tempRate
        table.attrs.tunerSlope = self.slope
        table.attrs.tunerAmplitude = self.ampl
        table.attrs.wavenumMin = self.wavenumMin
        table.attrs.wavenumMax = self.wavenumMax
        table.flush()

    def flushQueue(self, queue):
        while True:
            try:
                queue.get(False)
                continue
            except Empty:
                break

    def getConfigs(self):
        if "SPECIES" not in self.config:
            raise ValueError(
                "Please ensure [SPECIES] section is in the configuration file")
        for secname in self.config:
            if secname.startswith("ACTUAL"):
                aLaserNum = int(secname[6:])
                a = ActualLaser()
                if "COMMON" in self.config:
                    for option in self.config["COMMON"]:
                        if a.has_trait(option):
                            a.set_trait(option, self.config["COMMON"][option])
                for option in self.config[secname]:
                    a.set_trait(option, self.config[secname][option])
                self.actualLasers[aLaserNum] = a
            elif secname.startswith("VIRTUAL"):
                vLaserNum = int(secname[7:])
                v = VirtualLaser()
                if "COMMON" in self.config:
                    for option in self.config["COMMON"]:
                        if v.has_trait(option):
                            v.set_trait(option, self.config["COMMON"][option])
                for option in self.config[secname]:
                    v.set_trait(option, self.config[secname][option])
                self.virtualLasers[vLaserNum] = v
            elif secname.startswith("COMMON"):
                e = Environment()
                for option in self.config["COMMON"]:
                    if e.has_trait(option):
                        e.set_trait(option, self.config["COMMON"][option])
                self.env = e
            elif secname.startswith("SPECIES"):
                self.species = OrderedDict(self.config["SPECIES"])

    def makeAutoCal(self, wavenumMin, wavenumMax, t2w, w2t):
        ac = AutoCal()
        ac.ratio1Center = self.ratio1_cen
        ac.ratio2Center = self.ratio2_cen
        ac.ratio1Scale = self.ratio1_scale
        ac.ratio2Scale = self.ratio2_scale
        ac.ratio1Ampl = self.ratio1_scale
        ac.ratio2Ampl = self.ratio2_scale
        ac.wlmPhase = self.phase
        factor = 1.05 / min([ac.ratio1Scale, ac.ratio2Scale])
        ac.ratio1Scale *= factor
        ac.ratio2Scale *= factor
        ac.tEtalonCal = self.calTemperature
        ac.dTheta = 0.05
        thetaMin = (
            wavenumMin - self.wlmAngleToWaveNumber[1]) / self.wlmAngleToWaveNumber[0]
        thetaMax = (
            wavenumMax - self.wlmAngleToWaveNumber[1]) / self.wlmAngleToWaveNumber[0]
        ac.thetaBase = thetaMin - 3 * ac.dTheta
        ac.nCoeffs = int(
            np.ceil((thetaMax - thetaMin + 6 * ac.dTheta) / ac.dTheta))
        ac.sLinear0 = np.array(
            [self.wlmAngleToWaveNumber[0] * ac.dTheta,
             self.wlmAngleToWaveNumber[0] * ac.thetaBase + self.wlmAngleToWaveNumber[1]])
        ac.offset = 0
        ac.sLinear = ac.sLinear0 + np.asarray([0.0, ac.offset])
        ac.coeffs = np.zeros(ac.nCoeffs, dtype="d")
        ac.coeffsOrig = np.zeros(ac.nCoeffs, dtype="d")
        # Temperature sensitivity of etalon
        ac.wlmTempSensitivity = self.etalonTempSensitivity  # radians/degC
        ac.autocalStatus = 0
        ac.laserTemp2WaveNumber = lambda T: t2w(T)
        ac.waveNumber2LaserTemp = lambda W: w2t(W)
        return ac

    def makeWarmBoxCalibrationFile(self):
        # Perform analysis based on collected data
        wbCalFile = ConfigObj()
        wbCalFile.filename = self.wbCalFilename
        for self.laserNum in self.actualLasers:
            secName = "ACTUAL_LASER_%d" % self.laserNum
            wbCalFile[secName] = {}
        secName = "LASER_MAP"
        wbCalFile[secName] = {}
        with openFile(self.h5Filename, "r") as self.h5:
            for self.laserNum in self.actualLasers:
                lp = self.actualLasers[self.laserNum]
                assert isinstance(lp, ActualLaser)
                self.binMethod = lp.BIN_METHOD
                logging.info("Start processing of actual laser %d" %
                             (self.laserNum))
                table = self.h5.getNode("/laser_%d_ringdowns" % self.laserNum)
                data = table.read()
                self.coarseCurrent = table.attrs.coarseCurrent
                self.laserNum = table.attrs.laserNum
                self.cavityTemperature = table.attrs.cavityTemperature
                self.cavityPressure = table.attrs.cavityPressure
                self.threshold = table.attrs.threshold
                self.inletValve = table.attrs.inletValve
                self.tempMin = table.attrs.tempMin
                self.tempMax = table.attrs.tempMax
                self.tempRate = table.attrs.tempSweepRate
                self.slope = table.attrs.tunerSlope
                self.ampl = table.attrs.tunerAmplitude
                self.wavenumMin = table.attrs.wavenumMin
                self.wavenumMax = table.attrs.wavenumMax

                if "-f" in self.options:
                    lp = self.actualLasers[self.laserNum]
                    self.wavenumMin = lp.WAVENUM_MIN
                    self.wavenumMax = lp.WAVENUM_MAX

                dbname = "laser_%d_spectra" % self.laserNum
                hapi.db_begin(dbname)
                # Fetch from HITRAN if database tables do not exist
                if ("-f" in self.options) or not os.path.exists("%s/species" % dbname):
                    for f in glob.glob("%s/*" % dbname):
                        os.remove(f)
                    speciesAvailable = []
                    for molecule in self.species:
                        idList = [int(id) for id in self.species[molecule]]
                        try:
                            hapi.fetch_by_ids(molecule, idList,
                                              self.wavenumMin, self.wavenumMax)
                            speciesAvailable.append(molecule)
                        except:
                            pass
                    with open("%s/species" % dbname, "wb") as pp:
                        cPickle.dump(speciesAvailable, pp, -1)
                else:
                    with open("%s/species" % dbname, "rb") as pp:
                        speciesAvailable = cPickle.load(pp)
                self.speciesByLaser[self.laserNum] = speciesAvailable
                
                waveNum = 0.5 * (self.wavenumMin + self.wavenumMax)
                # Remove bad ringdowns
                ok = data["uncorrectedAbsorbance"] != 0
                data = data[ok]

                # Calculate parameters of ellipse
                ratio1 = data["ratio1"] / 32768.0
                ratio2 = data["ratio2"] / 32768.0
                plt.figure()
                plt.plot(ratio1, ratio2, '.')
                plt.grid(True)
                plt.xlabel("Ratio 1")
                plt.ylabel("Ratio 2")
                plt.title("WLM Orbit, Laser %d" % self.laserNum)
                if self.figBase is not None:
                    plt.savefig(self.figBase +
                                "_laser%d_wlm_orbit.png" % (self.laserNum))

                self.ratio1_cen, self.ratio2_cen, self.ratio1_scale, self.ratio2_scale, self.phase = parametricEllipse(
                    ratio1, ratio2)

                self.calTemperature = np.mean(data["etalonTemperature"])
                self.etalonTempSensitivity = -0.18465 * \
                    (waveNum / 6057.0)  # radians/degC
                theta = np.arctan2(
                    self.ratio1_scale * (ratio2 - self.ratio2_cen) - self.ratio2_scale *
                    (ratio1 - self.ratio1_cen) * np.sin(self.phase),
                    self.ratio2_scale * (ratio1 - self.ratio1_cen) * np.cos(self.phase))

                # Use brute force search to get the affine transformation to be applied to the
                #  laser temperature to give an apprximation to the WLM angle which may be used
                #  to rotate the measured angle to the correct revolution.

                slope_grid, offset_grid = np.meshgrid(
                    np.arange(-1.4, -2.4, -0.05), np.arange(-3, 4, 0.2))

                def calc_variation(params, laserTemp, theta):
                    slope, offset = params
                    theta_ref = slope * laserTemp + offset
                    thetaC = theta + 2 * np.pi * \
                        np.round((theta_ref - theta) / (2 * np.pi))
                    return np.sum(np.abs(np.diff(thetaC)))

                variation = []
                for slope, offset in zip(slope_grid.flatten(), offset_grid.flatten()):
                    variation.append(calc_variation(
                        [slope, offset], data["laserTemperature"], theta))

                variation = np.asarray(variation)
                which = np.argmin(variation)
                slope, offset = slope_grid.flatten()[which], offset_grid.flatten()[
                    which]
                logging.info(
                    "Approximate affine transformation for laser temperature to WLM angle: %.3f, %.3f" % (slope, offset))

                # Polish the minimization
                res = minimize(calc_variation, [slope, offset], (data[
                               "laserTemperature"], theta), method="Nelder-Mead")
                logging.info("Polished affine transformation for laser temperature to WLM angle: %.3f, %.3f" % (
                    res.x[0], res.x[1]))

                slope_laserTemp2WlmAngle, offset_laserTemp2WlmAngle = res.x
                theta_ref = slope_laserTemp2WlmAngle * \
                    data["laserTemperature"] + offset_laserTemp2WlmAngle

                thetaRaw = theta + 2 * np.pi * \
                    np.round((theta_ref - theta) / (2 * np.pi))
                # plt.figure()
                # plt.plot(thetaRaw, theta_ref, ".")
                # plt.xlabel("Wlm angle during FSR hopping")
                # plt.ylabel("Estimated angle from laser temperature")
                # plt.title("FSR hopping, laser %d" % (self.laserNum))
                # plt.grid(True)

                # thetaRaw is the WLM angle before etalon temperature correction
                # thetaCal is the WLM angle after correction
                thetaCal = thetaRaw + self.etalonTempSensitivity * \
                    (data["etalonTemperature"] - self.calTemperature)

                if USE_WLMSAT:
                    logging.info("Creating WlmSat object")
                    # Create a WlmSat object to handle laser current dependence of
                    #  WLM angle
                    wlmsat = WlmSat()
                    wlmsat.ratio1Ampl = self.ratio1_scale
                    wlmsat.ratio2Ampl = self.ratio2_scale
                    wlmsat.coarseCurrent = self.coarseCurrent
                    wlmsat.dTheta = 0.5
                    wlmsat.thetaBase = min(thetaRaw) - 3 * wlmsat.dTheta
                    wlmsat.nCoeffs = int(
                        1 + (max(thetaRaw) + 3 * wlmsat.dTheta - wlmsat.thetaBase) / wlmsat.dTheta)
                    wlmsat.coeffs = np.zeros(wlmsat.nCoeffs, dtype=float)

                    reg = 0.1
                    for i in range(2):
                        Inorm = (data["fineLaserCurrent"] - 32768.0) / 32768.0
                        groups = self.associateRingdownsByAngle(
                            thetaRaw - bspEval([0, 0], wlmsat.coeffs, (thetaRaw - wlmsat.thetaBase) / wlmsat.dTheta) * Inorm)

                        # plt.figure()
                        # for group in groups:
                        #    plt.plot([data["ratio1"][i] for i in group], [
                        #            data["ratio2"][i] for i in group], 'o')
                        # plt.grid(True)

                        wlmAngles = []
                        slopes = []

                        # Sort the lengths of the groups to cull groups which have the
                        # shortest lengths
                        groupLengths = np.sort(np.asarray(
                            [len(group) for group in groups]))
                        minGroupLen = groupLengths[len(groupLengths) // 20]

                        for group in groups:
                            Ifine = np.asarray(
                                [(data["fineLaserCurrent"][i] - 32768.0) / 32768.0 for i in group])
                            theta = np.asarray([thetaRaw[i] for i in group])
                            if len(group) > minGroupLen:
                                p = np.polyfit(Ifine, theta, 1)
                                wlmAngles.append(np.mean(theta))
                                slopes.append(p[0])

                        wlmAngles = np.asarray(wlmAngles)
                        slopes = np.asarray(slopes)
                        x = (wlmAngles - wlmsat.thetaBase) / wlmsat.dTheta
                        for i in range(50):
                            model = bspEval([0, 0], wlmsat.coeffs, x)
                            res = slopes - model
                            update = 0.1 * \
                                (bspUpdate(wlmsat.nCoeffs, x, res) -
                                 reg * penalty(2, wlmsat.coeffs))
                            wlmsat.coeffs += update

                    plt.figure()
                    slopes = np.asarray(slopes)
                    wlmAngles = np.asarray(wlmAngles)
                    wlmFine = np.linspace(
                        wlmsat.thetaBase, wlmsat.thetaBase + wlmsat.nCoeffs * wlmsat.dTheta, 1000)
                    plt.plot(wlmAngles, slopes, 'o', wlmFine, bspEval(
                        [0, 0], wlmsat.coeffs, (wlmFine - wlmsat.thetaBase) / wlmsat.dTheta))
                    plt.xlabel("Wavelength monitor angle (radians)")
                    plt.ylabel("WLM Laser Current Correction")
                    plt.title("WLM Laser Current Correction, laser %d" %
                              (self.laserNum))
                    plt.grid(True)
                    if self.figBase is not None:
                        plt.savefig(self.figBase +
                                    "_laser%d_wlm_laser_current_dep.png" % (self.laserNum))

                    thetaCal = thetaCal - \
                        bspEval([0, 0], wlmsat.coeffs, (thetaRaw -
                                                        wlmsat.thetaBase) / wlmsat.dTheta) * Inorm
                plt.figure()
                plt.plot(thetaCal, data["uncorrectedAbsorbance"], ".")
                plt.xlabel("Wavelength monitor angle (radians)")
                plt.ylabel("Uncorrected absorbance")
                plt.title("FSR hopping, laser %d" % (self.laserNum))
                plt.grid(True)
                if self.figBase is not None:
                    plt.savefig(self.figBase +
                                "_laser%d_loss_data.png" % (self.laserNum))

                logging.info("Starting bin_fsr")
                peak_pos, loss_mean, peak_std, loss_std = bin_fsr(
                    thetaCal, data["uncorrectedAbsorbance"],
                    self.binMethod,
                    figBase=self.figBase + "_laser%d" % (self.laserNum,))
                logging.info("Starting fit_fsr_spectrum")
                nu0, fsr, nu_err, fsr_err = fit_fsr_spectrum(
                    dbname, self.speciesByLaser[self.laserNum], self.wavenumMin, self.wavenumMax, self.cavityPressure,
                    self.cavityTemperature, loss_mean, self.env.CAVITY_FSR,
                    figBase=self.figBase + "_laser%d" % (self.laserNum,))

                # Calculate wlmAngle to wavenumber transformation
                waveNumber = nu0 + fsr * np.arange(len(peak_pos))
                self.wlmAngleToWaveNumber = np.polyfit(peak_pos, waveNumber, 1)
                # The value of self.wlmAngleToWaveNumber may be used to give linear
                # model slope and offset
                plt.figure()
                plt.plot(peak_pos, waveNumber -
                         np.polyval(self.wlmAngleToWaveNumber, peak_pos))
                plt.grid(True)
                plt.xlabel("Wavelength monitor angle (radians)")
                plt.ylabel("Difference from linear model (wavenumbers)")
                plt.title("WLM spline, laser %d" % (self.laserNum))
                if self.figBase is not None:
                    plt.savefig(self.figBase + "_laser%d_spline.png" %
                                (self.laserNum))

                fineCurrent = np.asarray(data["fineLaserCurrent"], dtype=float)
                laserTemperature = data["laserTemperature"]
                M = np.column_stack(
                    (np.ones(len(data)), laserTemperature, (fineCurrent - 32768)))
                res = np.linalg.lstsq(M, thetaCal)[0]
                freq = np.polyval(self.wlmAngleToWaveNumber,
                                  thetaCal - res[2] * (fineCurrent - 32768))
                t2w = bestFitCentered(laserTemperature, freq, 3)
                w2t = bestFitCentered(freq, laserTemperature, 3)
                # Next calculate transformation between laser temperature and
                #  wavelength monitor angle for the WlmSat object. The wavelength
                #  monitor angle is obtained by applying the inverse of self.wlmAngleToWaveNumber
                #  to the frequency in wavenumbers
                TtoA = bestFitCentered(
                    laserTemperature,
                    (freq - self.wlmAngleToWaveNumber[1]) / self.wlmAngleToWaveNumber[0], 3)

                temp = np.linspace(self.tempMin, self.tempMax, 1001)
                plt.figure()
                plt.plot(laserTemperature, freq, '.', alpha=0.5)
                plt.plot(temp, t2w(temp), lw=2)
                plt.grid(True)
                plt.xlabel("Laser temperature")
                plt.xlabel("Wavenumber")
                plt.title("Laser %d temperature to wavenumber" %
                          (self.laserNum,))
                if self.figBase is not None:
                    plt.savefig(self.figBase + "_laser%d_TtoW.png" %
                                (self.laserNum,))

                secName = "ACTUAL_LASER_%d" % self.laserNum
                wbCalFile[secName]["COARSE_CURRENT"] = self.coarseCurrent
                wbCalFile[secName]["T2W_0"] = t2w.coeffs[0]
                wbCalFile[secName]["T2W_1"] = t2w.coeffs[1]
                wbCalFile[secName]["T2W_2"] = t2w.coeffs[2]
                wbCalFile[secName]["T2W_3"] = t2w.coeffs[3]
                wbCalFile[secName]["TEMP_CEN"] = t2w.xcen
                wbCalFile[secName]["TEMP_SCALE"] = t2w.xscale
                wbCalFile[secName]["TEMP_ERMS"] = np.sqrt(t2w.residual)
                wbCalFile[secName]["W2T_0"] = w2t.coeffs[0]
                wbCalFile[secName]["W2T_1"] = w2t.coeffs[1]
                wbCalFile[secName]["W2T_2"] = w2t.coeffs[2]
                wbCalFile[secName]["W2T_3"] = w2t.coeffs[3]
                wbCalFile[secName]["WAVENUM_CEN"] = w2t.xcen
                wbCalFile[secName]["WAVENUM_SCALE"] = w2t.xscale
                wbCalFile[secName]["WAVENUM_ERMS"] = np.sqrt(w2t.residual)

                if USE_WLMSAT:
                    # Write out the WlmSat details for this actual laser
                    wlmsat.tempCen = TtoA.xcen
                    wlmsat.tempScale = TtoA.xscale
                    wlmsat.t2aCoeffs = TtoA.coeffs
                    wlmsat.updateIni(wbCalFile, self.laserNum)

                # Process any PZT sensitivity information associated with this
                # actual laser
                try:
                    pztscanTable = self.h5.getNode(
                        "/laser_%d_pztscan" % self.laserNum)
                    data = pztscanTable.read()
                    ratio1 = data["ratio1"] / 32768.0
                    ratio2 = data["ratio2"] / 32768.0
                    theta = np.arctan2(
                        self.ratio1_scale * (ratio2 - self.ratio2_cen) - self.ratio2_scale *
                        (ratio1 - self.ratio1_cen) * np.sin(self.phase),
                        self.ratio2_scale * (ratio1 - self.ratio1_cen) * np.cos(self.phase))
                    theta += self.etalonTempSensitivity * \
                        (data["etalonTemperature"] - self.calTemperature)
                    # Generate an AutoCal object to get frequencies
                    ac = self.makeAutoCal(
                        waveNumber.min(), waveNumber.max(), t2w, w2t)
                    # Update the spline coefficients
                    wn_actual = nu0 + fsr * np.arange(len(peak_pos))
                    for i in range(50):
                        ac.updateWlmCal(
                            peak_pos, wn_actual, relax=0.5, relaxDefault=0, relaxZero=0, relative=False)
                    thetaCal = ac.wlmAngleAndLaserTemp2ThetaCal(
                        theta, data["laserTemperature"])
                    freq = ac.thetaCal2WaveNumber(thetaCal)
                    TWOPI = 2 * np.pi
                    wrapped_freq = np.unwrap(
                        np.mod(TWOPI * freq / fsr, TWOPI)) / TWOPI
                    p = np.polyfit(data["pztValue"], wrapped_freq, 1)
                    plt.figure()
                    plt.plot(data["pztValue"], np.polyval(
                        p, data["pztValue"]), data["pztValue"], wrapped_freq, '.')
                    plt.xlabel("PZT digitizer units")
                    plt.ylabel("Cavity FSR")
                    plt.title("PZT Sensitivity: %.2f digU/FSR" % (1.0 / p[0],))
                    plt.grid(True)
                    if self.figBase is not None:
                        plt.savefig(self.figBase + "_laser%d_PZT_sensitivity.png" %
                                    (self.laserNum,))

                    logging.info("PZT Sensitivity: %.2f digU/FSR" %
                                 (1.0 / p[0],))
                    logging.info("RMS fit error: %.3f" % np.sqrt(
                        np.mean((wrapped_freq - np.polyval(p, data["pztValue"]))**2)))
                except NoSuchNodeError:
                    pass

                # Generate AutoCal objects for each virtual laser associated with this
                #  actual laser

                for vLaserNum in self.virtualLasers:
                    vLaser = self.virtualLasers[vLaserNum]
                    assert isinstance(vLaser, VirtualLaser)
                    if vLaser.ACTUAL == self.laserNum:
                        ac = self.makeAutoCal(
                            vLaser.WAVENUM_MIN, vLaser.WAVENUM_MAX, t2w, w2t)
                        # Update the spline coefficients
                        wn_actual = nu0 + fsr * np.arange(len(peak_pos))
                        for i in range(50):
                            ac.updateWlmCal(
                                peak_pos, wn_actual, relax=0.5, relaxDefault=0, relaxZero=0, relative=False)

                        ac.replaceOriginal()
                        logging.debug("Writing out data for virtual laser %d corresponding to actual laser %d" % (
                            vLaserNum, self.laserNum))
                        ac.offset = vLaser.OFFSET
                        ac.updateIni(wbCalFile, vLaserNum)
                        wbCalFile["LASER_MAP"]["ACTUAL_FOR_VIRTUAL_%d" %
                                               vLaserNum] = self.laserNum

                        # wn_pred = ac.thetaCal2WaveNumber(peak_pos)
                        # plt.figure()
                        # inRange = (wn_actual >= vLaser.WAVENUM_MIN) & (
                        #     wn_actual <= vLaser.WAVENUM_MAX)
                        # plt.plot(wn_actual[inRange],
                        #          wn_pred[inRange] - wn_actual[inRange])
                        # plt.grid(True)
                        # plt.title("Spline error for virtual laser %d (actual %d)" % (
                        #    vLaserNum, self.laserNum))

            # plt.show()
            logging.info("Writing out warm box calibration file: %s" %
                         self.wbCalFilename)
            wbCalFile.write()

    def measureDarkCurrents(self):
        # Collect dark current data with lasers turned off
        logging.info(
            "Turning off lasers, and measuring dark currents")
        for a in range(interface.MAX_LASERS):
            Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" %
                            (a + 1,), "LASER_CURRENT_CNTRL_DisabledState")

        time.sleep(1.0)
        self.flushQueue(self.sensorQueue)

        SensorType = None
        data = []
        # Generate a namedtuple to store all the sensor data. The names of the
        #  fields are generated dynamically from the sensor queue entries.
        while True:
            t, d, last = self.sensorQueue.get()
            if SensorType is None:
                tStart = t
                SensorType = namedtuple(
                    "Sensors", sorted(last.keys() + ["EPOCH_TIME"]))
            try:
                data.append(SensorType(EPOCH_TIME=unixTime(t), **last))
            except TypeError:
                # Get here if the fields have changed and we need to redefine
                # the namedtuple
                tStart = t
                SensorType = namedtuple(
                    "Sensors", sorted(last.keys() + ["EPOCH_TIME"]))
                data = [SensorType(EPOCH_TIME=unixTime(t), **last)]
            # Duration of dark current measurement in ms
            if t - tStart > 10000:
                break
        D = np.rec.fromrecords(data, names=SensorType._fields)
        table = self.h5.createTable(self.h5.root, name="laser_off", description=D,
                                    filters=self.filters)
        table.attrs.etalon1_mean = np.mean(D["Etalon1"])
        table.attrs.etalon1_std = np.std(D["Etalon1"])
        table.attrs.etalon2_mean = np.mean(D["Etalon2"])
        table.attrs.etalon2_std = np.std(D["Etalon2"])
        table.attrs.reference1_mean = np.mean(D["Reference1"])
        table.attrs.reference1_std = np.std(D["Reference1"])
        table.attrs.reference2_mean = np.mean(D["Reference2"])
        table.attrs.reference2_std = np.std(D["Reference2"])

        logging.info("Photodetector dark currents (digitizer units)")
        logging.info("Etalon 1: %.1f +/- %.2f" %
                     (table.attrs.etalon1_mean, table.attrs.etalon1_std))
        logging.info("Etalon 2: %.1f +/- %.2f" %
                     (table.attrs.etalon2_mean, table.attrs.etalon2_std))
        logging.info("Reference 1: %.1f +/- %.2f" %
                     (table.attrs.reference1_mean, table.attrs.reference1_std))
        logging.info("Reference 2: %.1f +/- %.2f" %
                     (table.attrs.reference2_mean, table.attrs.reference2_std))

        if not (5000 < table.attrs.etalon1_mean < 7000) or table.attrs.etalon1_std > 10:
            logging.warning("Etalon 1 dark current out of range")
        if not (5000 < table.attrs.etalon2_mean < 7000) or table.attrs.etalon2_std > 10:
            logging.warning("Etalon 2 dark current out of range")
        if not (5000 < table.attrs.reference1_mean < 7000) or table.attrs.reference1_std > 10:
            logging.warning("Reference 1 dark current out of range")
        if not (5000 < table.attrs.reference2_mean < 7000) or table.attrs.reference2_std > 10:
            logging.warning("Reference 2 dark current out of range")

        table.flush()

        # Set the dark current register values
        Driver.wrFPGA("FPGA_LASERLOCKER", "LASERLOCKER_ETA1",
                      int(table.attrs.etalon1_mean + 0.5))
        Driver.wrFPGA("FPGA_LASERLOCKER", "LASERLOCKER_REF1",
                      int(table.attrs.reference1_mean + 0.5))
        Driver.wrFPGA("FPGA_LASERLOCKER", "LASERLOCKER_ETA2",
                      int(table.attrs.etalon2_mean + 0.5))
        Driver.wrFPGA("FPGA_LASERLOCKER", "LASERLOCKER_REF2",
                      int(table.attrs.reference2_mean + 0.5))

    def run(self):
        fname, _ = os.path.splitext(self.env.FILENAME)
        self.h5Filename = fname + ".h5"
        self.wbCalFilename = fname + ".ini"
        self.figBase = fname

        if "-a" not in self.options:
            # Check that the driver can communicate
            try:
                Driver.allVersions()
            except:
                raise ValueError("Cannot communicate with driver, aborting")

            self.h5 = openFile(self.h5Filename, "w")
            self.filters = Filters(complevel=1, fletcher32=True)

            Driver.startEngine()
            try:
                nl = interface.MAX_LASERS
                regVault = Driver.saveRegValues(["LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" % (a + 1,) for a in range(nl)] +
                                                ["LASER%d_MANUAL_COARSE_CURRENT_REGISTER" % (a + 1,) for a in range(nl)] +
                                                ["LASER%d_MANUAL_FINE_CURRENT_REGISTER" % (a + 1,) for a in range(nl)] +
                                                ["LASER%d_TEMP_CNTRL_SWEEP_MAX_REGISTER" % (a + 1,) for a in range(nl)] +
                                                ["LASER%d_TEMP_CNTRL_SWEEP_MIN_REGISTER" % (a + 1,) for a in range(nl)] +
                                                ["LASER%d_TEMP_CNTRL_SWEEP_INCR_REGISTER" % (a + 1,) for a in range(nl)] +
                                                ["ANALYZER_TUNING_MODE_REGISTER",
                                                 "FLOW_CNTRL_STATE_REGISTER",
                                                 "PZT_OFFSET_VIRTUAL_LASER1",
                                                 "RDFITTER_META_BACKOFF_REGISTER",
                                                 "RDFITTER_META_SAMPLES_REGISTER",
                                                 "SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER",
                                                 "SPECT_CNTRL_MODE_REGISTER",
                                                 "TUNER_SWEEP_RAMP_HIGH_REGISTER",
                                                 "TUNER_SWEEP_RAMP_LOW_REGISTER",
                                                 "TUNER_WINDOW_RAMP_HIGH_REGISTER",
                                                 "TUNER_WINDOW_RAMP_LOW_REGISTER",
                                                 "VIRTUAL_LASER_REGISTER",
                                                 ("FPGA_TWGEN", "TWGEN_SLOPE_UP"),
                                                 ("FPGA_TWGEN", "TWGEN_SLOPE_DOWN"),
                                                 ("FPGA_TWGEN", "TWGEN_CS"),
                                                 ("FPGA_RDMAN", "RDMAN_OPTIONS"),
                                                 ("FPGA_INJECT", "INJECT_CONTROL"),
                                                 ("FPGA_LASERLOCKER",
                                                  "LASERLOCKER_OPTIONS"),
                                                 ("FPGA_LASERLOCKER", "LASERLOCKER_TUNING_OFFSET")])

                # Turn off frequency converters during calibration

                # RdFreqConverter.enableFrequencyConverter(False)

                # Start up flow control in a separate thread
                self.cavityPressureSetpoint = self.env.CAVITY_PRESSURE
                self.inletValve = self.env.INLET_VALVE

                self.flowStartTime = time.time()
                self.startFlowThread = threading.Thread(target=self.startFlow)
                self.startFlowThread.setDaemon(True)
                self.startFlowThread.start()

                self.measureDarkCurrents()
                self.waitForCavityPressure()

                for self.laserNum in self.actualLasers:
                    logging.info("Selecting laser %s" % self.laserNum)
                    self.collectFsrHoppingData()

                for self.laserNum in self.actualLasers:
                    self.collectPztFsrInfo()
                    break

            finally:
                Driver.wrDasReg("SPECT_CNTRL_STATE_REGISTER",
                                "SPECT_CNTRL_IdleState")
                Driver.restoreRegValues(regVault)
                time.sleep(1.0)
                # RdFreqConverter.enableFrequencyConverter(True)
                self.h5.close()

        self.makeWarmBoxCalibrationFile()
        self.sensorListener.stop()
        self.rindownListener.stop()

    def scanPzt(self):
        self.scanPztValue += 2000
        Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1", self.scanPztValue)

    def setupFsrHopping(self, laserTemperature):
        lp = self.actualLasers[self.laserNum]
        assert isinstance(lp, ActualLaser)
        self.coarseCurrent = lp.LASER_CURRENT
        self.tempMin = lp.TEMP_MIN
        self.tempMax = lp.TEMP_MAX
        self.tempRate = lp.TEMP_SWEEP_RATE
        self.slope = lp.TUNER_SLOPE
        self.ampl = lp.TUNER_AMPLITUDE
        self.threshold = lp.THRESHOLD
        self.wavenumMin = lp.WAVENUM_MIN
        self.wavenumMax = lp.WAVENUM_MAX

        Driver.wrDasReg("LASER%d_MANUAL_COARSE_CURRENT_REGISTER" %
                        self.laserNum, self.coarseCurrent)
        Driver.wrDasReg("LASER%d_MANUAL_FINE_CURRENT_REGISTER" %
                        self.laserNum, 32768)
        Driver.selectActualLaser(self.laserNum)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_USER_SETPOINT_REGISTER" %
                        self.laserNum, laserTemperature)
        Driver.wrDasReg("LASER%d_TEMP_CNTRL_STATE_REGISTER" %
                        self.laserNum, "TEMP_CNTRL_EnabledState")

        logging.info(
            "Turning laser on, and waiting for temperature to stabilize")

        Driver.wrDasReg("LASER%d_CURRENT_CNTRL_STATE_REGISTER" %
                        self.laserNum, "LASER_CURRENT_CNTRL_ManualState")
        # Set up optical switch
        setFPGAbits("FPGA_INJECT", "INJECT_CONTROL", [
                    ("LASER_SELECT", self.laserNum - 1)])

        # Set up analyzer for frequency hopping mode acquisition

        Driver.wrDasReg(
            "SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER", self.threshold)

        Driver.wrDasReg("ANALYZER_TUNING_MODE_REGISTER",
                        "ANALYZER_TUNING_FsrHoppingTuningMode")
        Driver.wrFPGA("FPGA_TWGEN", "TWGEN_SLOPE_UP", self.slope)
        Driver.wrFPGA("FPGA_TWGEN", "TWGEN_SLOPE_DOWN", self.slope)

        Driver.wrDasReg("TUNER_SWEEP_RAMP_LOW_REGISTER",
                        32768 - int(self.ampl))
        Driver.wrDasReg("TUNER_WINDOW_RAMP_LOW_REGISTER",
                        32768 - int(0.95 * self.ampl))
        Driver.wrDasReg("TUNER_WINDOW_RAMP_HIGH_REGISTER",
                        32768 + int(0.95 * self.ampl))
        Driver.wrDasReg("TUNER_SWEEP_RAMP_HIGH_REGISTER",
                        32768 + int(self.ampl))

        setFPGAbits("FPGA_TWGEN", "TWGEN_CS", [("TUNE_PZT", 0)])
        setFPGAbits("FPGA_RDMAN", "RDMAN_OPTIONS", [("LOCK_ENABLE", 0),
                                                    ("UP_SLOPE_ENABLE", 1),
                                                    ("DOWN_SLOPE_ENABLE", 1),
                                                    ("DITHER_ENABLE", 0)])
        Driver.wrDasReg("RDFITTER_META_BACKOFF_REGISTER", 1)
        Driver.wrDasReg("RDFITTER_META_SAMPLES_REGISTER", 1)
        setFPGAbits("FPGA_LASERLOCKER", "LASERLOCKER_OPTIONS",
                    [("DIRECT_TUNE", 1)])

    def startFlow(self):
        Driver1 = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                             APP_NAME, IsDontCareConnection=False)
        if self.inletValve > 0:
            if (Driver1.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_OutletControlState or
                abs(Driver1.rdDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER") - self.cavityPressureSetpoint) > 0.2 or
                    abs(Driver1.rdDasReg("CAVITY_PRESSURE_REGISTER") - self.cavityPressureSetpoint) > 0.2):
                Driver1.wrDasReg("FLOW_CNTRL_STATE_REGISTER",
                                "FLOW_CNTRL_DisabledState")
                time.sleep(1.0)
                while Driver1.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_OutletControlState:
                    Driver1.wrDasReg("VALVE_CNTRL_STATE_REGISTER",
                                    "VALVE_CNTRL_OutletControlState")
                    time.sleep(1.0)
                inlet = 0
                Driver1.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER", inlet)
                Driver1.wrDasReg(
                    "VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER", self.cavityPressureSetpoint)
                while inlet < self.inletValve:
                    if Driver1.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_OutletControlState:
                        Driver1.wrDasReg("VALVE_CNTRL_STATE_REGISTER",
                                        "VALVE_CNTRL_OutletControlState")
                    time.sleep(1.0)
                    inlet = min(self.inletValve, inlet + 1000)
                    Driver1.wrDasReg(
                        "VALVE_CNTRL_USER_INLET_VALVE_REGISTER", inlet)
        else:  # Use contol with no inlet valve
            if (Driver1.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_OutletOnlyControlState or
                abs(Driver1.rdDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER") - self.cavityPressureSetpoint) > 0.2 or
                    abs(Driver1.rdDasReg("CAVITY_PRESSURE_REGISTER") - self.cavityPressureSetpoint) > 0.2):
                Driver1.wrDasReg(
                    "VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER", self.cavityPressureSetpoint)
                while Driver1.rdDasReg("VALVE_CNTRL_STATE_REGISTER") != interface.VALVE_CNTRL_OutletOnlyControlState:
                    Driver1.wrDasReg("VALVE_CNTRL_STATE_REGISTER",
                                     "VALVE_CNTRL_OutletOnlyControlState")
                    time.sleep(1.0)
            
        # Wait for cavity pressure to get close to desired value and remain
        # there for 5s
        while True:
            while abs(Driver1.rdDasReg("CAVITY_PRESSURE_REGISTER") - self.cavityPressureSetpoint) > 0.2:
                time.sleep(1.0)
            time.sleep(5.0)
            if abs(Driver1.rdDasReg("CAVITY_PRESSURE_REGISTER") - self.cavityPressureSetpoint) < 0.2:
                break

    def streamFilter(self, result):
        # This filter is designed to enqueue sensor entries which all have the same timestamp.
        #  A 3-ple consisting of the timestamp, a dictionary of sensor data at that time
        #  and a dictionary of the most current sensor data as of that time
        #  is placed on the listener queue. The dictionary is keyed by the stream name
        #  (e.g. STREAM_Laser1Temp gives the key "Laser1Temp" obtained by starting from the 7'th
        #  character in the stream index)
        #  A state machine is used to cache the first sample that occure at a new time and to
        #  return the dictionary collected at the last time.
        self.latestDict[interface.STREAM_MemberTypeDict[result.streamNum]
                        [7:]] = result.value

        if self.streamFilterState == "RETURNED_RESULT":
            self.lastTime = self.cachedResult.timestamp
            self.resultDict = {
                interface.STREAM_MemberTypeDict[self.cachedResult.streamNum][7:]: self.cachedResult.value}

        if abs(result.timestamp - self.lastTime) > 5:
            self.cachedResult = interface.SensorEntryType(
                result.timestamp, result.streamNum, result.value)
            self.streamFilterState = "RETURNED_RESULT"
            if self.resultDict:
                return self.lastTime, self.resultDict.copy(), self.latestDict.copy()
            else:
                return
        else:
            self.resultDict[interface.STREAM_MemberTypeDict[result.streamNum]
                            [7:]] = result.value
            self.streamFilterState = "COLLECTING_DATA"

    def waitForCavityPressure(self):
        if self.startFlowThread.isAlive():
            logging.info("Waiting for cavity flow to stabilize")
            while time.time() - self.flowStartTime < 200:
                self.startFlowThread.join(timeout=1)
                sys.stdout.write(".")
                if not self.startFlowThread.isAlive():
                    sys.stdout.write("\n")
                    logging.info("Cavity pressure has been established")
                    break
            else:
                logging.error(
                    "Cavity pressure did not stabilize in time, check pump and sample handling.")
                raise RuntimeError


class FrequencyCalibration(object):

    def __init__(self, dbaseName, species, wmin, wmax, p_atm, T_K):
        hapi.db_begin(dbaseName)
        # Compute the basis functions on a fine grid which can be interpolated
        self.species = species
        self.bases = {}
        self.nuFine = np.arange(wmin, wmax, 0.001)
        for molecule in self.species:
            _, self.bases[molecule] = hapi.absorptionCoefficient_Voigt(
                SourceTables=molecule, Environment=dict(p=p_atm, T=T_K), OmegaGrid=self.nuFine)
        self.p_atm = p_atm
        self.T_K = T_K
        k = 1.3806488e-16
        atm = 1.01325e6
        self.Ndens = (p_atm * atm) / (k * T_K)

    def decimateData(self, data, decim=1):
        decimLength = len(data) // decim
        newdata = np.mean(
            data[:decimLength * decim].reshape((decimLength, decim)), axis=-1)
        return newdata

    def func_to_min(self, params, coarseData, decim=1, fullOutput=False):
        # Use linear least squares for amplitude and baseline calculation
        good = ~np.isnan(coarseData)
        nfsr = len(coarseData) * decim
        nuCoarse, models = self.makeModels(params, nfsr, decim)
        M = np.column_stack((np.ones(nfsr // decim), np.arange(nfsr // decim, dtype=float), np.arange(nfsr // decim, dtype=float)**2) +
                            tuple([models[molecule] for molecule in self.species]))
        result = np.linalg.lstsq(M[good, :], coarseData[good])[0]
        residual = np.dot(M[good, :], result) - coarseData[good]
        if fullOutput:
            msqres = np.mean(residual**2)
            sdev = np.sqrt(msqres * np.diag(np.linalg.inv(M.T.dot(M))))
            return dict(amplitudes=result, sdev=sdev, residual=residual)
        else:
            return residual

    def makeModels(self, params, nfsr, decim=1):
        nu0, fsr = params
        nuGrid = nu0 + np.arange(nfsr) * fsr
        models = {molecule: 0.0 for molecule in self.species}
        # Compute low-resolution models
        for k in xrange(decim):
            for molecule in self.species:
                models[molecule] += np.interp(
                    nuGrid[k:(nfsr // decim) * decim:decim], self.nuFine, self.bases[molecule])
        for molecule in self.species:
            models[molecule] = 1e6 * self.Ndens * models[molecule] / decim
        return nuGrid[:(nfsr // decim) * decim:decim], models


HELP_STRING = """
SelfCalibration.py [-a] [-f] [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options
override settings in the configuration file:

-h, --help           print this help
-a                   skip acquisition and perform analysis only
-f                   fresh start, force spectra reload from HITRAN
-c                   specify a config file:  default = "./SelfCalibration.ini"
"""


def printUsage():
    print HELP_STRING


def handleCommandSwitches():
    shortOpts = 'hafc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    # assemble a dictionary where the keys are the switches and values are
    # switch args...
    options = {}
    for o, a in switches:
        options.setdefault(o, a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h', "")
    # Start with option defaults...
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return configFile, options


if __name__ == "__main__":
    configFile, options = handleCommandSwitches()
    try:
        m = CalibrateAll(configFile, options)
        m.run()
    except:
        logging.error(traceback.format_exc())
