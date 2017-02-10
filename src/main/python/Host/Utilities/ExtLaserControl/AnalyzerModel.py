from Host.autogen import interface
from Host.Common import CmdFIFO, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_RDRESULTS, RPC_PORT_DRIVER
import numpy as np
from Queue import Empty, Queue
import sys
import time

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    "setup_extended_current", IsDontCareConnection = False)

# This file performs communication with the analyzer

class AnalyzerModel(object):
    def __init__(self, laser_current_models):
        self.rd_queue = Queue(1000)
        self.rd_listener = Listener.Listener(self.rd_queue,
                                             BROADCAST_PORT_RDRESULTS,
                                             interface.RingdownEntryType,
                                             retry = True,
                                             name = "Ringdown listener")

        qrange = np.linspace(0,200,51)
        lrange = np.linspace(50,150,51)
        self.qq, self.ll = np.meshgrid(qrange, lrange)
        self.merit = [np.zeros_like(self.qq)+1j*np.zeros_like(self.qq) for i in range(4)]
        self.lcm = laser_current_models

    def update_merit(self, actual_laser, fine_current):
        merit = np.exp(2j * np.pi * (self.qq * fine_current + self.ll) * fine_current)
        relax = 1.0 / self.lcm[actual_laser - 1].binning_rd
        self.merit[actual_laser - 1] = (1.0 - relax) * self.merit[actual_laser - 1] + relax * merit

    def find_optimal_model(self, actual_laser):
        lcm = self.lcm[actual_laser - 1]
        if lcm is not None:
            merit = self.merit[actual_laser - 1]
            # Find maximum absolute value of merit function
            best = np.unravel_index(np.abs(merit).argmax(), merit.shape)
            phase = np.angle(merit[best])
            coeffs = np.array([self.qq[best], self.ll[best], -phase / (2.0 * np.pi)])
            # We adjust the coefficient of the constant term by an integer to best fit the
            #  relationship between average current and fsr index
            fsr_indices = lcm.fsr_stats.keys()
            if fsr_indices:
                fine_currents = [(lcm.fsr_stats[index].average - 32768.0) / 65536.0 for index in fsr_indices]
                adjust = np.asarray(fsr_indices) - np.polyval(coeffs, fine_currents)
                print adjust
                coeffs[-1] += np.median(np.round(adjust))
            self.lcm[actual_laser - 1].coeffs = coeffs

    def process_ringdowns(self):
        while not self.rd_queue.empty():
            datum = self.rd_queue.get(False)
            actual_laser = 1 + (datum.laserUsed & 0x3)
            lcm = self.lcm[actual_laser - 1]  # Laser control model
            coeffs = lcm.coeffs  # Coefficients of current->freq transformation
            fsr_stats = lcm.fsr_stats  # Laser current statistics by FSR index
            if (datum.fineLaserCurrent <= lcm.upper_window and
                datum.fineLaserCurrent >= lcm.lower_window):
                fine_current = (datum.fineLaserCurrent - 32768.0) / 65536.0
                self.update_merit(actual_laser, fine_current)
                # Allocate the ringdown to an fsr index, based on the current
                #  coefficients
                if coeffs is not None:
                    fsr_index = np.polyval(coeffs, fine_current)
                    fsr_index_int = int(round(fsr_index))
                    lcm.update_fsr_stats(fsr_index_int, datum.fineLaserCurrent)

    def setup_current_gen(self, levels, alpha=0.5, actual_laser=1, bank=0, step_samples=500, 
        lower_window=None, upper_window=None):
        assert len(levels) <= 0x200
        Driver.wrRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, levels)
        # print Driver.rdRingdownMem(0x8000 + (actual_laser - 1) * 0x1000 + bank * 0x200, len(levels))
        if lower_window is None: 
            lower_window = max(0, min(levels) - 400)
        if upper_window is None: 
            upper_window = max(65535, max(levels) + 400)
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
        control = ((1 << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_MODE_B) |
                   ((actual_laser - 1) << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_LASER_SELECT_B) |
                   (bank << interface.LASERCURRENTGENERATOR_CONTROL_STATUS_BANK_SELECT_B))
        Driver.wrFPGA("FPGA_LASERCURRENTGENERATOR","LASERCURRENTGENERATOR_CONTROL_STATUS", control)

    def process_task(self):
        self.process_ringdowns()
        for l in range(4):
            laser_num = l + 1
            self.find_optimal_model(l + 1)
            lcm = self.lcm[l]
            if lcm is not None:
                in_window = lambda x : (x >= lcm.lower_window) and (x <= lcm.upper_window)
                print "Laser %d" % (laser_num, )
                print lcm.coeffs
                print lcm.fsr_stats
                # Update the list of levels in the laser current model
                # We find the minimum and maximum FSR index in fsr_stats
                #  and extend by two FSR on each side. These currents corresponding
                #  to these indices are then filtered so that at most one current
                #  is below the lower window and at most one is above the upper window.
                fsr_indices = lcm.fsr_stats.keys()
                # In order to calculate the currents corresponding to indices, we
                #  use the averages in fsr_stats, if possible. However, if an index
                #  is not a key in fsr_stats, a polynomial fit to the averages is
                #  used for interpolation and extrapolation
                if fsr_indices:
                    pfit = np.polyfit(fsr_indices, [lcm.fsr_stats[i].average for i in fsr_indices], 4)
                    imin, imax = min(fsr_indices), max(fsr_indices)
                    indices = range(imin - 3, imax + 4)
                    levels = []
                    for i in indices:
                        if i in fsr_indices:
                            levels.append(lcm.fsr_stats[i].average)
                        else:
                            levels.append(np.polyval(pfit, i))
                    filt_levels = []
                    for i, level in enumerate(levels):
                        if (in_window(level) or
                            (i < len(levels) - 1 and in_window(levels[i + 1])) or
                            (i >= 1 and in_window(levels[i - 1]))):
                            filt_levels.append(int(round(level)))
                    #filt_levels = filt_levels[0::2] + filt_levels[1::2]
                    #n = len(filt_levels)
                    #filt_levels = (filt_levels +
                    #               filt_levels[n//2-1:n//2+2] +
                    #               filt_levels[n//2-1:n//2+2] +
                    #               filt_levels[n//2-1:n//2+2] +
                    #               filt_levels[n//2-1:n//2+2])
                    if lcm.update_levels:
                        lcm.set("levels", filt_levels)
                    if lcm.update_waveform:
                        self.setup_current_gen(lcm.levels, lcm.slope_factor,
                                               laser_num, step_samples=lcm.time_between_steps,
                                               lower_window=lcm.lower_window, 
                                               upper_window=lcm.upper_window)
                    # Remove one sample from each bin, so as to expire old data
                    for index in lcm.fsr_stats.keys():
                        stats = lcm.fsr_stats[index]
                        if stats.num_samples <= 1:
                            del lcm.fsr_stats[index]
                        else:
                            lcm.fsr_stats[index].num_samples -= 1
