import matplotlib.pyplot as plt
from Host.autogen import interface
from Host.Common import CmdFIFO, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_RDRESULTS, RPC_PORT_DRIVER
import numpy as np
from Queue import Empty, Queue
from scipy.optimize import minimize
import sys
import time

# This version specifies a sequence ID

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    "setup_extended_current", IsDontCareConnection = False)
rd_queue = Queue(1000)
rdListener = Listener.Listener(rd_queue,
                            BROADCAST_PORT_RDRESULTS,
                            interface.RingdownEntryType,
                            retry = True,
                            name = "Ringdown listener")


def setup_current_gen(levels, alpha=0.5, actual_laser=1, bank=0, step_samples=600, 
    lower_window=43000, upper_window=53000, sequence_id=0):
    assert len(levels) <= 0x200

    Driver.wrRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, levels)
    Driver.rdRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, len(levels))

    period = len(levels)
    M = 1 << interface.LASER_CURRENT_GEN_ACC_WIDTH
    T = step_samples
    slow_slope = int(round((M / T) * alpha / (1 - alpha)))
    fast_slope = int(round((M / T) * (1 - alpha) / alpha))
    first_offset = int(round(M * (2 * alpha - 1) / (2 * alpha))) % M
    second_offset = int(round(M * (2 * alpha - 1) / (alpha - 1)))
    first_breakpoint = int(np.ceil((1 - alpha) * T / 2))
    second_breakpoint = int(np.ceil((1 + alpha) * T / 2))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SLOW_SLOPE", slow_slope)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FAST_SLOPE", fast_slope)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FIRST_OFFSET", first_offset)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SECOND_OFFSET", second_offset)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_FIRST_BREAKPOINT", first_breakpoint)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SECOND_BREAKPOINT", second_breakpoint)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_TRANSITION_COUNTER_LIMIT", step_samples)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_PERIOD_COUNTER_LIMIT", period)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_LOWER_WINDOW", lower_window)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_UPPER_WINDOW", upper_window)
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_SEQUENCE_ID", sequence_id)
    control = ((1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B) |
               ((actual_laser - 1) << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B) |
               (bank << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B))
    Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS", control)
    # Wait until the parameters have been loaded for the particular laser
    while (Driver.rdFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS") &
           (1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B)):
        time.sleep(0.01)

