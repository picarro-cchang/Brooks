from math import pi, sin, cos, log, sqrt
from numpy import arange
import random
from Host.autogen.interface import FPGA_REG_WIDTH

from myhdl import *
from MyHDL.Common.resolver import Resolver
from MyHDL.Common.Divider import Divider

LOW, HIGH = bool(0), bool(1)
mod = (1<<FPGA_REG_WIDTH)

def add_sim(x,y):
    return (x+y) % mod

def sub_sim(x,y):
    return (x-y) % mod

def div_sim(x,y):
    x = x % mod
    y = y % mod
    return x*(mod//2)//y

def signed_mul_sim(x,y):
    x = x % mod
    if x>mod//2: x -= mod
    y = y % mod
    if y>mod//2: y -= mod
    maxMag = float(mod//2)
    p = int(((x/maxMag)*(y/maxMag))*maxMag)
    if p<0: p += mod
    return p

def bench(fractionSize, errorMargin, nrTests=500):

    """ Test bench for use of Resolver in Fresnel formula
    for a FP etalon

    fractionSize: number of bits after the point
    errorMargin: margin for rounding errors on result
    nrTests: number of tests vectors

    """

    F = 1.2         # Finesse of etalon
    b = F/(F+2.0)   # Desired transmission is T = b/(1-b*cos(delta))
    print b
    
    # scaling factor to represent floats as integers
    M = 2**fractionSize
    M2 = M//2
    M4 = M//4
    
    num = int((1-b)*M)
    
    # error margin shorthand
    D = errorMargin

    # signals
    #cos_z0 = Signal(intbv(0, min=-D, max=M+D))
    #sin_z0 = Signal(intbv(0, min=-M-D, max=M+D))
    x0 = Signal(intbv(0, min=-M2, max=M2-1))
    y0 = Signal(intbv(0, min=-M2, max=M2-1))
    z0 = Signal(intbv(0, min=0, max=M-1))
    r0 = Signal(intbv(0, min=0, max=M2-1))
    xu = Signal(intbv(0, min=0, max=M-1))
    yu = Signal(intbv(0, min=0, max=M-1))
    div_num, div_den, div_quot = [Signal(intbv(0)[FPGA_REG_WIDTH:]) for i in range(3)]
    div_rfd, div_ce = [Signal(LOW) for i in range(2)]
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
    divider = Divider(clk=clock, reset=reset, N_in=div_num, D_in=div_den, Q_out=div_quot,
                      rfd_out=div_rfd, ce_in=div_ce, width=FPGA_REG_WIDTH)

    # clock generator
    @always(delay(10))
    def clockgen():
        clock.next = not clock

    # test vector setup
    #testAngles = [0.0, pi/4, pi/2, 3*pi/4, pi, 5*pi/4, 3*pi/2, 7*pi/4]
    #testAngles.extend([random.uniform(0, 2*pi) for i in range(nrTests)])
    #rList = [random.uniform(0,int(M/(2*An)-1)) for a in testAngles]

    testAngles = arange(0,2*pi,2*pi/nrTests)
    rList = [int(M2*b/An) for a in testAngles]
    
    @always_comb
    def logic1():
        xu.next = M2 + x0
        yu.next = M2 + y0
        
    @always_comb
    def logic2():
        div_num.next = num
        div_den.next = xu
        div_ce.next = done
        
    # actual test
    @instance
    def check():
        yield clock.negedge
        reset.next = False
        errtot = 0
        for z,r in zip(testAngles,rList):
            yield clock.negedge
            r0.next = int(r)
            z0.next = int(round(M2*z/pi))
            start.next = True
            yield clock.negedge
            start.next = False
            yield div_rfd.posedge
            exp_x0 = int(round(cos(z)*int(r)*An))
            exp_y0 = int(round(sin(z)*int(r)*An))
            assert abs(x0 - exp_x0) < D
            assert abs(y0 - exp_y0) < D
            errtot += abs(x0 - exp_x0) + abs(y0 - exp_y0)
        print errtot
        raise StopSimulation

    return instances()

def test_bench():
    fractionSize = 16
    errorMargin = fractionSize
#    tb = bench(fractionSize, errorMargin)
#    sim = Simulation(tb)
    sim = Simulation(traceSignals(bench,fractionSize, errorMargin))
    sim.run(quiet=1)

if __name__ == "__main__":
    test_bench()


