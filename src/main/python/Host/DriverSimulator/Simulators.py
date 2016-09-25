#!/usr/bin/python
#
"""
File Name: Simulators.py
Purpose: Simulators for analyzer components

File History:
    19-Sep-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)


class LaserSimulator(object):
    # This code simulates the behavior of a laser
    #
    # The default parameters are based on the following model implemented in the FPGA
    # When 5*coarse + fine changes by 65536, the laser frequency changes by 
    #  one FSR of the wavelength monitor or 50GHz (1.66782 wavenumbers)
    # The sensitivity of the laser frequency to current is thus -1.0596 GHz/mA
    #  or -0.035344 wavenumber/mA
    #
    # When 18*laserTemp(in millidegrees) changes by 65536, the laser frequency
    #  changes by 50GHz. The sensitivity of the laser frequency to current is 
    #  thus -13.7329 GHz/degree or -0.45808 wavenumber/degree
    #
    # The nominal frequency of the laser is attained at a laser current of 150mA
    #  and a laser temperature of 25 degC
    def __init__(self, nominal_wn = 6237.0, temp_sens = -0.45808, current_sens = -0.035344):
        self.nominal_wn = nominal_wn
        self.temp_sens = temp_sens
        self.current_sens = current_sens

    def wavenum(self, temp, current):
        return self.nominal_wn + self.temp_sens * (temp - 25.0) + self.current_sens * (current - 150.0)

class LaserDacModel(object):
    # The relationship between laser current DACs and laser current in mA is
    #
    # current = 0.00036 * (10*coarse + 2*fine)
    # Thus for coarse = 36000 and fine = 32768, we have a current of 153.193 mA
    #  1mA of current change results from changing the coarse value by 277.78 digU
    #  or the fine value by 1388,89 digU
    def __init__(self, coarse_sens = 0.0036, fine_sens = 0.00072, offset = 0):
        self.coarse_sens = coarse_sens
        self.fine_sens = fine_sens
        self.offset = offset

    def current_from_dac(self, coarse, fine):
        return self.offset + self.coarse_sens * coarse + self.fine_sens * fine

class InjectionSimulator(object):
    pass

class WlmModel(object):
    # This code simulates the behavior of the wavelength monitor. The wavelength monitor
    #  angle is theta and the etalon reflectivity factor is rho.
    # eta1 = rho * Ieta1 * (1 + cos(theta)) / (1 + rho * cos(theta)) + eta1_offset
    # ref1 = Iref1 * (1 - rho)/ (1 + rho * cos(theta)) + ref1_offset
    # eta2 = rho * Ieta2 * (1 + sin(theta + epsilon)) / (1 + rho * sin(theta + epsilon)) + eta2_offset
    # ref2 = Iref2 * (1 - rho)/ (1 + rho * sin(theta + epsilon)) + ref2_offset
    pass