class ClusterAnalysis(object):
    """Perform clustering of data in the range [0,1] using kernel density estimation with a Gaussian kernel
        of standard deviation sigma and an auxiliary array of size nbins for accumulating the probability
        density estimate"""
    def __init__(self, sigma, nbins):
        # The kernel is evaluated once on an array of size 2*nbins
        self.nbins = nbins
        self.sigma = sigma
        self.base = (np.arange(2*nbins) - nbins)/float(nbins)
        self.kernel = np.exp(-0.5*(self.base/self.sigma)**2)

    def cluster(self, values):
        """values is an array containing the data to cluster. Each value must be in the range [0,1]"""
        self.density = np.zeros(self.nbins, dtype=float)
        self.values = values
        for value in values:
            index = int(nbins*value + 0.5)
            self.density += self.kernel[nbins-index:2*nbins-index]
        # Find strict local minima. Note that the indices are shifted by 1 by the slicing, so
        #  we take this into account when converting back to normalized values
        min_indices = ((self.density[1:-1] < self.density[:-2]) & (self.density[1:-1] < self.density[2:]))
        bins = (1 + np.flatnonzero(min_indices)) / float(self.nbins)
        # Use digitize to classify values into clusters using the minima in the density estimate as
        #  the bin boundaries
        self.bin_indices = np.digitize(values, bins=bins)
        # Find means and number of values in each bin. Use NaN to indicate the absence of data.
        self.bin_sums = np.zeros(len(bins)+1, dtype=float)
        self.bin_sum_sq = np.zeros(len(bins)+1, dtype=float)
        self.bin_counts = np.zeros(len(bins)+1)
        for b,v in zip(self.bin_indices, values):
            self.bin_sums[b] += v
            self.bin_sum_sq[b] += v*v
            self.bin_counts[b] += 1
        self.bin_means = np.zeros(len(bins)+1, dtype=float)
        self.bin_std = np.zeros(len(bins)+1, dtype=float)
        for i in range(len(self.bin_counts)):
            if self.bin_counts[i] > 0:
                self.bin_means[i] = self.bin_sums[i] / self.bin_counts[i]
                self.bin_std[i] = np.sqrt(self.bin_sum_sq[i] / self.bin_counts[i] - self.bin_means[i]**2)
            else:
                self.bin_means[i] = np.nan
                self.bin_std[i] = np.nan
        self.bin_boundaries = bins
        
    def assign_modes(self, lrange, qrange=None):
        """After clustering, we need to assign integer mode numbers to each bin by fitting a quadratic
        polynomial to the mapping between bin means and mode number and optimizing the polynomial so 
        that the results at the bin means are as close to integers as possible. More specifically, if
        the bin means are v_k, we find coefficients A and B so that

        SUM  exp[i*2*pi*{A(v_k-0.5)^2 + B(v_k-0.5)}] has maximum magnitude
         k
        
        Note that the values v_k are shifted to the range -0.5 to 0.5, rather than 0 to 1, to improve
        numerical stability.        
        The optimization is carried out over a grid of coefficient values, and the result is further
        improved using the Nelder-Mead simplex algorithm. As a result of carrying out the optimization,
        we can determine if there are missing modes.
        """
        if qrange is None:
            qrange = np.linspace(0.0, 10.0, 40)
        
        qq, ll = np.meshgrid(qrange, lrange)
        merit = np.zeros_like(qq,dtype=complex)

        for i, value in enumerate(self.bin_means):
            if np.isnan(value):
                continue
            merit += np.exp(2j * np.pi * (qq * (value-0.5) + ll) * (value-0.5))
        # Find maximum absolute value of merit function
        best = np.unravel_index(np.abs(merit).argmax(), merit.shape)

        def ccost(params, values):
            vshifted = values - 0.5
            q, l = params
            return np.nansum(np.exp(2j * np.pi * (q * vshifted + l) * vshifted))
            
        def cost(params, values):
            vshifted = values - 0.5
            return -np.abs(ccost(params, values))

        guess = [qq[best], ll[best]]
        #res = minimize(cost, guess, args=(self.bin_means,), method='Nelder-Mead')
        #sol = res.x
        sol = guess
        
        phase = np.angle(ccost(sol, self.bin_means))
        self.coeffs = np.array([sol[0], sol[1], -phase/(2.0*np.pi)])
        self.mode_numbers = np.polyval(self.coeffs, self.bin_means - 0.5)
        print self.coeffs
        print self.mode_numbers
        
# We specify the range of laser currents defining the window of interest
upper_window = 52000
lower_window = 42000

#upper_window = 51000
#lower_window = 19000
dig_units_per_mode = 700
sigma = 100.0/65536.0
nbins = 1024

# Synthesize an initial set of levels for determining the current to mode mapping coefficients
sequence_id = 0
upper = upper_window + dig_units_per_mode
lower = lower_window - 3*dig_units_per_mode
nmodes = int(np.ceil(float(upper - lower) / dig_units_per_mode))
initialize = raw_input("Initialize levels? ")
initialize = initialize.strip()
if initialize and initialize[0].lower() in ['y']:
    levels = [int(level) for level in np.linspace(lower, upper, nmodes)]
            
    setup_current_gen(levels, alpha=0.5 , actual_laser=1, bank=0, step_samples=700, 
                      lower_window=lower_window, upper_window=upper_window, sequence_id=sequence_id)
    sequence_id += 1
ca = ClusterAnalysis(sigma, nbins)

qopt = None
lopt = None

