from math import pi, sin, cos, log
from numpy import arange
import random

from myhdl import *

from MyHDL.Common.SineComputer import SineComputer

def bench(fractionSize, errorMargin, nrTests=500):

    """ Test bench for SineComputer.

    fractionSize: number of bits after the point
    errorMargin: margin for rounding errors on result
    nrTests: number of tests vectors

    """

    # scaling factor to represent floats as integers
    M = 2**fractionSize

    # error margin shorthand
    D = errorMargin

    # signals
    #cos_z0 = Signal(intbv(0, min=-D, max=M+D))
    #sin_z0 = Signal(intbv(0, min=-M-D, max=M+D))
    cos_z0 = Signal(intbv(0, min=-M/2, max=M/2-1))
    sin_z0 = Signal(intbv(0, min=-M/2, max=M/2-1))
    z0 = Signal(intbv(0, min=0, max=M-1))
    done = Signal(False)
    start = Signal(False)
    clock = Signal(bool(0))
    reset = Signal(True)

    # design under test
    dut = SineComputer(cos_z0, sin_z0, done, z0, start, clock, reset)

    # clock generator
    @always(delay(10))
    def clockgen():
        clock.next = not clock

    # test vector setup
    testAngles = [0.0, pi/4, pi/2, 3*pi/4, pi, 5*pi/4, 3*pi/2, 7*pi/4]
    testAngles.extend([random.uniform(0, 2*pi) for i in range(nrTests)])
    testAngles = arange(0,2*pi,2*pi/nrTests)

    # actual test
    @instance
    def check():
        yield clock.negedge
        reset.next = False
        errtot = 0
        for z in testAngles:
            yield clock.negedge
            z0.next = int(round(M*(z/(2*pi))))
            start.next = True
            yield clock.negedge
            start.next = False
            yield done.posedge
            exp_cos_z0 = int(round(cos(z)*M/2))
            exp_sin_z0 = int(round(sin(z)*M/2))
            assert abs(cos_z0 - exp_cos_z0) < D
            assert abs(sin_z0 - exp_sin_z0) < D
            errtot += abs(cos_z0 - exp_cos_z0) + abs(sin_z0 - exp_sin_z0)
        print errtot
        raise StopSimulation

    return dut, clockgen, check

def test_bench():
    fractionSize = 16
    errorMargin = fractionSize
#    tb = bench(fractionSize, errorMargin)
#    sim = Simulation(tb)
    sim = Simulation(traceSignals(bench,fractionSize, errorMargin))
    sim.run(quiet=1)

if __name__ == "__main__":
    test_bench()


