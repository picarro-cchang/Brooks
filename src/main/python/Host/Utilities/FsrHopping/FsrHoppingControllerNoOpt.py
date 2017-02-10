#!/usr/bin/python
"""
File Name: FsrHoppingController.py
Purpose: Supervises FSR Hopping mode of G2000 analyzers

File History:
    14-Oct-2015  sze       Initial version

Copyright (c) 2015 Picarro, Inc. All rights reserved
"""
import argparse
from copy import deepcopy
from Host.autogen import interface
from Host.Common import CmdFIFO, configobj, Listener
from Host.Common.PConfigurable import PConfigurable
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.Common.SharedTypes import (BROADCAST_PORT_RDRESULTS, RPC_PORT_DRIVER,
                                     RPC_PORT_FSR_HOPPING_CONTROLLER,
                                     RPC_PORT_SPECTRUM_COLLECTOR)
import numpy as np
import os
import Pyro.errors
import Queue
from scipy.signal import order_filter
import sys
from threading import Thread
import time
from traitlets import (CaselessStrEnum, CBool, CFloat, CInt, Float, ForwardDeclaredInstance,
                       Instance, Integer, List)

APP_NAME = "FSR Hopping Controller"
APP_VERSION = "1.0.0"
EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    app_path = sys.executable
else:
    app_path = sys.argv[0]

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    APP_NAME, IsDontCareConnection = False)

SpectrumCollector = None