while True:
    time.sleep(10.0)
    while not rd_queue.empty():
        try:
            rd_queue.get(False)
        except Empty:
            continue
        rd_queue.task_done()
    
    nringdown = 500
    print "Collecting data from %d ringdowns" % nringdown
    values = []
    count = 0
    while True:
        try:
            datum = rd_queue.get(False)
            value = datum.fineLaserCurrent/65536.0
            values.append(value)
            count += 1
            if count % 50 == 0:
                sys.stdout.write('.')
            if count > nringdown:
                break
        except Empty:
            time.sleep(0.5)
    ca.cluster(values)
    avg_slope = (len(ca.bin_means)-1)/(ca.bin_means[-1]-ca.bin_means[0])
    if qopt is None:
        lrange = np.linspace(0.8*avg_slope,1.2*avg_slope,10)
        qrange = np.linspace(0.0, 10.0, 10)
    else:
        lrange = np.linspace(0.9*lopt,1.1*lopt,10)
        qrange = np.linspace(0.9*qopt,1.1*qopt,10)
    
    ca.assign_modes(lrange, qrange)
    qopt, lopt, _ = ca.coeffs
    
    mean_fine_currents = 65536.0 * ca.bin_means
    mode_numbers = np.array(np.round(ca.mode_numbers), dtype=int)
    
    mode_numbers = np.arange(len(ca.bin_means))
    # Find the levels between lower and upper corresponding to the modes
    pfit = np.polyfit(mode_numbers[~np.isnan(ca.bin_means)], mean_fine_currents[~np.isnan(ca.bin_means)], 3)
    
    slopes = {}
    bin_by_mode = {}
    for i, mode in enumerate(mode_numbers):
        slopes[mode] = np.polyval(np.polyder(pfit), mode)
        bin_by_mode[mode] = i
        print "%3d: %7.0f %7.0f (%4d) %7.0f" % (mode, 65536.0*ca.bin_means[i], 65536.0*ca.bin_std[i], 
                                                ca.bin_counts[i], slopes[mode])
                                                
    mode_min, mode_max = min(mode_numbers), max(mode_numbers)
    fsr_currents = []
    fsr_slopes = []
    for mode in range(mode_min-10, mode_max+10):
        if mode in mode_numbers and not np.isnan(ca.bin_means[bin_by_mode[mode]]):
            fsr_currents.append(int(round(ca.bin_means[bin_by_mode[mode]] * 65536.0)))
        else:
            fsr_currents.append(int(round(np.polyval(pfit, mode))))
        fsr_slopes.append(np.polyval(np.polyder(pfit),mode))

    fsr_currents = np.asarray(fsr_currents)
    peak_pos = [23250, 47200]
    peak_indices = [np.argmin(abs(fsr_currents - pk)) for pk in peak_pos]
    offsets = [[-2,-1,0,1,2,3], [-1,0,1]]
    dwells = [[3,3,6,6,3,3], [3,6,3]]
    #dwells = [[4,4,8,8,4,4], [4,8,4]]
    #dwells = [[5,5,10,10,5,5], [5,10,5]]
    #dwells = [[10,10,20,20,10,10], [5,10,5]]
    
    levels = []
    #offset = [-23, -22, -21, -20, -19, -18, -1, 0, 1]
    #dwells = [2,2,2,2,2,2,2, 2, 2]
    #dwells = [3,3,3,3,3,3,3, 6, 3, 3, 8, 3, 8]
    #dwells = [5,5,10,10,5,5, 5, 10, 5]
    #dwells = [10,10,20,20,10,10, 10, 20, 10]
    #offset = [-1,0,1]
    #dwells = [2,4,2]
    
    for i, (slope, current) in enumerate(zip(fsr_slopes, fsr_currents)):
        dwell = 1
        if not (lower <= current < upper):
            continue
        for j, pk in enumerate(peak_indices):
            try:
                idx = offsets[j].index(i-pk)
                dwell = dwells[j][idx]
            except ValueError:
                pass
        for j in range(dwell):
            levels.append(int(current - 0.1*slope))
            levels.append(int(current + 0.1*slope))
    
    print "Number of levels: ", len(levels), " Sequence ID: ", sequence_id
    setup_current_gen(levels, alpha=0.5 , actual_laser=1, bank=0, step_samples=500,
                      lower_window=lower_window, upper_window=upper_window, sequence_id=sequence_id)
    sequence_id += 1
