from math import pi, sin, cos, log, sqrt
from numpy import arange
import random

from myhdl import *

from MyHDL.Common.resolver import Resolver

def bench(fractionSize, errorMargin, nrTests=500):

    """ Test bench for Resolver.

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
    x0 = Signal(intbv(0, min=-M/2, max=M/2-1))
    y0 = Signal(intbv(0, min=-M/2, max=M/2-1))
    z0 = Signal(intbv(0, min=0, max=M-1))
    r0 = Signal(intbv(0, min=0, max=M/2-1))
    done = Signal(False)
    start = Signal(False)
    clock = Signal(bool(0))
    reset = Signal(True)

    # angle input bit width
    W = len(z0)
    N = W-2

    # calculate gain
    An = 1.0
    for i in range(N):
        An *= (sqrt(1.0 + 2**(-2*i)))
    print "Gain = %f" % (An,)

    # design under test
    dut = Resolver(x0, y0, done, r0, z0, start, clock, reset)

    # clock generator
    @always(delay(10))
    def clockgen():
        clock.next = not clock

    # test vector setup
    testAngles = [0.0, pi/4, pi/2, 3*pi/4, pi, 5*pi/4, 3*pi/2, 7*pi/4]
    testAngles.extend([random.uniform(0, 2*pi) for i in range(nrTests)])
    rList = [random.uniform(0,int(M/(2*An)-1)) for a in testAngles]

    testAngles = arange(0,2*pi,2*pi/nrTests)
    rList = [int(M/(2*An)-2) for a in testAngles]
    
    # actual test
    @instance
    def check():
        yield clock.negedge
        reset.next = False
        errtot = 0
        for z,r in zip(testAngles,rList):
            yield clock.negedge
            r0.next = int(r)
            z0.next = int(round(M*(z/(2*pi))))
            start.next = True
            yield clock.negedge
            start.next = False
            yield done.posedge
            exp_x0 = int(round(cos(z)*int(r)*An))
            exp_y0 = int(round(sin(z)*int(r)*An))
            assert abs(x0 - exp_x0) < D
            assert abs(y0 - exp_y0) < D
            errtot += abs(x0 - exp_x0) + abs(y0 - exp_y0)
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