def setup_current_generator(actual_laser, slope_factor, time_between_steps,
                            lower_window, upper_window, levels, sequence_id):
    assert len(levels) <= 0x200
    assert 1 <= actual_laser <= interface.MAX_LASERS
    bank = 0
    Driver.wrRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, levels)
    Driver.rdRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, len(levels))

    period = len(levels)
    M = 1 << interface.LASER_CURRENT_GEN_ACC_WIDTH
    T = time_between_steps
    slow_slope = int(round((M / T) * slope_factor / (1 - slope_factor)))
    fast_slope = int(round((M / T) * (1 - slope_factor) / slope_factor))
    first_offset = int(round(M * (2 * slope_factor - 1) / (2 * slope_factor))) % M
    second_offset = int(round(M * (2 * slope_factor - 1) / (slope_factor - 1)))
    first_breakpoint = int(np.ceil((1 - slope_factor) * T / 2))
    second_breakpoint = int(np.ceil((1 + slope_factor) * T / 2))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SLOW_SLOPE", slow_slope)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FAST_SLOPE", fast_slope)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FIRST_OFFSET", first_offset)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SECOND_OFFSET", second_offset)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FIRST_BREAKPOINT", first_breakpoint)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SECOND_BREAKPOINT", second_breakpoint)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT", T)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT", period)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_LOWER_WINDOW", lower_window)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_UPPER_WINDOW", upper_window)
    # Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SEQUENCE_ID", sequence_id)
    control = ((1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B) |
               ((actual_laser - 1) << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B) |
               (bank << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS", control)
    # Wait until the parameters have been loaded for the particular laser
    while (Driver.rdFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS") &
           (1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B)):
        time.sleep(0.01)
    # Turn on extended laser current mode
    inj = Driver.rdFPGA("FPGA_INJECT","INJECT_CONTROL2")
    Driver.wrFPGA("FPGA_INJECT","INJECT_CONTROL2", inj | (1<<interface.INJECT_CONTROL2_EXTENDED_CURRENT_MODE_B))
class ClusterAnalyzer(PConfigurable):
    """Perform clustering of data in the range [0,1] using kernel density estimation with a Gaussian kernel
        of standard deviation sigma and an auxiliary array of size nbins for accumulating the probability
        density estimate"""
    naverage = CFloat(1000.0, config=True)  # Effective number of values used to make histogram
    nbins = CInt(1024, config=True)  # Number of bins for accumulating histogram
    sigma = CFloat(100.0/65536.0, config=True)  # Half-width of kernel for density estimation
    base = Instance(np.ndarray)
    kernel = Instance(np.ndarray)
    laser_current_model = ForwardDeclaredInstance('LaserCurrentModel')
    density = Instance(np.ndarray)  # Density estimate updated by sample values, using exponential averaging
    min_bin_width = CFloat(None, allow_none=True, config=True)
    local_jump_estimator_halfwidth = CInt(3, config=True)
    bin_boundaries = Instance(np.ndarray)
    bin_counts = Instance(np.ndarray)
    bin_indices = Instance(np.ndarray)
    bin_means = Instance(np.ndarray)
    bin_sums = Instance(np.ndarray)
    mode_boundaries = Instance(np.ndarray, allow_none=True)
    mode_numbers = Instance(np.ndarray)

    def __init__(self, *args, **kwargs):
        super(ClusterAnalyzer, self).__init__(*args, **kwargs)
        self.initialize_kernel()

    def initialize_kernel(self):
        self.base = (np.arange(2*self.nbins) - self.nbins)/float(self.nbins)
        # The kernel is evaluated once on an array of size 2*nbins
        self.kernel = np.exp(-0.5*(self.base/self.sigma)**2)
        self.reset_density()

    def reset_density(self):
        self.density = np.zeros(self.nbins, dtype=float)

    def _nbins_changed(self):
        self.initialize_kernel()

    def _sigma_changed(self):
        self.initialize_kernel()

    def cluster(self, values):
        """values is an array containing the data to cluster. Each value must be in the range [0,1]"""
        values = np.asarray(values)
        for value in values:
            index = int(self.nbins*value + 0.5)
            self.density = (self.kernel[self.nbins-index:2*self.nbins-index] +
                            (self.naverage-1) * self.density) / self.naverage
        # Find strict local minima. Note that the indices are shifted by 1 by the slicing, so
        #  we take this into account when converting back to normalized values
        min_indices = ((self.density[1:-1] < self.density[:-2]) & (self.density[1:-1] < self.density[2:]))
        self.bin_boundaries = (1 + np.flatnonzero(min_indices)) / float(self.nbins)
        # Use digitize to classify values into clusters using the minima in the density estimate as
        #  the bin boundaries
        self.update_bins(values)
        self.assign_modes(values)

    def assign_modes(self, values):
        """After clustering, we need to assign integer mode numbers to each bin. We use a two-stage
        process (merge followed by mode assignment), considering the saparations between the bin_means,
        which we define to be dx

        1) Repeatedly look at the two bins with the smallest separation, and merge them until the
            smallest separation is greater than min_bin_width (if this is specified), or
            0.6 times the median bin separation (if min_bin_width is None)

        2) Recompute the bins on the basis of the new boundaries obtained in the merge phase. Use an
            order filter which computes the minimum value of dx in blocks of size 2*local_jump_estimator_halfwidth+1
            as a way of obtaining a local estimate of the mode separation. Fill in missing modes using
            dx divided by the local mode separation estimate
        """
        global SpectrumCollector
        dx = np.diff(self.bin_means)
        # Perform merge phase
        good = np.arange(len(dx))
        while len(dx) > 1:
            min_sep_pos = np.argmin(dx)
            min_sep = self.min_bin_width if self.min_bin_width is not None else 0.6*np.median(dx)
            if dx[min_sep_pos] >= min_sep:
                break
            dx_min = dx[min_sep_pos]
            if min_sep_pos > 0:
                dx[min_sep_pos-1] += 0.5 * dx_min
            if min_sep_pos < len(dx) - 1:
                dx[min_sep_pos+1] += 0.5 * dx_min
            dx = np.delete(dx, min_sep_pos)
            good = np.delete(good, min_sep_pos)
        self.bin_boundaries = self.bin_boundaries[good]
        self.update_bins(values)
        # Perform mode assignment
        dx = np.diff(self.bin_means)
        mx = order_filter(dx,np.ones(2*self.local_jump_estimator_halfwidth+1), 0)
        # Extend the FSR estimate out to the ends of the frequency range
        mx[:self.local_jump_estimator_halfwidth] = mx[self.local_jump_estimator_halfwidth]
        mx[-(self.local_jump_estimator_halfwidth+1):] = mx[-(self.local_jump_estimator_halfwidth+1)]
        mode_boundaries = []
        m = [0]
        # Go through assigning indices, using the local FSR estimates to determine jumps
        for i,d in enumerate(dx):
            jump = int(np.round(d/mx[i]))
            m.append(m[-1] + jump)
            for k in range(jump):
                # Calculate boundaries between modes, assuming that there are "jump" modes between self.bin_mean[i] and
                #  self.bin_mean[i+1]
                boundary_index = 2 * k + 1
                boundary = ((2 * jump - boundary_index) * self.bin_means[i] + boundary_index * self.bin_means[i+1]) / (2 * jump)
                mode_boundaries.append(boundary)
        self.mode_boundaries = np.asarray(mode_boundaries)
        self.mode_numbers = np.asarray(m)
        for m, v, c in zip(self.mode_numbers, self.bin_means, self.bin_counts):
            print "%3d: %7.0f (%4d)" % (m, 65536.0 * v, c)
        if SpectrumCollector is None:
            SpectrumCollector = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
                                       APP_NAME, IsDontCareConnection = False)
        try:
            SpectrumCollector.setFsrModeBoundaries(self.laser_current_model.actual_laser, 65536.0*self.mode_boundaries)
        except Pyro.errors.ProtocolError:
            Log("Cannot communicate with spectrum collector")
            SpectrumCollector = None


    def update_bins(self, values):
        self.bin_indices = np.digitize(values, bins=self.bin_boundaries)
        # Find means and number of values in each bin.
        self.bin_sums = np.zeros(len(self.bin_boundaries)+1, dtype=float)
        self.bin_counts = np.zeros(len(self.bin_boundaries)+1)
        for b,v in zip(self.bin_indices, values):
            self.bin_sums[b] += v
            self.bin_counts[b] += 1
        mask = (self.bin_counts > 0)
        self.bin_counts = self.bin_counts[mask]
        self.bin_means = self.bin_sums[mask] / self.bin_counts
        self.bin_boundaries = self.bin_boundaries[mask[:-1]]

class LaserCurrentModel(PConfigurable):
    actual_laser = CInt(-1)
    approx_mode_separation = CInt(700, config=True)
    batch_size = CInt(1000, config=True)
    centers = List(Float, [], config=True, json=True)
    cluster_analyzer = Instance(ClusterAnalyzer, args=(), config=True)
    dwells = List(List(Integer), [[]], config=True, json=True)
    levels = List(Integer, [])
    lower = Float()
    lower_window = CInt(20000, config=True)
    mode = CaselessStrEnum(values=['staircase', 'sawtooth'], default_value='staircase', config=True)
    offsets = List(List(Integer), [[]], config=True, json=True)
    reset_flag = CBool(False)
    sawtooth_size = CFloat(0.25, config=True)
    sequence_id = CInt(0)
    slope_factor = CFloat(0.5, config=True)
    time_between_steps = CInt(600, config=True)
    optimize_levels = CBool(False, config=True)
    upper = Float()
    upper_window = CInt(40000, config=True)
    window = List(Integer, [20000, 40000], minlen=2, maxlen=2)

    def __init__(self, *args, **kwargs):
        super(LaserCurrentModel, self).__init__(*args, **kwargs)
        self.cluster_analyzer.laser_current_model = self

    def __str__(self):
        values = []
        for attr_name in sorted(dir(self)):
            attr = getattr(self, attr_name)
            if not attr_name.startswith("_") and not callable(attr):
                values.append("\n\t%s: %s" % (attr_name, attr))
        return "LaserCurrentModel" + "".join(values) + "\n"

    def __repr__(self):
        return self.__str__()

    def _mode_changed(self):
        if self.mode == 'sawtooth':
            self.slope_factor = 0.5

    def _upper_window_changed(self):
        self.upper = min(self.upper_window + self.approx_mode_separation, 65535)
        self.window[1] = self.upper_window

    def _lower_window_changed(self):
        self.lower = max(self.lower_window - self.approx_mode_separation, 0)
        self.window[0] = self.lower_window

    def _window_changed(self):
        self.lower_window = self.window[0]
        self.upper_window = self.window[1]

    def _approx_mode_separation_changed(self):
        self._lower_window_changed()
        self._upper_window_changed()

    def setup_uniform_levels(self, reset_density=True):
        """Set the levels for the current generator to be uniformly spaced between lower and upper
        limits so that the spacing between modes is approx_mode_separation. The values of
        lower and upper are chosen to include the interval between lower_window and upper_window,
        with some additional padding to minimize edge effects"""
        nmodes = int(np.ceil(float(self.upper - self.lower) / self.approx_mode_separation))
        mode_currents = np.linspace(self.lower, self.upper, nmodes)
        slopes = (mode_currents[1] - mode_currents[0]) * np.ones_like(mode_currents)
        sawtooth_size = 0.25
        slope_factor = 0.5
        levels = []
        for slope, current in zip(slopes, mode_currents):
            if self.mode == 'sawtooth':
                levels.append(int(max(0, current - sawtooth_size*slope)))
                levels.append(int(min(65535, current + sawtooth_size*slope)))
            elif self.mode == 'staircase':
                levels.append(int(current))
        self.levels = levels
        self.sequence_id = 0
        setup_current_generator(self.actual_laser, slope_factor, self.time_between_steps,
                                self.lower_window, self.upper_window, self.levels, self.sequence_id)
        if reset_density:
            self.cluster_analyzer.reset_density()

    def cluster_currents(self, currents_at_rd):
        values = np.asarray(currents_at_rd) / 65536.0
        ca = self.cluster_analyzer
        ca.cluster(values)

    def setup_custom_levels(self, currents_at_rd):
        ca = self.cluster_analyzer
        self.cluster_currents(currents_at_rd)
        modes = np.arange(ca.mode_numbers.min(), ca.mode_numbers.max() + 1)
        mode_currents = np.interp(modes, ca.mode_numbers, 65536.0 * ca.bin_means)
        median_slope = np.median(np.diff(mode_currents))
        # Extend the mode currents on each side until we exceed lower and upper limits
        above = []
        current = mode_currents[-1]
        while True:
            current += median_slope
            above.append(current)
            if current > self.upper:
                break
        below = []
        current = mode_currents[0]
        while True:
            current -= median_slope
            below.append(current)
            if current < self.lower:
                break
        below.reverse()
        mode_currents = np.concatenate((np.asarray(below), mode_currents, np.asarray(above)))
        # Trim top and bottom to find values closest to self.lower and self.upper
        lower_index = np.argmin(abs(mode_currents - self.lower))
        upper_index = np.argmin(abs(mode_currents - self.upper))
        # Update self.lower and self.upper, making sure that self.lower lies between
        # self.lower_window - 2*self.approx_mode_separation and self.lower_window and
        # self.upper lies betwen self.upper_window and
        # self.upper_window + 2*self.approx_mode_separation
        self.lower = mode_currents[lower_index]
        self.lower = max(self.lower, 0.0, self.lower_window - 2*self.approx_mode_separation)
        self.lower = min(self.lower, self.lower_window)
        self.upper = mode_currents[upper_index]
        self.upper = min(self.upper, 65535.0, self.upper_window + 2*self.approx_mode_separation)
        self.upper = max(self.upper, self.upper_window)
        mode_currents = mode_currents[lower_index:upper_index+1]
        peak_indices = [np.argmin(abs(mode_currents - pk)) for pk in self.centers]
        sawtooth_size = self.sawtooth_size
        slope_factor = self.slope_factor
        levels = []
        for i, current in enumerate(mode_currents):
            dwell = 1
            if not (self.lower <= current < self.upper):
                continue
            if self.mode == 'sawtooth':
                for j, pk in enumerate(peak_indices):
                    try:
                        idx = self.offsets[j].index(i-pk)
                        dwell = self.dwells[j][idx]
                    except ValueError:
                        pass
                for j in range(dwell):
                    levels.append(int(current - sawtooth_size*median_slope))
                    levels.append(int(current + sawtooth_size*median_slope))
            elif self.mode == 'staircase':
                levels.append(int(current))

        print "Number of levels: ", len(levels)
        print "Lower", self.lower, "  Upper", self.upper
        print "Min current", mode_currents[0], "  Max current", mode_currents[-1]
        print levels
        self.levels = levels
        self.sequence_id += 1
        setup_current_generator(self.actual_laser, slope_factor, self.time_between_steps,
                                self.lower_window, self.upper_window, self.levels, self.sequence_id)

class Laser1(LaserCurrentModel):
    actual_laser = CInt(1)

class Laser2(LaserCurrentModel):
    actual_laser = CInt(2)

class Laser3(LaserCurrentModel):
    actual_laser = CInt(3)

class Laser4(LaserCurrentModel):
    actual_laser = CInt(4)

class FsrHoppingController(PConfigurable):
    config = Instance(configobj.ConfigObj)
    laser1 = Instance(Laser1, allow_none=True, config=True)
    laser2 = Instance(Laser2, allow_none=True, config=True)
    laser3 = Instance(Laser3, allow_none=True, config=True)
    laser4 = Instance(Laser4, allow_none=True, config=True)
    lcm = List(maxlen=interface.MAX_LASERS)
    currents_at_rd = List(List(Integer), [[] for _ in range(interface.MAX_LASERS)])
    rd_listener = Instance(Listener.Listener)
    rd_queue = Instance(Queue.Queue)
    rpc_server = Instance(CmdFIFO.CmdFIFOServer)
    rpc_thread = Instance(Thread)

    def __init__(self, options, *args, **kwargs):
        super(FsrHoppingController, self).__init__(*args, **kwargs)
        self.rd_queue = Queue.Queue(1000)
        self.rd_listener = Listener.Listener(self.rd_queue,
                                   BROADCAST_PORT_RDRESULTS,
                                   interface.RingdownEntryType,
                                   retry = True,
                                   name = "FsrHoppingController Ringdown listener")
        self.config = configobj.ConfigObj(options["config"], list_values=False)
        self.process_config()
        self.start_rpc_server()

    def process_config(self):
        self.configure({}, self.config)
        self.lcm.append(self.laser1)
        self.lcm.append(self.laser2)
        self.lcm.append(self.laser3)
        self.lcm.append(self.laser4)

    def flush_rd_queue(self):
        while not self.rd_queue.empty():
            try:
                self.rd_queue.get(False)
            except Queue.Empty:
                continue
            self.rd_queue.task_done()

    def main_loop(self):
        for lcm in self.lcm:
            if lcm is not None:
                lcm.setup_uniform_levels()
        ringdowns = 0
        while self.rpc_thread.isAlive():
            try:
                datum = self.rd_queue.get(False)
                ringdowns += 1
                if ringdowns % 50 == 0:
                    sys.stdout.write('.')
                # Get actual laser index in range 1-4
                actual_laser = (datum.laserUsed & 3) + 1
                self.currents_at_rd[actual_laser-1].append(datum.fineLaserCurrent)
                lcm = self.lcm[actual_laser-1]
                if len(self.currents_at_rd[actual_laser-1]) == lcm.batch_size:
                    if lcm.optimize_levels:
                        lcm.setup_custom_levels(self.currents_at_rd[actual_laser-1])
                    else:
                        if lcm.sequence_id == 0:
                            lcm.cluster_currents(self.currents_at_rd[actual_laser-1])
                            lcm.setup_uniform_levels(reset_density=False)
                        else:
                            lcm.setup_uniform_levels()
                    self.currents_at_rd[actual_laser-1] = []
            except Queue.Empty:
                for lcm in self.lcm:
                    if lcm is not None:
                        if lcm.reset_flag or (lcm.sequence_id > 0 and not lcm.optimize_levels):
                            lcm.reset_flag = False
                            lcm.setup_uniform_levels()
                time.sleep(0.2)
        print "Main loop ends due to termination of RPC thread"

    def get_lcm_param(self, name):
        results = []
        for laser in range(1, interface.MAX_LASERS+1):
            lcm = self.lcm[laser-1]
            if isinstance(lcm, LaserCurrentModel):
                results.append(getattr(lcm, name))
            else:
                results.append(None)
        return results

    def get_approx_mode_separation(self):
        """Get the list of approximate mode separations in units of fine
        laser current for each of the four lasers. If a laser is not present,
        the entry is None"""
        return self.get_lcm_param('approx_mode_separation')

    def get_batch_size(self):
        """Get the list of batch sizes indicating the number of ring-downs
        between updates of the waveform generator. If a laser is not
        present, the entry is None"""
        return self.get_lcm_param('batch_size')

    def get_mode(self):
        """Get the list of waveform generator modes for each of four lasers.
        Each can be the string "staircase" or "sawtooth". If a laser is not
        present, the entry is None"""
        return self.get_lcm_param('mode')

    def get_mode_boundaries(self):
        """Get the list of estimated fine laser currents which may be used to
        bin the ringdowns into cavity modes. If a laser is not
        present, the entry is None"""
        results = []
        for laser in range(1, interface.MAX_LASERS+1):
            lcm = self.lcm[laser-1]
            if isinstance(lcm, LaserCurrentModel) and lcm.cluster_analyzer.mode_boundaries is not None:
                results.append(65536.0 * lcm.cluster_analyzer.mode_boundaries)
            else:
                results.append(None)
        return results

    def get_optimize_levels_flags(self):
        """Get a list of four booleans indicating if a particular laser
        current waveform is a simple ramp (optimize levels flag is False)
        or if the current generator levels are adjusted using the currents
        at the times of the successful ringdowns (optimize levels flag is
        True)"""
        return self.get_lcm_param('optimize_levels')

    def get_sawtooth_scheme(self, laser):
        """Retrieve the center laser currents, FSR offsets and dwells for the
        specified laser"""
        lcm = self.lcm[laser-1]
        return dict(centers=lcm.centers, offsets=lcm.offsets, dwells=lcm.dwells)

    def get_sawtooth_size(self):
        """Get a list of the sizes of the sawteeth for each of the four lasers
        specified as fraction of the mode separation. The list entry is None if
        the laser is not used."""
        return self.get_lcm_param('sawtooth_size')

    def get_slope_factor(self):
        """Get a list of the slope factors for each of the four lasers. The slope
        factor specifies how the waveform transitions from one level to the next.
        The list entry is None if the laser is not used."""
        return self.get_lcm_param('slope_factor')

    def get_time_between_steps(self):
        """Get a list of the times (in units of 10us) between the waveform levels
        of the laser current generator for each of the four lasers.  The list entry
        is None if the laser is not used."""
        return self.get_lcm_param('time_between_steps')

    def get_window(self):
        """Get the window limits for all the lasers. The result is a list of four
        windows one for each laser, where a window is a two-element list containing
        the lower and upper limits, or is None, if the laser is not used."""
        return self.get_lcm_param('window')

    def set_lcm_param(self, name, value, lasers=None):
        if lasers is None:
            lasers = [1, 2, 3, 4]
        elif not hasattr(lasers, '__iter__'):  # If there is only one laser specified
            lasers = [lasers]
        for laser in lasers:
            lcm = self.lcm[laser-1]
            if isinstance(lcm, LaserCurrentModel):
                setattr(lcm, name, deepcopy(value))

    def reset_waveform(self, lasers=None):
        """Reset the fine laser current waveform to a linear ramp between the
        window limits for the specified laser or list of lasers. The resetting
        takes place at the earliest opportunity"""
        self.set_lcm_param('reset_flag', True, lasers)

    def set_approx_mode_separation(self, mode_sep, lasers=None):
        """Set the approximate cavity mode separation expressed in digitizer
        units of fine laser current for the specified laser or list of lasers"""
        self.set_lcm_param('approx_mode_separation', mode_sep, lasers)

    def set_batch_size(self, size, lasers=None):
        """Set the batch size, i.e., the number of ringdowns between
        updates of the waveform generator for the specified laser or
        list of lasers"""
        self.set_lcm_param('batch_size', size, lasers)

    def set_mode(self, mode, lasers=None):
        """Set waveform generator to "staircase" or "sawtooth" mode for
        the specified laser or list of lasers"""
        self.set_lcm_param('mode', mode, lasers)

    def set_optimize_levels_flags(self, flag, lasers=None):
        """Turn on or off the optimization of waveform generator levels
        for the specified laser or list of lasers. If the flag is False
        fo some laser, the generator ramps linearly between the limits
        of the window. When set to True, the optimization and update
        of the waveform generator occurs after pocessing "batch_size"
        ringdowns"""
        self.set_lcm_param('optimize_levels', flag, lasers)

    def set_sawtooth_size(self, tooth_size, lasers=None):
        """Set the tooth size (in fractions of the cavity mode spacing) for
        the laser current sweep as it transitions through a level when the
        generator is in sawtooth mode. This is applied to the laser or list
        of lasers specified. A value of 0.25 leads to a linear ramp for
        equally spaced levels"""
        if tooth_size < 0 or tooth_size > 1.0:
            raise ValueError("Sawtooth size should lie between 0.0 and 1.0")
        self.set_lcm_param('sawtooth_size', tooth_size, lasers)

    def set_slope_factor(self, slope_factor, lasers=None):
        """Adjusts the shape of the transition between levels for the laser or list
        of lasers specified. This is used primarily for staircase mode. A slope factor
        of 0.5 corresponds to a linear transition between levels, whereas smaller
        values of the slope factor leads to a reduced slope of transition through
        each level"""
        if slope_factor < 0 or slope_factor > 0.5:
            raise ValueError("Slope factor should lie between 0.0 and 0.5")
        self.set_lcm_param('slope_factor', slope_factor, lasers)

    def set_time_between_steps(self, interval, lasers=None):
        """Sets the time (in units of 10us) for the interval between one level and the
        next for the laser or list of lasers specified. This applies on the next update
        of the waveform generator for the specified lasers"""
        if interval <= 0:
            raise ValueError("Time between steps must be positive")
        self.set_lcm_param('time_between_steps', interval, lasers)

    def set_window(self, window, lasers=None):
        """Set the window limits for the laser of list of laser specified. The window
        must be a tuple or list of two integers, the values of the laser current at
        the lower and upper limits of the wondow."""
        self.set_lcm_param('window', window, lasers)

    def modify_sawtooth_scheme(self, laser, centers=None, offsets=None, dwells=None):
        """Modify the sawtooth scheme for a single laser by specifying a list of
        currents (centers) near to the peaks around which more ringdowns are to be
        collected. Both offsets and dwells are lists containing as many lists as there
        are peaks. Offsets specifies the list of integer mode offsets relative to the
        peak and dwells specify the number of ringdowns desired at these offsets.
        """
        lcm = self.lcm[laser-1]
        if centers is None:
            centers = lcm.centers
        else:
            centers = deepcopy(centers)
        if offsets is None:
            offsets = lcm.offsets
        else:
            offsets = deepcopy(offsets)
        if dwells is None:
            dwells = lcm.dwells
        else:
            dwells = deepcopy(dwells)
        # Check compatibility between dwells and offsets
        if len(offsets) != len(dwells):
            raise ValueError("Lengths of offsets and dwells lists should be equal")
        for pk_offsets, pk_dwells in zip(offsets, dwells):
            if len(pk_offsets) != len(pk_dwells):
                raise ValueError("Inconsistent number of elements for offsets and dwells")
        # Check compatibility of centers
        if (len(centers) > 0) and (len(centers) != len(offsets)):
            raise ValueError("Number of peak centers specified is incompatible with offsets and dwells")
        lcm.centers = centers
        lcm.offsets = offsets
        lcm.dwells = dwells

    def start_rpc_server(self):
        self.rpc_server = CmdFIFO.CmdFIFOServer(("", RPC_PORT_FSR_HOPPING_CONTROLLER),
                                        ServerName = APP_NAME,
                                        ServerDescription = "FSR Hopping controller",
                                        ServerVersion = APP_VERSION,
                                        threaded = True)
        self.rpc_thread = Thread(target=self.rpc_server.serve_forever)
        self.register_rpc()
        self.rpc_thread.setDaemon(True)
        self.rpc_thread.start()

    def register_rpc(self):
        self.rpc_server.register_function(self.get_approx_mode_separation)
        self.rpc_server.register_function(self.get_batch_size)
        self.rpc_server.register_function(self.get_mode)
        self.rpc_server.register_function(self.get_mode_boundaries)
        self.rpc_server.register_function(self.get_optimize_levels_flags)
        self.rpc_server.register_function(self.get_sawtooth_size)
        self.rpc_server.register_function(self.get_sawtooth_scheme)
        self.rpc_server.register_function(self.get_slope_factor)
        self.rpc_server.register_function(self.get_time_between_steps)
        self.rpc_server.register_function(self.get_window)
        self.rpc_server.register_function(self.modify_sawtooth_scheme)
        self.rpc_server.register_function(self.reset_waveform)
        self.rpc_server.register_function(self.set_approx_mode_separation)
        self.rpc_server.register_function(self.set_batch_size)
        self.rpc_server.register_function(self.set_mode)
        self.rpc_server.register_function(self.set_optimize_levels_flags)
        self.rpc_server.register_function(self.set_sawtooth_size)
        self.rpc_server.register_function(self.set_slope_factor)
        self.rpc_server.register_function(self.set_time_between_steps)
        self.rpc_server.register_function(self.set_window)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Fsr Hopping Controller")
    parser.add_argument('-c', dest='config', help='Name of configuration file',
                        default=os.path.splitext(os.path.abspath(app_path))[0] + ".ini")
    options_dict = vars(parser.parse_args())
    try:
        fhc = FsrHoppingController(options_dict)
        Log("%s started." % APP_NAME, dict(ConfigFile = options_dict['config']), Level = 0)
        fhc.main_loop()
    except Exception:
        LogExc("Unhandled exception")
    Log("Exiting program")
    time.sleep(1.0)